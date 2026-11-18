#!/usr/bin/env python3
"""拉取上游 docs2.x 分支的 docs/index.md（RTD 站实质内容，DR-001 范围）。

通道：gh api（认证直连优先）→ 失败走代理回退重试一次（全局网络回退规则）。
作为模块被 sync_docs.py 导入（--skip-docs-index 可跳过，供离线测试）；
也可独立运行调试：

  python3 scripts/fetch_docs_index.py            # 仅探测，打印 JSON 概要
  python3 scripts/fetch_docs_index.py --write    # 写入 source/docs-index.md
"""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = REPO_ROOT / "source"

REF = "docs2.x"
PROXY = "http://192.168.33.1:10808"   # 全局网络回退规则（AGENTS.md）


def _gh_api_json() -> dict:
    """gh api 直连 → 代理回退一次；均失败抛异常。

    命令为完全内联的字面量参数列表（静态常量，无任何 shell 拼接）。"""
    try:
        result = subprocess.run(
            ["gh", "api", "repos/gabime/spdlog/contents/docs/index.md?ref=docs2.x"],
            check=True, capture_output=True, text=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "")[:200]
        print(f"gh api direct failed ({stderr}), retrying via proxy {PROXY}",
              file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"gh api direct timed out, retrying via proxy {PROXY}",
              file=sys.stderr)
    env = dict(os.environ)
    env["HTTPS_PROXY"] = PROXY
    env["HTTP_PROXY"] = PROXY
    result = subprocess.run(
        ["gh", "api", "repos/gabime/spdlog/contents/docs/index.md?ref=docs2.x"],
        check=True, capture_output=True, text=True, timeout=120, env=env)
    return json.loads(result.stdout)


def fetch_docs_index() -> dict:
    """返回 {content, sha, size, html_url, ref}。content 为 utf-8 解码后的全文。"""
    data = _gh_api_json()
    if data.get("encoding") != "base64":
        raise RuntimeError(f"unexpected encoding: {data.get('encoding')!r}")
    content = base64.b64decode(data["content"]).decode("utf-8")
    return {
        "content": content,
        "sha": data["sha"],
        "size": data.get("size", len(content.encode("utf-8"))),
        "html_url": data.get("html_url", ""),
        "ref": REF,
    }


def write_docs_index(target_dir: Path = SOURCE_DIR) -> dict:
    info = fetch_docs_index()
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "docs-index.md").write_text(info["content"], encoding="utf-8")
    return info


def main():
    import argparse
    parser = argparse.ArgumentParser(description="拉取 docs2.x docs/index.md")
    parser.add_argument("--write", action="store_true", help="写入 source/docs-index.md")
    args = parser.parse_args()

    if args.write:
        info = write_docs_index()
    else:
        info = fetch_docs_index()
    print(json.dumps({k: v for k, v in info.items() if k != "content"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
