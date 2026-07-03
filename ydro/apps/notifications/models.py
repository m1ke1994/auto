from django.conf import settings
from django.db import models
from django.utils import timezone


class DashboardNews(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    body = models.TextField(verbose_name="Текст новости")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    published_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Дата публикации")
    is_published = models.BooleanField(default=False, db_index=True, verbose_name="Опубликована")
    is_important = models.BooleanField(default=False, db_index=True, verbose_name="Важная")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dashboard_news_created",
        verbose_name="Автор",
    )

    class Meta:
        ordering = ("-is_important", "-published_at", "-created_at")
        verbose_name = "Новость TrackNode"
        verbose_name_plural = "Новости TrackNode"
        indexes = [
            models.Index(fields=("is_published", "-published_at"), name="news_publish_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserNewsRead(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_reads",
        verbose_name="Пользователь",
    )
    news = models.ForeignKey(
        DashboardNews,
        on_delete=models.CASCADE,
        related_name="read_records",
        verbose_name="Новость",
    )
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Прочитано")

    class Meta:
        ordering = ("-read_at",)
        verbose_name = "Прочтение новости"
        verbose_name_plural = "Прочтения новостей"
        constraints = [
            models.UniqueConstraint(fields=("user", "news"), name="unique_user_news_read"),
        ]

    def __str__(self):
        return f"{self.user} — {self.news}"

