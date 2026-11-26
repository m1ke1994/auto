# Run from any working directory. Never deletes database volumes.
[CmdletBinding()]
param([switch]$SkipBuild, [switch]$Test, [switch]$RestartWatcher)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    foreach ($name in @('pending','running','status','logs')) {
        $null=New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot ('studio-jobs/'+$name))
    }
    $composeArgs = @('compose', '-p', 'tracknode20', '-f', 'docker-compose.yml', '-f', 'docker-compose.studio.yml')
    if (Test-Path '.env.studio.local' -PathType Leaf) {
        $composeArgs += @('--env-file', '.env.studio.local')
    }
    if ($RestartWatcher) {
        $active=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'studio-jobs/pending'),(Join-Path $PSScriptRoot 'studio-jobs/running') -Filter '*.json' -File)
        if ($active.Count -gt 0) { throw 'Do not restart the worker while a generation is queued or running.' }
        $pidFile=Join-Path $PSScriptRoot 'studio-jobs/watcher.pid'
        if (Test-Path -LiteralPath $pidFile -PathType Leaf) {
            $savedPid=0
            if ([int]::TryParse((Get-Content -LiteralPath $pidFile -Raw).Trim(),[ref]$savedPid)) {
                $process=Get-CimInstance Win32_Process -Filter ("ProcessId="+$savedPid)
                if ($process) {
                    $expected=Join-Path $PSScriptRoot 'studio-watch.ps1'
                    if (!$process.CommandLine -or $process.CommandLine.IndexOf($expected,[StringComparison]::OrdinalIgnoreCase) -lt 0) {
                        throw 'Saved watcher PID does not identify this workspace worker; refusing to stop it.'
                    }
                    Stop-Process -Id $savedPid -ErrorAction Stop
                    Wait-Process -Id $savedPid -Timeout 10 -ErrorAction SilentlyContinue
                    if (Get-Process -Id $savedPid -ErrorAction SilentlyContinue) { throw 'Worker did not stop.' }
                }
            }
            Remove-Item -LiteralPath $pidFile -Force
        }
    }
    function Invoke-StudioCompose {
        & docker @composeArgs @args
        if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed: $LASTEXITCODE ($args)" }
    }
    & docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not running.' }

    Write-Host '[1/4] Validate configuration'
    Invoke-StudioCompose config --quiet
    if (-not $SkipBuild) {
        Write-Host '[2/4] Build backend and frontend'
        Invoke-StudioCompose build backend frontend
    }
    Write-Host '[3/4] Start services and wait for real health checks'
    Invoke-StudioCompose up -d --no-build --wait --wait-timeout 360 postgres redis backend frontend

    Write-Host '[4/4] Check Django and migration status'
    Invoke-StudioCompose exec -T backend python manage.py check
    Invoke-StudioCompose exec -T backend python manage.py showmigrations ai_builder
    if ($Test) {
        Invoke-StudioCompose exec -T backend python manage.py test ai_builder --noinput
    }
    Invoke-StudioCompose ps
    $watcherPid=Join-Path $PSScriptRoot 'studio-jobs/watcher.pid'
    $watcherRunning=$false
    if (Test-Path -LiteralPath $watcherPid -PathType Leaf) {
        $savedPid=0
        if ([int]::TryParse((Get-Content -LiteralPath $watcherPid -Raw).Trim(),[ref]$savedPid)) {
            $watcherRunning=$null -ne (Get-Process -Id $savedPid -ErrorAction SilentlyContinue)
        }
    }
    if (!$watcherRunning) {
        $runner=(Get-Process -Id $PID).Path
        $watcher=Join-Path $PSScriptRoot 'studio-watch.ps1'
        $stdout=Join-Path $PSScriptRoot 'studio-jobs/watcher.log'
        $stderr=Join-Path $PSScriptRoot 'studio-jobs/watcher-error.log'
        $process=Start-Process -FilePath $runner -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$watcher) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        [IO.File]::WriteAllText($watcherPid,[string]$process.Id,[Text.UTF8Encoding]::new($false))
        Write-Host "Cinematic worker started: PID $($process.Id)"
    } else {
        Write-Host "Cinematic worker already running"
    }
    Write-Host 'Studio: http://localhost:8001/studio' -ForegroundColor Green
} catch {
    $failure = $_
    Write-Host 'Studio startup failed. Diagnostics:' -ForegroundColor Red
    & docker @composeArgs ps -a
    & docker @composeArgs logs --no-color --tail 120 backend frontend
    & docker inspect --format '{{json .State.Health}}' tracknode20-backend-1
    throw $failure
} finally {
    Pop-Location
}
