# Persistent local Studio worker

The previous startup checked a detached PowerShell watcher only once. The API
could accept new paid jobs while the watcher was absent. The process could be
gone with queued jobs left on disk. A stale stage alone never proves a crash.

The new per-workspace Windows Scheduled Task runs under the logged-in user,
independent of the VS Code terminal. A supervisor restarts a child watcher
after it exits and writes a timestamped heartbeat. The watcher acknowledges
readiness only after taking its exclusive lock and recovering interrupted
envelopes. Docker must be available before a queued job is claimed. On restart
the old recovery rules preserve terminal results and fail interrupted running
jobs instead of repeating paid requests. Pending jobs are not discarded.
The API refuses new jobs when the heartbeat is unavailable (enabled in the
local Studio Compose override); Studio polls and displays the worker state.

Start with .\\studio-worker.ps1; inspect with .\\studio-worker.ps1 -Status.
Start-studio also invokes the task setup. Task Scheduler registration may be
restricted by Windows policy. In that case the error is surfaced, not hidden.
A living legacy watcher is not automatically terminated; migrate when idle.
A running scheduled task is not forcibly restarted. The task runs at logon,
not as an always-on server when the user is logged out.

No heartbeat can prove that a paid network request is progressing. A live
busy watcher is not killed or replayed automatically. Windows/Docker execution
and Task Scheduler installation need local integration testing.

An interrupted job with its own result file, a local source ZIP, a built index
and valid technical/visual marker is finalized rather than retried. Other
interrupted jobs are marked failed; terminal records are left unchanged.
The offline Windows smoke test covers these cases using a temporary workspace.

## Test isolation

The local Compose runtime requires a live worker heartbeat. API tests use
private temporary job/output roots and explicitly disable the live-worker
requirement except in dedicated gate tests, which enable it and supply
controlled heartbeat fixtures. CI enables STUDIO_WORKER_REQUIRED=1 to match
the local runtime and catch environment-dependent regressions. The running
application retains the worker gate unchanged; a passing isolated API suite
is not proof of actual Windows/Docker worker connectivity.
