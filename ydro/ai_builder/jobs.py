import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.db import transaction
from .models import Project
from django.utils import timezone
from django.utils.dateparse import parse_datetime


RUN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TERMINAL = {"complete", "failed"}


def job_root():
    return Path(settings.STUDIO_JOB_ROOT)


def output_root():
    return Path(settings.STUDIO_OUTPUT_ROOT)


def _atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def queue_project(project, *, profile, asset_style, hero_mode, require_model):
    payload = {
        "version": 1,
        "project_id": str(project.id),
        "name": project.name,
        "prompt": project.prompt,
        "contacts": project.contacts,
        "profile": profile,
        "asset_style": asset_style,
        "hero_mode": hero_mode,
        "require_model": bool(require_model),
        "created_at": timezone.now().isoformat(),
    }
    _atomic_json(job_root() / "pending" / f"{project.id}.json", payload)


@transaction.atomic
def refresh_project(project):
    if project.engine != "cinematic" or project.generation_status in TERMINAL:
        return project
    # Polling requests may race. Refresh the locked row before applying a terminal state.
    project = Project.objects.select_for_update().get(pk=project.pk)
    if project.generation_status in TERMINAL:
        return project
    state_path = job_root() / "status" / f"{project.id}.json"
    if not state_path.is_file():
        return project
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return project
    if not isinstance(state, dict):
        return project
    status = state.get("status")
    if status not in {"queued", "running", "complete", "failed"}:
        return project
    run_directory = state.get("run_directory", "")
    if not isinstance(run_directory, str) or (run_directory and not RUN_NAME.fullmatch(run_directory)):
        return project
    error = state.get("error", "")
    stage = state.get("stage", "")
    if not isinstance(error, str) or not isinstance(stage, str):
        return project
    if (project.generation_status, project.generation_stage, project.generation_error, project.run_directory) == (status, stage[:80], error[:2000], run_directory):
        return project
    project.generation_status = status
    project.generation_stage = stage[:80]
    project.generation_error = error[:2000]
    project.run_directory = run_directory
    project.save(update_fields=["generation_status", "generation_stage", "generation_error", "run_directory", "updated_at"])
    if status == "complete" and run_directory and not project.versions.exists():
        from .versions import record
        record(project, kind="initial")
    return project


def project_dist(project):
    if project.engine != "cinematic" or project.generation_status != "complete" or not RUN_NAME.fullmatch(project.run_directory or ""):
        return None
    root = output_root().resolve()
    dist = (root / project.run_directory / "dist").resolve()
    try:
        dist.relative_to(root)
    except ValueError:
        return None
    return dist if (dist / "index.html").is_file() else None


def visual_result(project, dist):
    """Only the trusted pipeline marker certifies visual acceptance, never import status."""
    result = {"status": "unverified", "score": None, "threshold": 85}
    if dist is None or project.generation_stage not in {"verified", "technical-preview"}:
        return result
    try:
        path = dist.parent / "studio-result.json"
        if path.is_symlink() or path.stat().st_size > 4096:
            return result
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("technical_passed") is not True:
            return result
        status, score = data.get("status"), data.get("score")
        if status not in ("passed", "needs_revision", "unavailable", "skipped"):
            return result
        if status in ("passed", "needs_revision"):
            if type(score) is not int or not 0 <= score <= 100:
                return result
            if status == "passed" and score < 85:
                return result
        else:
            score = None
        return {"status": status, "score": score, "threshold": 85}
    except (OSError, ValueError, TypeError):
        return result

def progress_event(project):
    """Report the last real worker phase timestamp, not the last HTTP poll."""
    if project.engine != "cinematic":
        return None
    path = job_root() / "status" / f"{project.id}.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("status") != project.generation_status or state.get("stage") != project.generation_stage:
            return None
        raw = state.get("updated_at")
        if not isinstance(raw, str):
            return None
        stamp = parse_datetime(raw)
        if stamp is None or timezone.is_naive(stamp):
            return None
        return stamp.isoformat()
    except (OSError, ValueError, TypeError, OverflowError):
        return None
