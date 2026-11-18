#!/usr/bin/env python3
"""把指定文件的段落标记为 translated（M2 agent 翻译工作流的 state 更新步骤）。

用法：
  memgate python3 scripts/mark_translated.py --file index.md [--file QuickStart.md ...]

规则：
  - 仅 pending -> translated；不改动段落的 content 与 hash——源文 hash 保留供
    增量同步按 hash 迁移翻译状态（fmt 惯例，state 存源文视角）；
  - metadata 记 translator/translated_at（与 sync_docs.MIGRATE_META_KEYS 兼容）；
  - 写前将 state 备份为 .translation-state.json.bak（有实际变更时）；
  - excluded 文件（_Sidebar/_Footer）拒绝标记。
退出码：0=成功；2=文件不在 state。
"""

import argparse
import json
import shutil
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
STATE_FILE = REPO_ROOT / ".translation-state.json"


def main():
    parser = argparse.ArgumentParser(description="Mark file segments as translated")
    parser.add_argument('--file', required=True, action='append',
                        help="要标记的文件名（与 state files 键一致，可重复）")
    parser.add_argument('--translator', default='agent:glm-5.3-flash',
                        help="记入 metadata.translator 的标识")
    args = parser.parse_args()
    translator = args.translator

    state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    changed_total = 0
    missing = []
    for fname in args.file:
        fs = state.get('files', {}).get(fname)
        if fs is None:
            missing.append(fname)
            continue
        if fs.get('excluded'):
            print(f"SKIP (excluded): {fname}")
            continue
        changed = 0
        for seg in fs.get('segments', []):
            if seg.get('status') == 'pending':
                seg['status'] = 'translated'
                meta = seg.setdefault('metadata', {})
                meta['translator'] = translator
                meta['translated_at'] = time.strftime('%Y-%m-%d')
                changed += 1
        changed_total += changed
        print(f"{fname}: {changed} segments -> translated")

    if missing:
        print(f"ERROR: not in state: {', '.join(missing)}")
        return 2

    if changed_total:
        shutil.copy2(STATE_FILE, STATE_FILE.with_name(STATE_FILE.name + '.bak'))
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"state written ({changed_total} segments changed); backup: {STATE_FILE.name}.bak")
    else:
        print("nothing to change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
