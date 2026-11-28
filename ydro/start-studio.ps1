# Run from any working directory. Never deletes database volumes.
[CmdletBinding()]
param([switch]$SkipBuild, [switch]$Test, [switch]$RestartWatcher, [switch]$RefreshRuntime)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
$maintenance=$false
$promotionStarted=$false
$previousImages=@{}
$stagedImages=@{}
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
    function Assert-IdleQueue {
        $active=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'studio-jobs/pending'),(Join-Path $PSScriptRoot 'studio-jobs/running') -Filter '*.json' -File)
        if($active.Count){throw 'Finish queued/running jobs before refreshing Studio runtime.'}
    }
    function Get-RuntimeImageId([string]$Image) {
        try {
            $id=& docker image inspect --format '{{.Id}}' $Image 2>$null
            if($LASTEXITCODE -eq 0 -and $id -match '^sha256:[a-f0-9]{64}$'){return [string]$id}
        }catch{}
        return $null
    }
    if ($RestartWatcher -or $RefreshRuntime) { Assert-IdleQueue }
    if ($RefreshRuntime) {
        $suffix='refresh-'+[guid]::NewGuid().ToString('N')
        $agent='tracknode20-agent-openhands:latest'
        $audit='tracknode-studio-audit:latest'
        $stagedImages[$agent]='tracknode20-agent-openhands:'+$suffix
        $stagedImages[$audit]='tracknode-studio-audit:'+$suffix
        Write-Host '[Runtime] Build staged generator (existing Studio remains online)'
        & docker build -t $stagedImages[$agent] -f docker/studio-agent/Dockerfile docker/studio-agent
        if ($LASTEXITCODE -ne 0) { throw 'Studio agent image build failed; active runtime was not changed.' }
        Write-Host '[Runtime] Build staged browser audit'
        & docker build -t $stagedImages[$audit] -f docker/studio-audit/Dockerfile docker/studio-audit
        if ($LASTEXITCODE -ne 0) { throw 'Studio audit image build failed; active runtime was not changed.' }
        foreach($image in $stagedImages.Keys){$previousImages[$image]=Get-RuntimeImageId $image}
    }
    if ($RestartWatcher -or $RefreshRuntime) {
        Assert-IdleQueue
        $maintenance=$true
        Invoke-StudioCompose stop backend
        Assert-IdleQueue
        if ($RefreshRuntime) {
            $promotionStarted=$true
            foreach($image in @('tracknode20-agent-openhands:latest','tracknode-studio-audit:latest')){
                & docker tag $stagedImages[$image] $image
                if($LASTEXITCODE -ne 0){throw "Studio runtime promotion failed: $image"}
            }
            Write-Host 'STUDIO_RUNTIME_REFRESHED'
        }
        if ($RestartWatcher) { & (Join-Path $PSScriptRoot 'studio-worker.ps1') -Restart }
    }
    if (-not $SkipBuild) {
        Write-Host '[2/4] Build backend and frontend'
        Invoke-StudioCompose build backend frontend
    }
    Write-Host '[3/4] Start services and wait for real health checks'
    Invoke-StudioCompose up -d --no-build --wait --wait-timeout 360 postgres redis backend frontend
    $maintenance=$false
    $promotionStarted=$false

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
    if($maintenance){
        $rollbackOK=$true
        if($promotionStarted){
            foreach($image in $previousImages.Keys){
                try{
                    if($previousImages[$image]){
                        & docker tag $previousImages[$image] $image
                        if($LASTEXITCODE -ne 0){throw "Cannot restore $image"}
                    }else{
                        $rollbackOK=$false
                        Write-Warning "No previous image exists for $image"
                    }
                }catch{$rollbackOK=$false;Write-Warning $_.Exception.Message}
            }
        }
        if($rollbackOK){
            try{
                & docker @composeArgs start backend
                if($LASTEXITCODE -ne 0){throw 'Backend restart failed'}
                Write-Host 'STUDIO_BACKEND_RESTART_REQUESTED: verify health.'
            }catch{Write-Warning $_.Exception.Message}
        }else{Write-Warning 'Runtime rollback incomplete. Verify backend and runtime tags before retrying.'}
    }
    Write-Host 'Studio startup failed. Diagnostics:' -ForegroundColor Red
    & docker @composeArgs ps -a
    & docker @composeArgs logs --no-color --tail 120 backend frontend
    & docker inspect --format '{{json .State.Health}}' tracknode20-backend-1
    throw $failure
} finally {
    # Remove only this invocation's temporary image tags, never containers or volumes.
    foreach($image in $stagedImages.Values){
        try {
            if(Get-RuntimeImageId $image){& docker image rm $image | Out-Host}
        }catch{Write-Warning "Temporary runtime tag retained: $image"}
    }
    Pop-Location
}
