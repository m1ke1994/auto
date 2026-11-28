[CmdletBinding()]
param([ValidateRange(1,30)][int]$PollSeconds=2,[switch]$Once)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
& (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1')

$root=Join-Path $PSScriptRoot 'studio-jobs'
$pending=Join-Path $root 'pending'
$running=Join-Path $root 'running'
$status=Join-Path $root 'status'
$logs=Join-Path $root 'logs'
. (Join-Path $PSScriptRoot 'studio-worker-io.ps1')
$readyFile=Join-Path $root 'watcher-ready.json'
foreach($path in @($pending,$running,$status,$logs)){ $null=New-Item -ItemType Directory -Force -Path $path }

function Write-State([string]$Id,[hashtable]$State){
    $State.project_id=$Id
    $State.updated_at=[DateTimeOffset]::Now.ToString('o')
    $target=Join-Path $status ($Id+'.json')
    Write-StudioJson $target $State
}

function Get-VerifiedRun([string]$Id,[string]$Kind){
    $resultFile=Join-Path $running ($Id+'.result.txt')
    if(!(Test-Path -LiteralPath $resultFile -PathType Leaf)){throw 'Pipeline finished without a result directory'}
    $run=(Get-Content -LiteralPath $resultFile -Raw -Encoding UTF8).Trim()
    $outputRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'studio-agent-output')).Path
    $resolved=(Resolve-Path -LiteralPath $run).Path
    if(![string]::Equals((Split-Path -Parent $resolved),$outputRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Result escaped output root'}
    $runName=Split-Path -Leaf $resolved
    if($runName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$'){throw 'Invalid result run name'}
    if($Kind -eq 'block_edit' -and !$runName.StartsWith('block-edit-')){throw 'Invalid block candidate run'}
    if(!(Test-Path -LiteralPath (Join-Path $resolved 'dist/index.html') -PathType Leaf)){throw 'Successful pipeline has no built preview'}
    if(!(Test-Path -LiteralPath (Join-Path $resolved 'tracknode-agent-site.zip') -PathType Leaf)){throw 'Successful pipeline has no source archive'}
    $meta=Get-Content -LiteralPath (Join-Path $resolved 'studio-result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($meta.technical_passed -ne $true -or $meta.status -notin @('passed','needs_revision','unavailable','skipped')) {
        throw 'Invalid technical/visual result metadata'
    }
    $stage=if ($meta.status -eq 'passed') {'verified'} else {'technical-preview'}
    return @{status='complete';stage=$stage;error='';run_directory=$runName}
}

function Recover-InterruptedJobs {
    $claimedJobs=@(Get-ChildItem -LiteralPath $running -Filter '*.json' -File)
    if (!$claimedJobs.Count) { return }
    # Never recover while another pipeline may still be writing this workspace.
    $pipelineScripts=@('studio-watch.ps1','studio-manual-edit.ps1','studio-block-edit.ps1','studio-quality.ps1','studio-technical.ps1','studio-visual-review.ps1')
    $other=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $command=$_.CommandLine
        if (!$command -or $_.ProcessId -eq $PID) { return $false }
        foreach ($script in $pipelineScripts) {
            if ($command.IndexOf((Join-Path $PSScriptRoot $script),[StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
        }
        return $false
    })
    if ($other.Count) { throw 'Interrupted jobs exist but another local Studio pipeline is active. Recovery deferred.' }
    $images=@('tracknode20-agent-openhands:latest','tracknode-studio-build:latest','tracknode-studio-audit:latest')
    foreach ($image in $images) {
        $containers=@(& docker ps -q --filter "ancestor=$image")
        if ($LASTEXITCODE -ne 0) { throw 'Docker state unavailable; recovery deferred.' }
        if ($containers.Count) { throw 'A Studio pipeline container is still active; recovery deferred.' }
    }
    foreach ($file in $claimedJobs) {
        $id=$file.BaseName
        $guid=[guid]::Empty
        if (![guid]::TryParseExact($id,'D',[ref]$guid)) {
            throw 'Invalid interrupted job name; operator review required.'
        }
        $old=$null
        $statusPath=Join-Path $status ($id+'.json')
        if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
            try { $old=Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
        }
        if (!$old -or $old.project_id -ne $id -or $old.status -notin @('complete','failed')) {
            $recovered=$null
            try {
                $envelope=Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                if($envelope.project_id -eq $id -and $envelope.version -eq 1){$recovered=Get-VerifiedRun $id $envelope.kind}
            }catch{}
            if($recovered){
                Write-State $id $recovered
                Write-Host "STUDIO_JOB_RESULT_RECOVERED: $id"
            }else{
                Write-State $id @{status='failed';stage='failed';error='Studio worker interrupted. Original website preserved. Start a new edit manually.';run_directory=''}
            }
        }
        # Unique name preserves the original job even if a .done file already exists.
        $suffix='.interrupted.'+[guid]::NewGuid().ToString('N')+'.done'
        Move-Item -LiteralPath $file.FullName -Destination ($file.FullName+$suffix) -ErrorAction Stop
        Write-Host "STUDIO_JOB_RECOVERED: $id"
    }
}

function Process-Job([IO.FileInfo]$File){
    if($File.BaseName -notmatch '^[0-9a-fA-F-]{36}$'){ Move-Item -LiteralPath $File.FullName -Destination ($File.FullName+'.invalid') -Force; return }
    $id=$File.BaseName
    $claimed=Join-Path $running $File.Name
    try{ Move-Item -LiteralPath $File.FullName -Destination $claimed -ErrorAction Stop }catch{return}
    $resultFile=Join-Path $running ($id+'.result.txt')
    $jobLog=Join-Path $logs ($id+'.log')
    $terminalWritten=$false
    try{
        # Validate before dispatch: scripts may have changed since worker startup.
        & (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1') -Quiet
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
        if($job.contacts){$qualityArgs.ContactsJson=($job.contacts|ConvertTo-Json -Compress -Depth 3)}
        if ($job.kind -eq 'block_edit' -and $job.manual_edit -eq $true) {
            & (Join-Path $PSScriptRoot 'studio-manual-edit.ps1') -Job $job -ResultFile $resultFile -ProgressFile $qualityArgs.ProgressFile
        } elseif ($job.kind -eq 'block_edit') {
            & (Join-Path $PSScriptRoot 'studio-block-edit.ps1') -Job $job -ResultFile $resultFile -ProgressFile $qualityArgs.ProgressFile
        } else {
        # Do not merge native stderr here: BuildKit writes successful progress
        # there and PowerShell would turn it into a terminating ErrorRecord.
        # The watcher process itself already redirects stdout/stderr to files.
        & (Join-Path $PSScriptRoot 'studio-quality.ps1') @qualityArgs
        }
        $pipelineSucceeded=$?
        if(!$pipelineSucceeded){throw 'Cinematic pipeline returned an error; inspect the preserved job log'}
        Write-State $id (Get-VerifiedRun $id $job.kind)
        $terminalWritten=$true
    }catch{
        $message=($_.Exception.Message -replace '[\r\n]+',' ').Trim()
        if($message.Length -gt 1800){$message=$message.Substring(0,1800)}
        Write-State $id @{status='failed';stage='failed';error=$message;run_directory=''}
        $terminalWritten=$true
        Add-Content -LiteralPath $jobLog -Value ("`nSTUDIO_JOB_FAILED: "+$message) -Encoding UTF8
    }finally{
        if($terminalWritten -and (Test-Path -LiteralPath $claimed)){Move-Item -LiteralPath $claimed -Destination ($claimed+'.done') -Force}
    }
}

$lockPath=Join-Path $root 'watcher.lock'
try {
    $workerLock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
} catch {
    throw 'Another Studio watcher owns this workspace lock.'
}
try {
    [IO.File]::WriteAllText((Join-Path $root 'watcher.pid'),[string]$PID,[Text.UTF8Encoding]::new($false))
    Recover-InterruptedJobs
    do{
        Write-StudioJson $readyFile @{protocol=1;pid=$PID;updated_at=[DateTimeOffset]::UtcNow.ToString('o')}
        $next=@(Get-ChildItem -LiteralPath $pending -Filter '*.json' -File | Sort-Object CreationTime)
        foreach($file in $next){
            # Docker unavailable is not a failed generation. Leave unclaimed work
            # in pending for the supervisor to resume when Docker is back.
            & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
            if($LASTEXITCODE -ne 0){throw 'Docker unavailable before claiming job'}
            Write-Host "STUDIO_JOB_START: $($file.BaseName)"
            Process-Job $file
            Write-StudioJson $readyFile @{protocol=1;pid=$PID;updated_at=[DateTimeOffset]::UtcNow.ToString('o')}
        }
        if(!$Once){Start-Sleep -Seconds $PollSeconds}
    }while(!$Once)
} finally {
    $workerLock.Dispose()
}
