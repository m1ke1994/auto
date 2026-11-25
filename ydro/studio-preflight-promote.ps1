param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [string]$Prompt=""
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
if (!(Test-Path -LiteralPath ".env.studio.local" -PathType Leaf)) { throw "Missing .env.studio.local" }
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
if ($Prompt) {
    if ($Prompt.Length -lt 1 -or $Prompt.Length -gt 8000) { throw "Prompt must contain 1..8000 characters" }
    $planPath=Join-Path $run "plan.json"
    $plan=Get-Content -LiteralPath $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $sha=[System.Security.Cryptography.SHA256]::Create()
    try {
        $hash=$sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Prompt))
        $plan.brief_sha256=([BitConverter]::ToString($hash)).Replace("-","").ToLowerInvariant()
    } finally { $sha.Dispose() }
    $json=$plan | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($planPath,$json,(New-Object System.Text.UTF8Encoding($false)))
    Write-Host "PREFLIGHT_BRIEF_BOUND: supplied prompt hash saved; no planning API request"
}
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
& docker @compose build openhands | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Agent build failed ($LASTEXITCODE)" }
& docker @compose run --rm --no-deps --entrypoint python -v "$($run):/preflight" openhands /opt/studio-agent/asset_preflight.py promote | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Conditional promotion failed ($LASTEXITCODE); existing review and files preserved." }
$selection=Get-Content -LiteralPath (Join-Path $run "selection.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$selection | Select-Object status,reason,@{Name="SelectedModel";Expression={$_.selected.name}},@{Name="Score";Expression={$_.selected.visual_score}},@{Name="Tier";Expression={$_.selected.quality_tier}} | Format-List
