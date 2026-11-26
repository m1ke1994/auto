# Parse Studio scripts without running any pipeline or sending AI requests.
[CmdletBinding()]
param([switch]$Quiet)
$ErrorActionPreference='Stop'
$files=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'studio-*.ps1' -File)
$files+=Get-Item -LiteralPath (Join-Path $PSScriptRoot 'start-studio.ps1')
$failures=@()
foreach ($file in $files) {
    $tokens=$null
    $parseErrors=$null
    $null=[System.Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$parseErrors)
    foreach ($parseError in $parseErrors) {
        $failures+=('{0}:{1}:{2} {3}' -f $file.Name,$parseError.Extent.StartLineNumber,$parseError.Extent.StartColumnNumber,$parseError.ErrorId)
    }
}
if ($failures.Count -gt 0) {
    throw ("Studio PowerShell syntax check failed: "+($failures -join '; '))
}
if (!$Quiet) { Write-Host ("STUDIO_SCRIPTS_OK: "+$files.Count+" PowerShell files") }
