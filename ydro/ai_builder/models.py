import uuid
from django.conf import settings
from django.db import models

class Project(models.Model):
    ENGINE_CHOICES = (("quick", "Quick concept"), ("cinematic", "Cinematic agent"))
    STATUS_CHOICES = (
        ("complete", "Complete"),
        ("queued", "Queued"),
        ("running", "Running"),
        ("failed", "Failed"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    prompt = models.TextField()
    contacts = models.JSONField(default=dict, blank=True)
    style = models.CharField(max_length=20, default="auto")
    engine = models.CharField(max_length=16, choices=ENGINE_CHOICES, default="quick")
    generation_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="complete")
    generation_stage = models.CharField(max_length=80, blank=True)
    generation_error = models.TextField(blank=True)
    run_directory = models.CharField(max_length=128, blank=True)
    preview_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_revision = models.ForeignKey("Revision", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    class Meta:
        ordering = ["-created_at"]

class Revision(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="revisions")
    instruction = models.TextField()
    html = models.TextField()
    design = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=20, default="demo")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-id"]

class BlockEdit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="block_edits")
    block = models.CharField(max_length=16)
    instruction = models.TextField()
    base_run = models.CharField(max_length=128)
    base_stage = models.CharField(max_length=80)
    upgrade_motion = models.BooleanField(default=False)
    decision = models.CharField(max_length=16, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at", "-id"]
