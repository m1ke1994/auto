[CmdletBinding()]
param([ValidateRange(1,30)][int]$PollSeconds=2,[switch]$Once)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot

$root=Join-Path $PSScriptRoot 'studio-jobs'
$pending=Join-Path $root 'pending'
$running=Join-Path $root 'running'
$status=Join-Path $root 'status'
$logs=Join-Path $root 'logs'
foreach($path in @($pending,$running,$status,$logs)){ $null=New-Item -ItemType Directory -Force -Path $path }

function Write-State([string]$Id,[hashtable]$State){
    $State.project_id=$Id
    $State.updated_at=[DateTimeOffset]::Now.ToString('o')
    $target=Join-Path $status ($Id+'.json')
    $temp=$target+'.tmp'
    [IO.File]::WriteAllText($temp,($State|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temp -Destination $target -Force
}

function Process-Job([IO.FileInfo]$File){
    if($File.BaseName -notmatch '^[0-9a-fA-F-]{36}$'){ Move-Item -LiteralPath $File.FullName -Destination ($File.FullName+'.invalid') -Force; return }
    $id=$File.BaseName
    $claimed=Join-Path $running $File.Name
    try{ Move-Item -LiteralPath $File.FullName -Destination $claimed -ErrorAction Stop }catch{return}
    $resultFile=Join-Path $running ($id+'.result.txt')
    $jobLog=Join-Path $logs ($id+'.log')
    try{
        $job=Get-Content -LiteralPath $claimed -Raw -Encoding UTF8 | ConvertFrom-Json
        if($job.version -ne 1 -or $job.project_id -ne $id){throw 'Invalid job envelope'}
        if($job.name -isnot [string] -or $job.name.Length -lt 1 -or $job.name.Length -gt 120){throw 'Invalid project name'}
        if($job.prompt -isnot [string] -or $job.prompt.Length -lt 1 -or $job.prompt.Length -gt 8000){throw 'Invalid prompt'}
        if($job.profile -notin @('standard','premium','cinema')){throw 'Invalid profile'}
        if($job.asset_style -notin @('realistic','stylized')){throw 'Invalid asset style'}
        if($job.hero_mode -notin @('auto','immersive','product','split','cinematic','editorial','environment')){throw 'Invalid hero mode'}
        Write-State $id @{status='running';stage='preparing';error='';run_directory=''}
        $brief=$job.name+"`n`n"+$job.prompt
        if ($brief.Length -gt 8000) { $brief=$job.prompt }
        $qualityArgs=@{
            Prompt=$brief;Profile=$job.profile;AssetStyle=$job.asset_style;HeroMode=$job.hero_mode
            MaxRepairs=0;MaxTechnicalRepairs=0;ResultFile=$resultFile;AllowVisualWarnings=$true
            ProgressFile=(Join-Path $status ($id+'.json'))
        }
        if($job.require_model -eq $true){$qualityArgs.RequireModel=$true}
        # Do not merge native stderr here: BuildKit writes successful progress
        # there and PowerShell would turn it into a terminating ErrorRecord.
        # The watcher process itself already redirects stdout/stderr to files.
        & (Join-Path $PSScriptRoot 'studio-quality.ps1') @qualityArgs
        $pipelineSucceeded=$?
        if(!$pipelineSucceeded){throw 'Cinematic pipeline returned an error; inspect the preserved job log'}
        if(!(Test-Path -LiteralPath $resultFile -PathType Leaf)){throw 'Pipeline finished without a result directory'}
        $run=(Get-Content -LiteralPath $resultFile -Raw -Encoding UTF8).Trim()
        $outputRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'studio-agent-output')).Path
        $resolved=(Resolve-Path -LiteralPath $run).Path
        if(!(Test-Path -LiteralPath (Join-Path $resolved 'dist/index.html') -PathType Leaf)){throw 'Successful pipeline has no built preview'}
        if(!($resolved.StartsWith($outputRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase))){throw 'Result escaped output root'}
        $runName=Split-Path -Leaf $resolved
        $meta=Get-Content -LiteralPath (Join-Path $resolved 'studio-result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($meta.technical_passed -ne $true -or $meta.status -notin @('passed','needs_revision','unavailable','skipped')) {
            throw 'Invalid technical/visual result metadata'
        }
        $stage=if ($meta.status -eq 'passed') {'verified'} else {'technical-preview'}
        Write-State $id @{status='complete';stage=$stage;error='';run_directory=$runName}
    }catch{
        $message=($_.Exception.Message -replace '[\r\n]+',' ').Trim()
        if($message.Length -gt 1800){$message=$message.Substring(0,1800)}
        Write-State $id @{status='failed';stage='failed';error=$message;run_directory=''}
        Add-Content -LiteralPath $jobLog -Value ("`nSTUDIO_JOB_FAILED: "+$message) -Encoding UTF8
    }finally{
        if(Test-Path -LiteralPath $claimed){Move-Item -LiteralPath $claimed -Destination ($claimed+'.done') -Force}
    }
}

do{
    Get-ChildItem -LiteralPath $pending -Filter '*.json' -File | Sort-Object CreationTime | ForEach-Object { Process-Job $_ }
    if(!$Once){Start-Sleep -Seconds $PollSeconds}
}while(!$Once)
