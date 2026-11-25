param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema"
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$dist=(Resolve-Path -LiteralPath (Join-Path $run "dist")).Path
if (!(Test-Path -LiteralPath (Join-Path $dist "index.html") -PathType Leaf)) { throw "Missing built index.html" }
docker image inspect tracknode-studio-audit | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Build tracknode-studio-audit first." }
# Preserve original build, source, checkpoint and reports; no API key or network.
$out=(New-Item -ItemType Directory -Path (Join-Path $run ("audit-recheck-"+[guid]::NewGuid().ToString("N")))).FullName
Write-Host "AUDIT_RECHECK_OUTPUT: $out"
docker run --pull never --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($out):/report" tracknode-studio-audit $Profile | Out-Host
$code=$LASTEXITCODE
$reportPath=Join-Path $out "quality-report.json"
Write-Host "REPORT: $reportPath"
if (!(Test-Path -LiteralPath $reportPath -PathType Leaf)) { throw "Audit infrastructure failed ($code); existing build preserved." }
$r=Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "FUNCTIONAL_PASSED: $($r.functionalPassed)"
Write-Host "SCREENSHOTS_COMPLETE: $($r.screenshotsComplete)"
Write-Host "PREVIEW: $dist"
if ($code -ne 0 -or $r.passed -ne $true -or $r.functionalPassed -ne $true -or $r.screenshotsComplete -ne $true) {
    throw "Audit incomplete or failed ($code); report and build preserved. No paid AI calls."
}
Write-Host "BROWSER_AUDIT_PASSED: $out" -ForegroundColor Green
Write-Host "Source approval and artistic quality remain unverified by this command."
