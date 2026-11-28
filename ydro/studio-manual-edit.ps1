# Deterministic local edit, no AI key, no network, no paid repair.
param(
    [Parameter(Mandatory=$true)]$Job,
    [Parameter(Mandatory=$true)][string]$ResultFile,
    [Parameter(Mandatory=$true)][string]$ProgressFile
)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'studio-progress.ps1')
if($Job.base_run -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' -or $Job.block -ne 'manual'){throw 'Invalid manual edit'}
$root=(Resolve-Path -LiteralPath 'studio-agent-output').Path
$base=(Resolve-Path -LiteralPath (Join-Path $root $Job.base_run)).Path
if(![string]::Equals((Split-Path -Parent $base),$root,[StringComparison]::OrdinalIgnoreCase)){throw 'Invalid base run'}
$archive=(Resolve-Path -LiteralPath (Join-Path $base 'tracknode-agent-site.zip')).Path
$out=(New-Item -ItemType Directory -Path (Join-Path $root ('block-edit-'+[guid]::NewGuid().ToString('N')))).FullName
$payload=Join-Path $out 'manual-job.json'
$module=Join-Path $PSScriptRoot 'ai_builder/manual_edit.py'
[IO.File]::WriteAllText($payload,(@{source_fingerprint=$Job.source_fingerprint;changes=@($Job.changes)}|ConvertTo-Json -Depth 6 -Compress),[Text.UTF8Encoding]::new($false))
Write-StudioProgress $ProgressFile 'validate_patch'
& docker run --pull never --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs /tmp:rw,size=64m -v "$($module):/manual_edit.py:ro" -v "$($payload):/manual-job.json:ro" -v "$($archive):/repair-source.zip:ro" -v "$($out):/output" --entrypoint python tracknode20-agent-openhands /manual_edit.py /manual-job.json /repair-source.zip /output/tracknode-agent-site.zip
if($LASTEXITCODE -ne 0){throw 'Local text edit failed; original site preserved'}
$passed=& (Join-Path $PSScriptRoot 'studio-technical.ps1') -RunDirectory $out -Prompt $Job.prompt -Profile $Job.profile -MaxTechnicalRepairs 0 -ProgressFile $ProgressFile
Write-StudioProgress $ProgressFile 'finalizing'
[IO.File]::WriteAllText((Join-Path $passed 'studio-result.json'),'{"status":"skipped","score":null,"threshold":85,"technical_passed":true}',[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($ResultFile,$passed,[Text.UTF8Encoding]::new($false))
