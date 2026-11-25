param(
    [Parameter(Mandatory=$true)][string]$RunDirectory
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
if (!(Test-Path -LiteralPath ".env.studio.local" -PathType Leaf)) { throw "Missing .env.studio.local" }
$run=(Resolve-Path -LiteralPath $RunDirectory).Path
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
& docker @compose build openhands | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Agent build failed ($LASTEXITCODE)" }
& docker @compose run --rm --no-deps --entrypoint python -v "$($run):/preflight" openhands /opt/studio-agent/asset_preflight.py promote | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Conditional promotion failed ($LASTEXITCODE); existing review and files preserved." }
$selection=Get-Content -LiteralPath (Join-Path $run "selection.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$selection | Select-Object status,reason,@{Name="SelectedModel";Expression={$_.selected.name}},@{Name="Score";Expression={$_.selected.visual_score}},@{Name="Tier";Expression={$_.selected.quality_tier}} | Format-List
