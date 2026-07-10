import logging
import uuid
from datetime import datetime, timezone

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import ValidationError
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import JobStatus, RecommendationJob
from app.openai_service import generate
from app.schemas import JobCreate

settings = get_settings()
celery = Celery("tracknode_ai", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1)
logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=settings.MAX_RETRIES, soft_time_limit=settings.OPENAI_TIMEOUT_SECONDS + 10)
def process_job(self, job_id: str):
    with SessionLocal() as db:
        job = db.execute(select(RecommendationJob).where(RecommendationJob.id == uuid.UUID(job_id)).with_for_update()).scalar_one_or_none()
        if not job or job.deleted_at or job.status == JobStatus.completed:
            return
        job.status, job.started_at, job.attempt = JobStatus.processing, datetime.now(timezone.utc), job.attempt + 1
        db.commit()
        try:
            result, model, input_tokens, output_tokens = generate(JobCreate.model_validate(job.input_data))
            job.result, job.openai_model = result.model_dump(mode="json"), model
            job.input_tokens, job.output_tokens = input_tokens, output_tokens
            job.status, job.completed_at, job.error_message = JobStatus.completed, datetime.now(timezone.utc), None
            db.commit()
        except (RateLimitError, APITimeoutError, APIConnectionError, SoftTimeLimitExceeded) as exc:
            db.rollback()
            if self.request.retries < settings.MAX_RETRIES:
                raise self.retry(exc=exc, countdown=(30, 90, 270)[min(self.request.retries, 2)])
            _fail(db, job_id, "Временная ошибка сервиса OpenAI. Повторите запрос позже.")
        except (ValidationError, ValueError) as exc:
            db.rollback()
            if self.request.retries < settings.MAX_RETRIES:
                raise self.retry(exc=exc, countdown=(30, 90, 270)[min(self.request.retries, 2)])
            _fail(db, job_id, "Не удалось подготовить понятные рекомендации. Попробуйте повторить анализ.")
        except Exception:
            logger.exception("recommendation_generation_failed", extra={"job_id": job_id})
            db.rollback()
            _fail(db, job_id, "Не удалось сформировать рекомендации.")


def _fail(db, job_id, message):
    job = db.get(RecommendationJob, uuid.UUID(job_id))
    if job:
        job.status, job.error_message, job.completed_at = JobStatus.failed, message, datetime.now(timezone.utc)
        db.commit()
