# Shared atomic JSON writer, UTF-8 without BOM. Retry transient Windows file sharing.
function Write-StudioJson([string]$Path,[hashtable]$Payload){
    $temp=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    try {
        [IO.File]::WriteAllText($temp,($Payload|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
        for($attempt=0;$attempt -lt 8;$attempt++){
            try{
                if([IO.File]::Exists($Path)){
                    [IO.File]::Replace($temp,$Path,$null)
                }else{
                    [IO.File]::Move($temp,$Path)
                }
                return
            }catch{
                if($attempt -eq 7){throw}
                Start-Sleep -Milliseconds 100
            }
        }
    }finally{
        if([IO.File]::Exists($temp)){[IO.File]::Delete($temp)}
    }
}
