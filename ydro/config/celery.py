import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

TASK_MODULES = ("competitor_analysis.tasks", "seo_audit.tasks")

app = Celery("config", include=list(TASK_MODULES))
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.imports = tuple(set(app.conf.imports or ()) | set(TASK_MODULES))
app.autodiscover_tasks()
