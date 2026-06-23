from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compatibility wrapper. Use seed_demo_data for the a-meditation public site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-content",
            action="store_true",
            help="Pass through to seed_demo_data and replace existing section content with seed values.",
        )
        parser.add_argument(
            "--reset-users",
            action="store_true",
            help="Pass through to seed_demo_data. Never enabled by default.",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "seed_meditation_site is deprecated. Running seed_demo_data for slug 'a-meditation'..."
            )
        )
        call_command(
            "seed_demo_data",
            force_content=options["force_content"],
            reset_users=options["reset_users"],
        )
