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
    [switch]$ReturnResult,
    [switch]$SelfTest
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot

function Get-CandidateNames([string]$Json) {
    # Windows PowerShell 5.1 may emit a top-level JSON array as ONE pipeline
    # object. Parse an object containing the array instead; emit scalar names.
    $manifest=ConvertFrom-Json -InputObject ('{"items":' + $Json + '}') -ErrorAction Stop
    $items=$manifest.items
    if ($items -isnot [System.Array] -or $items.Count -gt 4) {
        throw "Invalid candidate manifest: expected an array of zero to four records"
    }
    for ($index=0; $index -lt $items.Count; $index++) {
        $expected="candidate-$($index+1)"
        $item=$items[$index]
        if ($item -isnot [PSCustomObject] -or $item.folder -cne $expected) {
            throw "Invalid candidate record at index $index; expected $expected"
        }
    }
    # Return individual strings, never the original array as a pipeline object.
    for ($index=0; $index -lt $items.Count; $index++) {
        Write-Output ("candidate-" + ($index+1))
    }
}

function Test-CandidateManifest {
    $samples=@(
        @{ Json='[]'; Expected='' },
        @{ Json='[{"folder":"candidate-1"}]'; Expected='candidate-1' },
        @{ Json='[{"folder":"candidate-1"},{"folder":"candidate-2"}]'; Expected='candidate-1,candidate-2' },
        @{ Json='[{"folder":"candidate-1"},{"folder":"candidate-2"},{"folder":"candidate-3"}]'; Expected='candidate-1,candidate-2,candidate-3' },
        @{ Json='[{"folder":"candidate-1"},{"folder":"candidate-2"},{"folder":"candidate-3"},{"folder":"candidate-4"}]'; Expected='candidate-1,candidate-2,candidate-3,candidate-4' }
    )
    foreach ($sample in $samples) {
        $actual=@(Get-CandidateNames $sample.Json)
        if (($actual -join ',') -cne $sample.Expected) {
            throw "Candidate manifest regression test failed"
        }
    }
    foreach ($invalid in @('{}','null','[{"folder":"../outside"}]','[{"folder":"candidate-1"},{"folder":"candidate-1"}]','[{},{},{}]','[{},{},{},{},{}]')) {
        $rejected=$false
        try { $null=Get-CandidateNames $invalid } catch { $rejected=$true }
        if (!$rejected) { throw "Candidate manifest accepted invalid input" }
    }
    Write-Host "CANDIDATE_MANIFEST_TESTS_PASSED: 0/1/2/3/4 candidates and invalid inputs"
}
Test-CandidateManifest
if ($SelfTest) { return }

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
    $oldCandidates=@(Get-CandidateNames (Get-Content -LiteralPath (Join-Path $out "candidates.json") -Raw -Encoding UTF8))
    if (Test-Path -LiteralPath (Join-Path $previous "catalog-review.json") -PathType Leaf) {
        Copy-Item -LiteralPath (Join-Path $previous "catalog-review.json") -Destination (Join-Path $out "catalog-review.json")
    }
    foreach ($folderName in $oldCandidates) {
        $sourceArchive=Join-Path (Join-Path $previous $folderName) "candidate.zip"
        if (!(Test-Path -LiteralPath $sourceArchive -PathType Leaf)) {
            throw "Saved candidate archive missing: $folderName"
        }
        $folder=(New-Item -ItemType Directory -Path (Join-Path $out $folderName)).FullName
        Copy-Item -LiteralPath $sourceArchive -Destination (Join-Path $folder "candidate.zip")
    }
    Write-Host "ASSET_RESUME: saved plan and archives; no search, downloads or planner API"
} else {
    $extra=@()
    if ($RequireModel) { $extra+= "--require-model" }
    if ($AssetQuery.Count -gt 6) { throw "Maximum six manual queries" }
    foreach ($query in $AssetQuery) { $extra+= @("--asset-query",$query) }
    if ($AssetSubject) { $extra+= @("--asset-subject",$AssetSubject) }
    if ($ExcludeModelId.Count -gt 16) { throw "Maximum 16 excluded model IDs" }
    foreach ($id in $ExcludeModelId) { $extra+= @("--exclude-model-id",$id) }
    & docker @compose run --rm --no-deps --entrypoint python -v "$($out):/preflight" openhands /opt/studio-agent/asset_preflight.py prepare --brief $Prompt --profile $Profile --style $AssetStyle --hero $HeroMode @extra | Out-Host
    Check "Asset preparation"
}
$candidates=@(Get-CandidateNames (Get-Content -LiteralPath (Join-Path $out "candidates.json") -Raw -Encoding UTF8))
Write-Host "ASSET_CANDIDATE_COUNT: $($candidates.Count)"
foreach ($folderName in $candidates) {
    if (!(Test-Path -LiteralPath (Join-Path (Join-Path $out $folderName) "candidate.zip") -PathType Leaf)) {
        throw "Candidate archive missing: $folderName"
    }
}
$rendered=0
foreach ($folderName in $candidates) {
    Write-Host "ASSET_RENDER_START: $folderName"
    $folder=Join-Path $out $folderName
    $archive=Join-Path $folder "candidate.zip"
    if (!(Test-Path -LiteralPath $archive -PathType Leaf)) {
        throw "Candidate archive missing: $folderName"
    }
    $source=Join-Path $folder "site"
    Expand-Archive -LiteralPath $archive -DestinationPath $source
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docker/studio-agent/CinemaModel.vue") -Destination (Join-Path $source "src/components/CinemaModel.vue") -Force
    $dist=(New-Item -ItemType Directory -Path (Join-Path $folder "dist")).FullName
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Candidate build rejected"
        continue
    }
    # Candidate folders are created by the isolated agent (uid 10001). Match
    # that uid so Playwright can write screenshots/diagnostics to the bind mount.
    docker run --rm --user 10001:10001 --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($folder):/report" --entrypoint node tracknode-studio-audit /opt/audit/asset-preview.mjs | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Candidate render rejected"
        continue
    }
    if (Test-Path -LiteralPath (Join-Path $folder "render-ok.json")) { $rendered++ }
}
Write-Host "ASSET_RENDER_COUNT: $rendered/$($candidates.Count)"
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
