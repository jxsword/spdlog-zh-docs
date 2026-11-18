#!/usr/bin/env python3
"""Markdown 语义切分（自 fmt-zh-docs sync_docs.py 的 segment_md 抽出为独立模块）。

行级切分（标题/代码块/表格/图片/HTML 块/段落），段落 sha256[:16] hash 是增量
状态机的迁移键。两处防死循环护栏源自 2026-11-18 fmt OOM 事故（DR-011），
属回归保护代码，修改前必读 tests/test_sync_docs.py 的 OOM 回归用例。
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Segment:
    id: str
    type: str
    content: str
    hash: str
    file_path: str
    line_start: int
    line_end: int
    metadata: Dict = field(default_factory=dict)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def segment_md(content: str, fname: str) -> List[Segment]:
    segs = []
    lines = content.split('\n')
    i = 0
    sec_idx = 0
    para_idx = 0
    cur_sec = ""
    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st.startswith('```'):
            start = i
            fence = st[:3]
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                i += 1
            if i < len(lines):
                i += 1
            code = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-code-{para_idx}", "code_block", code, compute_hash(code), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st.startswith('|') and '|' in st[1:]:
            start = i
            while i < len(lines) and lines[i].strip().startswith('|'):
                i += 1
            tbl = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-table-{para_idx}", "table", tbl, compute_hash(tbl), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st.startswith('#'):
            level = len(st) - len(st.lstrip('#'))
            title = st.lstrip('#').strip()
            segs.append(Segment(f"{fname}-h{level}-{sec_idx}", "heading", line, compute_hash(line), fname, i+1, i+1, {"level": level, "title": title}))
            cur_sec = title
            sec_idx += 1
            para_idx = 0
            i += 1
            continue
        if st.startswith('![') and '](' in st:
            segs.append(Segment(f"{fname}-img-{para_idx}", "image", line, compute_hash(line), fname, i+1, i+1, {"section": cur_sec}))
            para_idx += 1
            i += 1
            continue
        if st.startswith('<'):
            # HTML 块/跨行注释（<!-- ... --> 可跨多行，'>' 未必在首行）
            start = i
            while i < len(lines) and lines[i].strip() != '':
                i += 1
            html = '\n'.join(lines[start:i])
            segs.append(Segment(f"{fname}-html-{para_idx}", "html_block", html, compute_hash(html), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            continue
        if st:
            start = i
            paras = []
            while i < len(lines) and lines[i].strip() != '':
                ls = lines[i].strip()
                # i > start 才允许 break：首行必被消费，否则残缺行
                # （如 '![unclosed'）会生成空段且该行内容丢失
                if i > start and (ls.startswith('#') or ls.startswith('```') or (ls.startswith('|') and '|' in ls[1:]) or ls.startswith('![') or ls.startswith('<')):
                    break
                paras.append(lines[i])
                i += 1
            p = '\n'.join(paras)
            segs.append(Segment(f"{fname}-p-{para_idx}", "paragraph", p, compute_hash(p), fname, start+1, i, {"section": cur_sec}))
            para_idx += 1
            if i == start:
                # 防死循环护栏：内层循环未推进时强制前进一行，
                # 否则空 Segment 无限生成会撑爆内存（2026-11-18 OOM 事故根因）
                i += 1
        else:
            i += 1
    return segs
