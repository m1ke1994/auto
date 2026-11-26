import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from ai_builder.models import Project


class Command(BaseCommand):
    help = "Attach an already verified local cinematic run to a Studio user."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--run", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--prompt", default="Импортированный локальный результат studio-agent.")

    def handle(self, *args, **options):
        run_name=options["run"].strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}",run_name):
            raise CommandError("Invalid run directory")
        root=Path(settings.STUDIO_OUTPUT_ROOT).resolve()
        run=(root/run_name).resolve()
        try:
            run.relative_to(root)
        except ValueError:
            raise CommandError("Run escaped output root")
        report=run/"quality-report"/"quality-report.json"
        if not (run/"dist"/"index.html").is_file() or not report.is_file():
            raise CommandError("Run has no built preview or quality report")
        try:
            audit=json.loads(report.read_text(encoding="utf-8"))
        except (OSError,ValueError):
            raise CommandError("Invalid quality report")
        if audit.get("passed") is not True:
            raise CommandError("Only technically passed runs can be imported")
        user=get_user_model().objects.get(username=options["username"])
        project,created=Project.objects.get_or_create(
            owner=user,engine="cinematic",run_directory=run_name,
            defaults={
                "name":options["name"],"prompt":options["prompt"],"style":"cinema",
                "generation_status":"complete","generation_stage":"verified-import",
            },
        )
        self.stdout.write(self.style.SUCCESS(("Imported" if created else "Already present")+f": {project.id}"))
