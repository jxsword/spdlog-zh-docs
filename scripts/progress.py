#!/usr/bin/env python3
"""自动生成 reports/progress.md（页 × 段落状态统计）。

数据唯一来源 = .translation-state.json；自动生成禁手改（计划 R2）。
"""

import json
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
STATE_FILE = REPO_ROOT / ".translation-state.json"
REPORT = REPO_ROOT / "reports" / "progress.md"


def main():
    state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    rows = []
    total = Counter()
    for fname, fs in sorted(state.get('files', {}).items()):
        counts = Counter(s.get('status', 'pending') for s in fs['segments'])
        total.update(counts)
        n = sum(counts.values())
        done = counts.get('translated', 0) + counts.get('reviewed', 0)
        pct = f"{done / n * 100:.0f}%" if n else "—"
        rows.append((fname, fs.get('upstream_page_title', ''), n,
                     counts.get('translated', 0), counts.get('reviewed', 0),
                     counts.get('pending', 0), counts.get('skipped', 0), pct))

    grand = sum(total.values())
    done_all = total.get('translated', 0) + total.get('reviewed', 0)
    pct_all = f"{done_all / grand * 100:.1f}%" if grand else "—"

    lines = [
        "# 翻译进度看板（自动生成，禁手改）",
        "",
        f"> 生成: {time.strftime('%Y-%m-%d %H:%M:%S')} ｜ 数据源: .translation-state.json"
        f" ｜ 上游基线: {state.get('upstream_commit', '')[:12]}",
        "",
        "| 文件 | 上游页名 | 段数 | translated | reviewed | pending | skipped | 进度 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    lines.append("| **合计** | | " + f"**{grand}** | **{total.get('translated', 0)}** | "
                 f"**{total.get('reviewed', 0)}** | **{total.get('pending', 0)}** | "
                 f"**{total.get('skipped', 0)}** | **{pct_all}** |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding='utf-8')
    print(f"written: {REPORT}（{len(rows)} 文件，{grand} 段，总进度 {pct_all}）")


if __name__ == "__main__":
    main()
