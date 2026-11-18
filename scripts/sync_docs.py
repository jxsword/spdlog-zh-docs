#!/usr/bin/env python3
"""同步上游 spdlog 文档（GitHub wiki 快照 + docs2.x docs-index）— 全量与增量。

CLI:
  --init              全量同步 wiki HEAD（幂等 reconcile：state 已存在按 hash 迁移，上游消失页归档）
  --since <sha>       增量同步：diff since..HEAD，处理 A/M/D/R 变更 + 附件增删
  --dry-run           仅检测不写入（source/、state、archive 均不动）
  --repo URL          覆盖上游 wiki 仓库地址（测试注入本地 file:// 仓库）
  --skip-docs-index   跳过 docs2.x docs-index 拉取（离线测试用）
  --report            生成 sync 报告 reports/sync-<date>-<sha8>.md（计划 R2 范式）

wiki 形态（与 fmt 上游差异，计划 §6.1）:
  - flat 仓库：页面 *.md 全在根目录；非 .md 非 .git*/隐藏 = 附件 → source/assets/<相对路径>
  - 页名 slug 化：空格→连字符、保留编号；Home→index（站点 index，R1-7）；
    _Sidebar.md/_Footer.md excluded-skipped（不翻译）
  - [[wiki-link]] 与相对资产引用在分段建 hash 前转换（fix_links 模块）——
    source/ = 规范化上游快照，state 段落 hash 与 source/ 内容严格一致
  - docs-index 经 gh api 拉取（fetch_docs_index），入 state 统一增量管理

变更处理策略：
  A（新增）: 写入 source/，段落全部 pending
  M（修改）: 按段落 hash 迁移翻译状态，未变段落保留 translated/reviewed
  D（删除）: source/zh 归档至 archive/，不删翻译历史
  R（重命名）: 旧文件归档，新文件按 hash 迁移段落翻译状态
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fix_links import (build_page_slug_map, normalize_links,
                       slugify_page_title)
from segment_markdown import compute_hash, segment_md

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"
ZH_DIR = REPO_ROOT / "zh"
ARCHIVE_DIR = REPO_ROOT / "archive"
STATE_FILE = REPO_ROOT / ".translation-state.json"
REPORT_DIR = REPO_ROOT / "reports"
UPSTREAM_REPO = "https://github.com/gabime/spdlog.wiki.git"

# 原始页名（wiki 仓库名，含 .md）→ 不翻译，段落永久 skipped（计划 §6.1）
EXCLUDED_FROM_TRANSLATION = {"_Sidebar.md", "_Footer.md"}

SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")

# 段落迁移时随 hash 一并继承的翻译元数据键
MIGRATE_META_KEYS = ("translator", "translated_at", "reviewed_by", "reviewed_at")


@dataclass
class FileState:
    file_path: str
    upstream_hash: str
    upstream_commit: str
    segments: List[Dict]
    excluded: bool = False
    # 上游元数据（计划 §5：per-file 增 upstream_page_title/wiki_commit）
    upstream_page_title: str = ""   # 原始 wiki 页名（含空格，不含 .md）；docs-index 为 "docs/index.md"
    origin: str = "wiki"            # wiki | docs2.x


@dataclass
class TranslationState:
    upstream_repo: str
    upstream_commit: str
    docs_index_commit: str
    files: Dict[str, FileState]
    archived_files: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class SyncContext:
    """同步目标注入：生产用模块常量，测试注入 tmp_path 隔离目录。"""
    source_dir: Path
    zh_dir: Path
    archive_dir: Path
    state_file: Path
    excluded: frozenset = field(default_factory=lambda: frozenset(EXCLUDED_FROM_TRANSLATION))
    report_dir: Optional[Path] = None   # sync 报告目录；None → 仓库 reports/（测试须注入隔离目录）

    @property
    def assets_dir(self) -> Path:
        return self.source_dir / "assets"


@dataclass
class FileChange:
    file: str            # 显示名（R 为 "old -> new"，均用 slug 文件名）
    type: str            # A/M/D/R
    added_segments: int = 0
    removed_segments: int = 0
    kept_translated: int = 0
    action: str = ""     # applied / archived / would-apply / would-archive


def save_state(state_file: Path, state: TranslationState):
    """写 state；写前把旧文件落 .bak（计划 §8 回滚预案，*.bak 已 gitignore）。"""
    if state_file.exists():
        shutil.copy2(state_file, state_file.with_suffix(state_file.suffix + ".bak"))
    data = {
        'upstream_repo': state.upstream_repo,
        'upstream_commit': state.upstream_commit,
        'docs_index_commit': state.docs_index_commit,
        'files': {k: asdict(v) for k, v in state.files.items()},
        'archived_files': state.archived_files,
    }
    state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info("State saved (%d files)", len(state.files))


def load_state(state_file: Path) -> TranslationState:
    """从 JSON 载入；旧格式（缺 origin/upstream_page_title/docs_index_commit）向后兼容。"""
    data = json.loads(state_file.read_text(encoding='utf-8'))
    files = {}
    for k, v in data.get('files', {}).items():
        v.setdefault('excluded', False)
        v.setdefault('upstream_page_title', '')
        v.setdefault('origin', 'wiki')
        files[k] = FileState(**v)
    return TranslationState(
        upstream_repo=data.get('upstream_repo', ''),
        upstream_commit=data.get('upstream_commit', ''),
        docs_index_commit=data.get('docs_index_commit', ''),
        files=files,
        archived_files=data.get('archived_files', {}),
    )


# ---------- git 帮助函数（subprocess 一律内联字面量参数列表，无 shell 拼接） ----------

def _git(args: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True,
                            capture_output=True, text=True)
    return result.stdout


def _safe_join(base: Path, rel: str) -> Path:
    """resolve 后校验仍位于 base 内，防路径逃逸。"""
    base = base.resolve()
    p = (base / rel).resolve()
    if not p.is_relative_to(base):
        raise ValueError(f"path escapes {base}: {rel}")
    return p


def prepare_upstream(repo_url: str, workdir: Path) -> str:
    """blobless clone wiki 仓库（保留完整提交历史，--since diff 必需）并返回 HEAD SHA。

    wiki 为小仓库（页面 + 附件），无需 sparse-checkout。"""
    workdir.mkdir(parents=True)
    _git(["clone", "--filter=blob:none", repo_url, str(workdir)])
    return _git(["rev-parse", "HEAD"], cwd=workdir).strip()


def read_wiki(repo_dir: Path) -> Tuple[Dict[str, str], List[str]]:
    """读 wiki 工作树：根目录 *.md = 页面；非 .md 非 .git*/隐藏 = 附件相对路径。"""
    pages: Dict[str, str] = {}
    assets: List[str] = []
    for p in sorted(repo_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_dir).as_posix()
        if rel.split('/')[0] == '.git' or p.name.startswith('.'):
            continue
        if p.suffix == ".md" and "/" not in rel:
            pages[rel] = p.read_text(encoding='utf-8')
        elif p.suffix == ".md":
            logger.info("Skipping subdirectory markdown (not a wiki page): %s", rel)
        else:
            assets.append(rel)
    return pages, assets


# ---------- 段落状态迁移（自 fmt 移植） ----------

def migrate_segment_dicts(new_segs, old_segments: List[Dict],
                          excluded: bool) -> Tuple[List[Dict], int, int, int]:
    """按 hash 迁移旧段落翻译状态到新分段结果。

    返回 (新段落 dict 列表, added, removed, kept_translated)。
    未命中旧 hash 的段落标记 pending（excluded 文件一律 skipped）；
    非 excluded 文件继承到 skipped 状态时降级为 pending（排除集可能已变化）。"""
    old_by_hash = {s['hash']: s for s in old_segments}
    out = []
    added = 0
    kept = 0
    for seg in new_segs:
        d = asdict(seg)
        old = old_by_hash.get(seg.hash)
        if excluded:
            d['status'] = 'skipped'
        elif old:
            status = old.get('status') or 'pending'
            if status == 'skipped':
                status = 'pending'
            d['status'] = status
            old_meta = old.get('metadata', {})
            for k in MIGRATE_META_KEYS:
                if k in old_meta:
                    d['metadata'][k] = old_meta[k]
            if d['status'] in ('translated', 'reviewed'):
                kept += 1
        else:
            d['status'] = 'pending'
            added += 1
        out.append(d)
    removed = len({s['hash'] for s in old_segments} - {seg.hash for seg in new_segs})
    return out, added, removed, kept


def _archive_file(ctx: SyncContext, fname: str) -> int:
    """把 source/zh 中的文件移入 archive/（归档不删翻译历史）。"""
    moved = 0
    for root, sub in ((ctx.source_dir, "source"), (ctx.zh_dir, "zh")):
        f = root / fname
        if f.exists():
            dest_dir = _safe_join(ctx.archive_dir / sub, ".")
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(dest_dir / fname))
            moved += 1
    return moved


def _read_upstream_file(repo_dir: Path, rel: str) -> str:
    """读取上游工作树内文件；路径逃逸抛错。"""
    p = _safe_join(repo_dir, rel)
    if not p.is_file():
        raise FileNotFoundError(f"upstream file not found after checkout: {rel}")
    return p.read_text(encoding='utf-8')


_FSTATE_FIELDS = {"file_path", "upstream_hash", "upstream_commit", "segments",
                  "excluded", "upstream_page_title", "origin"}


def _fstate_from_dict(d: Dict) -> FileState:
    """从（可能是 archived_files 里的）dict 重建 FileState，容忍额外键。"""
    known = {k: v for k, v in d.items() if k in _FSTATE_FIELDS}
    known.setdefault('excluded', False)
    known.setdefault('upstream_page_title', '')
    known.setdefault('origin', 'wiki')
    return FileState(**known)


def _archive_state_entry(state: TranslationState, fname: str, head_sha: str):
    """把 state.files 中的条目移入 archived_files（幂等：不存在则跳过）。"""
    fstate = state.files.get(fname)
    if fstate is None:
        return
    d = asdict(fstate)
    d['archived_at'] = time.strftime("%Y-%m-%d")
    d['upstream_commit_at_archive'] = head_sha
    state.archived_files[fname] = d
    del state.files[fname]


def _apply_page(ctx: SyncContext, state: TranslationState, repo_dir: Path,
                t: str, old_path: str, new_path: str,
                head_sha: str, dry_run: bool, slug_map: Dict[str, str]) -> FileChange:
    """应用单个 wiki 页面变更到 source/、archive/ 与 state。

    幂等性：同一变更重复应用（CI 重跑）不重复归档、不重置已迁移状态。"""
    old_stem = Path(old_path).stem if old_path else None
    new_stem = Path(new_path).stem
    new_fname = _slug_fname(new_stem, slug_map)
    new_title = new_stem

    # D：归档 source/zh 与 state 条目，不删翻译历史
    if t == 'D':
        old_fname = _slug_fname(old_stem, slug_map)
        action = "would-archive" if dry_run else "archived"
        if not dry_run:
            _archive_file(ctx, old_fname)
            _archive_state_entry(state, old_fname, head_sha)
        return FileChange(old_fname, 'D', action=action)

    # A/M/R：读取上游新内容，wiki-link/资产引用规范化后按 hash 迁移旧段落状态
    content = _read_upstream_file(repo_dir, new_path)
    content = normalize_links(content, slug_map)

    old_fstate: Optional[FileState] = None
    display = new_fname
    if t == 'R':
        old_fname = _slug_fname(old_stem, slug_map)
        display = old_fname + " -> " + new_fname
        old_fstate = state.files.get(old_fname)
        from_archived = False
        if old_fstate is None and old_fname in state.archived_files:
            # 重跑场景：旧条目已归档，从归档恢复以迁移状态
            old_fstate = _fstate_from_dict(state.archived_files[old_fname])
            from_archived = True
        if not dry_run:
            _archive_file(ctx, old_fname)
            if not from_archived:
                _archive_state_entry(state, old_fname, head_sha)
    else:
        # A/M：state 已有条目（重跑场景）时按 hash 迁移，避免重置翻译状态
        old_fstate = state.files.get(new_fname)
        if old_fstate is None and t == 'M':
            logger.warning("M on unknown file %s, treating as A", new_fname)

    is_excluded = new_title + ".md" in ctx.excluded
    old_segments = old_fstate.segments if old_fstate is not None else []
    segs = segment_md(content, new_fname)
    seg_dicts, added, removed, kept = migrate_segment_dicts(segs, old_segments, is_excluded)
    fstate = FileState(
        file_path=new_fname,
        upstream_hash=compute_hash(content),
        upstream_commit=head_sha,
        segments=seg_dicts,
        excluded=is_excluded,
        upstream_page_title=new_title,
        origin="wiki",
    )
    action = "would-apply" if dry_run else "applied"
    if not dry_run:
        out = _safe_join(ctx.source_dir, new_fname)
        out.write_text(content, encoding='utf-8')
        state.files[new_fname] = fstate
    return FileChange(display, t if t != 'C' else 'A',
                      added_segments=added, removed_segments=removed,
                      kept_translated=kept, action=action)


def _apply_asset(ctx: SyncContext, t: str, rel: str, repo_dir: Path,
                 dry_run: bool) -> FileChange:
    """应用附件 A/M/D 变更到 source/assets/（附件不翻译，不占段落）。"""
    if t == 'D':
        target = _safe_join(ctx.assets_dir, rel)
        if not dry_run and target.exists():
            target.unlink()
        action = "would-delete" if dry_run else "deleted"
        return FileChange("assets/" + rel, 'D', action=action)
    if not dry_run:
        target = _safe_join(ctx.assets_dir, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_safe_join(repo_dir, rel).read_bytes())
    action = "would-apply" if dry_run else "applied"
    return FileChange("assets/" + rel, t, action=action)


def _slug_fname(stem: Optional[str], slug_map: Dict[str, str]) -> str:
    """页名 stem → slug 文件名；stem 为空返回空串。已知页名经 slug_map（含冲突校验）。"""
    if not stem:
        return ""
    if stem in slug_map:
        return slug_map[stem]
    return slugify_page_title(stem) + ".md"


def sync_init(ctx: SyncContext, repo_url: str, dry_run: bool = False,
              skip_docs_index: bool = False) -> Dict:
    """全量同步（幂等 reconcile）：拉 wiki HEAD 全量入库；state 已存在时按 hash 迁移，
    上游已消失的页面归档（D）。docs-index 经 gh api 拉取并入 state。"""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "wiki"
        sha = prepare_upstream(repo_url, repo)
        pages, assets = read_wiki(repo)
        titles = [Path(name).stem for name in pages]
        slug_map = build_page_slug_map(titles)
        logger.info("Pages: %s", sorted(pages.keys()))
        if assets:
            logger.info("Assets: %s", assets)

        docs_index = None
        if not skip_docs_index:
            import fetch_docs_index as fdi
            docs_index = fdi.fetch_docs_index()
            logger.info("docs-index sha: %s (%d bytes)",
                        docs_index["sha"], docs_index["size"])

        old_state: Optional[TranslationState] = None
        if ctx.state_file.exists():
            old_state = load_state(ctx.state_file)
        old_hashes = {k: v.upstream_hash for k, v in old_state.files.items()} if old_state else {}

        changes: List[FileChange] = []
        files_meta = []
        new_state = TranslationState(
            upstream_repo=repo_url, upstream_commit=sha,
            docs_index_commit=(docs_index or {}).get("sha", ""),
            files={},
            archived_files=dict(old_state.archived_files) if old_state else {},
        )
        new_fnames = set()
        for orig_name in sorted(pages.keys()):
            title = Path(orig_name).stem
            fname = slug_map[title]
            new_fnames.add(fname)
            content = pages[orig_name]
            content = normalize_links(content, slug_map)
            is_excluded = orig_name in ctx.excluded
            segs = segment_md(content, fname)
            old_fstate = old_state.files.get(fname) if old_state else None
            seg_dicts, added, removed, kept = migrate_segment_dicts(
                segs, old_fstate.segments if old_fstate else [], is_excluded)
            new_state.files[fname] = FileState(
                file_path=fname, upstream_hash=compute_hash(content),
                upstream_commit=sha, segments=seg_dicts, excluded=is_excluded,
                upstream_page_title=title, origin="wiki",
            )
            if old_state is None or old_hashes.get(fname) != compute_hash(content):
                has_change = True
                ctype = 'M' if (old_state is not None and fname in old_hashes) else 'A'
                changes.append(FileChange(fname, ctype, added_segments=added,
                                          removed_segments=removed,
                                          kept_translated=kept,
                                          action="would-apply" if dry_run else "applied"))
            files_meta.append({
                "orig": orig_name, "file": fname,
                "lines": len(content.splitlines()), "segments": len(seg_dicts),
                "excluded": is_excluded,
            })

        # docs-index 入 state（DR-001 范围；hash 变化记 M）
        if docs_index is not None:
            di_hash = compute_hash(docs_index["content"])
            old_di = old_state.files.get("docs-index.md") if old_state else None
            segs = segment_md(docs_index["content"], "docs-index.md")
            seg_dicts, added, removed, kept = migrate_segment_dicts(
                segs, old_di.segments if old_di else [], False)
            new_state.files["docs-index.md"] = FileState(
                file_path="docs-index.md", upstream_hash=di_hash,
                upstream_commit=sha, segments=seg_dicts, excluded=False,
                upstream_page_title="docs/index.md", origin="docs2.x",
            )
            if old_di is None or old_di.upstream_hash != di_hash:
                changes.append(FileChange("docs-index.md", 'M' if old_di else 'A',
                                          added_segments=added,
                                          removed_segments=removed,
                                          kept_translated=kept,
                                          action="would-apply" if dry_run else "applied"))
            files_meta.append({
                "orig": "docs/index.md (docs2.x)", "file": "docs-index.md",
                "lines": len(docs_index["content"].splitlines()),
                "segments": len(seg_dicts), "excluded": False,
            })

        # 上游已消失的页面 → 归档（D，不删翻译历史）
        vanished = (set(old_state.files.keys()) - new_fnames
                    - {"docs-index.md"}) if old_state else set()
        for fname in sorted(vanished):
            changes.append(FileChange(fname, 'D',
                                      action="would-archive" if dry_run else "archived"))
            if not dry_run:
                _archive_file(ctx, fname)
                _archive_state_entry(new_state, fname, sha)

        has_changes = bool(changes)

        if not dry_run:
            ctx.source_dir.mkdir(parents=True, exist_ok=True)
            for orig_name, content in pages.items():
                fname = slug_map[Path(orig_name).stem]
                content = normalize_links(content, slug_map)
                (_safe_join(ctx.source_dir, fname)).write_text(content, encoding='utf-8')
            for rel in assets:
                target = _safe_join(ctx.assets_dir, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(_safe_join(repo, rel).read_bytes())
            if docs_index is not None:
                (_safe_join(ctx.source_dir, "docs-index.md")).write_text(
                    docs_index["content"], encoding='utf-8')
            save_state(ctx.state_file, new_state)

        res = {
            "mode": "init",
            "repo": repo_url,
            "commit": sha,
            "docs_index_commit": (docs_index or {}).get("sha", ""),
            "dry_run": dry_run,
            "has_changes": has_changes,
            "files": files_meta,
            "assets": assets,
            "changes": [asdict(c) for c in changes],
        }
        return res


def sync_since(ctx: SyncContext, repo_url: str, since_sha: str,
               dry_run: bool = False, skip_docs_index: bool = False) -> Dict:
    """增量同步：diff since..HEAD，应用 A/M/D/R 变更 + 附件增删 + docs-index 比对。"""
    if not SHA40_RE.match(since_sha):
        raise ValueError(f"--since expects 40-hex sha, got: {since_sha!r}")
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "wiki"
        sha = prepare_upstream(repo_url, repo)
        # 校验 since 在拉取的历史内（不在则报错，避免静默漏检）
        _git(["cat-file", "-e", since_sha + "^{commit}"], cwd=repo)
        raw = _git(["diff", "--name-status", since_sha + ".." + sha], cwd=repo)
        triples = parse_name_status(raw)

        docs_index = None
        if not skip_docs_index:
            import fetch_docs_index as fdi
            docs_index = fdi.fetch_docs_index()

        state = load_state(ctx.state_file)  # 增量必须基于既有 state

        # 页名映射：以当前 HEAD 全页名构建（rename 目标/新页均可解析）
        pages_now, _ = read_wiki(repo)
        slug_map = build_page_slug_map([Path(n).stem for n in pages_now])

        changes: List[FileChange] = []
        for t, old, new in triples:
            target = new if t != 'D' else old
            if target.endswith(".md") and "/" not in target:
                changes.append(_apply_page(ctx, state, repo, t, old, new, sha,
                                           dry_run, slug_map))
            elif target.endswith(".md"):
                logger.info("Skipping subdirectory markdown change: %s %s -> %s",
                            t, old, new)
            else:
                changes.append(_apply_asset(ctx, t, target, repo, dry_run))

        # docs-index：内容 hash 与 state 比对，变更则按 M 迁移
        if docs_index is not None:
            di_hash = compute_hash(docs_index["content"])
            old_di = state.files.get("docs-index.md")
            if old_di is None or old_di.upstream_hash != di_hash:
                segs = segment_md(docs_index["content"], "docs-index.md")
                seg_dicts, added, removed, kept = migrate_segment_dicts(
                    segs, old_di.segments if old_di else [], False)
                if not dry_run:
                    (_safe_join(ctx.source_dir, "docs-index.md")).write_text(
                        docs_index["content"], encoding='utf-8')
                    state.files["docs-index.md"] = FileState(
                        file_path="docs-index.md", upstream_hash=di_hash,
                        upstream_commit=sha, segments=seg_dicts, excluded=False,
                        upstream_page_title="docs/index.md", origin="docs2.x",
                    )
                changes.append(FileChange("docs-index.md", 'M' if old_di else 'A',
                                          added_segments=added,
                                          removed_segments=removed,
                                          kept_translated=kept,
                                          action="would-apply" if dry_run else "applied"))
            state.docs_index_commit = docs_index["sha"]

        if not dry_run:
            state.upstream_commit = sha
            save_state(ctx.state_file, state)
        res = {
            "mode": "incremental",
            "repo": repo_url,
            "commit": sha,
            "docs_index_commit": state.docs_index_commit,
            "dry_run": dry_run,
            "has_changes": bool(changes),
            "changes": [asdict(c) for c in changes],
        }
        return res


def parse_name_status(raw: str) -> List[Tuple[str, str, str]]:
    """解析 git diff --name-status 输出为 (type, old, new) 列表。

    R/C 行形如 "R100\\told\\tnew"，其余为 "M\\tpath"。"""
    out = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            logger.warning("Skipping unparsable diff line: %r", line)
            continue
        code = parts[0]
        t = code[0]
        if t in ('R', 'C'):
            if len(parts) < 3:
                logger.warning("Rename/copy line missing paths: %r", line)
                continue
            out.append((t, parts[1], parts[2]))
        else:
            out.append((t, parts[1], parts[1]))
    return out


def write_report(res: Dict, report_dir: Optional[Path] = None) -> str:
    """生成 sync 报告 reports/sync-<date>-<sha8>.md（计划 R2 范式）。

    仅在 CLI --report 时调用；目录可注入（测试隔离），缺省仓库 reports/。"""
    report_dir = Path(report_dir or REPORT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)
    date = time.strftime("%Y-%m-%d")
    sha8 = res["commit"][:8]
    path = REPORT_DIR / ("sync-" + date + "-" + sha8 + ".md")
    lines = []
    lines.append("# 同步报告：" + res["mode"] + "（wiki @" + sha8 + "）")
    lines.append("")
    lines.append("> 生成: " + time.strftime('%Y-%m-%d %H:%M:%S') + " ｜ 上游: " + res["repo"])
    lines.append("> wiki HEAD: " + res["commit"] + " ｜ docs-index: "
                 + (res['docs_index_commit'] or '(未拉取)') + " ｜ dry-run: "
                 + str(res['dry_run']))
    lines.append("")
    total_lines = sum(f.get("lines", 0) for f in res.get("files", []))
    total_segs = sum(f.get("segments", 0) for f in res.get("files", []))
    if res.get("files"):
        lines.append("## 页面清单")
        lines.append("")
        lines.append("| 原始页名 | 入库文件 | 行数 | 段数 | excluded |")
        lines.append("|---|---|---:|---:|---|")
        for f in res["files"]:
            lines.append("| " + f['orig'] + " | " + f['file'] + " | "
                         + str(f['lines']) + " | " + str(f['segments']) + " | "
                         + ("是" if f['excluded'] else "否") + " |")
        lines.append("| **合计** |  | **" + str(total_lines) + "** | **"
                     + str(total_segs) + "** |  |")
        lines.append("")
    if res.get("assets"):
        lines.append("## 附件（source/assets/）")
        lines.append("")
        for a in res["assets"]:
            lines.append("- " + a)
        lines.append("")
    if res.get("changes"):
        lines.append("## 变更明细")
        lines.append("")
        lines.append("| 文件 | 类型 | 新增段 | 移除段 | 保留已译 | 动作 |")
        lines.append("|---|---|---:|---:|---:|---|")
        for c in res["changes"]:
            lines.append("| " + c['file'] + " | " + c['type'] + " | "
                         + str(c['added_segments']) + " | " + str(c['removed_segments'])
                         + " | " + str(c['kept_translated']) + " | " + c['action'] + " |")
        lines.append("")
    lines.append("**has_changes: " + str(res['has_changes'])
                 + "**（退出码口径：0=无变更 / 1=有变更需翻译 / 2=错误）")
    lines.append("")
    path.write_text("\n".join(lines), encoding='utf-8')
    logger.info("Report written: %s", path)
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sync_docs.py",
        description="同步上游 spdlog 文档（wiki 全量 --init + 增量 --since）")
    p.add_argument("--init", action="store_true", help="全量同步 wiki HEAD（幂等 reconcile）")
    p.add_argument("--since", metavar="SHA",
                   help="增量同步起点 commit SHA（40 位十六进制）")
    p.add_argument("--dry-run", action="store_true",
                   help="仅检测变更不写入（不更新 source/、state、archive/）")
    p.add_argument("--repo", default=UPSTREAM_REPO,
                   help="上游 wiki 仓库 URL（默认 gabime/spdlog.wiki.git；测试可注入本地 file:// 仓库）")
    p.add_argument("--skip-docs-index", action="store_true",
                   help="跳过 docs2.x docs-index 拉取（离线测试用）")
    p.add_argument("--report", action="store_true", help="生成 reports/ 同步报告")
    return p


def main(argv: Optional[List[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.since and not SHA40_RE.match(args.since):
        parser.error("--since 需为 40 位十六进制 commit SHA")
    if args.init and args.since:
        parser.error("--init 与 --since 互斥")
    if not (args.init or args.since):
        parser.error("需指定模式：--init（全量）/ --since（增量）")

    ctx = SyncContext(SOURCE_DIR, ZH_DIR, ARCHIVE_DIR, STATE_FILE)
    try:
        if args.since:
            res = sync_since(ctx, args.repo, args.since,
                             dry_run=args.dry_run, skip_docs_index=args.skip_docs_index)
        else:
            res = sync_init(ctx, args.repo, dry_run=args.dry_run,
                            skip_docs_index=args.skip_docs_index)
        if args.report:
            res["report"] = write_report(res, ctx.report_dir)
        print(json.dumps(res, ensure_ascii=False))
    except Exception as e:
        logger.error("Failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
