import uuid
from django.conf import settings
from django.db import models

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_revision = models.ForeignKey("Revision", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    class Meta:
        ordering = ["-created_at"]

class Revision(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="revisions")
    instruction = models.TextField()
    html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-id"]
