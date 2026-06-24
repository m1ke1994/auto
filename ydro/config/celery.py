import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config", include=["competitor_analysis.tasks"])
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.imports = tuple(set(app.conf.imports or ()) | {"competitor_analysis.tasks"})
app.autodiscover_tasks()
