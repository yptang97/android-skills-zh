#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描未翻译的英文段落，作为人工复核队列（不是硬性门槛）。

判定规则：剥离代码块后，某行满足
  - 不含中文字符
  - 长度 >= MIN_LEN
  - ASCII 字母占比 >= MIN_RATIO
  - 不是纯链接、表格分隔行、HTML 标签
就计为一个候选行。

用法::

    python scripts/audit_english.py                 # 全量，列出问题最多的文件
    python scripts/audit_english.py --path README.md --lines
    python scripts/audit_english.py --limit 60
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

LOCAL_ONLY_PREFIXES = (".git/", ".sync/", ".skills/", "scripts/")
LOCAL_ONLY_FILES = {".gitignore", "TRANSLATION-GLOSSARY.md", "SYNC.md"}
NO_TRANSLATE_PREFIXES = (".github/",)
NO_TRANSLATE_FILES = {"LICENSE.txt"}

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
ALPHA_RE = re.compile(r"[A-Za-z]")
SEP_RE = re.compile(r"^\s*\|?[\s:|-]{4,}\|?\s*$")
LINK_ONLY_RE = re.compile(r"^\s*(?:[-*]\s*)?\[[^\]]*\]\([^)]*\)\s*$")
TAG_RE = re.compile(r"^\s*<[^>]+>\s*$")


def should_translate(rel: str, roots: set[str]) -> bool:
    """与 scripts/sync_upstream.py 的翻译范围保持一致。"""
    if not rel.endswith(".md") or rel in NO_TRANSLATE_FILES or rel.startswith(NO_TRANSLATE_PREFIXES):
        return False
    if re.search(r"/references/android/", rel):
        return False
    if rel == "README.md":
        return True
    return any(rel.startswith(root + "/") for root in roots)


def walk_markdown(root: Path) -> list[str]:
    roots = {p.parent.relative_to(root).as_posix() for p in root.rglob("SKILL.md")}
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            rel = (Path(dirpath) / name).relative_to(root).as_posix()
            if rel in LOCAL_ONLY_FILES or rel.startswith(LOCAL_ONLY_PREFIXES) or not should_translate(rel, roots):
                continue
            out.append(rel)
    return sorted(out)


def audit_file(path: Path, min_len: int, min_ratio: float) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    in_fence = False
    in_frontmatter = False
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if idx == 1 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() in ("---", "..."):
                in_frontmatter = False
            continue
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        text = line.strip()
        if len(text) < min_len or CJK_RE.search(text):
            continue
        if SEP_RE.match(text) or LINK_ONLY_RE.match(text) or TAG_RE.match(text):
            continue
        if text.startswith(("<!--", "|", "```")):
            continue
        letters = len(ALPHA_RE.findall(text))
        if letters / max(len(text), 1) < min_ratio:
            continue
        if re.search(r"[.!?;:]\s", text) or letters > 40:
            hits.append((idx, text[:160]))
    return hits


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="只扫描单个文件")
    ap.add_argument("--limit", type=int, default=40, help="列出问题最多的文件数")
    ap.add_argument("--lines", action="store_true", help="显示具体行")
    ap.add_argument("--min-len", type=int, default=40)
    ap.add_argument("--min-ratio", type=float, default=0.55)
    args = ap.parse_args()

    files = [args.path] if args.path else walk_markdown(REPO)
    results = []
    for rel in files:
        hits = audit_file(REPO / rel, args.min_len, args.min_ratio)
        if hits:
            results.append((rel, hits))
    results.sort(key=lambda x: -len(x[1]))

    total = sum(len(h) for _, h in results)
    print(f"扫描 {len(files)} 个 markdown，{len(results)} 个文件存在疑似未翻译英文行，合计 {total} 行")
    for rel, hits in results[: args.limit]:
        print(f"  {rel}: {len(hits)} 行")
        if args.lines:
            for lineno, text in hits[:8]:
                print(f"      L{lineno}: {text}")
    if len(results) > args.limit:
        print(f"  … 还有 {len(results) - args.limit} 个文件")
    print("\n说明：本脚本只做复核标记，代码、命令、标识符与合理的英文术语都会被计入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
