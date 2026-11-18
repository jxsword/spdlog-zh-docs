"""protect_untranslatable.py 保护/还原机制测试（移植自 fmt-zh-docs，逐字）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from protect_untranslatable import protect, restore, generate_placeholder  # noqa: E402


class TestProtect:
    def test_code_block_protected(self):
        content = "text\n\n```cpp\nfmt::print(\"{}\");\n```\n\ntail\n"
        protected, pmap = protect(content)
        assert "fmt::print" not in protected
        assert len(pmap) == 1
        restored = restore(protected, pmap)
        assert restored == content

    def test_inline_code_protected(self):
        content = "Use `fmt::format` function."
        protected, pmap = protect(content)
        assert "`fmt::format`" not in protected
        assert "Use" in protected
        assert restore(protected, pmap) == content

    def test_html_tag_protected(self):
        content = '<div class="note">body text</div>'
        protected, pmap = protect(content)
        assert "<div" not in protected
        assert restore(protected, pmap) == content

    def test_image_protected(self):
        content = "![perf chart](perf.svg)"
        protected, pmap = protect(content)
        assert "perf.svg" not in protected
        assert restore(protected, pmap) == content

    def test_link_url_protected_text_kept(self):
        content = "See [the docs](https://fmt.dev/latest/) for details."
        protected, pmap = protect(content)
        assert "https://fmt.dev" not in protected
        # 链接文本保留可翻译
        assert "the docs" in protected
        assert restore(protected, pmap) == content

    def test_roundtrip_idempotent(self):
        content = "# T\n\n`code` and [link](https://x.y) and ```\nraw\n```\n"
        protected, pmap = protect(content)
        assert restore(protected, pmap) == content

    def test_placeholder_format(self):
        ph = generate_placeholder("CODE_BLOCK", "abc")
        assert ph.startswith("{{PROTECTED_CODE_BLOCK_")
        assert ph.endswith("}}")
        # 同内容占位符确定；不同内容不同
        assert generate_placeholder("CODE_BLOCK", "abc") == ph
        assert generate_placeholder("CODE_BLOCK", "abd") != ph


class TestRestoreSafety:
    def test_restore_unknown_placeholder_keeps_text(self):
        # 未知占位符（不在 map 中）原样保留，不抛错
        out = restore("keep {{PROTECTED_UNKNOWN_abc}}", {})
        assert out == "keep {{PROTECTED_UNKNOWN_abc}}"

    def test_multiple_same_type_placeholders(self):
        content = "`a` and `b`"
        protected, pmap = protect(content)
        assert len(pmap) == 2
        assert restore(protected, pmap) == content

    def test_validate_placeholder_absent_after_restore(self):
        content = "x `fmt::print` y"
        protected, pmap = protect(content)
        restored = restore(protected, pmap)
        assert "PROTECTED_" not in restored
