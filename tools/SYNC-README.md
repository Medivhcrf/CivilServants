# 学习记录同步（Windows）

把当天的学习记录提交并推送到 GitHub。

```powershell
./tools/sync.ps1 "Day 12：概括题 8/15，漏点集中在培训与资金"
```

做什么：
1. `git add -A`
2. `git commit -m "<说明>"`
3. `git push origin main`

只提交不推送：

```powershell
./tools/sync.ps1 "说明" -NoPush
```

**注意**：本脚本只同步 `main`。要让站点（GitHub Pages）也更新，需要再跑 `python tools/build_site.py` 与 `tools/publish.sh`（构建脚本在 Linux 环境下验证过，Windows 上需自备 python3）。
