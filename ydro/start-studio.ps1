# Run from any working directory. Never deletes database volumes.
[CmdletBinding()]
param([switch]$SkipBuild, [switch]$Test)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $composeArgs = @('compose', '-p', 'tracknode20', '-f', 'docker-compose.yml', '-f', 'docker-compose.studio.yml')
    if (Test-Path '.env.studio.local' -PathType Leaf) {
        $composeArgs += @('--env-file', '.env.studio.local')
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
