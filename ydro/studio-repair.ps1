param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [Parameter(Mandatory=$true)][string]$ReviewFile,
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [ValidateRange(1,1)][int]$MaxRepairs=1,
    [switch]$NoBuild
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$review=(Resolve-Path -LiteralPath $ReviewFile).Path
function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE); all previous outputs preserved" }
}
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
if (!(Test-Path -LiteralPath .env.studio.local)) { throw "Missing .env.studio.local" }
if (!$NoBuild) {
    & docker @compose build openhands
    Assert-Exit "Agent build"
    docker build -t tracknode-studio-build -f docker/studio-build/Dockerfile docker/studio-build
    Assert-Exit "Site builder build"
    docker build -t tracknode-studio-audit docker/studio-audit
    Assert-Exit "Browser audit build"
}
for ($i=1; $i -le $MaxRepairs; $i++) {
    $archive=(Resolve-Path -LiteralPath (Join-Path $run "tracknode-agent-site.zip")).Path
    $inputReview=Get-Content -LiteralPath $review -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($inputReview.status -ne "needs_revision" -or $inputReview.passed -ne $false) { throw "Expected a rejected visual review" }
    if ($inputReview.devices.desktop.scores.asset_quality -lt 18 -or $inputReview.devices.mobile.scores.asset_quality -lt 18) { throw "Asset quality too low; do not spend repair tokens until the asset has passed preflight." }
    $out=(New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/repair-" + [guid]::NewGuid().ToString()))).FullName
    Write-Host "REPAIR_ATTEMPT: $i/$MaxRepairs"
    Write-Host "REPAIR_OUTPUT: $out"
    & docker @compose run --rm --no-deps -v "$($archive):/repair-source.zip:ro" -v "$($review):/repair-review.json:ro" -v "$($out):/output" openhands --repair --profile $Profile --asset-style $AssetStyle --prompt $Prompt
    Assert-Exit "AI repair"
    $source=Join-Path $out "site"
    Expand-Archive -LiteralPath (Join-Path $out "tracknode-agent-site.zip") -DestinationPath $source
    $dist=(New-Item -ItemType Directory -Path (Join-Path $out "dist")).FullName
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build
    Assert-Exit "Offline Vite build"
    $audit=(New-Item -ItemType Directory -Path (Join-Path $out "quality-report")).FullName
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($audit):/report" tracknode-studio-audit $Profile
    Assert-Exit "Browser audit"
    $result=& (Join-Path $PSScriptRoot "studio-visual-review.ps1") -RunDirectory $out -Prompt $Prompt -NoBuild -ReturnResult
    if ($result.Code -eq 0) {
        Write-Host "REPAIR_ACCEPTED: $out"
        Write-Host "Preview folder: $dist"
        return
    }
    if ($result.Code -ne 2) { throw "Visual review unavailable. Outputs preserved." }
    $run=$out
    $review=$result.Report
}
Write-Host "REPAIR_LIMIT_REACHED: $run"
Write-Host "Last visual report: $review"
throw "Visual quality threshold not reached. No site automatically accepted or published."
