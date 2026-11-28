# Start/inspect a persistent per-user Windows Task Scheduler worker. No paid retry.
[CmdletBinding()]
param([switch]$Restart,[switch]$Status)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$root=Join-Path $PSScriptRoot 'studio-jobs'
foreach($dir in @('pending','running','status','logs')){$null=New-Item -ItemType Directory -Force -Path (Join-Path $root $dir)}
$sha=[Security.Cryptography.SHA256]::Create()
try{$key=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($PSScriptRoot.ToLowerInvariant())))).Replace('-','').Substring(0,16)}finally{$sha.Dispose()}
$name='TrackNode-Studio-'+$key
$health=Join-Path $root 'worker-health.json'
$task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if($Status){
    if($task){$task | Select-Object TaskName,State;Get-ScheduledTaskInfo -TaskName $name | Select-Object LastRunTime,LastTaskResult}
    else{Write-Host 'Persistent worker task is not registered.'}
    if(Test-Path -LiteralPath $health){Get-Content -LiteralPath $health -Raw -Encoding UTF8}
    Get-ChildItem -LiteralPath (Join-Path $root 'pending'),(Join-Path $root 'running') -Filter '*.json' -File | Select-Object Name,DirectoryName,LastWriteTime
    return
}
& (Join-Path $PSScriptRoot 'studio-validate-scripts.ps1') -Quiet
$watcherPath=Join-Path $PSScriptRoot 'studio-watch.ps1'
$active=@(Get-ChildItem -LiteralPath (Join-Path $root 'pending'),(Join-Path $root 'running') -Filter '*.json' -File)
if($task -and $task.State -eq 'Running'){
    if($Restart){
        if($active.Count){throw 'Do not restart the worker with queued or running jobs.'}
        # A scheduler stop might terminate the supervisor without its child.
        # Avoid stopping a live task; let it continue and use the new watcher
        # on its next safe start. Explicit upgrade of a running supervisor is separate.
        Write-Host 'Persistent worker already running; not terminating it.'
    }
}else{
    $pidPath=Join-Path $root 'watcher.pid'
    if(Test-Path -LiteralPath $pidPath){
        $oldId=0
        if([int]::TryParse((Get-Content -LiteralPath $pidPath -Raw).Trim(),[ref]$oldId)){
            $old=Get-CimInstance Win32_Process -Filter "ProcessId=$oldId"
            if($old -and $old.CommandLine -and $old.CommandLine.IndexOf($watcherPath,[StringComparison]::OrdinalIgnoreCase) -ge 0){
                if($active.Count){throw 'Legacy watcher is alive and jobs exist. Do not stop or duplicate it; inspect watcher.log.'}
                # Old watcher could claim a new HTTP request during the upgrade;
                # refuse implicit termination. Stop it explicitly when Studio is idle.
                throw 'Legacy watcher is still alive. Stop it only while Studio is idle before installing the persistent worker.'
            }
        }
    }
    $user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    $exe=(Get-Process -Id $PID).Path
    $script=Join-Path $PSScriptRoot 'studio-worker-supervisor.ps1'
    $action=New-ScheduledTaskAction -Execute $exe -Argument ('-NoLogo -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"') -WorkingDirectory $PSScriptRoot
    $trigger=New-ScheduledTaskTrigger -AtLogOn -User $user
    $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $null=Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
    Start-ScheduledTask -TaskName $name
}
# A live process or PID alone is not sufficient. Require a recent protocol handshake.
$deadline=[DateTimeOffset]::UtcNow.AddSeconds(35)
do{
    try{
        $data=Get-Content -LiteralPath $health -Raw -Encoding UTF8 | ConvertFrom-Json
        $age=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($data.updated_at)).TotalSeconds
        $live=Get-Process -Id $data.supervisor_pid -ErrorAction SilentlyContinue
        if($live -and $data.protocol -eq 1 -and $data.state -in @('ready','busy') -and $age -ge -5 -and $age -le 12){
            Write-Host "STUDIO_WORKER_READY: $($data.state), PID $($data.pid), task $name"
            return
        }
    }catch{}
    Start-Sleep -Seconds 2
}while([DateTimeOffset]::UtcNow -lt $deadline)
throw 'Worker not ready. Run .\studio-worker.ps1 -Status and inspect studio-jobs\supervisor.log and watcher-error.log.'
