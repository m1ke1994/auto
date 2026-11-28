# Exercise startup failure paths with fixture Docker commands only.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$tmp=Join-Path ([IO.Path]::GetTempPath()) ('tn-refresh-test-'+[guid]::NewGuid().ToString('N'))
# Invoking a separate .ps1 changes the meaning of script: inside a mock.
# Keep the fixture in an explicitly shared, temporary scope instead.
if(Get-Variable -Name TNRuntimeRefreshFixture -Scope Global -ErrorAction SilentlyContinue){throw 'Runtime refresh fixture already active'}
$global:TNRuntimeRefreshFixture=@{commands=[Collections.Generic.List[string]]::new();scenario='agent'}
try{
    $null=New-Item -ItemType Directory -Path $tmp
    Copy-Item (Join-Path $PSScriptRoot 'start-studio.ps1') $tmp
    Copy-Item (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1') $tmp
    function docker {
        $command=$args -join ' '
        $global:TNRuntimeRefreshFixture.commands.Add($command)
        $global:LASTEXITCODE=0
        if($args[0] -eq 'build'){
            if($global:TNRuntimeRefreshFixture.scenario -eq 'agent' -and $command.EndsWith('docker/studio-agent')){$global:LASTEXITCODE=1}
            if($global:TNRuntimeRefreshFixture.scenario -eq 'audit' -and $command.EndsWith('docker/studio-audit')){$global:LASTEXITCODE=1}
        }
        if($args[0] -eq 'image' -and $args[1] -eq 'inspect'){'sha256:'+('a'*64)}
        if($global:TNRuntimeRefreshFixture.scenario -eq 'promote' -and $args[0] -eq 'tag' -and $args[1] -like '*:refresh-*' -and $args[2] -eq 'tracknode-studio-audit:latest'){$global:LASTEXITCODE=1}
    }
    foreach($case in @('agent','audit','promote')){
        $global:TNRuntimeRefreshFixture.scenario=$case
        $global:TNRuntimeRefreshFixture.commands.Clear()
        $failed=$false
        try{& (Join-Path $tmp 'start-studio.ps1') -RefreshRuntime -SkipBuild}catch{
            if($_.Exception.Message -notmatch 'Studio (agent image build|audit image build|runtime promotion) failed'){throw}
            $failed=$true
        }
        if(!$failed){throw "Expected failure: $case"}
        $stops=@($global:TNRuntimeRefreshFixture.commands|Where-Object{$_ -match ' stop backend$'})
        $starts=@($global:TNRuntimeRefreshFixture.commands|Where-Object{$_ -match ' start backend$'})
        $restored=@($global:TNRuntimeRefreshFixture.commands|Where-Object{$_ -match '^tag sha256:[a-f0-9]{64} '})
        if($case -in @('agent','audit')){
            if($stops.Count -or $starts.Count -or $restored.Count){throw 'Failed staging interrupted the current runtime'}
        }else{
            if($stops.Count -ne 1 -or $starts.Count -ne 1 -or $restored.Count -ne 2){throw 'Failed promotion did not restore both image tags and restart backend'}
        }
    }
    Write-Host 'STUDIO_RUNTIME_REFRESH_RECOVERY_OK'
}finally{
    Remove-Variable -Name TNRuntimeRefreshFixture -Scope Global -ErrorAction SilentlyContinue
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Recurse -Force}
}
