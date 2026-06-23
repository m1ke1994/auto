from django.db import models


class Page(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    subtitle = models.TextField(blank=True, verbose_name="Подзаголовок")
    hero_image = models.ImageField(
        upload_to="pages/hero/",
        blank=True,
        null=True,
        verbose_name="Hero-изображение",
    )
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class PageSection(models.Model):
    page = models.ForeignKey(
        Page,
        related_name="sections",
        on_delete=models.CASCADE,
        verbose_name="Страница",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок секции")
    text = models.TextField(verbose_name="Текст")
    image = models.ImageField(
        upload_to="pages/sections/",
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    order = models.IntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Секция страницы"
        verbose_name_plural = "Секции страниц"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.page.title}: {self.title}"


class PageGalleryImage(models.Model):
    page = models.ForeignKey(
        Page,
        related_name="gallery",
        on_delete=models.CASCADE,
        verbose_name="Страница",
    )
    image = models.ImageField(upload_to="pages/gallery/", verbose_name="Изображение")
    order = models.IntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Изображение галереи"
        verbose_name_plural = "Галерея страниц"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.page.title} #{self.id}"
