param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [switch]$SkipVisualReview,
    [ValidateRange(0,1)][int]$MaxRepairs=0,
    [ValidateRange(0,1)][int]$MaxTechnicalRepairs=1,
    [ValidateSet("auto","immersive","product","split","cinematic","editorial","environment")][string]$HeroMode="auto",
    [switch]$RequireModel,
    [string]$PreflightDirectory=""
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
if ($PreflightDirectory) {
    $preflight=(Resolve-Path -LiteralPath $PreflightDirectory).Path
} else {
    $preflight=& (Join-Path $PSScriptRoot "studio-preflight.ps1") -Prompt $Prompt -Profile $Profile -AssetStyle $AssetStyle -HeroMode $HeroMode -RequireModel:$RequireModel -NoBuild -ReturnResult
}
$selection=Get-Content -LiteralPath (Join-Path $preflight "selection.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($selection.status -notin @("approved","no_model")) { throw "Preflight did not approve generation" }
if ($RequireModel -and $selection.status -ne "approved") { throw "Required model not approved" }
$out = (New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/" + [guid]::NewGuid().ToString())) -Force).FullName
Write-Host "Output: $out"
$prompt64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Prompt))
& docker @compose run --rm --no-deps -v "$($preflight):/preflight:ro" -v "$($out):/output" openhands --preflight --profile $Profile --asset-style $AssetStyle --prompt-b64 $prompt64
$generationExit=$LASTEXITCODE
if ($generationExit -ne 0 -and ($generationExit -ne 42 -or !(Test-Path -LiteralPath (Join-Path $out "source-failure.json")))) {
    throw "AI generation failed ($generationExit); checkpoint, if any, preserved: $out. No automatic paid retry for API or infrastructure errors."
}
$out = & (Join-Path $PSScriptRoot "studio-technical.ps1") -RunDirectory $out -Prompt $Prompt -Profile $Profile -AssetStyle $AssetStyle -MaxTechnicalRepairs $MaxTechnicalRepairs
$dist=Join-Path $out "dist"
$report=Join-Path $out "quality-report"
if ($SkipVisualReview) {
    Write-Host "Visual review skipped by request; artistic quality unverified."
} else {
    $result=& (Join-Path $PSScriptRoot "studio-visual-review.ps1") -RunDirectory $out -Prompt $Prompt -NoBuild -ReturnResult
    if ($result.Code -eq 2 -and $MaxRepairs -gt 0) {
        & (Join-Path $PSScriptRoot "studio-repair.ps1") -RunDirectory $out -ReviewFile $result.Report -Prompt $Prompt -Profile $Profile -AssetStyle $AssetStyle -MaxRepairs $MaxRepairs -NoBuild
    } elseif ($result.Code -ne 0) {
        throw "Visual review failed or requires revision. Outputs preserved: $out"
    } else {
        Write-Host "Technical and AI visual reviews passed; human acceptance remains separate."
    }
}
