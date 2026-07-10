from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.models import Site
from subscriptions.access import FEATURE_AI_RECOMMENDATIONS
from subscriptions.permissions import HasFeatureAccess

from ai_recommendations.client import AIRecommendationsClient, AIServiceError
from ai_recommendations.models import AIRecommendationJob
from ai_recommendations.payload import build_payload
from ai_recommendations.serializers import AIRecommendationCreateSerializer, AIRecommendationJobSerializer
from ai_recommendations.tasks import sync_job


class HasAIRecommendationsAccess(HasFeatureAccess):
    message = "AI-рекомендации недоступны на текущем тарифе."


class BaseView(APIView):
    permission_classes = (permissions.IsAuthenticated, HasAIRecommendationsAccess)
    required_feature = FEATURE_AI_RECOMMENDATIONS

    def jobs(self):
        queryset = AIRecommendationJob.objects.filter(user=self.request.user, site__owner=self.request.user, deleted_at__isnull=True, platform_hidden_at__isnull=True)
        return queryset


class JobListCreateView(BaseView):
    def get(self, request): return Response(AIRecommendationJobSerializer(self.jobs(), many=True).data)

    def post(self, request):
        if not settings.AI_RECOMMENDATIONS_ENABLED: return Response({"detail": "AI-рекомендации отключены."}, status=503)
        serializer = AIRecommendationCreateSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        site = Site.objects.filter(id=serializer.validated_data["site_id"], owner=request.user, is_active=True).first()
        if not site: return Response({"detail": "Сайт не найден."}, status=404)
        job = AIRecommendationJob.objects.create(site=site, user=request.user, recommendation_type=serializer.validated_data["recommendation_type"], period_from=serializer.validated_data["period_from"], period_to=serializer.validated_data["period_to"])
        payload = build_payload(job=job); job.input_snapshot = payload; job.save(update_fields=("input_snapshot", "updated_at"))
        try:
            remote = AIRecommendationsClient().create_job(payload)
        except AIServiceError as exc:
            job.status, job.error_message = job.Status.FAILED, str(exc); job.save();
            return Response(AIRecommendationJobSerializer(job).data, status=502)
        job.remote_job_id, job.status = remote["job_id"], remote["status"]; job.save()
        sync_job.apply_async((str(job.id),), countdown=settings.AI_RECOMMENDATIONS_POLL_INTERVAL_SECONDS)
        return Response(AIRecommendationJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class JobDetailView(BaseView):
    def get_job(self, pk):
        job = self.jobs().filter(id=pk).first()
        if not job: from rest_framework.exceptions import NotFound; raise NotFound("Задание не найдено.")
        return job
    def get(self, request, pk): return Response(AIRecommendationJobSerializer(self.get_job(pk)).data)
    def delete(self, request, pk):
        job = self.get_job(pk)
        if job.remote_job_id:
            try: AIRecommendationsClient().delete_job(job.remote_job_id)
            except AIServiceError: pass
        job.deleted_at, job.status = timezone.now(), job.Status.CANCELLED; job.save(); return Response(status=204)


class JobRetryView(JobDetailView):
    def post(self, request, pk):
        job = self.get_job(pk)
        if job.status != job.Status.FAILED: return Response({"detail": "Повторить можно только задание с ошибкой."}, status=409)
        remote = AIRecommendationsClient().retry_job(job.remote_job_id)
        job.status, job.error_message, job.result = remote["status"], "", None; job.save(); sync_job.delay(str(job.id))
        return Response(AIRecommendationJobSerializer(job).data, status=202)
