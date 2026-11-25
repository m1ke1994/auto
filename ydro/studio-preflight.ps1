param(
    [string]$Prompt="",
    [string]$ResumeDirectory="",
    [switch]$RenderOnly,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [ValidateSet("auto","immersive","product","split","cinematic","editorial","environment")][string]$HeroMode="auto",
    [switch]$RequireModel,
    [string[]]$AssetQuery=@(),
    [string]$AssetSubject="",
    [string[]]$ExcludeModelId=@(),
    [switch]$NoBuild,
    [switch]$ReturnResult
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
if (!$ResumeDirectory -and [string]::IsNullOrWhiteSpace($Prompt)) {
    throw "Prompt required for a new search"
}
if ($RenderOnly -and !$ResumeDirectory) {
    throw "RenderOnly requires ResumeDirectory to avoid paid planning requests"
}
if (!$RenderOnly -and !(Test-Path -LiteralPath .env.studio.local)) {
    throw "Missing .env.studio.local"
}
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
function Check([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE)" }
}
if (!$NoBuild) {
    if (!$RenderOnly) {
        & docker @compose build openhands | Out-Host
        Check "Agent build"
    }
    docker build -t tracknode-studio-build docker/studio-build | Out-Host
    Check "Builder build"
    docker build -t tracknode-studio-audit docker/studio-audit | Out-Host
    Check "Audit build"
}
$out=(New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/preflight-"+[guid]::NewGuid().ToString()))).FullName
Write-Host "PREFLIGHT_OUTPUT: $out"
if ($ResumeDirectory) {
    $previous=(Resolve-Path -LiteralPath $ResumeDirectory).Path
    foreach ($name in @("plan.json","candidates.json")) {
        Copy-Item -LiteralPath (Join-Path $previous $name) -Destination (Join-Path $out $name)
    }
    $oldCandidates=@(Get-Content -LiteralPath (Join-Path $out "candidates.json") -Raw -Encoding UTF8 | ConvertFrom-Json)
    if ($oldCandidates.Count -gt 2) { throw "Too many saved candidates" }
    foreach ($candidate in $oldCandidates) {
        if ($candidate.folder -notin @("candidate-1","candidate-2")) { throw "Unexpected saved candidate folder" }
        $folder=(New-Item -ItemType Directory -Path (Join-Path $out $candidate.folder)).FullName
        Copy-Item -LiteralPath (Join-Path (Join-Path $previous $candidate.folder) "candidate.zip") -Destination (Join-Path $folder "candidate.zip")
    }
    Write-Host "ASSET_RESUME: saved plan and archives; no search, downloads or planner API"
} else {
    $extra=@()
    if ($RequireModel) { $extra+= "--require-model" }
    if ($AssetQuery.Count -gt 2) { throw "Maximum two manual queries" }
    foreach ($query in $AssetQuery) { $extra+= @("--asset-query",$query) }
    if ($AssetSubject) { $extra+= @("--asset-subject",$AssetSubject) }
    if ($ExcludeModelId.Count -gt 16) { throw "Maximum 16 excluded model IDs" }
    foreach ($id in $ExcludeModelId) { $extra+= @("--exclude-model-id",$id) }
    & docker @compose run --rm --no-deps --entrypoint python -v "$($out):/preflight" openhands /opt/studio-agent/asset_preflight.py prepare --brief $Prompt --profile $Profile --style $AssetStyle --hero $HeroMode @extra | Out-Host
    Check "Asset preparation"
}
$candidates=@(Get-Content -LiteralPath (Join-Path $out "candidates.json") -Raw -Encoding UTF8 | ConvertFrom-Json)
if ($candidates.Count -gt 2) { throw "Too many candidates" }
$rendered=0
foreach ($candidate in $candidates) {
    if ($candidate.folder -notin @("candidate-1","candidate-2")) { throw "Unexpected candidate folder" }
    $folder=Join-Path $out $candidate.folder
    $source=Join-Path $folder "site"
    Expand-Archive -LiteralPath (Join-Path $folder "candidate.zip") -DestinationPath $source
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docker/studio-agent/CinemaModel.vue") -Destination (Join-Path $source "src/components/CinemaModel.vue") -Force
    $dist=(New-Item -ItemType Directory -Path (Join-Path $folder "dist")).FullName
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Candidate build rejected"
        continue
    }
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($folder):/report" --entrypoint node tracknode-studio-audit /opt/audit/asset-preview.mjs | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Candidate render rejected"
        continue
    }
    if (Test-Path -LiteralPath (Join-Path $folder "render-ok.json")) { $rendered++ }
}
Write-Host "ASSET_RENDER_COUNT: $rendered"
if ($RenderOnly) {
    Write-Host "RENDER_ONLY: no paid visual critic request; output: $out"
    if ($rendered -eq 0) { throw "No candidate rendered; inspect render-diagnostics.json" }
    if ($ReturnResult) { return $out }
    return
}
& docker @compose run --rm --no-deps --entrypoint python -v "$($out):/preflight" openhands /opt/studio-agent/asset_preflight.py select | Out-Host
$code=$LASTEXITCODE
Write-Host "Asset selection: $out\selection.json"
if ($code -ne 0) { throw "Preflight did not approve a required model ($code). No expensive generation started." }
if ($ReturnResult) { return $out }
