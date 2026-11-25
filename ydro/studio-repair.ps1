param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [Parameter(Mandatory=$true)][string]$ReviewFile,
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [ValidateRange(1,1)][int]$MaxRepairs=1,
    [switch]$NoBuild,
    [switch]$ForceRetry
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$review=(Resolve-Path -LiteralPath $ReviewFile).Path
$reviewHash=(Get-FileHash -LiteralPath $review -Algorithm SHA256).Hash.ToLowerInvariant()
$blocklistPath=Join-Path $PSScriptRoot "studio-repair-blocklist.json"
$ledgerPath=Join-Path $PSScriptRoot ".studio-repair-ledger.json"
if (!$ForceRetry) {
    if (Test-Path -LiteralPath $blocklistPath) {
        $blocked=Get-Content -LiteralPath $blocklistPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (@($blocked.sha256) -contains $reviewHash) {
            throw "This exact visual report has already triggered a paid repair attempt. No AI call made; patch the source and use studio-recheck.ps1 instead."
        }
    }
    if (Test-Path -LiteralPath $ledgerPath) {
        $ledger=Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (@($ledger.sha256) -contains $reviewHash) {
            throw "This exact visual report has already been used for repair in this workspace. No AI call made. Use -ForceRetry only if you intentionally accept another charge."
        }
    }
}
if ($ForceRetry) { Write-Warning "ForceRetry enabled: this repair may incur another API charge." }
function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE); all previous outputs preserved" }
}
function Test-ArchiveHasImportedModel([string]$ArchivePath) {
    Add-Type -AssemblyName System.IO.Compression
    $stream = [System.IO.File]::OpenRead($ArchivePath)
    $zip = $null
    try {
        $zip = [System.IO.Compression.ZipArchive]::new(
            $stream,
            [System.IO.Compression.ZipArchiveMode]::Read,
            $false
        )
        $entry = $zip.GetEntry("MODEL_CREDITS.json")
        if ($null -eq $entry) { return $false }
        if ($entry.Length -le 0 -or $entry.Length -gt 131072) {
            throw "Invalid MODEL_CREDITS.json size in source archive."
        }
        $reader = [System.IO.StreamReader]::new($entry.Open(), [Text.Encoding]::UTF8)
        try {
            $credits = ConvertFrom-Json -InputObject $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
        return (@($credits).Count -gt 0)
    }
    finally {
        if ($null -ne $zip) { $zip.Dispose() } else { $stream.Dispose() }
    }
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
    $reviewedDevices = @()
    foreach ($device in @("desktop","mobile")) {
        $deviceReview = $inputReview.devices.$device
        if ($device -eq "mobile" -and $deviceReview.status -eq "skipped_desktop_failed") { continue }
        $assetScore = $deviceReview.scores.asset_quality
        if ($null -eq $assetScore -or ($assetScore -isnot [int] -and $assetScore -isnot [long]) -or $assetScore -lt 0 -or $assetScore -gt 25) {
            throw "Visual review has an invalid asset_quality score for $device."
        }
        $reviewedDevices += $device
    }
    if ($reviewedDevices -notcontains "desktop") { throw "A desktop visual review is required before repair." }
    $lowAssetQuality = $false
    foreach ($device in $reviewedDevices) {
        if ($inputReview.devices.$device.scores.asset_quality -lt 18) { $lowAssetQuality = $true }
    }
    if ($lowAssetQuality) {
        if (Test-ArchiveHasImportedModel $archive) {
            throw "Imported 3D model asset quality is below 18/25; do not spend repair tokens. Re-run model preflight first."
        }
        Write-Host "PHOTO_ASSET_REPAIR_ALLOWED: no imported 3D model; targeted Pexels photo repair may address the visual critic's asset deficit." -ForegroundColor Yellow
    }
    $out=(New-Item -ItemType Directory -Path (Join-Path $PWD ("studio-agent-output/repair-" + [guid]::NewGuid().ToString()))).FullName
    Write-Host "REPAIR_ATTEMPT: $i/$MaxRepairs"
    Write-Host "REPAIR_OUTPUT: $out"
    $ledger=@{ version=1; sha256=@() }
    if (Test-Path -LiteralPath $ledgerPath) {
        $oldLedger=Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $ledger.sha256=@($oldLedger.sha256)
    }
    $ledger.sha256=@($ledger.sha256)+@($reviewHash)
    $tempLedger=$ledgerPath+".tmp"
    [IO.File]::WriteAllText($tempLedger,($ledger | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tempLedger -Destination $ledgerPath -Force
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
