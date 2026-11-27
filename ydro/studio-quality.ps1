param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [switch]$SkipVisualReview,
    [switch]$RebuildImages,
    [switch]$AllowVisualWarnings,
    [ValidateRange(0,1)][int]$MaxRepairs=0,
    [ValidateRange(0,1)][int]$MaxTechnicalRepairs=0,
    [ValidateSet("auto","immersive","product","split","cinematic","editorial","environment")][string]$HeroMode="auto",
    [switch]$RequireModel,
    [string]$PreflightDirectory="",
    [string]$ResultFile="",
    [string]$ProgressFile="",
    [string]$ContactsJson=""
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot "studio-progress.ps1")
if ($AllowVisualWarnings -and $MaxRepairs -gt 0) { throw "Preview mode does not allow automatic paid visual repairs." }
. (Join-Path $PSScriptRoot "studio-visual-policy.ps1")
if (!(Test-Path .env.studio.local)) { throw "Missing .env.studio.local" }
$compose = @("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE)" }
}
Write-StudioProgress $ProgressFile "preparing"
function Ensure-StudioImage([string]$Image,[scriptblock]$Build,[string]$Label) {
    $exists=$false
    if (!$RebuildImages) {
        & docker image inspect $Image *> $null
        $exists=($LASTEXITCODE -eq 0)
    }
    if ($exists) {
        Write-Host "IMAGE_READY: $Image (reuse local image)"
        return
    }
    Write-Host "IMAGE_BUILD: $Image"
    & $Build
    Assert-Exit "$Label build"
}
Ensure-StudioImage "tracknode20-agent-openhands:latest" { & docker @compose build openhands } "Agent"
Ensure-StudioImage "tracknode-studio-build:latest" { docker build -t tracknode-studio-build -f docker/studio-build/Dockerfile docker/studio-build } "Site builder"
Ensure-StudioImage "tracknode-studio-audit:latest" { docker build -t tracknode-studio-audit docker/studio-audit } "Browser audit"
& docker @compose run --rm --no-deps openhands --check
Assert-Exit "SDK check"
Write-StudioProgress $ProgressFile "assets"
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
Write-StudioProgress $ProgressFile "generating"
$prompt64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Prompt))
$contactArgs=@()
if ($ContactsJson -and $ContactsJson -ne '{}') {
    if ($ContactsJson.Length -gt 3000) { throw 'Contact data exceeds limit' }
    $contactArgs=@('--contacts-b64',[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($ContactsJson)))
}
& docker @compose run --rm --no-deps -v "$($preflight):/preflight:ro" -v "$($out):/output" openhands --preflight --profile $Profile --asset-style $AssetStyle --prompt-b64 $prompt64 @contactArgs
$generationExit=$LASTEXITCODE
if ($generationExit -ne 0 -and ($generationExit -ne 42 -or !(Test-Path -LiteralPath (Join-Path $out "source-failure.json")))) {
    throw "AI generation failed ($generationExit); checkpoint, if any, preserved: $out. No automatic paid retry for API or infrastructure errors."
}
$out = & (Join-Path $PSScriptRoot "studio-technical.ps1") -RunDirectory $out -Prompt $Prompt -Profile $Profile -AssetStyle $AssetStyle -MaxTechnicalRepairs $MaxTechnicalRepairs -ProgressFile $ProgressFile
$dist=Join-Path $out "dist"
$report=Join-Path $out "quality-report"
Write-StudioProgress $ProgressFile "visual-review"
if ($AllowVisualWarnings) {
    # This branch is reachable only after studio-technical returned a passed run.
    # Keep the strict CLI behavior below; Studio can inspect a technically valid draft.
    $visual=@{status='skipped';score=$null;threshold=85}
    if (!$SkipVisualReview) {
        $visual=@{status='unavailable';score=$null;threshold=85}
        try {
            $result=& (Join-Path $PSScriptRoot "studio-visual-review.ps1") -RunDirectory $out -Prompt $Prompt -NoBuild -ReturnResult
            $review=$null
            if ($result.Report -and (Test-Path -LiteralPath $result.Report -PathType Leaf)) {
                $review=Get-Content -LiteralPath $result.Report -Raw -Encoding UTF8 | ConvertFrom-Json
            }
            $visual=Get-StudioVisualOutcome $result.Code $review
        } catch {
            # Do not expose provider bodies/credentials. The review script retains diagnostics.
            Write-Warning "Visual review unavailable; keeping technically passed local preview."
        }
    }
    $visual.technical_passed=$true
    $meta=Join-Path $out "studio-result.json"
    [IO.File]::WriteAllText($meta,($visual | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
    Write-Host "STUDIO_PREVIEW_READY: $out; visual_status=$($visual.status); score=$($visual.score)"
    if ($visual.status -ne 'passed') { Write-Warning "Preview only: premium visual acceptance has not been achieved." }
} elseif ($SkipVisualReview) {
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
Write-StudioProgress $ProgressFile "finalizing"
if ($ResultFile) {
    $target=[IO.Path]::GetFullPath($ResultFile)
    $parent=Split-Path -Parent $target
    if (!(Test-Path -LiteralPath $parent -PathType Container)) { throw "ResultFile parent does not exist" }
    [IO.File]::WriteAllText($target,$out,[Text.UTF8Encoding]::new($false))
}
