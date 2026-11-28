# Windows task action: supervise the queue worker independently of the editor/terminal.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$root=Join-Path $PSScriptRoot 'studio-jobs'
$null=New-Item -ItemType Directory -Force -Path $root
. (Join-Path $PSScriptRoot 'studio-worker-io.ps1')
$lock=[IO.File]::Open((Join-Path $root 'supervisor.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$heartbeat=Join-Path $root 'worker-health.json'
$readyFile=Join-Path $root 'watcher-ready.json'
$supervisorLog=Join-Path $root 'supervisor.log'
$worker=$null
function Report-Worker([string]$State,[int]$WorkerId=0,[string]$Reason=''){
    try {
        Write-StudioJson $heartbeat @{protocol=1;state=$State;pid=$WorkerId;supervisor_pid=$PID;updated_at=[DateTimeOffset]::UtcNow.ToString('o');reason=$Reason}
    } catch { Write-Warning "Heartbeat write failed: $($_.Exception.Message)" }
}
function Log-Worker([string]$Message){
    Add-Content -LiteralPath $supervisorLog -Encoding UTF8 -Value ("{0:o} {1}" -f [DateTimeOffset]::Now,$Message)
}
try {
    while($true){
        Report-Worker 'starting' 0 'Waiting for Docker and queue worker'
        try {
            & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
            if($LASTEXITCODE -ne 0){throw 'Docker Desktop is not ready'}
            # Never remove a running worker's PID; the worker's exclusive lock is
            # the final safeguard even if a legacy worker races this startup.
            $pidFile=Join-Path $root 'watcher.pid'
            if(Test-Path -LiteralPath $pidFile){
                $oldId=0
                if([int]::TryParse((Get-Content -LiteralPath $pidFile -Raw).Trim(),[ref]$oldId)){
                    $old=Get-CimInstance Win32_Process -Filter "ProcessId=$oldId"
                    if($old -and $old.CommandLine -and $old.CommandLine.IndexOf((Join-Path $PSScriptRoot 'studio-watch.ps1'),[StringComparison]::OrdinalIgnoreCase) -ge 0){
                        throw 'An existing workspace watcher is still running; migration deferred'
                    }
                }
            }
            $stamp=[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssfff')
            foreach($name in @('watcher.log','watcher-error.log')){
                $path=Join-Path $root $name
                if(Test-Path -LiteralPath $path -PathType Leaf){
                    Move-Item -LiteralPath $path -Destination ($path+'.'+$stamp+'.old') -ErrorAction Stop
                }
            }
            $exe=(Get-Process -Id $PID).Path
            $script=Join-Path $PSScriptRoot 'studio-watch.ps1'
            $worker=Start-Process -FilePath $exe -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$script+'"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'watcher.log') -RedirectStandardError (Join-Path $root 'watcher-error.log') -PassThru
            Log-Worker "Watcher started: PID $($worker.Id)"
            while(!$worker.HasExited){
                $ready=$null
                try { $ready=Get-Content -LiteralPath $readyFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch {}
                if($ready -and $ready.pid -eq $worker.Id -and $ready.protocol -eq 1){
                    $age=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($ready.updated_at)).TotalSeconds
                    $running=@(Get-ChildItem -LiteralPath (Join-Path $root 'running') -Filter '*.json' -File -ErrorAction SilentlyContinue)
                    if($running.Count -gt 0){Report-Worker 'busy' $worker.Id}
                    elseif($age -ge -5 -and $age -le 15){Report-Worker 'ready' $worker.Id}
                    else{Report-Worker 'blocked' $worker.Id 'Watcher alive, no recent idle acknowledgement'}
                }else{Report-Worker 'starting' $worker.Id 'Waiting for watcher readiness'}
                Start-Sleep -Seconds 2
                $worker.Refresh()
            }
            Log-Worker "Watcher exited: code $($worker.ExitCode)"
            $worker.Dispose()
            $worker=$null
            Report-Worker 'recovering' 0 'Watcher exited; safe restart scheduled'
        }catch{
            Log-Worker ("Worker supervisor: "+$_.Exception.Message)
            # If monitoring itself failed, do not start a second worker or kill
            # the first: it may be executing a paid request.
            if($worker){
                try { if(!$worker.HasExited){throw 'A watcher is still alive; supervisor exits without replacing it'} } finally { $worker.Dispose();$worker=$null }
            }
            Report-Worker 'recovering' 0 'Worker unavailable; retrying startup'
        }
        Start-Sleep -Seconds 10
    }
}finally{
    Report-Worker 'offline' 0 'Supervisor stopped'
    $lock.Dispose()
}
