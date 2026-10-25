<#
.SYNOPSIS
  一次性配置本仓库的推送凭据，让 autosync / sync 无需再登录。
.DESCRIPTION
  把 GitHub token 写进 remote URL（存在 .git\config 里，不会被提交），
  这样 git 完全不经过凭据助手——绕开 Git Credential Manager 在无窗口环境里崩溃的问题。
  验证失败会自动把 origin 还原成干净的 URL。
.NOTES
  本文件必须保存为 UTF-8 with BOM：Windows PowerShell 5.1 无 BOM 时会按 GBK 解码，中文全变乱码。
.EXAMPLE
  .\tools\setup-credentials.cmd
.EXAMPLE
  .\tools\setup-credentials.ps1 -Token ghp_xxx
#>
param(
    [string]$Token,
    [string]$User = 'Medivhcrf',
    [string]$Repo = 'CivilServants'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$cleanUrl = "https://github.com/$User/$Repo.git"
$authUrl = "https://${User}:{0}@github.com/$User/$Repo.git"

function Invoke-Git {
    # 原生命令写 stderr 时，$ErrorActionPreference='Stop' 会把它当成异常抛出，
    # 所以在执行期间临时降级，靠 $LASTEXITCODE 判断成败。
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $text = (git -C $root @Args 2>&1 | Out-String)
        return [pscustomobject]@{ Code = $LASTEXITCODE; Text = $text }
    }
    finally { $ErrorActionPreference = $prev }
}

if (-not $Token) {
    $sec = Read-Host -AsSecureString '粘贴 GitHub token（输入时不显示，可直接右键粘贴）'
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $Token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$Token = $Token.Trim()
if ($Token -notmatch '^(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)$') {
    throw '格式不像 GitHub token（应以 ghp_ 或 github_pat_ 开头，且不含空格）'
}

# 1. 代理（当前网络下 github.com 直连不通）
if (-not (Invoke-Git config --local --get http.proxy).Text.Trim()) {
    Invoke-Git config --local http.proxy 'http://127.0.0.1:7890' | Out-Null
    Invoke-Git config --local https.proxy 'http://127.0.0.1:7890' | Out-Null
}

# 2. token 放进 remote URL，git 不再问凭据助手
Invoke-Git remote set-url origin ($authUrl -f $Token) | Out-Null
Write-Host '凭据已写入 .git\config（remote origin），不会提交到仓库。' -ForegroundColor Green
Write-Host '正在验证推送权限…'

$probe = Invoke-Git push --dry-run origin main
if ($probe.Code -ne 0) {
    Invoke-Git remote set-url origin $cleanUrl | Out-Null
    Write-Host '验证失败，已把 origin 还原成干净的 URL。' -ForegroundColor Red
    Write-Host $probe.Text
    Write-Host '常见原因：token 过期、没有 repo 权限（classic 需勾 repo）或 Contents 不是 Read and write（fine-grained）。' -ForegroundColor Yellow
    exit 1
}

Write-Host '验证通过。以后 autosync 会自动提交并推送，不需要再登录。' -ForegroundColor Green
Write-Host '想撤销：GitHub → Settings → Developer settings → 删除该 token，然后执行：'
Write-Host "  git remote set-url origin $cleanUrl"
