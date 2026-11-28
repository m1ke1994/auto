# Run from any working directory. Never deletes database volumes.
[CmdletBinding()]
param([switch]$SkipBuild, [switch]$Test, [switch]$RestartWatcher, [switch]$RefreshRuntime)
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
    & (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1')
    function Invoke-StudioCompose {
        & docker @composeArgs @args
        if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed: $LASTEXITCODE ($args)" }
    }
    & docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not running.' }

    Write-Host '[1/4] Validate configuration'
    Invoke-StudioCompose config --quiet
    if ($RestartWatcher -or $RefreshRuntime) {
        $active=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'studio-jobs/pending'),(Join-Path $PSScriptRoot 'studio-jobs/running') -Filter '*.json' -File)
        if($active.Count){throw 'Finish queued/running jobs before restarting the Studio worker.'}
        Invoke-StudioCompose stop backend
        if ($RefreshRuntime) {
            Write-Host '[Runtime] Refresh trusted generator and browser audit images'
            & docker compose --env-file .env.studio.local -p tracknode20-agent -f docker-compose.openhands.yml build openhands
            if ($LASTEXITCODE -ne 0) { throw 'Studio agent image build failed; generation remains disabled until startup succeeds.' }
            & docker build -t tracknode-studio-audit -f docker/studio-audit/Dockerfile docker/studio-audit
            if ($LASTEXITCODE -ne 0) { throw 'Studio audit image build failed; generation remains disabled until startup succeeds.' }
        }
        if ($RestartWatcher) { & (Join-Path $PSScriptRoot 'studio-worker.ps1') -Restart }
    }
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
    & (Join-Path $PSScriptRoot 'studio-worker.ps1')
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
