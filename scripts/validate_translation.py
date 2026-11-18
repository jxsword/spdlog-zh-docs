#!/usr/bin/env python3
"""Validate translation quality for spdlog documentation (wiki + docs2.x docs-index).

移植自 fmt-zh-docs 同名脚本（2026-11-19），改造三项见注释。
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
STATE_FILE = REPO_ROOT / ".translation-state.json"
GLOSSARY_FILE = REPO_ROOT / "config" / "glossary.yml"


def load_glossary() -> Dict[str, str]:
    terms = {}
    if not GLOSSARY_FILE.exists():
        return terms
    try:
        import yaml
        with open(GLOSSARY_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        for term in data.get('terms', []):
            en = term.get('en', '')
            zh = term.get('zh', '')
            if en and zh:
                terms[en] = zh
    except Exception as e:
        logger.warning("Failed to load glossary: %s", e)
    return terms


def load_banned() -> List[Dict]:
    """spdlog 扩展：从 glossary.yml 顶层 `banned:` 键加载禁用译名黑名单。

    每项可为纯字符串（禁用译名）或 dict（含 `bad` 与可选 `prefer`/`reason` 键）。
    纯字符串规范化为 {"bad": s, "prefer": "", "reason": ""}。
    文件不存在或无 banned 键返回 []；解析异常时 warning 并返回 []。
    """
    banned = []
    if not GLOSSARY_FILE.exists():
        return banned
    try:
        import yaml
        with open(GLOSSARY_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return banned
        for item in data.get('banned') or []:
            if isinstance(item, str):
                banned.append({"bad": item, "prefer": "", "reason": ""})
            elif isinstance(item, dict):
                banned.append({
                    "bad": item.get('bad', ''),
                    "prefer": item.get('prefer', ''),
                    "reason": item.get('reason', ''),
                })
    except Exception as e:
        logger.warning("Failed to load banned terms: %s", e)
        return []
    return banned


def load_state() -> Dict:
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_code_blocks(content: str) -> List[str]:
    """Extract all code blocks from markdown."""
    pattern = r'```[\s\S]*?```'
    return re.findall(pattern, content)


def extract_inline_code(content: str) -> List[str]:
    """Extract all inline code from markdown."""
    pattern = r'`[^`\n]+`'
    return re.findall(pattern, content)


def extract_html_tags(content: str) -> List[str]:
    """Extract all HTML tags from markdown."""
    pattern = r'<[^>]+>'
    return re.findall(pattern, content)


def extract_urls(content: str) -> List[str]:
    """Extract all URLs from markdown links."""
    pattern = r'\[[^\]]+\]\((https?://[^)]+)\)'
    return re.findall(pattern, content)


# HTML 两级检查的辅助结构（DR-013 认可的放宽策略：
# 严格顺序对比已移除——翻译语序调整导致 <b>/<code> 句内互换属正常现象）
VOID_TAGS = {'img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base',
             'col', 'embed', 'source', 'track', 'wbr'}


# markdown 自动链接：<scheme://...> 形式（scheme 后紧跟 ://，中间无空格/属性）。
# 注意不能用"含 ://"粗判——<a href="https://..."> 是合法锚点标签，URL 同样含 ://
AUTOLINK_PATTERN = re.compile(r'^<[a-zA-Z][a-zA-Z0-9+.-]*://')


def normalize_tag(tag: str):
    """Normalize an HTML tag string to (tag_name, is_closing).

    Returns None for non-tag tokens: comments (`<!...`) and markdown autolinks
    (`<https://...>`) — the latter would otherwise be mistaken for an
    unclosed `<https>` tag and break pairing checks.
    """
    if AUTOLINK_PATTERN.match(tag):
        return None
    m = re.match(r'^</?\s*([a-zA-Z][a-zA-Z0-9-]*)', tag)
    if not m:
        return None
    return (m.group(1).lower(), tag.startswith('</'))


def strip_code(content: str) -> str:
    """Remove code so structural checks operate on prose only:
    - fenced code blocks and inline code spans;
    - indented code blocks (lines starting with >= 4 spaces — the corpus
      convention; list continuation prose uses 2 spaces), EXCEPT lines
      inside HTML <pre> blocks, whose indented continuation lines are real
      content (e.g. grammar blocks in syntax.md) and must survive stripping.
    Prevents tokens like <your-target> or `src/format.cc` from triggering
    HTML-tag / glossary false positives."""
    content = re.sub(r'```[\s\S]*?```', ' ', content)
    content = re.sub(r'`[^`\n]+`', ' ', content)
    lines = content.split('\n')
    out = []
    in_pre = False
    for line in lines:
        # mkdocstrings 指令行（如 ::: print(format_string<T...>, T&&...)）
        # 是文档 DSL 而非散文；其 <T...> 会干扰 HTML 标签检查，两侧均剥离
        if line.lstrip().startswith(':::'):
            out.append(' ')
            continue
        low = line.lower()
        if in_pre:
            if '</pre' in low:
                in_pre = False
            out.append(line)
            continue
        if '<pre' in low:
            in_pre = True
            out.append(line)
            continue
        if re.match(r'^ {4,}\S', line):
            out.append(' ')
        else:
            out.append(line)
    return '\n'.join(out)


def tag_type_counts(tags: List[str]) -> Dict:
    """Multiset of (tag_name, is_closing) — any add/remove of a tag type is structural damage."""
    counts = {}
    for t in tags:
        norm = normalize_tag(t)
        if norm is None:
            continue
        counts[norm] = counts.get(norm, 0) + 1
    return counts


def check_pairing(tags: List[str]) -> bool:
    """Stack-based pairing check on target tags; void tags and comments ignored."""
    stack = []
    for t in tags:
        norm = normalize_tag(t)
        if norm is None:
            continue
        name, closing = norm
        if name in VOID_TAGS:
            continue
        if closing:
            if not stack or stack[-1] != name:
                return False
            stack.pop()
        else:
            stack.append(name)
    return not stack


def validate_file(source_path: Path, target_path: Path, glossary: Dict[str, str],
                  banned: List[Dict] = None) -> Dict:
    """Validate a single translated file."""
    errors = []
    warnings = []
    
    if not source_path.exists():
        errors.append(f"Source file not found: {source_path}")
        return {"errors": errors, "warnings": warnings}
    
    if not target_path.exists():
        errors.append(f"Target file not found: {target_path}")
        return {"errors": errors, "warnings": warnings}
    
    source_content = source_path.read_text(encoding='utf-8')
    target_content = target_path.read_text(encoding='utf-8')
    
    # 1. Code block integrity
    source_code_blocks = extract_code_blocks(source_content)
    target_code_blocks = extract_code_blocks(target_content)
    if len(source_code_blocks) != len(target_code_blocks):
        errors.append(f"Code block count mismatch: source={len(source_code_blocks)}, target={len(target_code_blocks)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_code_blocks, target_code_blocks)):
            if src != tgt:
                errors.append(f"Code block {i} modified in translation")
    
    # 2. Inline code integrity — multiset 计数（与 HTML 两级检查同一原则：
    #    语序调整导致句内顺序互换属正常翻译现象，计数一致即结构无损）
    source_inline = extract_inline_code(source_content)
    target_inline = extract_inline_code(target_content)
    src_counts = {}
    tgt_counts = {}
    for t in source_inline:
        src_counts[t] = src_counts.get(t, 0) + 1
    for t in target_inline:
        tgt_counts[t] = tgt_counts.get(t, 0) + 1
    if src_counts != tgt_counts:
        diff_parts = []
        for key in sorted(set(src_counts) | set(tgt_counts)):
            s, t = src_counts.get(key, 0), tgt_counts.get(key, 0)
            if s != t:
                diff_parts.append(f"{key}:{s}->{t}")
        errors.append("Inline code multiset mismatch (missing/extra/modified spans): " + ", ".join(diff_parts))
    
    # 3. HTML tag integrity — 两级检查（用户已认可，2026-11-19）
    #   L1(error): 按类型 multiset 计数对比，任何标签类型增删=结构破坏
    #   L2(error): 译文标签配对完整性（栈配对，忽略 void/注释）
    #   严格顺序对比已移除（语序调整属正常翻译现象）
    #   检查前剥离代码（含缩进式代码块），避免 <your-target> 等占位符误报
    source_html = extract_html_tags(strip_code(source_content))
    target_html = extract_html_tags(strip_code(target_content))
    src_counts = tag_type_counts(source_html)
    tgt_counts = tag_type_counts(target_html)
    if src_counts != tgt_counts:
        diff_parts = []
        for key in sorted(set(src_counts) | set(tgt_counts)):
            s, t = src_counts.get(key, 0), tgt_counts.get(key, 0)
            if s != t:
                kind = "close" if key[1] else "open"
                diff_parts.append(f"<{key[0]} {kind}>:{s}->{t}")
        errors.append("HTML tag type counts mismatch: " + ", ".join(diff_parts))
    if target_html and not check_pairing(target_html):
        errors.append("Translated HTML tags are unbalanced or improperly nested")
    
    # 4. URL integrity
    source_urls = extract_urls(source_content)
    target_urls = extract_urls(target_content)
    if len(source_urls) != len(target_urls):
        warnings.append(f"URL count mismatch: source={len(source_urls)}, target={len(target_urls)}")
    else:
        for i, (src, tgt) in enumerate(zip(source_urls, target_urls)):
            if src != tgt:
                warnings.append(f"URL {i} modified: {src} -> {tgt}")
    
    # 5. Glossary terminology consistency
    #    在剥离代码与 URL 后的正文上匹配英文术语，避免 `src/format.cc`
    #    标识符与 cppreference 链接（如 .../chrono/duration）触发子串误报
    source_prose = re.sub(r'https?://\S+', ' ', strip_code(source_content))
    for en_term, zh_term in glossary.items():
        if en_term in source_prose:
            if zh_term not in target_content:
                warnings.append(f"Glossary term '{en_term}' not translated as '{zh_term}'")
    
    # 6. Placeholder check (PROTECTED_* should not remain)
    if 'PROTECTED_' in target_content:
        errors.append("Unrestored PROTECTED_* placeholders found in translation")
    
    # --- spdlog 扩展检查（计划 §6.8 黑名单 / §6.3 断链）---

    # 6b. 术语黑名单：禁用译名不得出现在译文正文
    #     与检查 5 同样方式处理译文：剥离代码块/内联代码与 URL 后再匹配
    if banned:
        target_prose = re.sub(r'https?://\S+', ' ', strip_code(target_content))
        for entry in banned:
            bad = entry.get('bad', '')
            if not isinstance(bad, str) or not bad:
                continue
            if bad in target_prose:
                prefer = entry.get('prefer', '')
                msg = f"Banned term '{bad}' found in translation"
                if prefer:
                    msg += f", prefer '{prefer}'"
                errors.append(msg)

    # 6c. 断链检查：markdown 相对链接目标必须存在（锚点部分不校验）
    for _label, url in re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', target_content):
        path_part = url.split('#', 1)[0]
        # 纯锚点链接
        if not path_part:
            continue
        if path_part.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        # 绝对路径的 .md 目标不校验
        if path_part.endswith('.md') and path_part.startswith('/'):
            continue
        # 相对目标（assets/ 或相对 .md 等）：先查译文目录，再回退查源目录
        if (not (target_path.parent / path_part).exists()
                and not (source_path.parent / path_part).exists()):
            errors.append(f"Broken relative link: {path_part}")

    # 7. Structure check (heading levels)
    source_headings = re.findall(r'^#{1,6}\s+.+', source_content, re.MULTILINE)
    target_headings = re.findall(r'^#{1,6}\s+.+', target_content, re.MULTILINE)
    if len(source_headings) != len(target_headings):
        warnings.append(f"Heading count mismatch: source={len(source_headings)}, target={len(target_headings)}")
    
    return {"errors": errors, "warnings": warnings}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate translation quality")
    parser.add_argument("--file", default=None,
                        help="只校验指定文件（如 index.md）；缺省校验全部")
    args = parser.parse_args()

    state = load_state()
    glossary = load_glossary()
    banned = load_banned()
    logger.info("Loaded %d glossary terms, %d banned terms", len(glossary), len(banned))

    all_errors = []
    all_warnings = []

    targets = state.get('files', {}).keys()
    if args.file:
        if args.file not in state.get('files', {}):
            logger.error("File not in translation state: %s", args.file)
            sys.exit(2)
        targets = [args.file]

    for fname in targets:
        if state.get('files', {}).get(fname, {}).get('excluded'):
            # DR-014：excluded 文件（如 ChangeLog-old.md 历史变更日志）不翻译，
            # zh/ 仅有占位页，与 source 全量对比必然报错，故跳过校验
            logger.info("Skipping %s (excluded from translation, DR-014)", fname)
            continue
        # spdlog：全 pending 页不校验（M1 占位站阶段 zh 文件未生成时 validate 全量跑仍可绿）
        segs = state.get('files', {}).get(fname, {}).get('segments', [])
        if not any(s.get('status') in ('translated', 'reviewed') for s in segs):
            logger.info("Skipping %s (no translated segments yet)", fname)
            continue
        source_path = SOURCE_DIR / fname
        target_path = ZH_DIR / fname
        logger.info("Validating %s", fname)
        result = validate_file(source_path, target_path, glossary, banned=banned)
        for err in result['errors']:
            all_errors.append(f"{fname}: {err}")
        for warn in result['warnings']:
            all_warnings.append(f"{fname}: {warn}")
    
    if all_warnings:
        logger.warning("Warnings (%d):", len(all_warnings))
        for w in all_warnings:
            logger.warning("  %s", w)
    
    if all_errors:
        logger.error("Errors (%d):", len(all_errors))
        for e in all_errors:
            logger.error("  %s", e)
        sys.exit(1)
    else:
        logger.info("All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()