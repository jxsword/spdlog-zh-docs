#!/usr/bin/env python3
"""外链检查（低频，仅告警不阻断）。

提取 zh/ 与 source/ 中全部 http(s) 外链，可选联网 HEAD 校验（--check）。
默认离线仅统计与输出清单；计划 §6.5 门禁链不含本脚本（"仅告警不阻断"）。
CI 建议每周低频跑一次（可挂在 sync-upstream.yml 尾部，warning 不影响退出码）。
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).parent.parent.resolve()
SCAN_DIRS = ("zh", "source")

URL_RE = re.compile(r'https?://[^\s)\]>"\']+')


def extract_urls(content: str) -> List[str]:
    """提取正文中的 http(s) URL（代码块一并提取——外链检查不排除代码，仅告警）。"""
    return URL_RE.findall(content)


def collect(base: Path) -> Dict[str, List[str]]:
    """{url: [file:line, ...]} 全量收集。"""
    found: Dict[str, List[str]] = {}
    for d in SCAN_DIRS:
        for md in sorted((base / d).glob("*.md")) if (base / d).exists() else []:
            for i, line in enumerate(md.read_text(encoding='utf-8').splitlines(), 1):
                for url in extract_urls(line):
                    found.setdefault(url, []).append(f"{d}/{md.name}:{i}")
    return found


def check_url(url: str, timeout: int = 15) -> str:
    """curl HEAD 校验，返回状态：ok / http-<code> / error。<300 为 ok。"""
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", str(timeout), "-o", "/dev/null",
                            "-w", "%{http_code}", "-L", url],
                           capture_output=True, text=True, timeout=timeout + 5)
        code = r.stdout.strip()
        if code.isdigit() and int(code) < 300:
            return "ok"
        return f"http-{code or 'ERR'}"
    except (subprocess.TimeoutExpired, OSError):
        return "error"


def main():
    parser = argparse.ArgumentParser(description="外链检查（仅告警不阻断）")
    parser.add_argument("--check", action="store_true", help="联网 HEAD 校验（默认仅统计）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    urls = collect(REPO_ROOT)
    results = []
    for url in sorted(urls):
        status = check_url(url) if args.check else "unchecked"
        results.append({"url": url, "status": status,
                        "refs": urls[url]})

    bad = [r for r in results if r["status"] not in ("ok", "unchecked")]
    if args.json:
        print(json.dumps({"total": len(results), "bad": bad}, ensure_ascii=False, indent=2))
    else:
        print(f"外链总数: {len(results)}（{', '.join(SCAN_DIRS)}）")
        if not args.check:
            print("模式: 仅统计（--check 启用联网校验；本脚本仅告警不阻断）")
        for r in results:
            mark = "" if r["status"] in ("ok", "unchecked") else "  <-- 异常"
            print(f"  [{r['status']:>9s}] {r['url']}  ({len(r['refs'])} 处){mark}")
    # 仅告警：任何情况退出码 0
    sys.exit(0)


if __name__ == "__main__":
    main()
