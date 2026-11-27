"""Cinematic history: accepted build pointers, independent from transient job status.

Mutating helpers require an active transaction and a locked Project row.
No API calls, rebuilds, deletes, or automatic acceptance occur here.
"""
from django.db import transaction
from .models import Project
from .jobs import RUN_NAME
from .block_jobs import run_dist, state as edit_state
from .version_artifacts import build_manifest, matches_manifest


def archive_for(version):
    dist = run_dist(version.run_directory)
    if not dist:
        return None
    archive = dist.parent / "tracknode-agent-site.zip"
    return archive if archive.is_file() and not archive.is_symlink() else None


def record(project, *, kind, instruction="", edit=None, restored_from=None,
           run=None, stage=None, legacy=False):
    name = project.run_directory if run is None else run
    if not isinstance(name, str) or not RUN_NAME.fullmatch(name):
        raise ValueError("Invalid version run")
    last = project.versions.first()
    manifest = dict(restored_from.manifest) if restored_from and restored_from.manifest else {}
    if not manifest and not legacy:
        dist = run_dist(name)
        if dist:
            try:
                manifest = build_manifest(dist.parent)
            except (OSError, ValueError):
                pass
    return project.versions.create(
        number=(last.number + 1 if last else 1),
        run_directory=name,
        generation_stage=project.generation_stage if stage is None else stage,
        kind=kind, instruction=instruction, block_edit=edit,
        restored_from=restored_from, legacy=legacy, manifest=manifest,
    )


def ensure_history(project):
    """Idempotent lazy adoption of pre-version-engine projects.

    Reconstruct only known accepted runs. A missing legacy status is not evidence
    of a successful candidate. The existing active run is always retained.
    Legacy record timestamps describe adoption, not original acceptance.
    """
    if (project.engine != "cinematic" or project.generation_status != "complete"
            or not RUN_NAME.fullmatch(project.run_directory or "")):
        return None
    last = project.versions.first()
    if not last:
        for edit in project.block_edits.filter(
                decision__in=("accepted", "rolled_back")).order_by("created_at", "id"):
            if not RUN_NAME.fullmatch(edit.base_run or ""):
                continue
            if last is None or last.run_directory != edit.base_run:
                last = record(project, kind="baseline", run=edit.base_run,
                              stage=edit.base_stage, legacy=True)
            base = last
            s = edit_state(edit)
            if s["status"] == "complete":
                last = record(project, kind="accepted", instruction=edit.instruction,
                              edit=edit, run=s["run_directory"], stage="technical-preview", legacy=True)
                if edit.decision == "rolled_back":
                    last = record(project, kind="restored", run=base.run_directory,
                                  stage=base.generation_stage, restored_from=base, legacy=True)
    if not last or last.run_directory != project.run_directory:
        last = record(project, kind="baseline" if last else "initial",
                      legacy=True)
    return last


def version_data(version, active_id):
    dist = run_dist(version.run_directory)
    archive = archive_for(version)
    return {
        "id": str(version.id), "number": version.number, "kind": version.kind,
        "instruction": version.instruction, "created_at": version.created_at,
        "legacy": version.legacy, "current": version.id == active_id,
        "preview_path": f"/studio-preview/{version.id}/" if dist else "",
        "source_archive_available": bool(archive),
        "restorable": bool(dist and archive),
        "integrity": "recorded" if version.manifest else "unrecorded",
        "runtime_fingerprint": version.manifest.get("runtime", {}).get("src/cinematic-motion.js", ""),
        "archive_bytes": version.manifest.get("archive_bytes"),
        "restored_from": str(version.restored_from_id) if version.restored_from_id else None,
    }


@transaction.atomic
def history_data(project):
    if project.engine != "cinematic" or project.generation_status != "complete":
        return []
    locked = Project.objects.select_for_update().get(pk=project.pk)
    current = ensure_history(locked)
    return [version_data(v, current.id if current else None) for v in locked.versions.all()]


def verify_version(version):
    archive = archive_for(version)
    if not archive:
        return False
    # Older builds had no digest at acceptance. Seal only the files currently
    # present; do not claim this proves their historical integrity.
    if not version.manifest:
        try:
            manifest = build_manifest(archive.parent)
        except (OSError, ValueError):
            return False
        # Conditional write prevents concurrent sealing from overwriting a digest.
        version.project.versions.filter(pk=version.pk, manifest={}).update(manifest=manifest)
        version.refresh_from_db(fields=["manifest"])
        return version.manifest == manifest
    return matches_manifest(archive.parent, version.manifest)
