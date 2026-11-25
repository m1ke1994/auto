param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [string]$Prompt="",
    [switch]$NoBuild,
    [switch]$ReturnResult,
    [switch]$ForceRetry
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$run = (Resolve-Path -LiteralPath $RunDirectory).Path
$audit = (Resolve-Path -LiteralPath (Join-Path $run "quality-report")).Path
if (!(Test-Path -LiteralPath (Join-Path $audit "quality-report.json"))) { throw "Missing technical audit report" }
if (!(Test-Path -LiteralPath .env.studio.local)) { throw "Missing .env.studio.local" }
$reviewFiles = @((Get-Item -LiteralPath (Join-Path $audit "quality-report.json"))) + @(Get-ChildItem -LiteralPath $audit -File -Filter "*.png")
$reviewFiles = @($reviewFiles | Sort-Object Name)
if ($reviewFiles.Count -lt 6) { throw "Insufficient audit screenshots; no visual API call made." }
$material = [System.Text.StringBuilder]::new()
foreach ($file in $reviewFiles) {
    $fileHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    [void]$material.Append($file.Name).Append("|").Append($fileHash).Append([char]10)
}
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $fingerprint = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($material.ToString()))).Replace("-","").ToLowerInvariant()
}
finally { $sha.Dispose() }
$blocklistPath = Join-Path $PSScriptRoot "studio-visual-review-blocklist.json"
$ledgerPath = Join-Path $PSScriptRoot ".studio-visual-review-ledger.json"
if (!$ForceRetry) {
    if (Test-Path -LiteralPath $blocklistPath) {
        $blocked = Get-Content -LiteralPath $blocklistPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (@($blocked.fingerprints) -contains $fingerprint) {
            throw "This exact screenshot set was already sent for paid visual review. No API call made. Change the site, run offline recheck, then review new screenshots."
        }
    }
    if (Test-Path -LiteralPath $ledgerPath) {
        $ledger = Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (@($ledger.fingerprints) -contains $fingerprint) {
            throw "This exact screenshot set has already been reviewed in this workspace. No API call made. Use -ForceRetry only if you intentionally accept another charge."
        }
    }
}
if ($ForceRetry) { Write-Warning "ForceRetry enabled: an identical screenshot review may incur another API charge." }
$compose = @("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
if (!$NoBuild) {
    & docker @compose build openhands | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Critic build failed" }
}
$out = (New-Item -ItemType Directory -Path (Join-Path $run ("visual-review-" + [guid]::NewGuid().ToString("N")))).FullName
$ledger = @{ version=1; fingerprints=@() }
if (Test-Path -LiteralPath $ledgerPath) {
    $oldLedger = Get-Content -LiteralPath $ledgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $ledger.fingerprints = @($oldLedger.fingerprints)
}
$ledger.fingerprints = @($ledger.fingerprints) + @($fingerprint)
$tempLedger = $ledgerPath + ".tmp"
[IO.File]::WriteAllText($tempLedger,($ledger | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tempLedger -Destination $ledgerPath -Force
Write-Host "Visual review sends website screenshots to DeepSeek Flash using the existing API key."
$cli = @("--brief",$Prompt)
if ([string]::IsNullOrWhiteSpace($Prompt)) { $cli = @() }
& docker @compose run --rm --no-deps --entrypoint python -v "$($audit):/audit:ro" -v "$($out):/visual-output" openhands /opt/studio-agent/visual_critic.py @cli | Out-Host
$code = $LASTEXITCODE
Write-Host "Visual review report: $out\visual-review.json"
if ($ReturnResult) {
    return [pscustomobject]@{ Code=$code; Report=(Join-Path $out "visual-review.json") }
}
if ($code -ne 0) { throw "Visual review failed or requires revision ($code). Existing site preserved." }
