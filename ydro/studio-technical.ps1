param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [Parameter(Mandatory=$true)][string]$Prompt,
    [ValidateSet("standard","premium","cinema")][string]$Profile="cinema",
    [ValidateSet("realistic","stylized")][string]$AssetStyle="realistic",
    [ValidateRange(0,1)][int]$MaxTechnicalRepairs=0,
    [string]$ProgressFile=""
)
# This helper expects prebuilt trusted agent/builder/audit images.
# Only stdout return value is the technically passed run directory.
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot "studio-progress.ps1")
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
$prompt64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Prompt))
$repairableChecks=@("rendered","noHorizontalOverflow","footer","progress","noBrokenImages","noJsErrors","noMissingAssets","noExternalRequests","completeSections","headerNavigation","heroCTA","serviceCards","heroFraming","heroImportedModel","cameraChanges","modelMotionChanges","scenes","scrollMotion","sceneComponents","carouselControls","carouselRuntime","noVisibleHorizontalScrollbars","storyProgress","storyVisuals","heroLayout","heroObjectLayout","publicContacts","heroFilm","heroBackgroundCenter","heroFullTurn")
for ($attempt=0; $attempt -le $MaxTechnicalRepairs; $attempt++) {
    $archive=Join-Path $run "tracknode-agent-site.zip"
    $failure=Join-Path $run "technical-failure.json"
    $sourceFailure=Join-Path $run "source-failure.json"
    $diagnostic=$null
    if (!(Test-Path -LiteralPath $archive -PathType Leaf)) {
        $archive=Join-Path $run "source-checkpoint.zip"
        if (!(Test-Path -LiteralPath $archive -PathType Leaf) -or !(Test-Path -LiteralPath $sourceFailure -PathType Leaf)) {
            throw "No recoverable source-gate checkpoint: $run"
        }
        $diagnostic=Get-Content -LiteralPath $sourceFailure -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($diagnostic.kind -ne "tracknode-technical-failure" -or $diagnostic.stage -ne "source") { throw "Invalid source failure report" }
    } else {
        # Fresh attempt directories only. Never overwrite a prior build or audit.
        $source=Join-Path $run "site"
        $dist=Join-Path $run "dist"
        $report=Join-Path $run "quality-report"
        if ((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $dist) -or (Test-Path -LiteralPath $report)) {
            throw "Technical pipeline requires a fresh attempt directory; existing results preserved: $run"
        }
        Write-StudioProgress $ProgressFile "building"
        Expand-Archive -LiteralPath $archive -DestinationPath $source
        $null=New-Item -ItemType Directory -Path $dist
        $buildLog=Join-Path $run "build.log"
        $previousPreference=$ErrorActionPreference
        try {
            $ErrorActionPreference="Continue"
            docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "$($source):/source:ro" -v "$($dist):/output" tracknode-studio-build 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $buildLog | Out-Host
            $buildExit=$LASTEXITCODE
        } finally { $ErrorActionPreference=$previousPreference }
        if ($buildExit -ne 0) {
            $log=Get-Content -LiteralPath $buildLog -Raw
            # Conservative classification: only known compiler failures are sent to AI.
            if ($buildExit -ne 1 -or $log -notmatch '(?i)error during build|build failed with [0-9]+ error|VueCompilerError' -or $log -match '(?i)ENOSPC|ENOMEM|EACCES|EPERM|EIO|out of memory|heap limit|context canceled|snapshot|docker daemon|OCI runtime|no space left|permission denied|read-only file system|cannot find module.*(/opt/studio|node_modules)|failed to (mount|copy|extract)') {
                throw "Build infrastructure or unclassified error ($buildExit); no paid repair. See $buildLog"
            }
            $tail=($log -split "\r?\n" | Select-Object -Last 90) -join "\n"
            if ($tail.Length -gt 12000) { $tail=$tail.Substring($tail.Length-12000) }
            $diagnostic=@{kind="tracknode-technical-failure";stage="build";diagnostic=$tail}
        } else {
            if (!(Test-Path -LiteralPath (Join-Path $dist "index.html") -PathType Leaf)) { throw "No built index.html; no paid repair: $run" }
            Write-Host "SOURCE_AND_BUILD_READY: $run"
            Write-Host "Preview folder: $dist"
            Write-StudioProgress $ProgressFile "auditing"
            $null=New-Item -ItemType Directory -Path $report
            docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($report):/report" tracknode-studio-audit $Profile | Out-Host
            $auditExit=$LASTEXITCODE
            $reportPath=Join-Path $report "quality-report.json"
            if (!(Test-Path -LiteralPath $reportPath -PathType Leaf)) { throw "Browser audit infrastructure failure ($auditExit); no paid repair: $run" }
            $audit=Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($auditExit -eq 0 -and $audit.passed -eq $true) {
                Write-Host "QUALITY_CHECKS_PASSED: $report"
                if ($attempt -gt 0) { Write-Host "TECHNICAL_REPAIR_ACCEPTED: $run" }
                return $run
            }
            if ($audit.screenshotFailures -and @($audit.screenshotFailures).Count -gt 0) { throw "Screenshot capture incomplete; functional checks are recorded. No paid repair: $reportPath" }
            if ($audit.functionalPassed -eq $true -and $audit.screenshotsComplete -ne $true) {
                $detail=@()
                if ($audit.missingScreenshots) { $detail+="missing: "+($audit.missingScreenshots -join ', ') }
                if ($audit.unexpectedScreenshots) { $detail+="unexpected: "+($audit.unexpectedScreenshots -join ', ') }
                if ($audit.duplicateScreenshots) { $detail+="duplicate: "+($audit.duplicateScreenshots -join ', ') }
                if (!$detail.Count) { $detail+="screenshot manifest mismatch" }
                throw "Screenshot manifest incomplete ($($detail -join '; ')); functional checks passed. No paid repair: $reportPath"
            }
            if ($auditExit -ne 1 -or $audit.passed -ne $false -or $audit.error -or @($audit.checks).Count -ne 2) { throw "Browser audit infrastructure or invalid report; no paid repair: $run" }
            $failed=@(foreach ($device in $audit.checks) {
                foreach ($check in $device.checks.PSObject.Properties) {
                    if ($check.Value -ne $true) { $check.Name }
                }
            })
            $unsupported=@($failed | Where-Object { $_ -notin $repairableChecks })
            if ($failed.Count -eq 0) { throw "Audit rejected without failed functional checks; inspect report metadata. No paid repair: $reportPath" }
            if ($unsupported.Count -gt 0) { throw "Audit failure requires separate diagnosis (possibly model/WebGL): $($unsupported -join ', '); no paid repair: $reportPath" }
            $diagnostic=@{kind="tracknode-technical-failure";stage="audit";audit=$audit}
        }
    }
    [IO.File]::WriteAllText($failure,($diagnostic | ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
    if ($attempt -ge $MaxTechnicalRepairs) {
        $summary=$diagnostic.stage
        if ($diagnostic.stage -eq "audit") {
            $summary=(@(foreach ($device in $diagnostic.audit.checks) {
                foreach ($check in $device.checks.PSObject.Properties) {
                    if ($check.Value -ne $true) { "$($device.name):$($check.Name)" }
                }
            }) -join ", ")
        }
        throw "TECHNICAL_REPAIR_LIMIT_REACHED [$summary]: $run; previous versions preserved. No paid retry."
    }
    $next=(New-Item -ItemType Directory -Path (Join-Path (Split-Path -Parent $run) ("technical-repair-"+[guid]::NewGuid().ToString("N")))).FullName
    Write-Host "TECHNICAL_REPAIR_ATTEMPT: $($attempt+1)/$MaxTechnicalRepairs; stage=$($diagnostic.stage)"
    Write-Host "TECHNICAL_REPAIR_OUTPUT: $next"
    & docker @compose run --rm --no-deps -v "$($archive):/repair-source.zip:ro" -v "$($failure):/repair-review.json:ro" -v "$($next):/output" openhands --technical-repair --profile $Profile --asset-style $AssetStyle --prompt-b64 $prompt64 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Technical repair failed ($LASTEXITCODE); all previous attempts and new checkpoint preserved: $next" }
    $run=$next
}
throw "Technical pipeline ended without acceptance."
