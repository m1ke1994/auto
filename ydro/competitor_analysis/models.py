from django.db import models

from apps.sites.models import Site
from clients.models import Client


def competitor_analysis_pdf_upload_to(instance, filename: str) -> str:
    site_id = instance.site_id or "site"
    return f"competitor-analysis/site-{site_id}/{filename}"


class CompetitorAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает запуска"
        RUNNING = "running", "Выполняется"
        DONE = "done", "Готово"
        ERROR = "error", "Ошибка"

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="competitor_analyses",
        verbose_name="Сайт",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="competitor_analyses",
        verbose_name="Клиент",
    )
    competitors = models.JSONField(default=list, blank=True, verbose_name="Домены конкурентов")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус",
    )
    results = models.JSONField(default=dict, blank=True, verbose_name="Результаты анализа")
    pdf_file = models.FileField(
        upload_to=competitor_analysis_pdf_upload_to,
        null=True,
        blank=True,
        verbose_name="PDF-отчёт",
    )
    errors = models.JSONField(default=list, blank=True, verbose_name="Ошибки")
    celery_task_id = models.CharField(max_length=255, blank=True, default="", verbose_name="Celery task ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершено")

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["site", "status", "created_at"]),
            models.Index(fields=["client", "created_at"]),
        ]
        verbose_name = "Анализ конкурентов"
        verbose_name_plural = "Анализы конкурентов"

    def __str__(self) -> str:
        return f"Анализ конкурентов #{self.pk} {self.site_id} ({self.status})"
