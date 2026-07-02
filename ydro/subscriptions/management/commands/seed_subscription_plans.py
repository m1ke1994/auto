from django.core.management.base import BaseCommand

from subscriptions.plan_catalog import seed_subscription_plans


class Command(BaseCommand):
    help = "Create or update the six subscription plans used by the billing dashboard."

    def handle(self, *args, **options):
        created, updated = seed_subscription_plans()
        self.stdout.write(
            self.style.SUCCESS(
                f"Subscription plans synchronized: created={created}, updated={updated}."
            )
        )
