<#
.SYNOPSIS
  构建站点并发布到 GitHub Pages（Windows 版 publish.sh）。
.DESCRIPTION
  1. 跑 tools/build_site.py 重建 docs/
  2. 提交并对 main 推送
  3. 把 docs/ 同步到 gh-pages 分支（GitHub Pages 从这里发布）
.PARAMETER Message
  提交信息，默认「更新学习资料与站点」。
.PARAMETER Python
  python 解释器路径；不填则依次尝试 python / python3 / py。
.EXAMPLE
  .\tools\publish-site.cmd
.EXAMPLE
  .\tools\publish-site.cmd "Day 12：补上学习记录"
#>
param(
    [Parameter(Position = 0)][string]$Message = '更新学习资料与站点',
    [string]$Python = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $text = (git -C $root @GitArgs 2>&1 | Out-String)
        return [pscustomobject]@{ Code = $LASTEXITCODE; Text = $text }
    }
    finally { $ErrorActionPreference = $prev }
}

function Invoke-GitAt {
    param([string]$Dir, [Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $text = (git -C $Dir @GitArgs 2>&1 | Out-String)
        return [pscustomobject]@{ Code = $LASTEXITCODE; Text = $text }
    }
    finally { $ErrorActionPreference = $prev }
}

# ---------------------------------------------------------------- 找 python
if (-not $Python) {
    foreach ($cand in @('python', 'python3', 'py')) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $prev = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $cmd.Source -V *> $null
            if ($LASTEXITCODE -eq 0) { $Python = $cmd.Source; break }
        }
        finally { $ErrorActionPreference = $prev }
    }
}
if (-not $Python) {
    throw '找不到可用的 python。请安装 Python 3，或用 -Python 指定解释器路径。'
}

Write-Host "▸ 1/4 构建站点（$Python）"
& $Python (Join-Path $root 'tools\build_site.py')
if ($LASTEXITCODE -ne 0) { throw 'build_site.py 执行失败' }

# build_site.py 会删掉整个 docs/，所以打印版必须在构建之后生成
Write-Host "▸ 2/4 生成打印版任务单（$Python）"
& $Python (Join-Path $root 'tools\make_handout.py')
if ($LASTEXITCODE -ne 0) { Write-Host '  打印版生成失败，继续发布（docx 可手动打印）' }

Write-Host ''
Write-Host '▸ 3/4 提交并推送 main'
Invoke-Git add -A | Out-Null
$staged = @(Invoke-Git diff --cached --name-only).Text
if (-not $staged.Trim()) {
    Write-Host '  main 无变化，跳过提交'
}
else {
    $r = Invoke-Git commit -q -m $Message
    if ($r.Code -ne 0) { throw "git commit 失败：$($r.Text)" }
    Write-Host "  已提交：$((Invoke-Git log --oneline -1).Text.Trim())"
}
$r = Invoke-Git push origin main
if ($r.Code -ne 0) { throw "git push main 失败：$($r.Text)" }
Write-Host '  main 已推送'

Write-Host ''
Write-Host '▸ 4/4 同步到 gh-pages'
$r = Invoke-Git fetch --depth 1 origin gh-pages
if ($r.Code -ne 0) { throw "拉取 gh-pages 失败：$($r.Text)" }

$wt = Join-Path (Split-Path -Parent $root) ('_ghpages-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$r = Invoke-Git worktree add --detach $wt FETCH_HEAD
if ($r.Code -ne 0) { throw "创建 worktree 失败：$($r.Text)" }

try {
    Get-ChildItem -LiteralPath $wt -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
    Get-ChildItem -LiteralPath (Join-Path $root 'docs') -Force | Copy-Item -Destination $wt -Recurse -Force

    Invoke-GitAt $wt add -A | Out-Null
    $staged = @(Invoke-GitAt $wt diff --cached --name-only).Text
    if (-not $staged.Trim()) {
        Write-Host '  gh-pages 无变化'
    }
    else {
        $r = Invoke-GitAt $wt commit -q -m $Message
        if ($r.Code -ne 0) { throw "gh-pages commit 失败：$($r.Text)" }
        $r = Invoke-GitAt $wt push origin HEAD:gh-pages
        if ($r.Code -ne 0) { throw "gh-pages 推送失败：$($r.Text)" }
        Write-Host '  gh-pages 已推送'
    }
}
finally {
    Invoke-Git worktree remove --force $wt | Out-Null
}

Write-Host ''
Write-Host '完成。' -ForegroundColor Green
Write-Host '  仓库：https://github.com/Medivhcrf/CivilServants'
Write-Host '  站点：https://medivhcrf.github.io/CivilServants/（Pages 构建需 1–2 分钟）'


