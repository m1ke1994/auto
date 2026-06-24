import logging

from celery import shared_task
from django.utils import timezone

from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.services.analyzer import AnalysisCanceled, run_competitor_analysis

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="competitor_analysis.run")
def run_competitor_analysis_task(self, analysis_id: int) -> None:
    analysis = CompetitorAnalysis.objects.filter(id=analysis_id).first()
    if analysis is None:
        logger.warning("competitor_analysis.task analysis not found analysis_id=%s", analysis_id)
        return

    task_id = str(getattr(self.request, "id", "") or "")
    if analysis.status == CompetitorAnalysis.Status.CANCELED:
        logger.info("competitor_analysis.task canceled before start analysis_id=%s", analysis_id)
        return

    analysis.celery_task_id = task_id or analysis.celery_task_id
    analysis.status = CompetitorAnalysis.Status.RUNNING
    analysis.finished_at = None
    analysis.save(update_fields=["celery_task_id", "status", "finished_at", "updated_at"])

    try:
        run_competitor_analysis(analysis)
    except AnalysisCanceled:
        analysis.status = CompetitorAnalysis.Status.CANCELED
        analysis.finished_at = timezone.now()
        analysis.save(update_fields=["status", "finished_at", "updated_at"])
    except Exception as exc:
        logger.exception("competitor_analysis.task failed analysis_id=%s", analysis_id)
        analysis.refresh_from_db(fields=["status"])
        if analysis.status == CompetitorAnalysis.Status.CANCELED:
            return
        analysis.status = CompetitorAnalysis.Status.FAILED
        analysis.finished_at = timezone.now()
        analysis.errors = [{"error": str(exc) or "Не удалось выполнить анализ конкурентов."}]
        analysis.save(update_fields=["status", "finished_at", "errors", "updated_at"])
