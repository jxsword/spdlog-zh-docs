"""sync_docs.py 增量同步测试（spdlog wiki 形态）。

用本地临时 git 仓库（file:// URL）模拟 flat wiki 仓库，覆盖：
  - CLI 参数校验（--since 40 位十六进制 / --init 与 --since 互斥 / 缺模式报错）
  - slug 规范化（空格→连字符、Home→index）与 excluded（_Sidebar/_Footer）
  - 全量同步（--init）：页面 + 附件（非 .md → source/assets/）
  - 增量同步 A/M/D/R 全变更类型 + 段落翻译状态按 hash 迁移 + 归档不删历史
  - --dry-run 零写入、幂等性（同变更重复应用不重置状态）
  - docs-index 注入路径（monkeypatch fetch，离线）

Mimosa 纪律：subprocess 一律内联参数列表；路径 pathlib resolve 校验。
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import sync_docs  # noqa: E402
from sync_docs import (  # noqa: E402
    SyncContext,
    parse_name_status,
    sync_init,
    sync_since,
)


# ---------- 工具 ----------

def git(*args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   capture_output=True, text=True)


def rev_head(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                          check=True, capture_output=True, text=True).stdout.strip()


def tree_hash(root: Path) -> str:
    """目录树内容指纹（dry-run 零写入断言用）。"""
    h = hashlib.sha256()
    if not root.exists():
        return "missing"
    for p in sorted(root.rglob("*")):
        h.update(str(p.relative_to(root)).encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


@pytest.fixture
def upstream(tmp_path) -> Path:
    """本地"上游"flat wiki 仓库：含空格页名、Home、excluded 页与附件。"""
    repo = tmp_path / "upstream-wiki"
    repo.mkdir()
    git("init", "-b", "master", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test Upstream", cwd=repo)
    (repo / "api.md").write_text("# API\n\npara one\n\npara two\n", encoding="utf-8")
    (repo / "Usage basics.md").write_text("# Usage basics\n\nintro text\n\nmore text\n",
                                          encoding="utf-8")
    (repo / "Home.md").write_text("# Home\n\nwelcome\n- [api](api)\n", encoding="utf-8")
    (repo / "_Sidebar.md").write_text("- [Home](Home)\n", encoding="utf-8")
    (repo / "legacy.md").write_text("# Legacy\n\nold stuff\n", encoding="utf-8")
    (repo / "img").mkdir()
    (repo / "img" / "logo.png").write_bytes(b"\x89PNG-fake")
    git("add", ".", cwd=repo)
    git("commit", "-m", "c0: initial wiki", cwd=repo)
    return repo


def make_ctx(tmp_path) -> SyncContext:
    return SyncContext(
        source_dir=tmp_path / "source",
        zh_dir=tmp_path / "zh",
        archive_dir=tmp_path / "archive",
        state_file=tmp_path / ".translation-state.json",
        report_dir=tmp_path / "reports",
    )


def mark_all_translated(ctx: SyncContext, fname: str):
    """把 state 中指定文件全部段落标记为 translated（模拟 M2 已翻译完）。"""
    state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
    for seg in state["files"][fname]["segments"]:
        seg["status"] = "translated"
        seg["metadata"]["translator"] = "test-agent"
        seg["metadata"]["translated_at"] = "2026-11-19"
    ctx.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def init_and_mark(tmp_path: Path, upstream: Path):
    """模块级助手：全量同步并把 api.md / Usage-basics.md 标记为已翻译。"""
    ctx = make_ctx(tmp_path)
    sync_init(ctx, f"file://{upstream}", skip_docs_index=True)
    mark_all_translated(ctx, "api.md")
    mark_all_translated(ctx, "Usage-basics.md")
    return ctx, rev_head(upstream)


# ---------- CLI 参数校验 ----------

class TestArgumentValidation:
    def _fake_sync(self, monkeypatch):
        calls = {}

        def fake_init(ctx, repo_url, dry_run=False, skip_docs_index=False):
            calls["mode"] = "init"
            return {"mode": "init"}

        def fake_since(ctx, repo_url, since, dry_run=False, skip_docs_index=False):
            calls["mode"] = "since"
            calls["since"] = since
            return {"mode": "incremental"}

        monkeypatch.setattr(sync_docs, "sync_init", fake_init)
        monkeypatch.setattr(sync_docs, "sync_since", fake_since)
        return calls

    def test_since_rejects_non_40hex(self, monkeypatch):
        self._fake_sync(monkeypatch)
        for bad in ("abc123", "15090480", "z" * 40, "12345"):
            with pytest.raises(SystemExit) as e:
                sync_docs.main(["--since", bad])
            assert e.value.code == 2, f"{bad} should be rejected"

    def test_since_accepts_40hex(self, monkeypatch):
        calls = self._fake_sync(monkeypatch)
        sha = "a" * 40
        sync_docs.main(["--since", sha])
        assert calls["mode"] == "since" and calls["since"] == sha

    def test_init_and_since_mutually_exclusive(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit) as e:
            sync_docs.main(["--init", "--since", "a" * 40])
        assert e.value.code == 2

    def test_requires_mode_flag(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit) as e:
            sync_docs.main([])
        assert e.value.code == 2

    def test_dry_run_alone_rejected(self, monkeypatch):
        self._fake_sync(monkeypatch)
        with pytest.raises(SystemExit):
            sync_docs.main(["--dry-run"])


# ---------- slug 规范化与 excluded ----------

class TestSlugAndExcluded:
    def test_init_slugs_and_excluded(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}", skip_docs_index=True)
        assert res["mode"] == "init" and res["has_changes"] is True
        files = {f["file"] for f in res["files"]}
        assert "Usage-basics.md" in files, "空格页名 → 连字符 slug"
        assert "index.md" in files, "Home → index（站点 index，R1-7）"
        assert "_Sidebar.md" in files
        by_file = {f["file"]: f for f in res["files"]}
        assert by_file["_Sidebar.md"]["excluded"] is True
        assert by_file["index.md"]["excluded"] is False
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert state["files"]["_Sidebar.md"]["segments"][0]["status"] == "skipped"
        assert state["files"]["index.md"]["upstream_page_title"] == "Home"
        assert state["files"]["Usage-basics.md"]["upstream_page_title"] == "Usage basics"

    def test_init_writes_assets_preserving_relpath(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}", skip_docs_index=True)
        assert (ctx.assets_dir / "img" / "logo.png").read_bytes() == b"\x89PNG-fake"

    def test_init_dry_run_writes_nothing(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}", dry_run=True, skip_docs_index=True)
        assert res["dry_run"] is True
        assert not (tmp_path / "source").exists()
        assert not ctx.state_file.exists()


# ---------- 增量同步 ----------

class TestSyncSince:
    def _init_and_mark(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}", skip_docs_index=True)
        mark_all_translated(ctx, "api.md")
        mark_all_translated(ctx, "Usage-basics.md")
        return ctx, rev_head(upstream)

    def test_full_cycle_MARD(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        zh_dir = tmp_path / "zh"
        zh_dir.mkdir()
        (zh_dir / "Usage-basics.md").write_text("# 使用基础（翻译历史）\n", encoding="utf-8")

        # 上游三连提交：M 改 api.md 一段；A 加新页；R 改名 legacy→old-api；D 删？无——legacy 用 R
        (upstream / "api.md").write_text("# API\n\npara one CHANGED\n\npara two\n", encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c1: modify api", cwd=upstream)
        (upstream / "new page.md").write_text("# New\n\nbrand new\n", encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c2: add new page", cwd=upstream)
        git("mv", "legacy.md", "old-api.md", cwd=upstream)
        git("commit", "-m", "c3: rename legacy", cwd=upstream)

        res = sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)
        assert res["mode"] == "incremental" and res["has_changes"] is True
        by_file = {c["file"]: c for c in res["changes"]}
        assert by_file["api.md"]["type"] == "M"
        assert by_file["new-page.md"]["type"] == "A", "新页名含空格 → slug 入库"
        rename = next(c for c in res["changes"] if c["type"] == "R")
        assert rename["file"] == "legacy.md -> old-api.md"

        # source/：新文件在、改名后的不在
        assert (tmp_path / "source" / "new-page.md").exists()
        assert (tmp_path / "source" / "old-api.md").exists()
        assert not (tmp_path / "source" / "legacy.md").exists()
        # 归档不删翻译历史
        assert (tmp_path / "archive" / "source" / "legacy.md").exists()
        assert (tmp_path / "archive" / "zh" / "Usage-basics.md").exists() is False

        # state：归档条目与新条目
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert "old-api.md" in state["files"] and "legacy.md" in state["archived_files"]

        # api.md 段落迁移：仅被改写的一段 pending，其余保持 translated + 元数据
        api = {s["content"]: s for s in state["files"]["api.md"]["segments"]}
        changed = api["para one CHANGED"]
        assert changed["status"] == "pending"
        for content in ("# API", "para two"):
            seg = api[content]
            assert seg["status"] == "translated"
            assert seg["metadata"]["translator"] == "test-agent"
        assert by_file["api.md"]["added_segments"] == 1
        assert by_file["api.md"]["kept_translated"] == 2

        # old-api.md（原 legacy.md）状态按 hash 迁移（legacy 未译过 → pending）
        assert all(s["status"] == "pending"
                   for s in state["files"]["old-api.md"]["segments"])
        # upstream commit 前进
        assert state["upstream_commit"] == rev_head(upstream)

    def test_asset_changes_synced(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        # 第一轮：M 更新 logo + A 新增 extra → 均同步入库
        (upstream / "img" / "logo.png").write_bytes(b"\x89PNG-updated")
        (upstream / "img" / "extra.svg").write_bytes(b"<svg/>")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "assets updated", cwd=upstream)
        res1 = sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)
        types1 = {c["file"]: c["type"] for c in res1["changes"]
                  if c["file"].startswith("assets/")}
        assert types1 == {"assets/img/logo.png": "M", "assets/img/extra.svg": "A"}
        assert (ctx.assets_dir / "img" / "extra.svg").read_bytes() == b"<svg/>"
        assert (ctx.assets_dir / "img" / "logo.png").read_bytes() == b"\x89PNG-updated"

        # 第二轮：D 删除两个附件 → source/assets 内同步移除
        sha1 = rev_head(upstream)
        (upstream / "img" / "extra.svg").unlink()
        (upstream / "img" / "logo.png").unlink()
        git("add", "-A", ".", cwd=upstream)
        git("commit", "-m", "assets removed", cwd=upstream)
        res2 = sync_since(ctx, f"file://{upstream}", sha1, skip_docs_index=True)
        types2 = [c["type"] for c in res2["changes"] if c["file"].startswith("assets/")]
        assert types2.count("D") == 2
        assert not (ctx.assets_dir / "img" / "logo.png").exists()
        assert not (ctx.assets_dir / "img" / "extra.svg").exists()

    def test_dry_run_writes_nothing(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        (upstream / "api.md").write_text("# API\n\npara one EDITED\n\npara two\n",
                                         encoding="utf-8")
        git("add", ".", cwd=upstream)
        git("commit", "-m", "c1", cwd=upstream)

        snap = {d: tree_hash(d) for d in (tmp_path / "source", tmp_path / "zh",
                                          tmp_path / "archive", ctx.state_file)}
        res = sync_since(ctx, f"file://{upstream}", sha0, dry_run=True,
                         skip_docs_index=True)
        assert res["dry_run"] is True and res["has_changes"] is True
        assert res["changes"][0]["action"] == "would-apply"
        for d, h in snap.items():
            assert tree_hash(d) == h, f"dry-run wrote to {d}"

    def test_no_changes_when_since_is_head(self, tmp_path, upstream):
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        res = sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)
        assert res["has_changes"] is False and res["changes"] == []

    def test_rerun_same_since_is_idempotent(self, tmp_path, upstream):
        """CI 重跑：同一 since 重复应用不得重置已迁移的翻译状态。"""
        ctx, sha0 = self._init_and_mark(tmp_path, upstream)
        git("mv", "legacy.md", "old-api.md", cwd=upstream)
        git("commit", "-m", "rename", cwd=upstream)
        sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)
        state1 = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert "old-api.md" in state1["files"]
        # 第二次运行（模拟失败重试）
        sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)
        state2 = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert set(state2["files"].keys()) == set(state1["files"].keys())
        # api.md 未变更，状态不因重跑翻转
        api_statuses = {s["status"] for s in state2["files"]["api.md"]["segments"]}
        assert api_statuses == {"translated"}

    def test_since_unknown_sha_fails_cleanly(self, tmp_path, upstream):
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}", skip_docs_index=True)
        bogus = "f" * 40
        with pytest.raises(subprocess.CalledProcessError):
            sync_since(ctx, f"file://{upstream}", bogus, skip_docs_index=True)


# ---------- docs-index 注入路径 ----------

class TestDocsIndex:
    def test_docs_index_fetched_and_tracked(self, tmp_path, upstream, monkeypatch):
        fake = {"content": "# spdlog docs\n\nhello index\n", "sha": "deadbeef" * 5,
                "size": 30, "html_url": "", "ref": "docs2.x"}
        import fetch_docs_index as fdi
        monkeypatch.setattr(fdi, "fetch_docs_index", lambda: dict(fake))
        ctx = make_ctx(tmp_path)
        res = sync_init(ctx, f"file://{upstream}")  # 不跳过 docs-index
        assert res["docs_index_commit"] == fake["sha"]
        assert (tmp_path / "source" / "docs-index.md").exists()
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        di = state["files"]["docs-index.md"]
        assert di["origin"] == "docs2.x" and di["upstream_page_title"] == "docs/index.md"
        assert all(s["status"] == "pending" for s in di["segments"])

    def test_docs_index_change_is_M_on_since(self, tmp_path, upstream, monkeypatch):
        # 全程离线：init 与增量均注入假 fetch（skip_docs_index 只用于明确
        # 不想动 docs-index 的调用；检测 M 的那次必须真正走注入的 fetch）
        import fetch_docs_index as fdi
        fake1 = {"content": "# spdlog docs\n\nhello index\n", "sha": "deadbeef" * 5,
                 "size": 30, "html_url": "", "ref": "docs2.x"}
        monkeypatch.setattr(fdi, "fetch_docs_index", lambda: dict(fake1))
        ctx = make_ctx(tmp_path)
        sync_init(ctx, f"file://{upstream}")  # 不跳过 → state 记入 fake1 的 docs-index
        mark_all_translated(ctx, "api.md")
        sha0 = rev_head(upstream)
        sync_since(ctx, f"file://{upstream}", sha0, skip_docs_index=True)  # wiki 无变化
        fake2 = dict(fake1, content="# spdlog docs\n\nhello index CHANGED\n",
                     sha="feedface" * 5)
        monkeypatch.setattr(fdi, "fetch_docs_index", lambda: dict(fake2))
        res = sync_since(ctx, f"file://{upstream}", sha0)  # 不跳过 → 走 fake2
        di_changes = [c for c in res["changes"] if c["file"] == "docs-index.md"]
        assert len(di_changes) == 1 and di_changes[0]["type"] == "M"
        state = json.loads(ctx.state_file.read_text(encoding="utf-8"))
        assert state["docs_index_commit"] == fake2["sha"]
        changed_segs = [s for s in state["files"]["docs-index.md"]["segments"]
                        if s["content"] == "hello index CHANGED"]
        assert changed_segs and changed_segs[0]["status"] == "pending"
