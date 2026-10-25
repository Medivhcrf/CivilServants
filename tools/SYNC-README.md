# 学习记录同步（Windows）

## 平时不用管

学完、批改完，我（AI 助教）会自动执行：

```powershell
.\tools\autosync.cmd
```

它做三件事，且**幂等**（重复跑没有副作用）：

1. 工作区有改动 → `git add -A` ＋ 自动生成提交信息（`auto: 学习记录同步 2026-10-25 21:40`）→ `commit`
2. 本地领先 `origin/main` → `git push`
3. 什么都没变 → 直接退出

日志在 `.git\autosync.log`（在 `.git` 里，不提交、不影响仓库）。

`.cmd` 只是包装：直接跑 `.ps1` 会被本机执行策略拦（"禁止运行脚本"），包装里用 `-ExecutionPolicy Bypass` 绕过，不改系统设置。想双击也行。

## 一次性配置（必须做一次）

```powershell
.\tools\setup-credentials.cmd
```

按提示粘贴 GitHub token（输入不回显）。它会：

- 把 token 写进 **remote URL**（存在 `.git\config` 里，**永远不会被提交**）
- 因此 git 完全不走凭据助手，绕开 Git Credential Manager 在无窗口环境里崩溃的问题
- 顺便配上代理 `http://127.0.0.1:7890`（当前网络下 `github.com` 直连不通）
- 跑一次 `push --dry-run` 验证；失败会自动把 origin 还原成干净 URL 并说明原因

token 建议用 **fine-grained、只授权 `CivilServants`、Contents: Read and write、90 天**。过期后重跑一次即可。

撤销：GitHub 删掉该 token，然后 `git remote set-url origin https://github.com/Medivhcrf/CivilServants.git`。

## 想自己写说明时

```powershell
.\tools\sync.ps1 "Day 12：概括题 8/15，漏点集中在培训与资金"
```

只提交不推送：`.\tools\sync.ps1 "说明" -NoPush`

## 定时兜底（可选）

想让「哪天没跟 AI 对话也自动同步」，注册一个每天 22:30 的计划任务（在**你自己的终端**里跑，沙箱里 schtasks 会被拒）：

```powershell
schtasks /Create /F /SC DAILY /ST 22:30 /TN "CivilServants AutoSync" /TR "cmd /c E:\Harness\repos\CivilServants\tools\autosync.cmd"
```

删除：`schtasks /Delete /TN "CivilServants AutoSync" /F`

## 维护提示

- `*.ps1` 必须保存为 **UTF-8 with BOM**。Windows PowerShell 5.1 对无 BOM 的 UTF-8 按 GBK 解码，中文全变乱码，脚本直接语法错误。
- 本脚本只同步 `main`。要让站点（GitHub Pages）也更新，需要再跑 `python tools/build_site.py` 与 `tools/publish.sh`（构建脚本在 Linux 环境下验证过，Windows 上需自备 python3）。
