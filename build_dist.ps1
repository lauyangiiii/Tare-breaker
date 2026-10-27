# build_dist.ps1 —— 一键产出可交付物
#   dist/tare_breaker-<ver>-py3-none-any.whl       pip 安装用
#   dist/tare-breaker-<ver>-portable.zip           免安装用
#   dist/SHA256SUMS.txt                            校验用
#
#   powershell -ExecutionPolicy Bypass -File .\build_dist.ps1
param(
    [string]$Version = "0.1.0",
    [switch]$SkipWheel
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }

Remove-Item -Recurse -Force "$root\dist" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$root\dist" | Out-Null

# ---------------------------------------------------------------- 1. wheel
if (-not $SkipWheel) {
    Write-Host "[1/5] 构建 wheel + sdist ..."
    & $py setup.py bdist_wheel -d "$root\dist" *> $null
    if ($LASTEXITCODE -ne 0) { throw "wheel 构建失败" }
    & $py setup.py sdist -d "$root\dist" *> $null
    if ($LASTEXITCODE -ne 0) { throw "sdist 构建失败" }
    Remove-Item -Recurse -Force "$root\build", "$root\*.egg-info" -ErrorAction SilentlyContinue
} else {
    Write-Host "[1/5] 跳过构建"
}

# ---------------------------------------------------------------- 2. portable
Write-Host "[2/5] 组装免安装包 ..."
$name = "tare-breaker-$Version-portable"
$stage = "$root\dist\_stage\$name"
New-Item -ItemType Directory -Force -Path $stage | Out-Null

Copy-Item "$root\src" -Destination "$stage\src" -Recurse
Remove-Item -Recurse -Force "$stage\src\__pycache__" -ErrorAction SilentlyContinue
Copy-Item "$root\README.md", "$root\INSTALL.md", "$root\LICENSE" -Destination $stage
New-Item -ItemType Directory -Force -Path "$stage\examples" | Out-Null
Get-ChildItem "$root\out" -Filter *.md -ErrorAction SilentlyContinue |
    Copy-Item -Destination "$stage\examples"

# 启动器（纯 ASCII，避免 cmd 编码问题）
@'
@echo off
setlocal
python "%~dp0src\harness.py" %*
'@ | Set-Content -Path "$stage\tare-breaker.cmd" -Encoding ascii

@'
@echo off
setlocal
python "%~dp0src\compose.py" %*
'@ | Set-Content -Path "$stage\tb-compose.cmd" -Encoding ascii

@'
#!/usr/bin/env sh
exec python3 "$(dirname "$0")/src/harness.py" "$@"
'@ | Set-Content -Path "$stage\tare-breaker.sh" -Encoding ascii

@'
#!/usr/bin/env sh
exec python3 "$(dirname "$0")/src/compose.py" "$@"
'@ | Set-Content -Path "$stage\tb-compose.sh" -Encoding ascii

# .cmd 需要 CRLF；.sh 需要 LF，保证类 Unix 下可直接执行
foreach ($f in @("tare-breaker.cmd", "tb-compose.cmd")) {
    $p = Join-Path $stage $f
    $t = [IO.File]::ReadAllText($p) -replace "`r`n", "`n" -replace "`n", "`r`n"
    [IO.File]::WriteAllText($p, $t)
}
foreach ($f in @("tare-breaker.sh", "tb-compose.sh")) {
    $p = Join-Path $stage $f
    if (Test-Path $p) {
        $t = [IO.File]::ReadAllText($p) -replace "`r`n", "`n"
        [IO.File]::WriteAllText($p, $t)
    }
}

Write-Host "[3/5] 打包 portable zip ..."
$zip = "$root\dist\$name.zip"
Compress-Archive -Path "$stage\*" -DestinationPath $zip -CompressionLevel Optimal
Remove-Item -Recurse -Force "$root\dist\_stage"

# ---------------------------------------------------------------- 3b. 纯源码包
Write-Host "[4/5] 打包源码 zip ..."
$srcName = "tare-breaker-$Version-src"
$srcStage = "$root\dist\_stage\$srcName"
New-Item -ItemType Directory -Force -Path $srcStage | Out-Null
Copy-Item "$root\src" -Destination "$srcStage\src" -Recurse
Remove-Item -Recurse -Force "$srcStage\src\__pycache__" -ErrorAction SilentlyContinue
Copy-Item "$root\README.md", "$root\INSTALL.md", "$root\LICENSE", "$root\pyproject.toml", `
    "$root\setup.py", "$root\MANIFEST.in", "$root\build_dist.ps1", "$root\.gitignore" -Destination $srcStage
New-Item -ItemType Directory -Force -Path "$srcStage\examples" | Out-Null
Get-ChildItem "$root\out" -Filter *.md -ErrorAction SilentlyContinue |
    Copy-Item -Destination "$srcStage\examples"
Compress-Archive -Path "$srcStage\*" -DestinationPath "$root\dist\$srcName.zip" -CompressionLevel Optimal
Remove-Item -Recurse -Force "$root\dist\_stage"

# ---------------------------------------------------------------- 4. 校验和
Write-Host "[5/5] 生成 SHA256SUMS.txt ..."
$lines = Get-ChildItem "$root\dist" -File |
    Where-Object { $_.Extension -in ".whl", ".zip", ".gz" } |
    ForEach-Object { "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name }
$lines | Set-Content "$root\dist\SHA256SUMS.txt" -Encoding ascii

Write-Host ""
Write-Host "完成，产物在 dist/："
Get-ChildItem "$root\dist" | Select-Object Name, @{n = "Size"; e = { "{0:N1} KB" -f ($_.Length / 1KB) } } | Format-Table -AutoSize
