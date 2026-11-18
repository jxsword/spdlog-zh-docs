"""fix_links.py wiki 形态测试（计划 R1-1/R1-2/R1-7 与 §6.3 落地验证）。

覆盖：slug 规则（空格→连字符、Home→index、编号保留）、slug 冲突检测、
[[wiki-link]] 四种形态转换、裸页名链接补 .md（上游实测全库即此形态）、
锚点保留、外链/.md/绝对路径不动、相对附件 → assets/、zh 侧锚点重映射、
保护器 LINK 模式（URL 护、文本可译）与 WIKI_LINK 模式。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import fix_links as fl  # noqa: E402
from fix_links import (  # noqa: E402
    build_page_slug_map,
    convert_wiki_links,
    fix_relative_links,
    generate_anchor_map,
    normalize_links,
    slugify,
    slugify_page_title,
)

FIXTURES = Path(__file__).parent / "fixtures" / "wiki-form"


@pytest.fixture
def slug_map():
    titles = [p.stem for p in FIXTURES.glob("*.md")]
    return build_page_slug_map(titles)


# ---------- slug 规则 ----------

class TestSlugRules:
    def test_space_to_hyphen_and_number_kept(self):
        assert slugify_page_title("Usage basics") == "Usage-basics"
        assert slugify_page_title("3.-Custom formatting") == "3.-Custom-formatting"
        assert slugify_page_title("FAQ") == "FAQ"

    def test_home_maps_to_index(self):
        assert slugify_page_title("Home") == "index"

    def test_slug_collision_raises(self):
        # "A B" 与 "A-B" 同 slug → 必须报错而非静默错挂
        with pytest.raises(ValueError):
            build_page_slug_map(["A B", "A-B"])

    def test_github_anchor_slug(self):
        assert slugify("Overflow Policy!") == "overflow-policy"


# ---------- [[wiki-link]] 转换 ----------

class TestConvertWikiLinks:
    def test_plain_link(self, slug_map):
        assert convert_wiki_links("[[QuickStart]]", slug_map) == "[QuickStart](QuickStart.md)"

    def test_pipe_text_link(self, slug_map):
        out = convert_wiki_links("[[QuickStart|快速开始]]", slug_map)
        assert out == "[快速开始](QuickStart.md)"

    def test_anchor_link(self, slug_map):
        out = convert_wiki_links("[[Flush-policy#overflow-policy|政策]]", slug_map)
        assert out == "[政策](Flush-policy.md#overflow-policy)"

    def test_same_page_anchor(self, slug_map):
        assert convert_wiki_links("[[#intro]]", slug_map) == "[#intro](#intro)"
        assert convert_wiki_links("[[#intro|简介]]", slug_map) == "[简介](#intro)"

    def test_dangling_target_warns_but_converts(self, slug_map):
        out = convert_wiki_links("[[Missing Page]]", slug_map,
                                 warn_cb=lambda m: None)
        assert out == "[Missing Page](Missing-Page.md)"


# ---------- 裸页名/资产链接规范化 ----------

class TestNormalizeLinks:
    def test_bare_page_name_gets_md(self, slug_map):
        assert normalize_links("- [QuickStart](QuickStart)", slug_map) == \
            "- [QuickStart](QuickStart.md)"

    def test_bare_page_name_with_space_title(self):
        smap = build_page_slug_map(["Thread Safety"])
        assert normalize_links("[Thread Safety](Thread-Safety)", smap) == \
            "[Thread Safety](Thread-Safety.md)"

    def test_anchor_preserved(self):
        smap = build_page_slug_map(["Flush policy"])
        assert normalize_links("[Flush policy](Flush-policy#overflow-policy)", smap) == \
            "[Flush policy](Flush-policy.md#overflow-policy)"

    def test_external_and_md_untouched(self, slug_map):
        content = "[up](https://github.com/gabime/spdlog) [x](Other.md) [rt](#sec)"
        assert normalize_links(content, slug_map) == content

    def test_relative_asset_gets_assets_prefix(self, slug_map):
        assert normalize_links("![logo](logo.png)", slug_map) == "![logo](assets/logo.png)"
        assert normalize_links("[doc](guide.pdf)", slug_map) == "[doc](assets/guide.pdf)"

    def test_already_assets_prefix_untouched(self, slug_map):
        assert normalize_links("![logo](assets/logo.png)", slug_map) == \
            "![logo](assets/logo.png)"

    def test_no_double_bracket_residue(self, slug_map):
        out = normalize_links((FIXTURES / "Home.md").read_text(encoding="utf-8"), slug_map)
        assert "[[" not in out, "转换后不得残留 [[ wiki 语法"
        for ln in out.splitlines():
            if "](" in ln:
                assert ln.count("[") == ln.count("]"), f"括号不平衡: {ln!r}"

    def test_normalize_idempotent(self, slug_map):
        once = normalize_links((FIXTURES / "Home.md").read_text(encoding="utf-8"), slug_map)
        assert normalize_links(once, slug_map) == once


# ---------- zh 侧：锚点重映射 ----------

class TestZhAnchorRemap:
    def test_anchor_map_and_fix_relative_links(self, tmp_path):
        src = tmp_path / "source"
        zh = tmp_path / "zh"
        zh.mkdir()
        (src).mkdir(exist_ok=True)
        (src / "p.md").write_text("# Overflow Policy\n\nbody\n", encoding="utf-8")
        (zh / "p.md").write_text("# 溢出策略\n\n正文 [x](p.md#overflow-policy)\n",
                                 encoding="utf-8")
        amap = generate_anchor_map(src, zh)
        assert amap == {"overflow-policy": "溢出策略"}
        out = fix_relative_links((zh / "p.md").read_text(encoding="utf-8"), amap)
        assert "(p.md#溢出策略)" in out

    def test_missing_anchor_kept_as_is(self, tmp_path):
        src = tmp_path / "source"
        zh = tmp_path / "zh"
        zh.mkdir()
        src.mkdir(exist_ok=True)
        (src / "p.md").write_text("# A\n", encoding="utf-8")
        (zh / "p.md").write_text("# 甲\n[x](p.md#unknown)\n", encoding="utf-8")
        amap = generate_anchor_map(src, zh)
        out = fix_relative_links((zh / "p.md").read_text(encoding="utf-8"), amap)
        assert "(p.md#unknown)" in out, "未映射锚点原样保留"


# ---------- 保护器联动 ----------

class TestProtectWikiForm:
    def test_link_url_protected_text_kept(self):
        from protect_untranslatable import protect, restore
        content = "See [the FAQ](FAQ.md#configs) for details."
        protected, pmap = protect(content)
        assert "FAQ.md#configs" not in protected
        assert "the FAQ" in protected
        assert restore(protected, pmap) == content

    def test_wiki_link_pattern(self):
        from protect_untranslatable import protect, restore
        content = "jump [[Some Page]] here"
        protected, pmap = protect(content)
        assert "[[Some Page]]" not in protected
        assert restore(protected, pmap) == content


# ---------- fixture 页端到端 ----------

class TestFixtureEndToEnd:
    def test_fixture_home_normalized(self, slug_map):
        content = (FIXTURES / "Home.md").read_text(encoding="utf-8")
        out = normalize_links(content, slug_map)
        assert "[QuickStart](QuickStart.md)" in out, "[[QuickStart]] 转换"
        assert "[自定义格式说明占位](3.-Custom-formatting.md)" in out
        assert "[Thread Safety](Thread-Safety.md)" in out, "裸页名补 .md"
        assert "[Flush policy](Flush-policy.md#overflow-policy)" in out
        assert "(#intro)" in out, "同页锚点"
        assert "https://github.com/gabime/spdlog" in out, "外链原样"

    def test_fixture_numbered_page(self, slug_map):
        content = (FIXTURES / "3.-Custom formatting.md").read_text(encoding="utf-8")
        out = normalize_links(content, slug_map)
        assert "[[Custom formatting|self link]]" not in out
        assert "self link](3.-Custom-formatting.md)" in out
        # 嵌套围栏代码块内容不受链接处理影响
        assert 'spdlog::set_pattern("[%H:%M:%S] [%l] %v");' in out
        assert "| Flag | Meaning |" in out, "表格结构保留"
