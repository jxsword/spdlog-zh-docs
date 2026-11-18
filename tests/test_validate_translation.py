"""validate_translation.py 校验器测试（移植 fmt 覆盖面 + spdlog 三扩展）。

覆盖：代码块/占位符/术语表检查、HTML 两级检查（类型计数 + 配对）、
内联代码 multiset、自动链接不误判、spdlog 扩展（黑名单 6b / 断链 6c）、
load_banned 解析。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import validate_translation as vt  # noqa: E402


# ---------- fmt 移植覆盖面 ----------

class TestBasics:
    def test_extract_code_blocks(self):
        content = "a\n```cpp\nint x;\n```\nb\n```\nplain\n```\nc"
        blocks = vt.extract_code_blocks(content)
        assert len(blocks) == 2
        assert "int x;" in blocks[0]

    def test_extract_inline_code(self):
        content = "use `spdlog::info` and `SPDLOG_TRACE` here"
        assert len(vt.extract_inline_code(content)) == 2

    def test_extract_urls(self):
        content = "[docs](https://spdlog.readthedocs.io) and [gh](https://github.com/gabime/spdlog)"
        urls = vt.extract_urls(content)
        assert urls == ["https://spdlog.readthedocs.io",
                        "https://github.com/gabime/spdlog"]

    def test_detects_modified_code_block(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("```cpp\nint x = 1;\n```", encoding="utf-8")
        tgt.write_text("```cpp\nint x = 2;\n```", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("Code block 0 modified" in e for e in result["errors"])

    def test_detects_placeholder_residue(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("```cpp\nx\n```", encoding="utf-8")
        tgt.write_text("```cpp\nx\n```\n残留 {{PROTECTED_CODE_BLOCK_deadbeef}}", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("PROTECTED_" in e for e in result["errors"])

    def test_glossary_warning(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("A format string example.", encoding="utf-8")
        tgt.write_text("一个 format string 示例。", encoding="utf-8")
        result = vt.validate_file(src, tgt, {"format string": "格式字符串"})
        assert any("not translated" in w for w in result["warnings"])

    def test_missing_files(self, tmp_path):
        result = vt.validate_file(tmp_path / "no.md", tmp_path / "no2.md", {})
        assert result["errors"]


class TestHTMLTwoLevel:
    def test_reordered_tags_pass(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('<b>fast</b> than <code>sprintf</code> here', encoding="utf-8")
        tgt.write_text('比 <code>sprintf</code> 更<b>快</b>的地方', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == [] and result["warnings"] == []

    def test_tag_type_count_mismatch_is_error(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('<div><b>bold</b></div>', encoding="utf-8")
        tgt.write_text('<b>bold</b>', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("HTML tag type counts mismatch" in e for e in result["errors"])

    def test_unbalanced_pairing_is_error(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('<div><b>text</b></div>', encoding="utf-8")
        tgt.write_text('<div><b>text</div>', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("unbalanced" in e for e in result["errors"])

    def test_void_tags_ignored(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('<p>chart <img src="perf.svg"> done</p>', encoding="utf-8")
        tgt.write_text('<p>图表 <img src="perf.svg"> 完成</p>', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_autolinks_not_tags(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('- <https://github.com/gabime/spdlog> repo\n', encoding="utf-8")
        tgt.write_text('- <https://github.com/gabime/spdlog>：仓库\n', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []

    def test_inline_multiset_reorder_pass_and_missing_caught(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('set `A` to `TRUE` for `B`', encoding="utf-8")
        tgt.write_text('为 `B` 将 `A` 设为 `TRUE`', encoding="utf-8")
        assert vt.validate_file(src, tgt, {})["errors"] == []
        tgt.write_text('使用 `fmt::format`', encoding="utf-8")
        src.write_text('use `fmt::format` and `FMT_STRING`', encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("multiset mismatch" in e for e in result["errors"])

    def test_glossary_check_ignores_code_and_urls(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text('compile `src/spdlog.cc` see [dur](https://x.org/w/chrono/duration)',
                       encoding="utf-8")
        tgt.write_text('编译 `src/spdlog.cc`，见 [dur](https://x.org/w/chrono/duration)',
                       encoding="utf-8")
        result = vt.validate_file(src, tgt, {"duration": "时长", "format": "格式化"})
        assert result["warnings"] == []


# ---------- spdlog 扩展：6b 黑名单 ----------

class TestBannedTerms:
    def test_banned_term_is_error(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("The logger writes to a sink.", encoding="utf-8")
        tgt.write_text("日志记录器写入到日志槽。", encoding="utf-8")
        result = vt.validate_file(src, tgt, {}, banned=[{"bad": "日志槽", "prefer": "接收器"}])
        assert any("Banned term '日志槽'" in e for e in result["errors"])
        assert any("prefer '接收器'" in e for e in result["errors"])

    def test_banned_not_triggered_in_code(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        # 代码块内容两侧逐字一致（代码块等量校验通过），禁用词仅出现于代码块内
        code_block = "```cpp\nsink->log(日志槽); // banned word only in code\n```"
        src.write_text("configure:\n\n" + code_block + "\n", encoding="utf-8")
        tgt.write_text("配置：\n\n" + code_block + "\n", encoding="utf-8")
        result = vt.validate_file(src, tgt, {}, banned=[{"bad": "日志槽"}])
        assert result["errors"] == []

    def test_banned_none_by_default(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("sink here", encoding="utf-8")
        tgt.write_text("日志槽 here", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert result["errors"] == []


# ---------- spdlog 扩展：6c 断链 ----------

class TestBrokenLinks:
    def _pair(self, tmp_path):
        src = tmp_path / "source"; zh = tmp_path / "zh"
        src.mkdir(exist_ok=True); zh.mkdir(exist_ok=True)
        return src, zh

    def test_missing_relative_md_is_error(self, tmp_path):
        src, zh = self._pair(tmp_path)
        (src / "a.md").write_text("see [b](b.md)", encoding="utf-8")
        t = zh / "a.md"
        t.write_text("参见 [b](b.md)", encoding="utf-8")
        result = vt.validate_file(src / "a.md", t, {})
        assert any("Broken relative link: b.md" in e for e in result["errors"])

    def test_link_resolved_via_source_fallback(self, tmp_path):
        """zh 目标缺失但 source 存在（未译页）→ 不算断链。"""
        src, zh = self._pair(tmp_path)
        (src / "b.md").write_text("# B", encoding="utf-8")
        t = zh / "a.md"
        t.write_text("参见 [b](b.md)", encoding="utf-8")
        result = vt.validate_file(src / "a.md", t, {})
        assert not any("Broken relative link" in e for e in result["errors"])

    def test_link_in_zh_ok(self, tmp_path):
        src, zh = self._pair(tmp_path)
        (src / "a.md").write_text("x", encoding="utf-8")
        (zh / "b.md").write_text("# 乙", encoding="utf-8")
        t = zh / "a.md"
        t.write_text("参见 [b](b.md#sec)", encoding="utf-8")
        result = vt.validate_file(src / "a.md", t, {})
        assert not any("Broken relative link" in e for e in result["errors"])

    def test_assets_link_checked(self, tmp_path):
        src, zh = self._pair(tmp_path)
        (src / "a.md").write_text("![i](assets/pic.png)", encoding="utf-8")
        t = zh / "a.md"
        t.write_text("![图](assets/pic.png)", encoding="utf-8")
        result = vt.validate_file(src / "a.md", t, {})
        assert any("Broken relative link: assets/pic.png" in e for e in result["errors"])
        (zh / "assets").mkdir()
        (zh / "assets" / "pic.png").write_bytes(b"png")
        result = vt.validate_file(src / "a.md", t, {})
        assert not any("Broken relative link" in e for e in result["errors"])

    def test_external_and_anchor_skipped(self, tmp_path):
        src, zh = self._pair(tmp_path)
        (src / "a.md").write_text("x", encoding="utf-8")
        t = zh / "a.md"
        t.write_text("[gh](https://github.com/gabime/spdlog) [页内](#top) [邮件](mailto:a@b.c)",
                     encoding="utf-8")
        result = vt.validate_file(src / "a.md", t, {})
        assert not any("Broken relative link" in e for e in result["errors"])


# ---------- load_banned 解析 ----------

class TestLoadBanned:
    def test_loads_banned_list(self, tmp_path, monkeypatch):
        g = tmp_path / "glossary.yml"
        g.write_text(
            "terms: []\nbanned:\n  - bad: 日志槽\n    prefer: 接收器\n    reason: 误译\n"
            "  - 日志池\n",
            encoding="utf-8")
        monkeypatch.setattr(vt, "GLOSSARY_FILE", g)
        banned = vt.load_banned()
        assert banned[0] == {"bad": "日志槽", "prefer": "接收器", "reason": "误译"}
        assert banned[1] == {"bad": "日志池", "prefer": "", "reason": ""}

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(vt, "GLOSSARY_FILE", tmp_path / "none.yml")
        assert vt.load_banned() == []

    def test_no_banned_key(self, tmp_path, monkeypatch):
        g = tmp_path / "glossary.yml"
        g.write_text("terms: []\n", encoding="utf-8")
        monkeypatch.setattr(vt, "GLOSSARY_FILE", tmp_path / "none.yml")
        assert vt.load_banned() == []


# ---------- B1 门禁修复回归（2026-11-19，Custom-formatting.md 实测暴露） ----------

class TestInlineMultiBacktickSpans:
    """行内 N≥2 反引号 span（CommonMark）：规范化后源/译对称，span 间连词可译。"""

    def test_normalize_triple_backtick_spans(self):
        src = "implement ```clone()``` and ```format(...)``` methods"
        out = vt.normalize_inline_spans(src)
        assert out == "implement `clone()` and `format(...)` methods"

    def test_prose_between_spans_translatable_no_multiset_error(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("use ```clone()``` and ```format(...)``` here", encoding="utf-8")
        tgt.write_text("在此使用 ```clone()``` 和 ```format(...)```。", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert not any("Inline code multiset" in e for e in result["errors"])

    def test_modified_span_content_still_caught(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("use ```clone()``` here", encoding="utf-8")
        tgt.write_text("在此使用 ```cloneX()```。", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("Inline code multiset" in e for e in result["errors"])

    def test_fenced_block_open_line_not_normalized(self):
        # 行首围栏（``` 后同行无闭合）不得被规范化改写
        src = "```cpp\nint x;\n```\n"
        assert vt.normalize_inline_spans(src) == src


class TestSourceUnbalancedTagExemption:
    """源文自带的未配对伪标签（<my_formatter_flag>）原样保留不算译文缺陷。"""

    def test_source_pseudo_tag_preserved_passes(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("bound to a <my_formatter_flag> instance", encoding="utf-8")
        tgt.write_text("绑定到一个 <my_formatter_flag> 实例", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert not any("unbalanced" in e for e in result["errors"])

    def test_breaking_source_balanced_tag_still_caught(self, tmp_path):
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("see <b>bold</b> text and <my_formatter_flag>", encoding="utf-8")
        tgt.write_text("参见 </b>加粗<b> 文本和 <my_formatter_flag>", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("unbalanced" in e for e in result["errors"])

    def test_unbalanced_tag_count_mismatch_still_caught(self, tmp_path):
        # L1 类型计数不受豁免影响：译文多出/少掉伪标签仍报错
        src = tmp_path / "s.md"; tgt = tmp_path / "t.md"
        src.write_text("a <my_formatter_flag> instance", encoding="utf-8")
        tgt.write_text("一个实例", encoding="utf-8")
        result = vt.validate_file(src, tgt, {})
        assert any("HTML tag type counts mismatch" in e for e in result["errors"])
