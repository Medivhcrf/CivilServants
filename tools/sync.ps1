<#
.SYNOPSIS
  把学习记录提交并推送到 GitHub。
.EXAMPLE
  ./tools/sync.ps1 "Day 12：概括题 8/15，漏点集中在培训与资金"
.EXAMPLE
  ./tools/sync.ps1 "Day 12" -NoPush
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message,
    [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
        throw "not a git repository: $root"
    }

    git add -A
    $staged = git diff --cached --name-only
    if (-not $staged) {
        Write-Host "没有变更，跳过提交。"
    }
    else {
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) { throw "git commit 失败" }
        Write-Host "已提交：$Message"
    }

    if ($NoPush) {
        Write-Host "已跳过推送（-NoPush）。"
        return
    }

    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "git push 失败：请检查凭据或网络" }
    Write-Host "已推送到 origin/main。"
}
finally {
    Pop-Location
}
