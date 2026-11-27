param(
    [Parameter(Mandatory=$true)]$Job,
    [Parameter(Mandatory=$true)][string]$ResultFile,
    [Parameter(Mandatory=$true)][string]$ProgressFile
)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot 'studio-progress.ps1')
if ($Job.base_run -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' -or $Job.block -notin @('home','about','services','benefits','contacts','header','footer')) {throw 'Invalid block edit'}
$root=(Resolve-Path -LiteralPath 'studio-agent-output').Path
$base=(Resolve-Path -LiteralPath (Join-Path $root $Job.base_run)).Path
if (!(($base).StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase))) {throw 'Invalid base run'}
$archive=(Resolve-Path -LiteralPath (Join-Path $base 'tracknode-agent-site.zip')).Path
$out=(New-Item -ItemType Directory -Path (Join-Path $root ('block-edit-'+[guid]::NewGuid().ToString('N')))).FullName
$compose=@('compose','--env-file','.env.studio.local','-p','tracknode20-agent','-f','docker-compose.openhands.yml')
$statusDir=[IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ProgressFile))
$statusName=[IO.Path]::GetFileName($ProgressFile)
$progressContainerPath="/studio-status/$statusName"
# Images are prebuilt by the update command; no rebuild on each edit.
$payload=@{block=$Job.block;instruction=$Job.instruction;upgrade_motion=($Job.upgrade_motion -eq $true)}
if ($Job.local_hero_film -eq $true) {
    $payload.local_hero_film=$true
    if ($null -ne $Job.hero_options) {$payload.hero_options=$Job.hero_options}
}
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($payload|ConvertTo-Json -Compress)))
Write-StudioProgress $ProgressFile 'generating'
if ($Job.local_hero_film -eq $true) {
    & docker run --pull never --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 2 --pids-limit 128 --tmpfs /tmp:rw,size=64m -e "TN_BLOCK_JOB=$encoded" -e "TN_PROGRESS_FILE=$progressContainerPath" -v "$($statusDir):/studio-status" -v "$($archive):/repair-source.zip:ro" -v "$($out):/output" --entrypoint python tracknode20-agent-openhands /opt/studio-agent/block_edit.py
} else {
    & docker @compose run --rm --no-deps --entrypoint python -e "TN_BLOCK_JOB=$encoded" -e "TN_PROGRESS_FILE=$progressContainerPath" -v "$($statusDir):/studio-status" -v "$($archive):/repair-source.zip:ro" -v "$($out):/output" openhands /opt/studio-agent/block_edit.py
}
if ($LASTEXITCODE -ne 0) {
    $message='Block edit failed; original preview preserved'
    $diagnostic=Join-Path $out 'block-edit-error.json'
    if (Test-Path -LiteralPath $diagnostic -PathType Leaf) {
        try {
            $data=Get-Content -LiteralPath $diagnostic -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($data.stage -match '^[a-z_]{1,40}$' -and $data.reason -match '^[A-Za-z0-9 :_-]{1,160}$') {
                $message="Block edit failed [$($data.stage)]: $($data.reason); original preview preserved"
            }
        } catch { }
    }
    throw $message
}
$passed=& (Join-Path $PSScriptRoot 'studio-technical.ps1') -RunDirectory $out -Prompt $Job.prompt -Profile $Job.profile -MaxTechnicalRepairs 0 -ProgressFile $ProgressFile
Write-StudioProgress $ProgressFile 'finalizing'
[IO.File]::WriteAllText((Join-Path $passed 'studio-result.json'),'{"status":"skipped","score":null,"threshold":85,"technical_passed":true}',[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($ResultFile,$passed,[Text.UTF8Encoding]::new($false))
