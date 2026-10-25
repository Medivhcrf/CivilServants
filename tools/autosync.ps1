<#
.SYNOPSIS
  自动提交并推送学习记录。用于「每次学习完成后自动同步」，可被定时任务调用，也可手动跑。
.DESCRIPTION
  - 工作区有改动 → git add -A + 自动生成提交信息 → commit
  - 本地领先 origin/main → push
  - 无改动、无待推 → 什么都不做（幂等，可反复调用）
  - 日志写到 %LOCALAPPDATA%\CivilServants\autosync.log，不进仓库
.EXAMPLE
  ./tools/autosync.ps1
.EXAMPLE
  ./tools/autosync.ps1 -NoPush      # 只提交，不推送
#>
param(
    [switch]$NoPush,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
# 日志放 .git 里：不受版本控制、不会被提交，也不需要额外的目录权限
$log = Join-Path (Join-Path $root '.git') 'autosync.log'

function Write-Log([string]$msg) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -LiteralPath $log -Value $line -Encoding utf8
    if (-not $Quiet) { Write-Host $msg }
}

Push-Location $root
try {
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { throw "not a git repository: $root" }

    # 1. 有改动就提交
    $dirty = @(git status --porcelain)
    if ($dirty.Count -gt 0) {
        git add -A
        $msg = 'auto: 学习记录同步 ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')
        git commit -q -m $msg
        if ($LASTEXITCODE -ne 0) { throw 'git commit 失败' }
        Write-Log "committed: $msg（$($dirty.Count) 个文件）"
    }
    else {
        Write-Log '无改动，跳过提交'
    }

    if ($NoPush) { Write-Log '已跳过推送（-NoPush）'; return }

    # 2. 有领先就推送
    $ErrorActionPreference = 'Continue'   # git 写 stderr 时不要当成异常
    $ahead = [int](git rev-list --count 'origin/main..main')
    if ($ahead -le 0) { Write-Log '没有待推送的提交'; return }

    $out = git push origin main 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -ne 0) {
        Write-Log "PUSH FAILED(exit $code): $($out.Trim())"
        exit 1
    }
    Write-Log "pushed $ahead commit(s) → origin/main"
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    Pop-Location
}
