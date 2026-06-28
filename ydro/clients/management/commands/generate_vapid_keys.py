from cryptography.hazmat.primitives import serialization
from django.core.management.base import BaseCommand
from py_vapid import Vapid, b64urlencode


class Command(BaseCommand):
    help = "Generate a VAPID key pair for WEB_PUSH_VAPID_* environment variables."

    def handle(self, *args, **options):
        vapid = Vapid()
        vapid.generate_keys()
        private_bytes = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
        public_bytes = vapid.public_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )

        self.stdout.write(f"WEB_PUSH_VAPID_PUBLIC_KEY={b64urlencode(public_bytes)}")
        self.stdout.write(f"WEB_PUSH_VAPID_PRIVATE_KEY={b64urlencode(private_bytes)}")
        self.stdout.write("WEB_PUSH_VAPID_SUBJECT=mailto:admin@tracknode.ru")
        self.stderr.write(self.style.WARNING("Store the private key securely and do not commit it."))
