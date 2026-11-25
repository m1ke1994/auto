param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [switch]$SkipVisualReview
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (!(Test-Path .env.studio.local)) { throw "Missing .env.studio.local" }
$compose = @("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE)" }
}
& docker @compose build openhands
Assert-Exit "Agent build"
& docker @compose run --rm --no-deps openhands --check
Assert-Exit "SDK check"
docker build -t tracknode-studio-build -f docker/studio-build/Dockerfile docker/studio-build
Assert-Exit "Site builder build"
docker build -t tracknode-studio-audit docker/studio-audit
Assert-Exit "Browser audit image build"
$out = (New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/" + [guid]::NewGuid().ToString())) -Force).FullName
Write-Host "Output: $out"
& docker @compose run --rm --no-deps -v "$($out):/output" openhands --profile $Profile --asset-style $AssetStyle --prompt $Prompt
Assert-Exit "AI generation"
$archive = Join-Path $out "tracknode-agent-site.zip"
if (!(Test-Path -LiteralPath $archive)) { throw "Missing source ZIP" }
$source = Join-Path $out "site"
Expand-Archive -LiteralPath $archive -DestinationPath $source
$dist = (New-Item -ItemType Directory -Path (Join-Path $out "dist")).FullName
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build
Assert-Exit "Offline Vite build"
if (!(Test-Path (Join-Path $dist "index.html"))) { throw "No built index.html" }
Write-Host "SOURCE_AND_BUILD_READY: $out"
Write-Host "Preview folder: $dist"
$report = (New-Item -ItemType Directory -Path (Join-Path $out "quality-report")).FullName
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($report):/report" tracknode-studio-audit $Profile
Assert-Exit "Browser quality audit (source and dist preserved)"
Write-Host "QUALITY_CHECKS_PASSED: $report"
if ($SkipVisualReview) {
    Write-Host "Visual review skipped by request; artistic quality unverified."
} else {
    & (Join-Path $PSScriptRoot "studio-visual-review.ps1") -RunDirectory $out -Prompt $Prompt -NoBuild
    Write-Host "Technical and AI visual reviews passed; human acceptance remains separate."
}
