param()
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$out=(New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot ("studio-agent-output/hero-smoke-"+[guid]::NewGuid().ToString("N"))) -Force).FullName
$source=(New-Item -ItemType Directory -Path (Join-Path $out "site")).FullName
$dist=(New-Item -ItemType Directory -Path (Join-Path $out "dist")).FullName
$report=(New-Item -ItemType Directory -Path (Join-Path $out "report")).FullName
$utf8=[Text.UTF8Encoding]::new($false)
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docker/studio-agent/HeroObjectStage.vue") -Destination $source
[IO.File]::WriteAllText((Join-Path $source "index.html"),'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="app"></div><script type="module" src="/main.js"></script></body></html>',$utf8)
[IO.File]::WriteAllText((Join-Path $source "vite.config.js"),"import { defineConfig } from 'vite'; import vue from '@vitejs/plugin-vue'; export default defineConfig({plugins:[vue()],base:'./'});",$utf8)
[IO.File]::WriteAllText((Join-Path $source "main.js"),"import {createApp} from 'vue'; import App from './App.vue'; createApp(App).mount('#app');",$utf8)
$app=@'
<script setup>
import HeroObjectStage from './HeroObjectStage.vue'
const preset=new URLSearchParams(location.search).get('preset')||'serum'
</script>
<template>
  <main><section class="hero"><div class="copy"><p>TRACKNODE / COMPONENT TEST</p><h1>Atelier</h1><p>Offline procedural object smoke fixture</p></div><HeroObjectStage :preset="preset" brand="ATELIER" :label="preset" /></section><section class="end"><h2>End of test</h2></section></main>
</template>
<style>
*{box-sizing:border-box}body{margin:0;background:#1d1a17;color:#eee4d5;font:18px Georgia,serif}.hero{min-height:110vh;display:grid;grid-template-columns:1fr 1fr;align-items:start;padding:12vh 6vw;gap:4vw}.copy{min-width:0;padding-top:18vh}h1{font-size:clamp(50px,8vw,110px);margin:0}.end{min-height:200vh;background:#eee4d5;color:#26221e;padding:10vh 6vw}@media(max-width:760px){.hero{grid-template-columns:1fr;padding:5vh 6vw;gap:20px}.copy{padding-top:0}}
</style>
'@
[IO.File]::WriteAllText((Join-Path $source "App.vue"),$app,$utf8)
Write-Host "HERO_SMOKE_OUTPUT: $out"
docker run --pull never --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs "/work:rw,exec,size=256m,uid=1000,gid=1000" --tmpfs "/tmp:rw,size=64m" -v "${source}:/source:ro" -v "${dist}:/output" tracknode-studio-build
if($LASTEXITCODE -ne 0){throw "Smoke fixture build failed: $out"}
docker run --pull never --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 3 --pids-limit 256 --shm-size 256m --tmpfs "/tmp:rw,exec,size=512m,mode=1777" -v "${dist}:/site:ro" -v "${report}:/report" --entrypoint node tracknode-studio-audit /opt/audit/hero-smoke.mjs
$code=$LASTEXITCODE
$p=Join-Path $report "hero-smoke.json"
if(!(Test-Path -LiteralPath $p)){throw "Missing smoke report: $out"}
Get-Content -LiteralPath $p -Raw -Encoding UTF8 | Out-Host
$result=Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json
if($code -ne 0 -or $result.passed -ne $true -or @($result.tests).Count -ne 18){throw "Hero smoke failed; artifacts preserved: $out"}
Write-Host "HERO_SMOKE_ALL_PASSED: $out" -ForegroundColor Green
