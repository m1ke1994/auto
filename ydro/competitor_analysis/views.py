from __future__ import annotations

import logging
from urllib.parse import quote

from celery import current_app
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.models import Site
from clients.models import Client
from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.security import DomainValidationError, normalize_public_domain
from competitor_analysis.serializers import CompetitorAnalysisCreateSerializer, CompetitorAnalysisSerializer

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {
    CompetitorAnalysis.Status.PENDING,
    CompetitorAnalysis.Status.RUNNING,
    "processing",
}


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
        return CompetitorAnalysis.objects.filter(site=site, client=client).order_by("-created_at")

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

        try:
            normalize_public_domain(site.domain, resolve_dns=False)
        except DomainValidationError as exc:
            return Response({"ok": False, "detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CompetitorAnalysisCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analysis = CompetitorAnalysis.objects.create(
            site=site,
            client=client,
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
        if not analysis.pdf_file:
            return Response({"ok": False, "detail": "PDF ещё не сформирован."}, status=status.HTTP_404_NOT_FOUND)

        try:
            with analysis.pdf_file.open("rb") as file_obj:
                pdf_bytes = file_obj.read()
        except FileNotFoundError:
            return Response({"ok": False, "detail": "PDF-файл не найден."}, status=status.HTTP_404_NOT_FOUND)

        filename = analysis.pdf_file.name.rsplit("/", 1)[-1] or f"competitor-analysis-{analysis.id}.pdf"
        quoted_filename = quote(filename)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted_filename}"
        response["Cache-Control"] = "no-store"
        return response
