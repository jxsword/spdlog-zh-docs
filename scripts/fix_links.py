#!/usr/bin/env python3
"""链接处理：[[wiki-link]]→标准 md 链接转换（sync 期对 source/ 调用）
+ 译文页相对链接/锚点/资产引用修复（M2 对 zh/ 调用）。

wiki 形态要点（计划 §6.3）：
  - [[Page]] / [[Page|text]] / [[Page#anchor|text]] 转标准链接；
    目标名按 slug 映射不译（成为 URL 一部分，由占位符保护），显示文本可译；
  - 相对资产引用（![](img.png)）改写为 assets/img.png（附件同步入 source/assets/）；
  - 锚点沿用 GitHub wiki 的标题 slug，zh 侧经 anchor_map 重映射。
"""

import logging
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"

# GitHub wiki 页名 → slug（计划 §6.1：空格→连字符、保留编号；Home 作站点 index）
SITE_INDEX_PAGE = "Home"


def slugify_page_title(title: str) -> str:
    """wiki 页标题 → slug 文件名（不含 .md）。'Home' 映射为 'index'（站点 index，R1-7）。"""
    if title == SITE_INDEX_PAGE:
        return "index"
    slug = re.sub(r'\s+', '-', title.strip())
    slug = slug.strip('-')
    return slug


def slugify(text: str) -> str:
    """标题文本 → URL 锚点 slug（GitHub wiki 风格）。"""
    text = re.sub(r'^#+\s*', '', text)
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = text.strip('-')
    return text


def extract_headings(content: str) -> List[Tuple[int, str]]:
    """Extract all headings with their level."""
    headings = []
    for line in content.split('\n'):
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((level, title))
    return headings


def build_page_slug_map(page_titles: List[str]) -> Dict[str, str]:
    """原始页名（不含 .md）→ slug 文件名（含 .md）。冲突时报错（防链接错挂）。"""
    slug_map: Dict[str, str] = {}
    for title in page_titles:
        slug = slugify_page_title(title)
        fname = slug + ".md"
        for t, f in slug_map.items():
            if f == fname:
                raise ValueError(f"slug collision: {title!r} and {t!r} both -> {fname}")
        slug_map[title] = fname
    return slug_map


# [[Page]] / [[Page|text]] / [[Page#anchor]] / [[Page#anchor|text]] / [[#anchor]]
WIKI_LINK_RE = re.compile(r'\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]')


def convert_wiki_links(content: str, slug_map: Dict[str, str],
                       warn_cb: Optional[Callable[[str], None]] = None) -> str:
    """把 GitHub wiki 链接语法转为标准 md 链接（sync 期在分段/建 hash 前调用，
    保证 .translation-state.json 的段落 hash 与 source/ 内容一致）。

    - [[Page]]            -> [Page](Page.md)
    - [[Page|text]]       -> [text](Page.md)
    - [[Page#sec|text]]   -> [text](Page.md#sec)
    - [[#sec]] / [[#sec|x]] -> [x|sec](#sec)  同页锚点
    - 目标页不在 slug_map（悬空 wiki-link）: 照常 slug 化输出，warn 提示，
      由 validate 断链检查在 M2 阶段暴露。
    """
    def _warn(msg: str):
        if warn_cb is not None:
            warn_cb(msg)
        else:
            logger.warning(msg)

    def replace(match: re.Match) -> str:
        target = match.group(1).strip()
        text = (match.group(2) or '').strip() or target
        if target.startswith('#'):
            anchor = target[1:].strip()
            return f"[{text}](#{anchor})"
        if '#' in target:
            page, anchor = target.split('#', 1)
            page, anchor = page.strip(), anchor.strip()
        else:
            page, anchor = target, ''
        if page in slug_map:
            fname = slug_map[page]
        elif page + ".md" in slug_map.values():
            # 已是 slug 形态的目标（如 [[Usage-basics]]）容错直取
            fname = page + ".md"
        else:
            fname = slugify_page_title(page) + ".md"
            _warn(f"dangling wiki-link target {page!r} -> {fname} (not in page map)")
        url = fname + (f"#{anchor}" if anchor else "")
        return f"[{text}]({url})"

    return WIKI_LINK_RE.sub(replace, content)


