from __future__ import annotations

import logging
from urllib.parse import quote

from celery import current_app
from django.core.files.storage import default_storage
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.models import Site
from clients.models import Client
from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.serializers import CompetitorAnalysisCreateSerializer, CompetitorAnalysisSerializer

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {
    CompetitorAnalysis.Status.PENDING,
    CompetitorAnalysis.Status.RUNNING,
    "processing",
}
COMPLETED_STATUSES = {
    CompetitorAnalysis.Status.COMPLETED,
    CompetitorAnalysis.Status.DONE,
}


def json_error(detail: str, http_status: int):
    return JsonResponse({"ok": False, "detail": detail}, status=http_status, json_dumps_params={"ensure_ascii": False})


class AnyAcceptRenderer(BaseRenderer):
    media_type = "*/*"
    format = "any"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return str(data).encode("utf-8")


class AdminSiteCompetitorAccessMixin:
    permission_classes = [permissions.IsAuthenticated]

    def _platform_admin(self) -> bool:
        user = self.request.user
        return bool(getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))

    def get_site(self) -> Site:
        qs = Site.objects.select_related("owner").filter(is_active=True)
        if not self._platform_admin():
            qs = qs.filter(owner=self.request.user)

        site = qs.filter(id=self.kwargs["site_id"]).first()
        if site is None:
            raise NotFound(detail="Сайт не найден.")
        return site

    def get_client_for_site(self, site: Site) -> Client:
        client = Client.objects.filter(owner=site.owner).first()
        if client is None:
            raise PermissionDenied(detail="Для владельца сайта не найден клиент.")
        if not self._platform_admin() and not client.is_active:
            raise PermissionDenied(detail="Клиент неактивен.")
        return client

    def get_queryset(self):
        site = self.get_site()
        client = self.get_client_for_site(site)
        return CompetitorAnalysis.objects.select_related("site", "client").filter(site=site, client=client).order_by("-created_at")

    def get_analysis(self) -> CompetitorAnalysis:
        analysis = self.get_queryset().filter(id=self.kwargs["analysis_id"]).first()
        if analysis is None:
            raise NotFound(detail="Анализ не найден.")
        return analysis


class CompetitorAnalysisListView(AdminSiteCompetitorAccessMixin, APIView):
    def get(self, request, site_id: int):
        rows = CompetitorAnalysisSerializer(self.get_queryset()[:30], many=True).data
        return Response({"ok": True, "rows": rows}, status=status.HTTP_200_OK)


class CompetitorAnalysisCreateView(AdminSiteCompetitorAccessMixin, APIView):
    def post(self, request, site_id: int):
        site = self.get_site()
        client = self.get_client_for_site(site)

        serializer = CompetitorAnalysisCreateSerializer(data=request.data, context={"site": site})
        serializer.is_valid(raise_exception=True)

        analysis = CompetitorAnalysis.objects.create(
            site=site,
            client=client,
            user_domain=serializer.validated_data["user_domain"],
            competitor_domain=serializer.validated_data["competitor_domain"],
            competitors=serializer.validated_data["competitors"],
            status=CompetitorAnalysis.Status.PENDING,
        )

        queued = True
        try:
            from competitor_analysis.tasks import run_competitor_analysis_task

            run_competitor_analysis_task.delay(analysis.id)
        except Exception as exc:
            queued = False
            logger.exception("Failed to enqueue competitor analysis analysis_id=%s", analysis.id)
            analysis.status = CompetitorAnalysis.Status.FAILED
            analysis.finished_at = timezone.now()
            analysis.errors = [{"error": str(exc) or "Не удалось поставить анализ в очередь."}]
            analysis.save(update_fields=["status", "finished_at", "errors", "updated_at"])

        data = CompetitorAnalysisSerializer(analysis).data
        data["ok"] = True
        data["queued"] = queued
        return Response(data, status=status.HTTP_201_CREATED)


class CompetitorAnalysisDetailView(AdminSiteCompetitorAccessMixin, APIView):
    def get(self, request, site_id: int, analysis_id: int):
        return Response(CompetitorAnalysisSerializer(self.get_analysis()).data, status=status.HTTP_200_OK)


class CompetitorAnalysisCancelView(AdminSiteCompetitorAccessMixin, APIView):
    def post(self, request, site_id: int, analysis_id: int):
        analysis = self.get_analysis()
        if analysis.status not in ACTIVE_STATUSES:
            return Response(
                {
                    "ok": True,
                    "id": analysis.id,
                    "status": analysis.status,
                    "detail": "Анализ уже завершён.",
                },
                status=status.HTTP_200_OK,
            )

        task_id = str(analysis.celery_task_id or "").strip()
        analysis.status = CompetitorAnalysis.Status.CANCELED
        analysis.finished_at = timezone.now()
        analysis.errors = [{"error": "Анализ остановлен пользователем."}]
        analysis.save(update_fields=["status", "finished_at", "errors", "updated_at"])

        revoked = False
        if task_id:
            try:
                current_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
                revoked = True
            except Exception:
                logger.exception("Failed to revoke competitor analysis task analysis_id=%s task_id=%s", analysis.id, task_id)

        data = CompetitorAnalysisSerializer(analysis).data
        data["ok"] = True
        data["revoked"] = revoked
        data["detail"] = "Анализ остановлен."
        return Response(data, status=status.HTTP_200_OK)


class CompetitorAnalysisPdfView(AdminSiteCompetitorAccessMixin, APIView):
    renderer_classes = [AnyAcceptRenderer]

    def get(self, request, site_id: int, analysis_id: int):
        analysis = self.get_analysis()
        if analysis.status not in COMPLETED_STATUSES:
            return json_error("PDF доступен только после завершения анализа.", status.HTTP_409_CONFLICT)

        pdf_name = str(getattr(analysis.pdf_file, "name", "") or "").strip()
        if not pdf_name:
            return json_error("PDF ещё не сформирован.", status.HTTP_404_NOT_FOUND)

        storage = getattr(analysis.pdf_file, "storage", None) or default_storage
        if not storage.exists(pdf_name):
            logger.warning(
                "competitor_analysis.pdf missing analysis_id=%s site_id=%s pdf_name=%s",
                analysis.id,
                analysis.site_id,
                pdf_name,
            )
            return json_error("PDF-файл отсутствует в хранилище. Запустите анализ повторно.", status.HTTP_404_NOT_FOUND)

        filename = pdf_name.rsplit("/", 1)[-1] or f"competitor-analysis-{analysis.id}.pdf"
        quoted_filename = quote(filename)
        try:
            pdf_file = storage.open(pdf_name, "rb")
        except (FileNotFoundError, OSError):
            logger.warning(
                "competitor_analysis.pdf open failed analysis_id=%s site_id=%s pdf_name=%s",
                analysis.id,
                analysis.site_id,
                pdf_name,
            )
            return json_error("PDF-файл отсутствует в хранилище. Запустите анализ повторно.", status.HTTP_404_NOT_FOUND)

        response = FileResponse(pdf_file, as_attachment=True, filename=filename, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted_filename}"
        response["Cache-Control"] = "no-store"
        return response
