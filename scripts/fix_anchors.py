#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复中文标题导致的页内锚点失效。

上游标题是英文，slug 形如 `#backend-guidelines`；标题译成中文后 GitHub 生成的
slug 变成中文，原文里的 `](#backend-guidelines)` 就跳不过去了。

做法：按标题顺序把上游标题与本地标题一一对应，对每个失效的页内链接，在对应的
本地标题行尾追加 `<a id="原 slug"></a>`，让旧锚点继续可用。不改任何链接目标，
不改标题文字，不改代码块。

用法::

    python scripts/fix_anchors.py --dry-run     # 只报告
    python scripts/fix_anchors.py               # 实际写入
    python scripts/fix_anchors.py --path a.md   # 只处理单文件
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN_FILE = REPO / ".sync" / "plan.json"
UPSTREAM_DIR = REPO.parent / "android-skills-upstream"

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.M)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
ANCHOR_LINK_RE = re.compile(r"\]\(#([^)\s]+)\)")


def strip_fences(text: str) -> str:
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]
                continue
            out.append(line)
        elif line.strip().startswith(fence * 3):
            fence = None
    return "\n".join(out)


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[^\w\- ]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


def headings(text: str) -> list[tuple[str, str]]:
    """返回 [(整行, 标题文本)]，跳过代码块内的 #。"""
    body = strip_fences(text)
    return [(m.group(0), m.group(2)) for m in HEADING_RE.finditer(body)]


def process(rel: str, up: Path, dry: bool) -> tuple[int, list[str]]:
    src, dst = up / rel, REPO / rel
    if not dst.exists():
        return 0, []
    src_text = src.read_text(encoding="utf-8", errors="replace")
    dst_text = dst.read_text(encoding="utf-8", errors="replace")

    anchors = set(ANCHOR_LINK_RE.findall(strip_fences(dst_text)))
    if not anchors:
        return 0, []

    dst_heads = headings(dst_text)
    dst_slugs = {slugify(t) for _, t in dst_heads}
    missing = sorted(a for a in anchors if a not in dst_slugs)
    if not missing:
        return 0, []

    src_heads = headings(src_text)
    if len(src_heads) != len(dst_heads):
        return 0, [f"{rel}: 标题数量不一致（{len(src_heads)}/{len(dst_heads)}），跳过"]

    slug_to_index = {}
    for i, (_, title) in enumerate(src_heads):
        slug_to_index.setdefault(slugify(title), i)

    lines = dst_text.splitlines()
    fixed, notes = 0, []
    for anchor in missing:
        idx = slug_to_index.get(anchor)
        if idx is None:
            notes.append(f"{rel}: 找不到锚点 #{anchor} 对应标题")
            continue
        head_line = dst_heads[idx][0]
        target = next((n for n, line in enumerate(lines) if line == head_line), None)
        if target is None:
            notes.append(f"{rel}: 定位标题行失败 #{anchor}")
            continue
        if f'id="{anchor}"' in lines[target]:
            continue
        lines[target] = f'{lines[target]} <a id="{anchor}"></a>'
        fixed += 1
        notes.append(f"{rel}: 补锚点 #{anchor} → 「{dst_heads[idx][1]}」")

    if fixed and not dry:
        dst.write_text("\n".join(lines) + ("\n" if dst_text.endswith("\n") else ""), encoding="utf-8")
    return fixed, notes


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="只处理单个文件（相对仓库根）")
    ap.add_argument("--dry-run", action="store_true", help="只报告，不写入")
    args = ap.parse_args()

    plan = {}
    if PLAN_FILE.exists():
        plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
    up = Path(plan.get("upstream_dir") or UPSTREAM_DIR)

    if args.path:
        files = [args.path]
    else:
        files = [it["path"] for it in plan.get("translate", [])]

    total, notes = 0, []
    for rel in files:
        n, msg = process(rel, up, args.dry_run)
        total += n
        notes.extend(msg)

    for m in notes:
        print(m)
    print(f"\n补锚点 {total} 处" + ("（dry-run，未写入）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
