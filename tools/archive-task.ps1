# 出今天的任务单之前先跑一次：把当前 申论/今日任务.md 存进 申论/任务存档/<日期>.md
# 已存在则跳过，绝不覆盖。用法：  .\tools\archive-task.cmd
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$today = Join-Path $root '申论\今日任务.md'
if (-not (Test-Path $today)) { throw "找不到 $today" }

$raw = Get-Content -Raw -Encoding UTF8 $today
if ($raw -notmatch '(\d{4}-\d{2}-\d{2})') { throw '今日任务.md 里找不到日期（yyyy-MM-dd）' }
$date = $Matches[1]

$outDir = Join-Path $root '申论\任务存档'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir "$date.md"

if (Test-Path $out) {
    Write-Host "已存在，跳过（不覆盖）：申论/任务存档/$date.md"
    exit 0
}

$body = [regex]::Replace($raw, '(?m)^# .*$', "# $date 任务单", 1)
[System.IO.File]::WriteAllText($out, $body, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "已归档：申论/任务存档/$date.md"
