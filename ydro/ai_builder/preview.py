import mimetypes
from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt

from .jobs import project_dist, refresh_project
from .models import Project, BlockEdit, ProjectVersion
from .block_jobs import state as edit_state, run_dist


@xframe_options_exempt
def cinematic_preview(request, token, path="index.html"):
    project=Project.objects.filter(preview_token=token,engine="cinematic").first()
    if project:
        dist=project_dist(refresh_project(project))
    else:
        version=ProjectVersion.objects.filter(pk=token).first()
        if version:
            dist=run_dist(version.run_directory)
        else:
            edit=get_object_or_404(BlockEdit,pk=token)
            status=edit_state(edit)
            dist=run_dist(status["run_directory"]) if status["status"]=="complete" else None
    if not dist:
        raise Http404
    requested=(dist/(path or "index.html")).resolve()
    try:
        requested.relative_to(dist.resolve())
    except ValueError:
        raise Http404
    if not requested.is_file():
        raise Http404
    content_type=mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
    response=FileResponse(requested.open("rb"),content_type=content_type)
    response["Cache-Control"]="no-store" if project or requested.name=="index.html" else "private, max-age=3600"
    response["Content-Security-Policy"]="default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors http://localhost:8001 http://127.0.0.1:8001"
    return response
