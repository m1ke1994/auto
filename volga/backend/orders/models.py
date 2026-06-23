from django.db import models

from core.models import Service


class RequestStatus(models.TextChoices):
    NEW = "new", "Новая"
    PROCESSED = "processed", "Обработана"


class ContactRequest(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя")
    phone = models.CharField(max_length=255, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    message = models.TextField(blank=True, verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
        verbose_name="Статус",
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка через контакты"
        verbose_name_plural = "Заявки через контакты"

    def __str__(self):
        return f"{self.name} ({self.phone or self.email})"


class ServiceRequest(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="order_requests",
        verbose_name="Услуга",
    )
    tariff = models.CharField(max_length=255, blank=True, verbose_name="Тариф")
    name = models.CharField(max_length=255, verbose_name="Имя")
    phone = models.CharField(max_length=255, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
        verbose_name="Статус",
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на услугу"
        verbose_name_plural = "Заявки на услуги"

    def __str__(self):
        return f"{self.name} — {self.service.title}"


class DayScenarioRequest(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    date = models.DateField(verbose_name="Дата")
    guests = models.PositiveIntegerField(verbose_name="Гостей")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итоговая стоимость")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
        verbose_name="Статус",
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на сценарий дня"
        verbose_name_plural = "Заявки на сценарий дня"

    def __str__(self):
        return f"{self.name} — {self.date}"

# Create your models here.
