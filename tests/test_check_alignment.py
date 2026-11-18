"""check_alignment.py 结构对齐检查测试（B2 新增）。

覆盖：漏译检测（stopwords 分级）、fence span 豁免（segment_md 围栏错位误判）、
hr 守卫、fence_spans 行区间计算。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import check_alignment as ca  # noqa: E402


@pytest.fixture()
def dirs(tmp_path, monkeypatch):
    """src/ 与 zh/ 分离的临时仓库布局（check_file 按 fname 在两目录取同名文件）。"""
    src, zh = tmp_path / "src", tmp_path / "zh"
    src.mkdir(); zh.mkdir()
    monkeypatch.setattr(ca, "SOURCE_DIR", src)
    monkeypatch.setattr(ca, "ZH_DIR", zh)
    return src, zh


class TestFenceSpans:
    def test_real_fence_span(self):
        text = "prose\n```c++\ncode\n```\nmore prose\n"
        assert ca.fence_spans(text) == [(2, 4)]

    def test_inline_span_same_line_self_closes(self):
        # 行内 ```span``` 同行自闭合：不产生跨行 span（正则最短匹配）
        text = "a ```x``` b\n```\nblk\n```\n"
        spans = ca.fence_spans(text)
        assert spans[0] == (1, 1)
        assert spans[1] == (2, 4)


class TestUntranslatedDetection:
    def test_untranslated_prose_is_error(self, dirs):
        src, zh = dirs
        text = "The logger will flush the file and you can use it."
        (src / "s.md").write_text(text, encoding="utf-8")
        (zh / "s.md").write_text(text, encoding="utf-8")
        errors, warnings = ca.check_file("s.md", {"files": {"s.md": {}}})
        assert any("left untranslated" in e for e in errors)

    def test_translated_prose_passes(self, dirs):
        src, zh = dirs
        (src / "s.md").write_text(
            "The logger will flush the file and you can use it.", encoding="utf-8")
        (zh / "s.md").write_text("日志记录器将刷新文件，您可以直接使用。", encoding="utf-8")
        errors, warnings = ca.check_file("s.md", {"files": {"s.md": {}}})
        assert not any("left untranslated" in e for e in errors)

    def test_fence_internal_code_paragraph_exempt(self, dirs):
        """FAQ 形态：以行内三反引号 span 开头的散文行误导行级分段器，
        使真实围栏内的代码行被判成段落——逐字节保留应豁免，不报漏译。"""
        src, zh = dirs
        (src / "s.md").write_text(
            "```SPDLOG_FMT_EXTERNAL``` macro must be defined.\n"
            "\n"
            "## Section\n"
            "\n"
            "```c++\n"
            'spdlog::info("Hello {}", "world"); // some comment here\n'
            'spdlog::info("Another one"); // and more comment text\n'
            "```\n",
            encoding="utf-8")
        (zh / "s.md").write_text(
            "必须定义 ```SPDLOG_FMT_EXTERNAL``` 宏。\n"
            "\n"
            "## 小节\n"
            "\n"
            "```c++\n"
            'spdlog::info("Hello {}", "world"); // some comment here\n'
            'spdlog::info("Another one"); // and more comment text\n'
            "```\n",
            encoding="utf-8")
        errors, warnings = ca.check_file("s.md", {"files": {"s.md": {}}})
        assert not any("untranslated" in e for e in errors)
        assert not any("identical to source" in w for w in warnings)


class TestHrGuard:
    def test_hr_count_mismatch_is_error(self, dirs):
        src, zh = dirs
        (src / "s.md").write_text("正文一\n\n***\n\n正文二\n", encoding="utf-8")
        (zh / "s.md").write_text("正文一\n\n正文二\n", encoding="utf-8")
        errors, warnings = ca.check_file("s.md", {"files": {"s.md": {}}})
        assert any("horizontal-rule" in e for e in errors)
