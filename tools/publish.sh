#!/usr/bin/env bash
# 构建站点并发布到 GitHub Pages。
#
#   ./tools/publish.sh                 # 用默认提交信息
#   ./tools/publish.sh "更新第3课"      # 自定义提交信息
#
# 做三件事：
#   1. 构建 docs/（桌面版 + 手机版 + 总目录）
#   2. 提交并推送 main
#   3. 把 docs/ 同步到 gh-pages 分支（GitHub Pages 从这里发布）
#
# 站点地址：https://medivhcrf.github.io/CivilServants/

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MSG="${1:-更新学习资料与站点}"
REPO="git@github.com:Medivhcrf/CivilServants.git"
BRANCH="gh-pages"

echo "▸ 1/3 构建站点"
python3 tools/build_site.py

echo
echo "▸ 2/3 提交并推送 main"
git add -A
if git diff --cached --quiet; then
  echo "  main 无变化，跳过提交"
else
  git commit -q -m "$MSG"
  echo "  已提交：$(git log --oneline -1)"
fi
git push -q origin main
echo "  main 已推送"

echo
echo "▸ 3/3 同步到 $BRANCH"
TMP="$(mktemp -d /tmp/publish-XXXXXX)"
cleanup() {
  case "$TMP" in
    /tmp/publish-*) rm -rf "$TMP" ;;
    *) echo "  拒绝清理可疑路径：$TMP" >&2 ;;
  esac
}
trap cleanup EXIT

git clone -q --branch "$BRANCH" "$REPO" "$TMP"
# 清空分支内容（保留 .git）
find "$TMP" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -a docs/. "$TMP"/

cd "$TMP"
git add -A
if git diff --cached --quiet; then
  echo "  $BRANCH 无变化"
else
  git commit -q -m "$MSG"
  git push -q origin "$BRANCH"
  echo "  $BRANCH 已推送"
fi

echo
echo "✅ 完成"
echo "   仓库：https://github.com/Medivhcrf/CivilServants"
echo "   站点：https://medivhcrf.github.io/CivilServants/"
