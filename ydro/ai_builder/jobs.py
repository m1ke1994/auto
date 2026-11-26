import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.utils import timezone


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
        "profile": profile,
        "asset_style": asset_style,
        "hero_mode": hero_mode,
        "require_model": bool(require_model),
        "created_at": timezone.now().isoformat(),
    }
    _atomic_json(job_root() / "pending" / f"{project.id}.json", payload)


def refresh_project(project):
    if project.engine != "cinematic" or project.generation_status in TERMINAL:
        return project
    state_path = job_root() / "status" / f"{project.id}.json"
    if not state_path.is_file():
        return project
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return project
    status = state.get("status")
    if status not in {"queued", "running", "complete", "failed"}:
        return project
    run_directory = state.get("run_directory", "")
    if run_directory and not RUN_NAME.fullmatch(run_directory):
        return project
    error = state.get("error", "")
    stage = state.get("stage", "")
    if not isinstance(error, str) or not isinstance(stage, str):
        return project
    project.generation_status = status
    project.generation_stage = stage[:80]
    project.generation_error = error[:2000]
    project.run_directory = run_directory
    project.save(update_fields=["generation_status", "generation_stage", "generation_error", "run_directory", "updated_at"])
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
