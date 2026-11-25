param(
    [Parameter(Mandatory=$true)][string]$RunDirectory,
    [switch]$Review
)
$ErrorActionPreference="Stop"
# Use a single maintained implementation for both entry points.
& (Join-Path $PSScriptRoot "studio-preflight.ps1") -ResumeDirectory $RunDirectory -RenderOnly:(-not $Review)