def normalize_links(content: str, slug_map: Dict[str, str]) -> str:
    """链接规范化（sync 期在分段建 hash 前调用，source/ = 规范化上游快照）：

    1. [[Page]] / [[Page|text]] wiki 语法 → 标准 md 链接（convert_wiki_links）；
    2. 裸页名链接 [text](Page-Name)（GitHub wiki 实测全库即此形态，无 [[..]]）
       → [text](Page-Name.md)，锚点一并保留；目标按 slug_map（原始页名或 slug 均可命中）；
    3. 相对资产引用 [t](img.png) → assets/img.png（wiki 附件同步在 source/assets/）；
    4. 绝对 URL（http/https 等）、锚点、.md/.html 目标原样保留（计划 §6.1）。"""
    content = convert_wiki_links(content, slug_map)

    slug_fnames = set(slug_map.values())

    def replace(match: re.Match) -> str:
        text_part = match.group(1)   # 完整括号文本部分："[text]" 或 "![alt]"
        url = match.group(2)
        stripped = url.strip()
        if (stripped.startswith(('http://', 'https://', '/', '#', 'assets/',
                                 'mailto:', '<'))
                or stripped.endswith(('.md', '.html'))
                or not stripped):
            return match.group(0)
        if '?' in stripped or '*' in stripped:
            return match.group(0)
        page_part, _, anchor = stripped.partition('#')
        suffix = "#" + anchor if anchor else ""
        # 裸页名链接：URL = slug（去 .md）或原始页名 → 补 .md（可带锚点）
        if page_part + ".md" in slug_fnames:
            return f"{text_part}({page_part}.md{suffix})"
        if page_part in slug_map:
            return f"{text_part}({slug_map[page_part]}{suffix})"
        # 其余相对目标视为附件引用
        return f"{text_part}(assets/{stripped})"

    return re.sub(r'(!\[[^\]]*\]|\[[^\]]*\])\(([^)\s]+)\)', replace, content)


def generate_anchor_map(source_dir: Path, target_dir: Path) -> Dict[str, str]:
    """Generate mapping from source heading slugs to target heading slugs."""
    anchor_map = {}

    for source_file in sorted(source_dir.glob("*.md")):
        target_file = target_dir / source_file.name
        if not target_file.exists():
            continue

        source_content = source_file.read_text(encoding='utf-8')
        target_content = target_file.read_text(encoding='utf-8')

        source_headings = extract_headings(source_content)
        target_headings = extract_headings(target_content)

        if len(source_headings) != len(target_headings):
            logger.warning("Heading count mismatch in %s: source=%d, target=%d",
                           source_file.name, len(source_headings), len(target_headings))
            continue

        for (src_level, src_title), (tgt_level, tgt_title) in zip(source_headings, target_headings):
            if src_level != tgt_level:
                logger.warning("Heading level mismatch: %s vs %s", src_title, tgt_title)
            src_slug = slugify(src_title)
            tgt_slug = slugify(tgt_title)
            if src_slug != tgt_slug:
                anchor_map[src_slug] = tgt_slug

    return anchor_map


def fix_relative_links(content: str, anchor_map: Dict[str, str]) -> str:
    """Fix relative .md links and anchor references."""
    # [text](file.md) 原样；[text](file.md#anchor) 的 anchor 经 anchor_map 重映射
    def replace_md_link(match):
        text = match.group(1)
        url = match.group(2)
        if url.endswith('.md') or '.md#' in url:
            parts = url.split('#', 1)
            file_part = parts[0]
            if len(parts) > 1:
                anchor = parts[1]
                new_anchor = anchor_map.get(anchor, anchor)
                return f"[{text}]({file_part}#{new_anchor})"
        return match.group(0)

    content = re.sub(r'\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)', replace_md_link, content)
    return content


def inject_anchor_ids(content: str, anchor_map: Dict[str, str]) -> str:
    """Inject HTML id attributes into headings for anchor linking (attr_list 语法)."""
    lines = content.split('\n')
    result = []

    for line in lines:
        match = re.match(r'^(#{1,6})\s+(.+?)\s*(?:\{#([\w-]+)\})?$', line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            slug = slugify(title)
            # 反查：zh 标题 slug 已等于某源 slug 的映射目标时，锚回源 slug，
            # 使译文中的源锚点链接（经 anchor_map 重映射后）仍可命中
            target_slug = slug
            for src, tgt in anchor_map.items():
                if tgt == slug:
                    target_slug = src
                    break
            line = f"{'#' * level} {title} {{#{target_slug}}}"
        result.append(line)

    return '\n'.join(result)


def process_file(target_path: Path, anchor_map: Dict[str, str]):
    """Process a single translated file to fix links and inject anchors.

    zh 侧不重写资产/页链接（sync 期已在 source 规范化，译文继承），仅锚点重映射。"""
    content = target_path.read_text(encoding='utf-8')

    content = fix_relative_links(content, anchor_map)
    content = inject_anchor_ids(content, anchor_map)

    target_path.write_text(content, encoding='utf-8')
    logger.info("Processed links in %s", target_path.name)


def main():
    anchor_map = generate_anchor_map(SOURCE_DIR, ZH_DIR)
    logger.info("Generated anchor map with %d entries", len(anchor_map))

    map_file = REPO_ROOT / "config" / "anchor_map.yml"
    map_file.parent.mkdir(exist_ok=True)
    import yaml
    map_file.write_text(yaml.dump(anchor_map, allow_unicode=True), encoding='utf-8')
    logger.info("Saved anchor map to %s", map_file)

    for target_file in sorted(ZH_DIR.glob("*.md")):
        process_file(target_file, anchor_map)

    logger.info("Link fixing complete")


if __name__ == "__main__":
    main()
