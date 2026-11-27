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
