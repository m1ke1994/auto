param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [switch]$Review
)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$out=(Resolve-Path -LiteralPath $RunDirectory).Path
$root=(Resolve-Path -LiteralPath ".\studio-agent-output").Path
if (!$out.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $out -Leaf) -notmatch '^preflight-[0-9a-f-]{36}$') { throw "Choose an existing preflight output directory" }
$candidates=Get-Content -LiteralPath (Join-Path $out "candidates.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if (!$candidates) { throw "No downloaded candidate in this run" }
docker build -t tracknode-studio-audit docker/studio-audit | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Audit image build failed" }
$ready=0
foreach ($candidate in $candidates) {
    if ($candidate.folder -notmatch '^candidate-[12]$') { throw "Unexpected candidate folder" }
    $folder=Join-Path $out $candidate.folder
    $dist=(Resolve-Path -LiteralPath (Join-Path $folder "dist")).Path
    if (!(Test-Path -LiteralPath (Join-Path $dist "index.html"))) { throw "Existing candidate build missing" }
    Write-Host "RESUME_RENDER: $folder"
    docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "$($dist):/site:ro" -v "$($folder):/report" --entrypoint node tracknode-studio-audit /opt/audit/asset-preview.mjs | Out-Host
    if ($LASTEXITCODE -eq 0) { $ready++ }
    Write-Host "Render diagnostics: $folder\render-diagnostics.json"
}
if ($ready -eq 0) { throw "No candidate rendered. No DeepSeek request made." }
if (!$Review) {
    Write-Host "RESUME_RENDER_PASSED: $ready candidate(s). No DeepSeek request made."
    Write-Host "Use -Review only when you want to run the single visual critic request."
    return
}
$compose=@("compose","--env-file",".env.studio.local","-p","tracknode20-agent","-f","docker-compose.openhands.yml")
& docker @compose run --rm --no-deps --entrypoint python -v "$($out):/preflight" openhands /opt/studio-agent/asset_preflight.py select | Out-Host
$code=$LASTEXITCODE
Write-Host "Asset selection: $out\selection.json"
if ($code -ne 0) { throw "Candidate selection did not pass ($code). No site generation started." }
