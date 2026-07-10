#!/bin/sh
set -eu
if [ "${1:-}" = "gunicorn" ]; then alembic upgrade head; fi
exec "$@"

