from django.db import models
from django.utils.text import slugify


class HeroBlock(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Имя",
        default="Лиза Стручкова",
    )
    description = models.TextField(
        verbose_name="Описание",
        default="Делюсь событиями, тишиной и тёплыми практиками в Конаково.",
    )
    background_image = models.ImageField(
        upload_to="hero/background/",
        verbose_name="Фоновое изображение",
    )
    avatar = models.ImageField(
        upload_to="hero/avatar/",
        verbose_name="Аватар",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Hero-блок"
        verbose_name_plural = "Hero-блок"

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    phone = models.CharField(
        max_length=255,
        blank=True,
        default="+7 (985) 200-63-22",
        verbose_name="Телефон",
    )
    email = models.EmailField(
        blank=True,
        default="elizaveta-struchkova@yandex.ru",
        verbose_name="Email",
    )
    telegram_url = models.URLField(
        blank=True,
        default="https://t.me/novoe_konakovo",
        verbose_name="Ссылка Telegram",
    )
    telegram_username = models.CharField(
        max_length=255,
        blank=True,
        default="@novoe_konakovo",
        verbose_name="Подпись Telegram",
    )
    address = models.TextField(
        blank=True,
        default="Тверская область, Конаковский район, природный кластер «Новое Конаково».",
        verbose_name="Адрес",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"


class Review(models.Model):
    class RatingChoices(models.IntegerChoices):
        ONE = 1, "1"
        TWO = 2, "2"
        THREE = 3, "3"
        FOUR = 4, "4"
        FIVE = 5, "5"

    avatar = models.ImageField(upload_to="reviews/", null=True, blank=True)
    name = models.CharField(max_length=255)
    event_name = models.CharField(max_length=255)
    rating = models.PositiveSmallIntegerField(choices=RatingChoices.choices)
    text = models.TextField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.name} ({self.event_name})"


class Article(models.Model):
    class ContentTypeChoices(models.TextChoices):
        ARTICLE = "article", "Статья"
        VIDEO = "video", "Видео"

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    preview_image = models.ImageField(upload_to="articles/", null=True, blank=True)
    preview_description = models.TextField()
    content = models.TextField()
    content_type = models.CharField(max_length=20, choices=ContentTypeChoices.choices)
    video_url = models.URLField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    published_date = models.DateField(verbose_name="Дата публикации")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Статья / Видео"
        verbose_name_plural = "Статьи и видео"
        ordering = ["-published_date", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "article"
            slug = base_slug
            index = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{index}"
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)


class News(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Краткое описание")
    image = models.ImageField(upload_to="news/", verbose_name="Изображение")
    published_date = models.DateField(verbose_name="Дата публикации")
    content = models.JSONField(verbose_name="Контент (абзацы)")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-published_date", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "news"
            slug = base_slug
            index = 1
            while News.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{index}"
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Service(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        verbose_name="Изображение карточки",
    )
    is_active = models.BooleanField(default=True)
    is_category = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.title


class ServiceImage(models.Model):
    service = models.ForeignKey(
        Service,
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name="Услуга",
    )
    image = models.ImageField(upload_to="services/gallery/", verbose_name="Изображение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Изображение услуги"
        verbose_name_plural = "Галерея услуг"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.service.title} #{self.id}"


class Tariff(models.Model):
    service = models.ForeignKey(Service, related_name="tariffs", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    duration = models.CharField(max_length=255, blank=True)
    price = models.IntegerField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("service", "slug")

    def __str__(self):
        return f"{self.service.title}: {self.title}"


class ScheduleDay(models.Model):
    date = models.DateField(unique=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "День расписания"
        verbose_name_plural = "Дни расписания"

    def __str__(self):
        return self.date.isoformat()


class ScheduleEvent(models.Model):
    day = models.ForeignKey(
        ScheduleDay,
        related_name="events",
        on_delete=models.CASCADE,
    )
    service = models.ForeignKey(
        Service,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="schedule_events/",
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    time_start = models.TimeField()
    time_end = models.TimeField()
    price = models.IntegerField(null=True, blank=True)
    color = models.CharField(max_length=20, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["time_start", "order"]
        verbose_name = "Событие расписания"
        verbose_name_plural = "События расписания"

    def __str__(self):
        return f"{self.day.date} {self.title}"
