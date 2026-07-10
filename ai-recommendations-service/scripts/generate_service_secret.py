#!/usr/bin/env python3
import secrets

for name in ("CORE_SERVICE_TOKEN", "AI_RECOMMENDATIONS_SIGNING_SECRET", "POSTGRES_PASSWORD"):
    print(f"{name}={secrets.token_urlsafe(48)}")

