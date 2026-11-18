#!/usr/bin/env python3
"""结构对齐检查（计划 §6.5「结构对等 100%」的机检实现，B1 起 agent 自检 + 批次门禁复用）。

zh/ 译文与 source/ 原文做两视图比对：

  A. 正则视图（与 validate_translation.py 同源）：```...``` 围栏块逐块计数 + 逐字节对比。
  B. 行走视图（segment_markdown.segment_md 同一分段器）：段块总数 / 逐块类型 /
     标题级别 / 图片 URL / 表格行数对齐。

  只用 B 做结构、不用 B 比代码内容的原因：segment_md 是行级分段器，会把行内
  ```span``` 形态（如 Custom-formatting.md 第 5 行）误并为 code_block——该历史
  行为在源/译两侧一致发生，结构仍可对齐；代码逐字节守卫由视图 A（+ validate
  内联代码 multiset）承担。

另做漏译检测：段落译文与源文逐字节相同、且源文英文停用词 ≥3 时判为漏译（错误）；
停用词 1–2 或实词 ≥3 时降级为告警（人工复核）。页头注入的「原文」行（^> 原文：）
在比对前剥离，不参与分段。

退出码：0=全部通过；1=存在错误；2=用法错误。
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from segment_markdown import segment_md  # noqa: E402  同一分段器保证视图 B 与 state 一致

SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
STATE_FILE = REPO_ROOT / ".translation-state.json"

# 页头注入行（make 原文链接由编排管线统一注入，agent 不生成）
SRC_LINE_RE = re.compile(r'^> 原文：')

# 代码守卫视图 A：与 validate_translation.extract_code_blocks 完全同源
FENCE_RE = re.compile(r'```[\s\S]*?```')

# 分隔线（剥离代码后整行匹配）
HR_LINE_RE = re.compile(r'^\s*(\*\*\*|---)\s*$')

# 漏译检测：译文与源文逐字节相同时，按英文停用词计数判定
STOPWORDS = {
    'the', 'a', 'an', 'you', 'your', 'and', 'or', 'of', 'to', 'is', 'are',
    'this', 'that', 'it', 'will', 'for', 'with', 'if', 'on', 'in', 'be',
    'can', 'use', 'using', 'when', 'would', 'should', 'must', 'need', 'only',
    'each', 'all', 'every', 'not', 'by', 'as', 'from', 'at', 'we', 'our',
}
WORD_RE = re.compile(r'[A-Za-z]{2,}')


def strip_src_lines(text: str) -> str:
    return '\n'.join(l for l in text.split('\n') if not SRC_LINE_RE.match(l))


def prose_words(text: str) -> list:
    """剥离内联代码/URL/Markdown 标记后的英文词序列。"""
    t = re.sub(r'`[^`\n]+`', ' ', text)
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'[*_>#~"()\[\]]', ' ', t)
    return WORD_RE.findall(t)


def stopword_count(text: str) -> int:
    return sum(1 for w in prose_words(text) if w.lower() in STOPWORDS)


def check_file(fname: str, state: dict) -> list:
    """返回该文件的错误列表（告警单独返回，见 check_file_verbose）。"""
    errors, warnings = [], []
    fs = state.get('files', {}).get(fname)
    if fs is None:
        return [f"{fname}: not in translation state"], warnings
    src_path = SOURCE_DIR / fname
    tgt_path = ZH_DIR / fname
    if not src_path.exists():
        return [f"{fname}: source missing: {src_path}"], warnings
    if not tgt_path.exists():
        return [f"{fname}: target missing: {tgt_path}"], warnings

    src_text = src_path.read_text(encoding='utf-8')
    tgt_text = strip_src_lines(tgt_path.read_text(encoding='utf-8'))

    # 视图 A：围栏代码块逐字节守卫（与 validate 同源）
    src_code = FENCE_RE.findall(src_text)
    tgt_code = FENCE_RE.findall(tgt_text)
    if len(src_code) != len(tgt_code):
        errors.append(f"code block count mismatch: source={len(src_code)}, target={len(tgt_code)}")
    else:
        for i, (s, t) in enumerate(zip(src_code, tgt_code)):
            if s != t:
                errors.append(f"code block {i} modified (must be byte-identical)")

    # 视图 B：同一分段器的结构对齐
    src_segs = segment_md(src_text, fname)
    tgt_segs = segment_md(tgt_text, fname)
    if len(src_segs) != len(tgt_segs):
        errors.append(
            f"segment count mismatch: source={len(src_segs)}, target={len(tgt_segs)}")
    else:
        for i, (s, t) in enumerate(zip(src_segs, tgt_segs)):
            if s.type != t.type:
                errors.append(
                    f"segment {i} type mismatch: source={s.type}, target={t.type} "
                    f"(source content: {s.content[:60]!r})")
                continue
            if s.type == 'heading' and s.metadata.get('level') != t.metadata.get('level'):
                errors.append(f"segment {i} heading level mismatch")
            if s.type == 'image':
                su = re.search(r'\(([^)]*)\)', s.content)
                tu = re.search(r'\(([^)]*)\)', t.content)
                if not su or not tu or su.group(1) != tu.group(1):
                    errors.append(f"segment {i} image URL modified")
            if s.type == 'table':
                srows = sum(1 for l in s.content.split('\n') if l.strip().startswith('|'))
                trows = sum(1 for l in t.content.split('\n') if l.strip().startswith('|'))
                if srows != trows:
                    errors.append(
                        f"segment {i} table row count mismatch: {srows} -> {trows}")
            if s.type == 'paragraph':
                if not t.content.strip():
                    errors.append(f"segment {i} paragraph empty in translation")
                elif t.content == s.content:
                    sc = stopword_count(s.content)
                    words = prose_words(s.content)
                    if sc >= 3:
                        errors.append(
                            f"segment {i} paragraph left untranslated "
                            f"(identical to source, {sc} stopwords)")
                    elif sc >= 1 or len(words) >= 3:
                        warnings.append(
                            f"segment {i} paragraph identical to source — review "
                            f"({s.content[:50]!r})")

    # 分隔线守卫（剥离代码后整行计数，防 *** 被并入正文行或丢失）
    src_bare = FENCE_RE.sub(' ', src_text)
    tgt_bare = FENCE_RE.sub(' ', tgt_text)
    src_hr = sum(1 for l in src_bare.split('\n') if HR_LINE_RE.match(l))
    tgt_hr = sum(1 for l in tgt_bare.split('\n') if HR_LINE_RE.match(l))
    if src_hr != tgt_hr:
        errors.append(f"horizontal-rule line count mismatch: source={src_hr}, target={tgt_hr}")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Check structural alignment of zh translation")
    parser.add_argument('--file', action='append', default=None,
                        help="只检查指定文件（可重复）；缺省检查 state 内全部非 excluded 文件")
    args = parser.parse_args()

    state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    targets = args.file or [
        f for f, fs in state.get('files', {}).items()
        # 全量模式只检查已开工页（存在 translated/reviewed 段）：
        # 未开翻页 zh 目标尚不存在，报缺目标只是噪音
        if not fs.get('excluded')
        and any(s.get('status') in ('translated', 'reviewed') for s in fs.get('segments', []))
    ]

    total_err = total_warn = 0
    for fname in targets:
        errors, warnings = check_file(fname, state)
        total_err += len(errors)
        total_warn += len(warnings)
        status = "OK" if not errors else "FAIL"
        if errors or warnings:
            print(f"[{status}] {fname} ({len(errors)} errors, {len(warnings)} warnings)")
            for e in errors:
                print(f"  ERROR: {e}")
            for w in warnings:
                print(f"  WARN:  {w}")
        else:
            print(f"[{status}] {fname}")

    if total_err:
        print(f"\nalignment check FAILED: {total_err} errors, {total_warn} warnings")
        sys.exit(1)
    print(f"\nalignment check passed ({total_warn} warnings to review)")
    sys.exit(0)


if __name__ == "__main__":
    main()
