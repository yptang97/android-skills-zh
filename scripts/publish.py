#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布中文本地化技能包版本。

版本规则：`<上游版本>-zh.<本地修订号>`，例如上游 `1.0.17` → `1.0.17-zh.1`。
上游版本变化时修订号重新从 1 开始；同名上游版本内容再次更新则修订号递增。
这样插件市场能靠 version 字符串变化感知到中文包有新版本，也不会与上游版本号冲突。

做的事：
  1. 计算下一个版本号
  2. 写入 `.claude-plugin/plugin.json`、`.codex-plugin/plugin.json` 的 version
  3. 记录 `.sync/l10n-version.json`（供 sync_upstream.py 保留本地版本号）
  4. （--push）commit、打 tag、push、尝试创建 GitHub Release

用法::

    python scripts/publish.py --dry-run
    python scripts/publish.py --push
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN_FILES = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]
VERSION_FILE = REPO / ".sync" / "l10n-version.json"
ZH_SUFFIX_RE = re.compile(r"^(?P<base>.+?)-zh\.(?P<rev>\d+)$")


def run(*args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if check and proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def upstream_version() -> str:
    data = json.loads((REPO / PLUGIN_FILES[0]).read_text(encoding="utf-8"))
    raw = str(data.get("version", "0.0.0"))
    m = ZH_SUFFIX_RE.match(raw)
    return m.group("base") if m else raw


def existing_tags(base: str) -> list[int]:
    out = run("tag", "-l", f"v{base}-zh.*")
    revs = []
    for line in out.splitlines():
        m = re.search(rf"^v{re.escape(base)}-zh\.(\d+)$", line.strip())
        if m:
            revs.append(int(m.group(1)))
    return sorted(revs)


def next_version() -> tuple[str, str]:
    base = upstream_version()
    revs = existing_tags(base)
    rev = (revs[-1] + 1) if revs else 1
    return base, f"{base}-zh.{rev}"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="提交、打 tag 并推送")
    ap.add_argument("--dry-run", action="store_true", help="只显示将要做的事")
    args = ap.parse_args()

    if run("status", "--short"):
        print("工作区不干净，先提交内容再发布：")
        print(run("status", "--short"))
        return 1

    base, version = next_version()
    tag = f"v{version}"
    print(f"上游版本 {base} → 发布版本 {version}")

    if args.dry_run:
        print(f"[dry-run] 将写入 version={version}，tag={tag}")
        return 0

    for rel in PLUGIN_FILES:
        path = REPO / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = version
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        json.dumps({"upstream_version": base, "version": version, "tag": tag}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    if not args.push:
        print("已写入版本号，未提交（加 --push 提交并推送）")
        return 0

    run("add", "-A")
    run("commit", "-m", f"release: {version} 中文技能包")
    run("tag", "-a", tag, "-m", f"中文技能包 {version}")
    run("push", "origin", "HEAD")
    run("push", "origin", tag)
    print(f"已推送 commit 与 tag {tag}")

    notes = f"上游 android/skills {base} 的简体中文本地化版本。"
    rel = subprocess.run(
        ["gh", "release", "create", tag, "--title", f"中文技能包 {version}", "--notes", notes],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if rel.returncode == 0:
        print("已创建 GitHub Release")
    else:
        print(f"GitHub Release 未创建（tag 已推送）: {rel.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
