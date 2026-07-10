import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from redis import Redis
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import engine, get_db
from app.models import JobStatus, RecommendationJob
from app.schemas import JobAccepted, JobCreate, JobResponse
from app.security import verify_request
from app.worker import celery, process_job

settings = get_settings()


@asynccontextmanager
async def lifespan(_app):
    yield
    engine.dispose()


app = FastAPI(title="TrackNode AI Recommendations", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def body_limit(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and int(length) > settings.MAX_REQUEST_BODY_SIZE:
        return Response("Request body too large", status_code=413)
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tracknode-ai-recommendations", "version": "1.0.0"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    checks = {"postgres": False, "redis": False, "worker": False, "settings": settings.ready}
    try:
        db.execute(text("SELECT 1")); checks["postgres"] = True
    except Exception:
        pass
    try:
        redis = Redis.from_url(settings.REDIS_URL); checks["redis"] = bool(redis.ping()); redis.close()
        replies = celery.control.inspect(timeout=1).ping() or {}; checks["worker"] = bool(replies)
    except Exception:
        pass
    if not all(checks.values()):
        raise HTTPException(503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


def response(job):
    return JobResponse(job_id=job.id, external_job_id=job.external_job_id, status=job.status.value, recommendation_type=job.recommendation_type, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at, result=job.result, error=job.error_message, openai_model=job.openai_model, input_tokens=job.input_tokens, output_tokens=job.output_tokens)


@app.post("/api/v1/recommendations/jobs", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_request)])
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    if not settings.AI_RECOMMENDATIONS_ENABLED:
        raise HTTPException(503, "AI recommendations are disabled")
    existing = db.scalar(select(RecommendationJob).where(RecommendationJob.external_job_id == payload.external_job_id, RecommendationJob.deleted_at.is_(None)))
    if existing:
        return JobAccepted(job_id=existing.id, external_job_id=existing.external_job_id, status=existing.status.value, created_at=existing.created_at)
    job = RecommendationJob(external_job_id=payload.external_job_id, site_id=payload.site_id, site_domain=payload.site_domain, recommendation_type=payload.recommendation_type, input_data=payload.model_dump(mode="json"))
    db.add(job); db.commit(); db.refresh(job); process_job.delay(str(job.id))
    return JobAccepted(job_id=job.id, external_job_id=job.external_job_id, status=job.status.value, created_at=job.created_at)


def find_job(db, clause):
    job = db.scalar(select(RecommendationJob).where(clause, RecommendationJob.deleted_at.is_(None)))
    if not job: raise HTTPException(404, "Job not found")
    return job


@app.get("/api/v1/recommendations/jobs/by-external-id/{external_id}", response_model=JobResponse, dependencies=[Depends(verify_request)])
def by_external_id(external_id: uuid.UUID, db: Session = Depends(get_db)):
    return response(find_job(db, RecommendationJob.external_job_id == external_id))


@app.get("/api/v1/recommendations/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(verify_request)])
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    return response(find_job(db, RecommendationJob.id == job_id))


@app.post("/api/v1/recommendations/jobs/{job_id}/retry", response_model=JobAccepted, dependencies=[Depends(verify_request)])
def retry_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = find_job(db, RecommendationJob.id == job_id)
    if job.status != JobStatus.failed: raise HTTPException(409, "Only failed jobs can be retried")
    job.status, job.error_message, job.started_at, job.completed_at = JobStatus.queued, None, None, None
    db.commit(); process_job.delay(str(job.id))
    return JobAccepted(job_id=job.id, external_job_id=job.external_job_id, status=job.status.value, created_at=job.created_at)


@app.delete("/api/v1/recommendations/jobs/{job_id}", status_code=204, dependencies=[Depends(verify_request)])
def delete_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = find_job(db, RecommendationJob.id == job_id)
    job.deleted_at = datetime.now(timezone.utc)
    if job.status in (JobStatus.queued, JobStatus.processing): job.status = JobStatus.cancelled
    db.commit()
