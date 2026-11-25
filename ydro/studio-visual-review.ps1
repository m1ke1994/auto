param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [string]$Prompt="",
    [switch]$NoBuild,
    [switch]$ReturnResult
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$run = (Resolve-Path -LiteralPath $RunDirectory).Path
$audit = (Resolve-Path -LiteralPath (Join-Path $run "quality-report")).Path
if (!(Test-Path -LiteralPath (Join-Path $audit "quality-report.json"))) { throw "Missing technical audit report" }
if (!(Test-Path -LiteralPath .env.studio.local)) { throw "Missing .env.studio.local" }
$compose = @("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
if (!$NoBuild) {
    & docker @compose build openhands | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Critic build failed" }
}
$out = (New-Item -ItemType Directory -Path (Join-Path $run ("visual-review-" + [guid]::NewGuid().ToString("N")))).FullName
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
