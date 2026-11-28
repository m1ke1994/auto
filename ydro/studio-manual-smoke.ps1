# Exercise the real watcher/manual/technical/progress scripts in a temporary
# workspace. Docker commands are fixtures: no real containers, network or AI.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('tn-manual-test-'+[guid]::NewGuid().ToString('N'))
$oldLocation=Get-Location
try{
    $null=New-Item -ItemType Directory -Path $tmp
    foreach($name in @('studio-watch.ps1','studio-worker-io.ps1','studio-validate-scripts.ps1','studio-manual-edit.ps1','studio-technical.ps1','studio-progress.ps1')){
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $tmp
    }
    . (Join-Path $tmp 'studio-worker-io.ps1')
    $jobs=Join-Path $tmp 'studio-jobs'
    foreach($name in @('pending','running','status','logs')){
        $null=New-Item -ItemType Directory -Force -Path (Join-Path $jobs $name)
    }
    $base=Join-Path $tmp 'studio-agent-output/original'
    $null=New-Item -ItemType Directory -Force -Path (Join-Path $base 'dist')
    $null=New-Item -ItemType Directory -Force -Path (Join-Path $tmp 'fixture')
    [IO.File]::WriteAllText((Join-Path $tmp 'fixture/index.html'),'<h1>Fixture</h1>')
    [IO.File]::WriteAllText((Join-Path $base 'dist/index.html'),'<h1>Original</h1>')
    $archive=Join-Path $base 'tracknode-agent-site.zip'
    Compress-Archive -LiteralPath (Join-Path $tmp 'fixture/index.html') -DestinationPath $archive
    $before=(Get-FileHash -LiteralPath $archive).Hash
    $id=[guid]::NewGuid().ToString()
    $statePath=Join-Path $jobs "status/$id.json"
    Write-StudioJson (Join-Path $jobs "pending/$id.json") @{
        version=1;project_id=$id;kind='block_edit';manual_edit=$true;block='manual'
        name='Fixture';prompt='Fixture site';profile='standard';asset_style='realistic'
        hero_mode='auto';base_run='original';source_fingerprint=('a'*64)
        changes=@(@{id=('b'*32);text='New title'})
    }
    function docker {
        $global:LASTEXITCODE=0
        if($args[0] -eq 'info'){return}
        if($args[0] -ne 'run' -or $args -notcontains 'none'){throw 'Unexpected Docker command in offline test'}
        $current=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $mount=@($args | Where-Object {$_ -is [string] -and $_.EndsWith(':/output')})
        if($args -contains 'tracknode20-agent-openhands'){
            if($current.stage -ne 'validate_patch' -or $mount.Count -ne 1){throw 'Manual patch stage missing'}
            $output=$mount[0].Substring(0,$mount[0].Length-8)
            Copy-Item -LiteralPath $archive -Destination (Join-Path $output 'tracknode-agent-site.zip')
        }elseif($args -contains 'tracknode-studio-build'){
            if($current.stage -ne 'building' -or $mount.Count -ne 1){throw 'Build stage missing'}
            $output=$mount[0].Substring(0,$mount[0].Length-8)
            [IO.File]::WriteAllText((Join-Path $output 'index.html'),'<h1>Candidate</h1>')
        }elseif($args -contains 'tracknode-studio-audit'){
            $report=@($args | Where-Object {$_ -is [string] -and $_.EndsWith(':/report')})
            if($current.stage -ne 'auditing' -or $report.Count -ne 1){throw 'Audit stage missing'}
            $output=$report[0].Substring(0,$report[0].Length-8)
            Write-StudioJson (Join-Path $output 'quality-report.json') @{passed=$true}
        }else{throw 'Unexpected fixture container'}
    }
    & (Join-Path $tmp 'studio-watch.ps1') -Once
    $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if($state.status -ne 'complete' -or $state.stage -ne 'technical-preview'){
        throw "Manual pipeline failed: $($state.error)"
    }
    $candidate=Join-Path (Join-Path $tmp 'studio-agent-output') $state.run_directory
    if(!(Test-Path -LiteralPath (Join-Path $candidate 'dist/index.html'))){throw 'Candidate missing'}
    if((Get-FileHash -LiteralPath $archive).Hash -ne $before){throw 'Original archive changed'}
    if([IO.File]::ReadAllText((Join-Path $base 'dist/index.html')) -ne '<h1>Original</h1>'){throw 'Original preview changed'}
    if(!(Test-Path -LiteralPath (Join-Path $jobs "running/$id.json.done"))){throw 'Job not archived'}
    . (Join-Path $tmp 'studio-progress.ps1')
    $guard=Join-Path $jobs 'status/guard.json'
    Write-StudioJson $guard @{status='running';stage='preparing'}
    $rejected=$false
    try{Write-StudioProgress $guard 'invalid_stage'}catch{if($_.Exception.Message -eq 'Unknown Studio stage'){$rejected=$true}else{throw}}
    if(!$rejected){throw 'Invalid progress stage accepted'}
    Write-Host 'STUDIO_MANUAL_PIPELINE_OK'
}finally{
    Set-Location $oldLocation
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
}
