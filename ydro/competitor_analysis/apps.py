from django.apps import AppConfig


class CompetitorAnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "competitor_analysis"
    verbose_name = "Анализ конкурентов"

    def ready(self):
        import competitor_analysis.tasks  # noqa: F401
