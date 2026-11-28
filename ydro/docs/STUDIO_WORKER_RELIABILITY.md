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
