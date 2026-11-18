#!/usr/bin/env python3
"""Protect untranslatable content in markdown (code blocks, inline code, HTML, links).

移植自 fmt-zh-docs 同名脚本（逐字，2026-11-19），语义与模式表保持一致。"""

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ProtectedSegment:
    placeholder: str
    original: str
    type: str


PROTECTED_PATTERNS = [
    (re.compile(r'```[\s\S]*?```'), 'CODE_BLOCK'),
    (re.compile(r'<[^>]+>'), 'HTML_TAG'),
    (re.compile(r'\{%[\s\S]*?%\}'), 'JINJA_TEMPLATE'),
    (re.compile(r'!![a-zA-Z-]+'), 'YAML_TAG'),
    (re.compile(r'\[\[.*?\]\]'), 'WIKI_LINK'),
    (re.compile(r'!\[[^\]]*\]\([^)]+\)'), 'IMAGE'),
    (re.compile(r'\[([^\]]+)\]\(([^)]+)\)'), 'LINK'),
    (re.compile(r'`[^`\n]+`'), 'INLINE_CODE'),
]


def generate_placeholder(seg_type: str, content: str) -> str:
    hash_suffix = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8]
    return f"{{{{PROTECTED_{seg_type}_{hash_suffix}}}}}"


def protect(content: str) -> Tuple[str, Dict[str, str]]:
    """Replace untranslatable content with placeholders.
    
    Returns:
        (protected_content, placeholder_map)
    """
    placeholder_map = {}
    protected = content
    
    for pattern, seg_type in PROTECTED_PATTERNS:
        def replace(match):
            original = match.group(0)
            if seg_type == 'LINK':
                # For links, only protect the URL part, keep link text translatable
                link_text = match.group(1)
                url = match.group(2)
                url_placeholder = generate_placeholder('URL', url)
                placeholder_map[url_placeholder] = url
                return f"[{link_text}]({url_placeholder})"
            
            placeholder = generate_placeholder(seg_type, original)
            placeholder_map[placeholder] = original
            return placeholder
        
        protected = pattern.sub(replace, protected)
    
    return protected, placeholder_map


def restore(protected_content: str, placeholder_map: Dict[str, str]) -> str:
    """Restore original content from placeholders."""
    restored = protected_content
    for placeholder, original in placeholder_map.items():
        restored = restored.replace(placeholder, original)
    return restored


def protect_segments(segments: List[dict]) -> List[dict]:
    """Protect untranslatable content in a list of segment dicts."""
    protected_segments = []
    for seg in segments:
        if seg.get('type') == 'code_block':
            # Code blocks already isolated, just mark as protected
            protected_segments.append({**seg, 'protected': True})
        else:
            protected_content, placeholder_map = protect(seg.get('content', ''))
            protected_segments.append({
                **seg,
                'content': protected_content,
                '_placeholder_map': placeholder_map
            })
    return protected_segments


def restore_segments(segments: List[dict]) -> List[dict]:
    """Restore untranslatable content in segment dicts."""
    restored = []
    for seg in segments:
        if '_placeholder_map' in seg:
            restored_content = restore(seg['content'], seg['_placeholder_map'])
            restored.append({**seg, 'content': restored_content})
            del seg['_placeholder_map']
        else:
            restored.append(seg)
    return restored


if __name__ == "__main__":
    # Test
    test_md = """
# Title

Use `fmt::format` to format strings.

```cpp
fmt::print("Hello, {}!", "world");
```

See [fmt documentation](https://fmt.dev) for details.

<div class="note">This is HTML</div>
"""
    
    protected, pmap = protect(test_md)
    print("=== Protected ===")
    print(protected)
    print("\n=== Placeholder Map ===")
    for k, v in pmap.items():
        print(f"  {k} -> {v[:50]}...")
    
    restored = restore(protected, pmap)
    print("\n=== Restored ===")
    print(restored)
    print("\n=== Match ===")
    print(restored == test_md)