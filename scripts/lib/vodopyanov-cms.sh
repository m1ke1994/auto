#!/usr/bin/env bash
# Internal shared operation. The caller must:
#  - validate its inputs and server state
#  - acquire /tmp/yadro-autodeploy.lock (FD 9)
#  - cd into the ydro compose directory
#  - define the dc() function, closing FD 9 in spawned Docker processes.
# Do NOT call this file as a standalone deployment script.
vodopyanov_cms_register() {
  local mode="$1"
  if [[ "$mode" != "--check" && "$mode" != "--apply" ]]; then
    echo "Invalid CMS mode: $mode" >&2
    return 2
  fi

  # Building an image does not recreate/restart the production backend.
  dc build backend

  if [[ "$mode" == "--apply" ]]; then
    mkdir -p /home/alex/auto/backups
    local backup
    backup="$(mktemp "/home/alex/auto/backups/before_vodopyanov_cms_$(date +%F_%H-%M-%S)_XXXXXX.dump")"
    if ! dc exec -T postgres pg_dump -U yadro_user -Fc yadro_db > "$backup"; then
      echo "PostgreSQL backup failed; registration aborted: $backup" >&2
      return 1
    fi
    if [[ ! -s "$backup" ]] || ! dc exec -T postgres pg_restore --list < "$backup" > /dev/null; then
      echo "PostgreSQL backup could not be verified; registration aborted: $backup" >&2
      return 1
    fi
    echo "Readable backup: $backup"
  fi

  # A one-shot management container. Bypass backend entrypoint to avoid
  # migrations, startup seeds and any restart of production containers.
  dc run --rm --no-deps -T --entrypoint python backend manage.py seed_vodopyanov_site "$mode"
}
