# Project Version Engine — Stage 8 MVP

Cinematic projects now have an append-only database registry of accepted builds.
Quick projects retain the existing Revision path. No new AI calls or site rebuilds
are required for historical preview, export or restore.

- First access adopts the current run and reconstructs known accepted / rolled-back
  legacy BlockEdit records. Missing legacy status files cannot reconstruct an unknown
  candidate; adoption timestamps are not historical acceptance times.
- Every accepted edit and restore appends a numbered entry. Restoring is a new history
  event, not deletion or mutation of later versions. The current build pointer and
  history event change in the same DB transaction.
- Candidate decisions remain separate; rejected and failed edits stay in the edit log.
- Owner/project checks, per-owner and project row locks, active-job guards and an
  expected current version protect restoration against concurrent changes.
- Historical preview uses the same opaque UUID capability URL and CSP as existing
  Studio previews. The list, export and restore APIs require the project owner.
- The Versions tab allows preview, return to current, restoration and ZIP download.
- Builds and source archives are referenced, not duplicated. Keep the existing output
  directory backed up; a missing archive disables restoration. A future backup/manifest
  stage should add artifact hashes, engine version and retention management.

Local validation:
1. Apply migration 0006_project_version.
2. Run Django ai_builder tests and frontend production build.
3. On LUMERA, open Versions, preview a past build, restore and restore forward again.
4. Verify candidate/active job conflicts, historical ZIP and ownership checks.
5. Confirm no assets, existing projects or volumes were modified.


## Artifact integrity and backup

Migration 0007 stores a SHA-256 fingerprint of the original source ZIP and
the entire built dist tree. Trusted runtime files and STORYBOARD.json have
separate fingerprints if present. No artificial engine version is assigned.
New versions capture a manifest when artifacts are available; legacy or
previously unavailable manifests are sealed at first explicit verification.
This cannot prove what a legacy file contained before sealing.

Restore and historical ZIP export verify the stored manifest and reject a
modified or missing artifact. The history list does not rehash every build on
every poll. "Recorded" means a fingerprint exists, not a fresh verification.
The Versions tab also offers a side-by-side comparison against the active
build (stacked on smaller screens).

Local backup (idle Studio, no changes to source runs):
```powershell
docker compose -p tracknode20 -f docker-compose.yml -f docker-compose.studio.yml exec -T backend python manage.py studio_version_backup
```
The command copies accepted builds to studio-version-backups, verifies the
copy, writes version.json, skips identical existing copies, and never
deletes or overwrites a backup. Keep this directory and the PostgreSQL
database on independent backup storage. Recovery of a lost run is an
operator procedure: compare version.json and copy the verified snapshot
to its original run_directory while Studio is idle; do not overwrite a
live run. No automatic pruning is enabled; this avoids deleting any
version or artifact still referenced by a project.


## Interrupted worker recovery

The watcher holds an exclusive workspace file handle for its entire life.
On startup it inspects orphaned running envelopes. Recovery is conservative:
if Docker state cannot be read, a known pipeline container exists, or another
local pipeline is detected, it refuses to recover. Otherwise terminal states
are preserved and nonterminal interrupted jobs become failed; original job
envelopes are archived under a unique .done name. There is no automatic paid
retry. This does not cancel a live slow request or prove why the worker exited.
The status UI can release the failed edit once it polls the backend.
