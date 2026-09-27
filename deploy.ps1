#Requires -Version 5.1
# 自动部署：拉取最新代码 -> uv sync -> 重启应用（配合任务计划程序定时执行）
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$port = 8082

Set-Location $root

$before = git rev-parse HEAD
git fetch origin
if ($LASTEXITCODE) { throw 'git fetch failed' }
git merge --ff-only origin/main
if ($LASTEXITCODE) { throw 'local diverged from origin/main, manual fix needed' }
$after = git rev-parse HEAD
$changed = $before -ne $after

$listening = [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
if (-not $changed -and $listening) {
    Write-Host "[$(Get-Date -f 'HH:mm:ss')] up to date, app running, nothing to do"
    return
}

Write-Host "[$(Get-Date -f 'HH:mm:ss')] uv sync..."
uv sync
if ($LASTEXITCODE) { throw 'uv sync failed' }

if ($listening) {
    Get-NetTCPConnection -LocalPort $port -State Listen | ForEach-Object {
        Write-Host "[$(Get-Date -f 'HH:mm:ss')] stopping pid $($_.OwningProcess)"
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

Write-Host "[$(Get-Date -f 'HH:mm:ss')] start app..."
New-Item -ItemType Directory -Force -Path "$root\logs" | Out-Null
Start-Process -FilePath 'uv' -ArgumentList 'run', 'app.py' `
    -WorkingDirectory $root -WindowStyle Hidden `
    -RedirectStandardOutput "$root\logs\app.out.log" `
    -RedirectStandardError "$root\logs\app.err.log"
Write-Host "[$(Get-Date -f 'HH:mm:ss')] done"
