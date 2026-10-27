$ErrorActionPreference = 'Stop'
# 生成今天的打印版任务单（docx + PDF），输出到 docs/print/，站点可直接下载。
# 用法：.\tools\handout.cmd            （等价于跑这个 ps1）
# 说明：.ps1 在本机被执行策略拦，所以实际调用走 handout.cmd。

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = $null
foreach ($cand in @('python', 'python3', 'py')) {
    $c = Get-Command $cand -ErrorAction SilentlyContinue
    if ($c) { $py = $c.Source; break }
}
if (-not $py) {
    $py = 'C:\Users\onesk\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
}
if (-not (Test-Path $py)) { throw "找不到 python，请用 -Python 指定" }

& $py 'tools\make_handout.py'
exit $LASTEXITCODE
