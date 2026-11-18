"""sync_docs.py / segment_markdown.py 切分测试，重点覆盖 OOM 死循环回归场景。

事故根因（fmt DR-011，2026-11-18）：段落分支中，行以 `<` 开头但同行无 `>`
（跨行 HTML 注释 `<!--`）时，内层循环立即 break 且外层 i 不推进，无限生成
空 Segment 直至内存耗尽。修复：HTML 分支放宽为 startswith('<') 整块捕获 +
段落分支护栏 if i == start: i += 1。护栏代码修改前必须先跑本文件。
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from segment_markdown import segment_md, compute_hash  # noqa: E402

SRC_DIR = Path(__file__).parent.parent / "source"


# ---------- OOM 回归测试（必须最快执行，防超时拖垮 CI） ----------

class TestOOMRegression:
    """任何用例失败都意味着死循环护栏被破坏，须立即修复。"""

    def test_crossline_html_comment_no_infinite_loop(self):
        """跨行 HTML 注释（<!-- 无同行 >）不得触发死循环。"""
        content = "# Title\n\n<!-- this comment\nspans multiple lines\nwithout > on first line -->\n\nText after.\n"
        segs = segment_md(content, "test.md")
        assert len(segs) == 3
        assert all(s.content.strip() for s in segs)

    def test_bare_unclosed_html_tag_no_infinite_loop(self):
        """裸 `<` 开头行（如 `<!--`，同行无 `>`）是事故原始触发输入。"""
        content = "intro text\n\n<!--\n\noutro\n"
        segs = segment_md(content, "test.md")
        assert len(segs) == 3
        assert not any(not s.content.strip() for s in segs)

    def test_lone_angle_bracket_line(self):
        """孤立 '<' 字符行也必须推进。"""
        segs = segment_md("a\n\n<\n\nb\n", "test.md")
        assert len(segs) == 3
        assert not any(not s.content.strip() for s in segs)

    def test_no_empty_segments_generated(self):
        """任何输入都不得产生空 content 段（事故中空段无限生成的特征）。"""
        tricky_cases = [
            "<!--\n",
            "< \n",
            "<x\n",
            "text\n<\n",
            "```\nunclosed\n",
            "|\n",
            "![unclosed\n",
            "#\n",
        ]
        for content in tricky_cases:
            segs = segment_md(content, "test.md")
            empties = [s for s in segs if not s.content.strip()]
            assert not empties, f"empty segments for input {content!r}: {empties}"

    def test_real_source_files_complete_quickly(self):
        """真实 source/ 全量分段必须 5 秒内完成、无空段，且与 state 段数一致
        （自洽断言，防状态漂移；不硬编码段数，上游变更后仍有效）。"""
        state_file = Path(__file__).parent.parent / ".translation-state.json"
        if not SRC_DIR.exists() or not any(SRC_DIR.glob("*.md")):
            pytest.skip("source/ not synced yet")
        start = time.monotonic()
        total = 0
        for f in SRC_DIR.glob("*.md"):
            segs = segment_md(f.read_text(encoding="utf-8"), f.name)
            empties = [s for s in segs if not s.content.strip()]
            assert not empties, f"{f.name} has empty segments"
            total += len(segs)
        elapsed = time.monotonic() - start
        assert elapsed < 5, f"segmentation too slow: {elapsed:.1f}s"
        if state_file.exists():
            import json
            state = json.loads(state_file.read_text(encoding="utf-8"))
            state_total = sum(len(fs["segments"]) for fs in state["files"].values())
            assert total == state_total, (
                f"segmentation drift: fresh={total} state={state_total}")


# ---------- 常规分段行为 ----------

class TestSegmentBasics:
    def test_code_block_isolated(self):
        content = "text before\n\n```cpp\nspdlog::info(\"{}\", 42);\n```\n\ntext after\n"
        segs = segment_md(content, "t.md")
        types = [s.type for s in segs]
        assert types == ["paragraph", "code_block", "paragraph"]
        code = segs[1]
        assert code.content.startswith("```cpp")
        assert code.content.endswith("```")

    def test_nested_fence_content_preserved(self):
        """已知限制（fmt 切分器行为，fmt 语料实证可接受）：四反引号外层围栏会被
        内层 ``` 行提前闭合，内外层内容拆为多个段（部分标注为 paragraph）。
        断言底线：任何行都不丢失（protect 的 CODE_BLOCK 模式同理按最短闭合，
        翻译后代码块等量校验兜底）。真实语料实测无四反引号围栏（2026-11-19）。"""
        content = "para\n\n````md\ninner:\n```cpp\nx = 1;\n```\ntail\n````\n\nafter\n"
        segs = segment_md(content, "t.md")
        joined = "\n".join(s.content for s in segs)
        assert "x = 1;" in joined and "tail" in joined and "after" in joined
        lines = content.split("\n")
        covered = set()
        for s in segs:
            for ln in range(s.line_start, s.line_end + 1):
                covered.add(ln)
        for idx, line in enumerate(lines, start=1):
            if line.strip():
                assert idx in covered, f"line {idx} not covered: {line!r}"

    def test_table_isolated(self):
        content = "| Type | Effect |\n|------|--------|\n| `basic` | left |\n\ntext\n"
        segs = segment_md(content, "t.md")
        assert segs[0].type == "table"
        assert len(segs[0].content.splitlines()) == 3

    def test_heading_records_level_and_resets_para_index(self):
        content = "# A\n\np1\n\n## B\n\np2\n"
        segs = segment_md(content, "t.md")
        headings = [s for s in segs if s.type == "heading"]
        assert [h.metadata["level"] for h in headings] == [1, 2]
        assert headings[0].id.endswith("-h1-0")
        assert headings[1].id.endswith("-h2-1")

    def test_multi_line_paragraph_merged(self):
        content = "line one\nline two\nline three\n\nnext para\n"
        segs = segment_md(content, "t.md")
        paras = [s for s in segs if s.type == "paragraph"]
        assert len(paras) == 2
        assert "line one\nline two\nline three" == paras[0].content

    def test_ids_unique_within_file(self):
        content = "# A\n\np1\n\n```cpp\nx\n```\n\n| a | b |\n|---|---|\n\n![img](x.svg)\n"
        segs = segment_md(content, "t.md")
        ids = [s.id for s in segs]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"

    def test_segment_fields_complete(self):
        segs = segment_md("# T\n\nbody\n", "t.md")
        for s in segs:
            assert s.id and s.type and s.file_path == "t.md"
            assert s.line_start >= 1 and s.line_end >= s.line_start
            assert len(s.hash) == 16
            assert isinstance(s.metadata, dict)

    def test_hash_stable(self):
        assert compute_hash("abc") == compute_hash("abc")
        assert compute_hash("abc") != compute_hash("abd")
        assert len(compute_hash("x")) == 16


# ---------- 结构覆盖（无内容丢失） ----------

class TestNoContentLoss:
    def test_segments_reconstruct_original(self):
        """分段并按 line_start/line_end 重组应覆盖全部非空行。"""
        content = "# Title\n\npara A\ncontinues\n\n```cpp\nint x;\n```\n\n| a |\n|---|\n\n<!-- c\n--> \n\nend\n"
        segs = segment_md(content, "t.md")
        lines = content.split("\n")
        covered = set()
        for s in segs:
            for ln in range(s.line_start, s.line_end + 1):
                covered.add(ln)
        for idx, line in enumerate(lines, start=1):
            if line.strip():
                assert idx in covered, f"line {idx} not covered by any segment: {line!r}"
