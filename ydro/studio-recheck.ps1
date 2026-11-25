param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [switch]$FixHorizontalOverflow
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$run = (Resolve-Path -LiteralPath $RunDirectory).Path
$oldSource = Join-Path $run "site"
if (!(Test-Path -LiteralPath (Join-Path $oldSource "src/style.css") -PathType Leaf)) {
    throw "Existing generated site/src/style.css not found"
}
if ($FixHorizontalOverflow) {
    $oldReport = Join-Path $run "quality-report/quality-report.json"
    if (!(Test-Path -LiteralPath $oldReport -PathType Leaf)) { throw "Previous audit required for overflow containment" }
    $reportData = Get-Content -LiteralPath $oldReport -Raw -Encoding UTF8 | ConvertFrom-Json
    $failed = @(foreach ($device in $reportData.checks) {
        foreach ($check in $device.checks.PSObject.Properties) {
            if ($check.Value -ne $true) { "$($device.name):$($check.Name)" }
        }
    })
    if ($failed.Count -ne 1 -or $failed[0] -ne "desktop:noHorizontalOverflow") {
        throw "This CSS containment patch is only for an isolated desktop overflow failure"
    }
}
# Never alter the original generated ZIP, source, dist, or report.
$out = (New-Item -ItemType Directory -Path (Join-Path (Split-Path -Parent $run) ("recheck-" + [guid]::NewGuid().ToString("N")))).FullName
$source = Join-Path $out "site"
Copy-Item -LiteralPath $oldSource -Destination $source -Recurse
if ($FixHorizontalOverflow) {
    $css = Join-Path $source "src/style.css"
    $patch = @'

/* TrackNode local overflow containment. No nested scroll container. */
html, body {
  max-width: 100%;
  overflow-x: clip;
  overflow-y: visible;
}
#app {
  max-width: 100%;
  min-width: 0;
}
'@
    [IO.File]::AppendAllText($css, [Environment]::NewLine + $patch + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    Write-Host "CSS containment applied to COPY only; inspect screenshots for clipped content."
}
$dist = (New-Item -ItemType Directory -Path (Join-Path $out "dist")).FullName
$report = (New-Item -ItemType Directory -Path (Join-Path $out "quality-report")).FullName
Write-Host "RECHECK_OUTPUT: $out"
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build
if ($LASTEXITCODE -ne 0) { throw "Offline build failed; original and copy preserved: $out" }
if (!(Test-Path -LiteralPath (Join-Path $dist "index.html") -PathType Leaf)) { throw "No built index.html" }
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($report):/report" tracknode-studio-audit $Profile
if ($LASTEXITCODE -ne 0) { throw "Browser audit failed; original and copy preserved: $out" }
$reportPath = Join-Path $report "quality-report.json"
if (!(Test-Path -LiteralPath $reportPath -PathType Leaf)) { throw "No audit report" }
$result = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($result.passed -ne $true) { throw "Browser audit did not pass; files preserved: $out" }
Write-Host "QUALITY_CHECKS_PASSED: $report"
Write-Host "PREVIEW: $dist"
Write-Host "Visual acceptance remains separate. This copy has no newly approved source ZIP."
