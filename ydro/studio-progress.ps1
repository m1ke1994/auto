# Real phase transitions, not a timer-based percentage. No output on the success stream.
function Write-StudioProgress([string]$ProgressFile,[string]$Stage) {
    if ([string]::IsNullOrWhiteSpace($ProgressFile)) { return }
    if ($Stage -notin @('preparing','assets','generating','building','auditing','visual-review','finalizing')) { throw 'Unknown Studio stage' }
    $state=Get-Content -LiteralPath $ProgressFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($state.status -ne 'running') { throw 'Cannot update an inactive Studio job' }
    $state.stage=$Stage
    $state.updated_at=[DateTimeOffset]::UtcNow.ToString('o')
    $temp=$ProgressFile+'.progress.tmp'
    [IO.File]::WriteAllText($temp,($state|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temp -Destination $ProgressFile -Force
    Write-Host "STUDIO_PROGRESS: $Stage"
}
