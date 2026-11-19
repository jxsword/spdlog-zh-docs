#!/usr/bin/env bash
# sync_upstream.sh —— 双源同步总控（计划 §6.1，libuv 范式）
#
# 用法: scripts/sync_upstream.sh --init [--dry-run] [--repo URL] [--skip-docs-index]
#       scripts/sync_upstream.sh --since <sha> [--dry-run] [--repo URL] [--skip-docs-index]
#   --init          全量同步 wiki HEAD（幂等 reconcile，可安全重跑）
#   --since <sha>   增量同步（起点为 state 上次 wiki HEAD）
#   增量起点查询: python3 -c "import json;print(json.load(open('.translation-state.json'))['upstream_commit'])"
#
# 流程: 前置检查 → sync_docs.py（clone wiki + 规范化入库 + docs-index + state + 报告）
#       → source/assets → zh/assets 镜像（附件不翻译，构建目录需要）
#
# 幂等性: sync_docs.py --init 按 hash 迁移既有翻译状态，重跑不重置译文进度。
# 分支策略: 本脚本不建分支；CI 增量（sync-upstream.yml）自行创建 sync/<date> 分支开 PR。
#
# 退出码: 0=无变更 / 1=有变更需翻译 / 2=错误（libuv 范式，供 CI 判断）

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

usage() { sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2; }

MODE_ARGS=()
case "${1:-}" in
    --init) MODE_ARGS=(--init) ;;
    --since) [ $# -ge 2 ] || { echo "FATAL: --since 需要 40 位十六进制 SHA" >&2; exit 2; }
             MODE_ARGS=(--since "$2"); shift ;;
    -h|--help) usage ;;
    *) echo "FATAL: 首参数须为 --init 或 --since（见 --help）" >&2; usage ;;
esac
shift 2>/dev/null || true

# 其余参数透传（--dry-run / --repo URL / --skip-docs-index）
PASSTHROUGH=()
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run|--skip-docs-index) PASSTHROUGH+=("$1") ;;
        --repo) [ $# -ge 2 ] || { echo "FATAL: --repo 需要 URL" >&2; exit 2; }
                PASSTHROUGH+=("--repo" "$2"); shift ;;
        *) echo "FATAL: 未知参数: $1" >&2; usage ;;
    esac
    shift
done

echo "=============================================="
echo "== sync_upstream: ${MODE_ARGS[*]} $(date '+%F %T')"
echo "=============================================="

# --- 1. 前置检查 ---
echo "== [1/3] 前置检查 =="
for tool in git python3; do
    command -v "$tool" >/dev/null || { echo "FATAL: 缺少工具: $tool" >&2; exit 2; }
done

# 工作区必须干净（sync 会写 source/ 与 state；libuv 范式）
if [ -n "$(git status --porcelain)" ]; then
    echo "FATAL: 工作区不干净，请先提交或还原（git status）" >&2
    echo "  重跑指引: a) 提交当前改动后重跑；b) 放弃未入库改动: git checkout -- source zh && rm -f .translation-state.json*" >&2
    exit 2
fi

# --- 2. 同步（sync_docs.py 输出 JSON，报告由其内部落盘 reports/）---
echo "== [2/3] 同步执行 =="
SYNC_JSON="$(mktemp /tmp/spdlog-sync-json.XXXXXX)"
trap 'rm -f "$SYNC_JSON"' EXIT
# shellcheck disable=SC2086
if ! python3 scripts/sync_docs.py "${MODE_ARGS[@]}" "${PASSTHROUGH[@]}" --report > "$SYNC_JSON"; then
    echo "FATAL: sync_docs.py 执行失败（见上方日志），未写入或已回滚详见 state.bak" >&2
    exit 2
fi
python3 - "$SYNC_JSON" <<'PYEOF'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print("== 同步结果 ==")
print("  mode: %s | wiki HEAD: %s | docs-index: %s" % (
    data["mode"], data["commit"], data["docs_index_commit"] or "(未拉取)"))
print("  has_changes: %s | 报告: %s" % (data["has_changes"], data.get("report", "(无)")))
for f in data.get("files", []):
    print("    page: %-38s lines=%-5d segments=%-4d excluded=%s" % (
        f["file"], f.get("lines", 0), f.get("segments", 0), f.get("excluded", False)))
for c in data.get("changes", []):
    print("    change: %-40s %s (+%d/-%d segs, kept %d) %s" % (
        c["file"], c["type"], c["added_segments"], c["removed_segments"],
        c["kept_translated"], c["action"]))
PYEOF

# --- 3. 附件镜像 source/assets → zh/assets（mkdocs docs_dir=zh，附件不翻译）---
# 增量镜像（M3 演练修复）：rm -rf 会误删 zh 侧自备资产（如 docs-index 的
# logos/jetbrains-variant-4.svg，上游 docs2.x 附件未经 fetch_docs_index 同步），
# 故只增不删；上游同名资产以 source/assets 为准覆盖。
echo "== [3/3] 附件镜像 =="
if [ -d source/assets ]; then
    mkdir -p zh/assets
    cp -a source/assets/. zh/assets/
    echo "  zh/assets 已增量镜像（$(find zh/assets -type f | wc -l) 个文件）"
else
    echo "  无上游附件，跳过（zh/assets 内 zh 侧自备资产保留不清理）"
fi

HAS_CHANGES="$(python3 -c "import json,sys;print('1' if json.load(open(sys.argv[1],encoding='utf-8'))['has_changes'] else '0')" "$SYNC_JSON")"

echo "=============================================="
if [ "$HAS_CHANGES" = "1" ]; then
    echo "== 完成: 有变更需翻译（退出码 1）——按 translation-board 补译 → validate → PR"
    exit 1
else
    echo "== 完成: 无变更（退出码 0）"
    exit 0
fi
