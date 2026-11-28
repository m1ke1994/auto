# TrackNode Studio development contract

- Work in tracknode-2.0. Preserve production main, existing project artifacts, DB volumes and secrets.
- Read docs/ROADMAP.md, docs/PROJECT_VERSION_ENGINE.md, docs/STUDIO_WORKER_RELIABILITY.md, docs/VISUAL_EDITOR.md and docs/AI_BLOCK_EDITOR_V2.md before changing the Studio.
- Implement a bounded change, add regression tests, run the relevant existing tests and new tests; inspect actual logs and fix failures before calling a stage verified.
- Keep old sites and the cinematic runtime compatible. Never mutate accepted source/dist in place; build candidates, audit them and preserve explicit accept/discard.
- No automatic paid generation/repair/retry or external publish. Use demo fixtures for automated tests; report real paid tests separately.
- Check PowerShell syntax, Django migrations, backend tests, Vue build, worker recovery, agent patch tests and real browser checks. Inspect screenshot artifacts for UI changes; a green build alone is not visual acceptance.
- Use only the workspace's Docker/Studio services, no destructive cleanup. Do not print .env, tokens, credentials or full resolved compose configs.
- Keep tests and docs current. Record exact commit and actual verification evidence, list remaining limitations. Do not mark an unexecuted local integration test as passed.
