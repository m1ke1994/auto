import io
import zipfile
from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project, Revision
from .generator import generate_demo

class ProjectInput(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    prompt = serializers.CharField(max_length=8000)

class EditInput(serializers.Serializer):
    instruction = serializers.CharField(max_length=8000)

def revision_data(r):
    return {"id": r.id, "instruction": r.instruction, "html": r.html, "created_at": r.created_at}

def project_data(p, detail=False):
    data = {"id": str(p.id), "name": p.name, "prompt": p.prompt, "created_at": p.created_at, "published_revision": p.published_revision_id, "mode": "demo"}
    if detail:
        data["revisions"] = [revision_data(r) for r in p.revisions.all()[:30]]
    return data

class StudioView(APIView):
    permission_classes = [IsAuthenticated]
    def initial(self, *args, **kwargs):
        if not getattr(settings, "STUDIO_DEMO_ENABLED", False):
            raise Http404
        super().initial(*args, **kwargs)
    def project(self, request, pk):
        return get_object_or_404(Project, pk=pk, owner=request.user)

class Projects(StudioView):
    def get(self, request):
        return Response([project_data(p) for p in Project.objects.filter(owner=request.user)[:100]])
    @transaction.atomic
    def post(self, request):
        s = ProjectInput(data=request.data)
        s.is_valid(raise_exception=True)
        if Project.objects.filter(owner=request.user).count() >= 20:
            return Response({"detail": "Лимит демо: 20 проектов."}, status=400)
        p = Project.objects.create(owner=request.user, **s.validated_data)
        Revision.objects.create(project=p, instruction=p.prompt, html=generate_demo(p.name, p.prompt))
        return Response(project_data(p, True), status=201)

class Detail(StudioView):
    def get(self, request, pk):
        return Response(project_data(self.project(request, pk), True))

class Edit(StudioView):
    @transaction.atomic
    def post(self, request, pk):
        p = get_object_or_404(Project.objects.select_for_update(), pk=pk, owner=request.user)
        s = EditInput(data=request.data)
        s.is_valid(raise_exception=True)
        if p.revisions.count() >= 30:
            return Response({"detail": "Лимит демо: 30 версий."}, status=400)
        instruction = s.validated_data["instruction"]
        Revision.objects.create(project=p, instruction=instruction, html=generate_demo(p.name, p.prompt, instruction))
        return Response(project_data(p, True))

class Publish(StudioView):
    @transaction.atomic
    def post(self, request, pk, revision):
        p = get_object_or_404(Project.objects.select_for_update(), pk=pk, owner=request.user)
        p.published_revision = get_object_or_404(p.revisions, pk=revision)
        p.save(update_fields=["published_revision"])
        return Response(project_data(p, True))

class Export(StudioView):
    def get(self, request, pk, revision):
        p = self.project(request, pk)
        r = get_object_or_404(p.revisions, pk=revision)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("index.html", r.html)
            z.writestr("README.txt", "TrackNode Studio demo. Static HTML; no real backend or analytics integration.")
        response = HttpResponse(output.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="tracknode-site.zip"'
        return response
