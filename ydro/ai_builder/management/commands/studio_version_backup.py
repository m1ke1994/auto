"""Explicit local backup of accepted builds, independent from AI and worker."""
import json
import shutil
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from ai_builder.models import Project
from ai_builder.versions import archive_for, history_data, verify_version
from ai_builder.version_artifacts import matches_manifest


class Command(BaseCommand):
    help = "Copy accepted version artifacts to a separate directory; never overwrite or delete backups."

    def add_arguments(self, parser):
        parser.add_argument("--project", help="Project UUID; omit to back up all complete Cinema projects")
        parser.add_argument("--destination", default="/studio-version-backups")

    def handle(self, *args, **options):
        dest = Path(options["destination"]).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        projects = Project.objects.filter(engine="cinematic", generation_status="complete")
        if options["project"]:
            projects = projects.filter(pk=options["project"])
            if not projects.exists():
                raise CommandError("Complete cinematic project not found")
        failures = []
        for project in projects.iterator():
            history_data(project)
            for version in project.versions.all():
                if not verify_version(version):
                    failures.append(f"{project.id}/v{version.number}: unavailable or changed")
                    continue
                source = archive_for(version).parent
                target = dest / str(project.id) / str(version.id)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if not matches_manifest(target, version.manifest):
                        failures.append(f"{project.id}/v{version.number}: existing backup differs")
                    continue
                with tempfile.TemporaryDirectory(prefix=".staging-", dir=target.parent) as temp:
                    staging = Path(temp) / "snapshot"
                    staging.mkdir()
                    shutil.copytree(source / "dist", staging / "dist")
                    shutil.copy2(source / "tracknode-agent-site.zip", staging)
                    marker = source / "studio-result.json"
                    if marker.is_file() and not marker.is_symlink():
                        shutil.copy2(marker, staging)
                    if not matches_manifest(staging, version.manifest):
                        failures.append(f"{project.id}/v{version.number}: copy verification failed")
                        continue
                    metadata = {"project_id": str(project.id), "version_id": str(version.id),
                                "number": version.number, "run_directory": version.run_directory,
                                "stage": version.generation_stage, "manifest": version.manifest}
                    (staging / "version.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                    if target.exists():
                        failures.append(f"{project.id}/v{version.number}: concurrent backup")
                        continue
                    staging.rename(target)
                self.stdout.write(self.style.SUCCESS(f"Backed up {project.id}/v{version.number}"))
        if failures:
            raise CommandError("; ".join(failures))
