# Offline recovery test. Runs only in a temporary workspace; never calls Docker or AI.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('tn-worker-test-'+[guid]::NewGuid().ToString('N'))
$oldLocation=Get-Location
try{
    $null=New-Item -ItemType Directory -Path $tmp
    foreach($name in @('studio-watch.ps1','studio-worker-io.ps1','studio-validate-scripts.ps1','start-studio.ps1')){
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $tmp
    }
    . (Join-Path $tmp 'studio-worker-io.ps1')
    $jobs=Join-Path $tmp 'studio-jobs'
    foreach($name in @('pending','running','status','logs')){$null=New-Item -ItemType Directory -Force -Path (Join-Path $jobs $name)}
    $good=[guid]::NewGuid().ToString()
    $bad=[guid]::NewGuid().ToString()
    $terminal=[guid]::NewGuid().ToString()
    foreach($id in @($good,$bad,$terminal)){
        Write-StudioJson (Join-Path $jobs "running/$id.json") @{version=1;project_id=$id;kind='block_edit'}
        Write-StudioJson (Join-Path $jobs "status/$id.json") @{project_id=$id;status='running'}
    }
    Write-StudioJson (Join-Path $jobs "status/$terminal.json") @{project_id=$terminal;status='failed';error='previous'}
    $run=Join-Path $tmp 'studio-agent-output/block-edit-test'
    $null=New-Item -ItemType Directory -Force -Path (Join-Path $run 'dist')
    [IO.File]::WriteAllText((Join-Path $run 'dist/index.html'),'test')
    [IO.File]::WriteAllText((Join-Path $run 'tracknode-agent-site.zip'),'fixture')
    Write-StudioJson (Join-Path $run 'studio-result.json') @{technical_passed=$true;status='skipped'}
    [IO.File]::WriteAllText((Join-Path $jobs "running/$good.result.txt"),$run)
    function docker { $global:LASTEXITCODE=0; if($args[0] -ne 'ps'){throw 'Unexpected Docker command in recovery test'} }
    & (Join-Path $tmp 'studio-watch.ps1') -Once
    foreach($id in @($good,$bad,$terminal)){
        $state=Get-Content -LiteralPath (Join-Path $jobs "status/$id.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        $expected=if($id -eq $good){'complete'}else{'failed'}
        if($state.status -ne $expected){throw "Unexpected recovered state: $id"}
        if($id -eq $terminal -and $state.error -ne 'previous'){throw 'Existing terminal state overwritten'}
        if($id -eq $good -and $state.run_directory -ne 'block-edit-test'){throw 'Validated result was not recovered'}
    }
    if(@(Get-ChildItem -LiteralPath (Join-Path $jobs 'running') -Filter '*.json').Count){throw 'Interrupted envelopes still running'}
    if(@(Get-ChildItem -LiteralPath (Join-Path $jobs 'running') -Filter '*.done').Count -ne 3){throw 'Original envelopes not preserved'}
    if(!(Test-Path -LiteralPath (Join-Path $jobs 'watcher-ready.json'))){throw 'Readiness acknowledgement missing'}
    Write-Host 'STUDIO_WORKER_RECOVERY_OK'
}finally{
    Set-Location $oldLocation
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
}
