from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ai_builder.models import Project, BlockEdit
from ai_builder.jobs import project_dist, refresh_project
from ai_builder.block_jobs import active_for_owner, state, queue_edit

class Command(BaseCommand):
    help = "Queue an offline audited subject-directed Hero film (preserves existing copy) for an existing project."

    def add_arguments(self, parser):
        parser.add_argument("--preview-token", required=True)

    def handle(self, *args, **options):
        if not settings.STUDIO_CINEMATIC_ENABLED:
            raise CommandError("Studio cinematic mode is disabled")
        try:
            candidate=Project.objects.get(preview_token=options["preview_token"],engine="cinematic")
        except (Project.DoesNotExist, ValueError):
            raise CommandError("Cinematic project not found")
        with transaction.atomic():
            owner=get_user_model().objects.select_for_update().get(pk=candidate.owner_id)
            project=Project.objects.select_for_update().get(pk=candidate.pk)
            for active in Project.objects.filter(owner=owner,engine="cinematic",generation_status__in=("queued","running")):
                refresh_project(active)
            if active_for_owner(owner) or Project.objects.filter(owner=owner,engine="cinematic",generation_status__in=("queued","running")).exists():
                raise CommandError("An active generation must finish first")
            if any(state(e)["status"]=="complete" for e in project.block_edits.filter(decision="pending")):
                raise CommandError("Accept or discard the current candidate in Studio first")
            dist=project_dist(project)
            if not dist or not (dist.parent/"tracknode-agent-site.zip").is_file():
                raise CommandError("The current project needs a completed source archive")
            if project.block_edits.count()>=30:
                raise CommandError("Local edit limit reached")
            edit=BlockEdit.objects.create(project=project,block="home",base_run=project.run_directory,base_stage=project.generation_stage,instruction="Subject-directed Hero film (local, no AI)",upgrade_motion=True)
            transaction.on_commit(lambda:queue_edit(edit,local_hero_film=True))
        self.stdout.write(self.style.SUCCESS(f"LOCAL_HERO_FILM_QUEUED: {edit.id}"))
