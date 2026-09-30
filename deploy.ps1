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

# 日志目录结构：
#   logs\live\<渠道>.p<pid>_<启动时间>.log  应用运行期按进程、按渠道写入
#   logs\archive\<YYYY-MM-DD>\<渠道>.log     每天 00:05 归档
#   logs\console\app.out.log / app.err.log   控制台输出（由本脚本重定向）
# 应用自身已保证“每进程一个文件”，因此不会出现多进程争抢同一日志文件。
$logRoot = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $logRoot 'live') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $logRoot 'archive') | Out-Null
$consoleDir = Join-Path $logRoot 'console'
New-Item -ItemType Directory -Force -Path $consoleDir | Out-Null

# 每次部署轮转控制台输出，避免单个文件无限增长
foreach ($name in @('app.out.log', 'app.err.log')) {
    $path = Join-Path $consoleDir $name
    if (Test-Path $path) {
        $stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
        Move-Item -Force $path (Join-Path $consoleDir "$name.$stamp.bak") -ErrorAction SilentlyContinue
    }
}

Write-Host "[$(Get-Date -f 'HH:mm:ss')] start app..."
$env:CCSA_LOG_DIR = $logRoot
# 生产环境不做热重载：热重载会派生子进程、重复初始化调度器与日志文件
$env:CCSA_RELOAD = '0'
Start-Process -FilePath 'uv' -ArgumentList 'run', 'app.py' `
    -WorkingDirectory $root -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $consoleDir 'app.out.log') `
    -RedirectStandardError (Join-Path $consoleDir 'app.err.log')
Write-Host "[$(Get-Date -f 'HH:mm:ss')] done"
