# build_dist.ps1 - build all four artifacts.
# Thin wrapper around tools/make_artifacts.py (cross-platform, same output as CI).
#
#   .\build_dist.ps1
#   .\build_dist.ps1 -SkipBuild     # reuse existing wheel/sdist
param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
$extra = @()
if ($SkipBuild) { $extra += "--skip-build" }

& $py tools\make_artifacts.py @extra
if ($LASTEXITCODE -ne 0) { throw "artifact build failed" }
