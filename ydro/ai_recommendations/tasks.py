from celery import shared_task
from django.conf import settings
from django.utils.dateparse import parse_datetime

from ai_recommendations.client import AIRecommendationsClient, AIServiceTemporaryError
from ai_recommendations.models import AIRecommendationJob


@shared_task(bind=True, autoretry_for=(AIServiceTemporaryError,), retry_backoff=10, retry_backoff_max=300, max_retries=5)
def sync_job(self, job_id):
    job = AIRecommendationJob.objects.filter(id=job_id, deleted_at__isnull=True).first()
    if not job or job.status in (job.Status.COMPLETED, job.Status.FAILED, job.Status.CANCELLED) or not job.remote_job_id: return
    remote = AIRecommendationsClient().get_job(job.remote_job_id)
    job.poll_attempts += 1
    remote_status = remote["status"]
    if job.status == job.Status.COMPLETED: return
    job.status = remote_status
    job.started_at = parse_datetime(remote["started_at"]) if remote.get("started_at") else job.started_at
    job.completed_at = parse_datetime(remote["completed_at"]) if remote.get("completed_at") else job.completed_at
    if remote_status == job.Status.COMPLETED: job.result, job.error_message = remote.get("result"), ""
    elif remote_status == job.Status.FAILED: job.error_message = remote.get("error") or "Не удалось сформировать рекомендации."
    job.save()
    if remote_status in (job.Status.QUEUED, job.Status.PROCESSING):
        if job.poll_attempts >= settings.AI_RECOMMENDATIONS_MAX_POLL_ATTEMPTS:
            job.status, job.error_message = job.Status.FAILED, "Превышено время ожидания AI-сервиса."
            job.save(update_fields=("status", "error_message", "updated_at"))
            return
        sync_job.apply_async((str(job.id),), countdown=settings.AI_RECOMMENDATIONS_POLL_INTERVAL_SECONDS)
