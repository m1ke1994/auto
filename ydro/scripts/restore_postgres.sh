#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

if [ "$#" -ne 1 ]; then
  echo "Usage: sh scripts/restore_postgres.sh backups/backup_YYYY-MM-DD_HH-MM-SS.sql" >&2
  exit 2
fi

backup_file="$1"

if [ ! -f .env ]; then
  echo "Production .env was not found." >&2
  exit 1
fi

if [ ! -s "$backup_file" ]; then
  echo "Backup file was not found or is empty: $backup_file" >&2
  exit 1
fi

case "$backup_file" in
  backups/*.sql) ;;
  *)
    echo "Backup file must be a .sql file inside backups/." >&2
    exit 1
    ;;
esac

echo "Creating safety backup before restore..."
sh scripts/backup_postgres.sh

echo "Stopping services that may write to PostgreSQL..."
docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  stop backend celery_worker celery_beat telegram_polling

echo "Restoring $backup_file..."
cat "$backup_file" | docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec -T postgres \
  sh -c 'psql --single-transaction -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

echo "Starting application services..."
docker compose \
  --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d backend celery_worker celery_beat telegram_polling

echo "Restore completed."
