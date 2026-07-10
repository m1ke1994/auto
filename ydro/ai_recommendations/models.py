import uuid

from django.conf import settings
from django.db import models


class AIRecommendationJob(models.Model):
    class Type(models.TextChoices):
        SEO = "seo", "SEO"
        CONVERSION = "conversion", "Конверсия"
        COMBINED = "combined", "Комплексный"

    class Status(models.TextChoices):
        QUEUED = "queued", "В очереди"
        PROCESSING = "processing", "Выполняется"
        COMPLETED = "completed", "Готово"
        FAILED = "failed", "Ошибка"
        CANCELLED = "cancelled", "Отменено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_job_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    remote_job_id = models.UUIDField(null=True, blank=True, unique=True)
    site = models.ForeignKey("sites.Site", on_delete=models.CASCADE, related_name="ai_recommendation_jobs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_recommendation_jobs")
    recommendation_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    period_from = models.DateField()
    period_to = models.DateField()
    input_snapshot = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    poll_attempts = models.PositiveIntegerField(default=0)
    openai_model = models.CharField(max_length=100, blank=True, default="")
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    prompt_version = models.CharField(max_length=50, default="business-owner-v1")
    platform_reviewed_at = models.DateTimeField(null=True, blank=True)
    platform_hidden_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("user", "site", "status"))]
