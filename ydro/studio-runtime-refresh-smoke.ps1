# Exercise startup failure paths with fixture Docker commands only.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('tn-refresh-test-'+[guid]::NewGuid().ToString('N'))
$script:commands=[Collections.Generic.List[string]]::new()
$script:scenario='agent'
try{
    $null=New-Item -ItemType Directory -Path $tmp
    Copy-Item (Join-Path $PSScriptRoot 'start-studio.ps1') $tmp
    Copy-Item (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1') $tmp
    function docker {
        $command=$args -join ' '
        $script:commands.Add($command)
        $global:LASTEXITCODE=0
        if($args[0] -eq 'build'){
            if($script:scenario -eq 'agent' -and $command.EndsWith('docker/studio-agent')){$global:LASTEXITCODE=1}
            if($script:scenario -eq 'audit' -and $command.EndsWith('docker/studio-audit')){$global:LASTEXITCODE=1}
        }
        if($args[0] -eq 'image' -and $args[1] -eq 'inspect'){'sha256:'+('a'*64)}
        if($script:scenario -eq 'promote' -and $args[0] -eq 'tag' -and $args[1] -like '*:refresh-*' -and $args[2] -eq 'tracknode-studio-audit:latest'){$global:LASTEXITCODE=1}
    }
    foreach($case in @('agent','audit','promote')){
        $script:scenario=$case
        $script:commands.Clear()
        $failed=$false
        try{& (Join-Path $tmp 'start-studio.ps1') -RefreshRuntime -SkipBuild}catch{
            if($_.Exception.Message -notmatch 'Studio (agent image build|audit image build|runtime promotion) failed'){throw}
            $failed=$true
        }
        if(!$failed){throw "Expected failure: $case"}
        $stops=@($script:commands|Where-Object{$_ -match ' stop backend$'})
        $starts=@($script:commands|Where-Object{$_ -match ' start backend$'})
        $restored=@($script:commands|Where-Object{$_ -match '^tag sha256:[a-f0-9]{64} '})
        if($case -in @('agent','audit')){
            if($stops.Count -or $starts.Count -or $restored.Count){throw 'Failed staging interrupted the current runtime'}
        }else{
            if($stops.Count -ne 1 -or $starts.Count -ne 1 -or $restored.Count -ne 2){throw 'Failed promotion did not restore both image tags and restart backend'}
        }
    }
    Write-Host 'STUDIO_RUNTIME_REFRESH_RECOVERY_OK'
}finally{
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
}
