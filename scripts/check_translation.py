#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验中文本地化仓库与上游的结构一致性。

检查项：
  [error] 上游每个受管文件在本地都存在
  [error] frontmatter key 集合、name/license 值、metadata 块与上游一致
  [error] fenced code block 的数量与语言标注序列一致
  [error] Markdown 链接目标（`](...)`）多重集一致
  [warn ] inline code 片段在上游出现但本地缺失
  [warn ] 标题数量与上游不一致（可能误删章节）

用法::

    python scripts/check_translation.py                 # 全量校验
    python scripts/check_translation.py --path README.md
    python scripts/check_translation.py --json          # 机器可读输出
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO / ".sync"
PLAN_FILE = SYNC_DIR / "plan.json"

_env_upstream = os.environ.get("ANDROID_SKILLS_UPSTREAM", "").strip()
UPSTREAM_DIR = (
    Path(_env_upstream).expanduser().resolve()
    if _env_upstream
    else (REPO.parent / "android-skills-upstream").resolve()
)

LOCAL_ONLY_PREFIXES = (".git/", ".sync/", ".skills/", "scripts/")
LOCAL_ONLY_FILES = {".gitignore", "TRANSLATION-GLOSSARY.md", "SYNC.md"}
NO_TRANSLATE_PREFIXES = (".github/",)
NO_TRANSLATE_FILES = {"LICENSE.txt"}
OFFICIAL_DOC_MIRROR_RE = re.compile(r"/references/android/")
# 本地剔除的 skill 目录（与 scripts/sync_upstream.py 的 EXCLUDED_PREFIXES 保持一致）
EXCLUDED_PREFIXES = ("wear/", "cars/", "device-ai/", "xr/")
# 这些 frontmatter 键的值必须与上游逐字一致，只有 description 之类说明性值可以翻译
FIXED_SCALAR_KEYS = ("name", "license", "allowed-tools", "disable-model-invocation")

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^\s`]*)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.M)

REPO_REF_LOCAL = "yptang97/android-skills-zh"
LOCAL_SECTION_RE = re.compile(r"<!--\s*local:begin\s*-->.*?<!--\s*local:end\s*-->", re.S)


def strip_local_sections(text: str) -> str:
    """移除本地补充区块（`<!-- local:begin -->`…`<!-- local:end -->`），不参与结构比对。"""
    return LOCAL_SECTION_RE.sub("", text)


def normalize_repo_ref(text: str) -> str:
    """把安装命令里的仓库路径归一化，允许本地化仓库路径替换上游路径。"""
    return text.replace(REPO_REF_LOCAL, "<REPO>").replace("android/skills", "<REPO>")



def is_local_only(rel: str) -> bool:
    return rel in LOCAL_ONLY_FILES or rel.startswith(LOCAL_ONLY_PREFIXES)


def should_translate(rel: str, roots: set[str]) -> bool:
    """与 scripts/sync_upstream.py 的翻译范围保持一致。"""
    if not rel.endswith(".md") or rel in NO_TRANSLATE_FILES or rel.startswith(NO_TRANSLATE_PREFIXES):
        return False
    if OFFICIAL_DOC_MIRROR_RE.search(rel):
        return False
    if rel == "README.md":
        return True
    return any(rel.startswith(root + "/") for root in roots)


def skill_roots(up: Path) -> set[str]:
    return {p.parent.relative_to(up).as_posix() for p in up.rglob("SKILL.md")}


def walk_files(root: Path) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        base = Path(dirpath)
        for name in filenames:
            out.append((base / name).relative_to(root).as_posix())
    return sorted(out)


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines(keepends=True)
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            return "".join(lines[1:idx]), "".join(lines[idx + 1:])
    return None, text


def parse_frontmatter(block: str) -> tuple[list[str], dict[str, str], str]:
    keys: list[str] = []
    scalars: dict[str, str] = {}
    meta_lines: list[str] = []
    in_meta = False
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if in_meta:
            if raw.startswith((" ", "\t")) or line.startswith("- "):
                meta_lines.append(line.strip())
                continue
            in_meta = False
        if raw[0] not in (" ", "\t") and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            keys.append(key)
            if key == "metadata":
                in_meta = True
            else:
                scalars[key] = value.strip()
    return keys, scalars, "\n".join(meta_lines)


def strip_code(text: str) -> str:
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
                fence = None
            out.append("")
            continue
        if m:
            fence = m.group(2)
            out.append("")
            continue
        out.append(INLINE_CODE_RE.sub("``", line))
    return "\n".join(out)


def fences(text: str) -> list[str]:
    result, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(2)
                result.append(m.group(3).lower())
        elif m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
            fence = None
    return result


def fence_blocks(text: str) -> list[tuple[str, str]]:
    """返回每个 fenced code block 的 (语言标注, 内容哈希)。代码块内容必须逐字一致。"""
    import hashlib

    blocks: list[tuple[str, str]] = []
    fence, lang, buf = None, "", []
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence, lang, buf = m.group(2), m.group(3).lower(), []
            continue
        if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
            body = normalize_repo_ref("\n".join(buf))
            blocks.append((lang, hashlib.sha1(body.encode("utf-8")).hexdigest()[:10]))
            fence = None
            continue
        buf.append(line)
    return blocks


def frontmatter_syntax_errors(block: str) -> list[str]:
    """粗检 YAML frontmatter 结构：顶层必须是 `key:`，续行必须缩进。"""
    problems = []
    for idx, raw in enumerate(block.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in (" ", "\t", "-"):
            continue
        if ":" not in raw:
            problems.append(f"第 {idx} 行不是合法的 YAML 键值行: {raw[:60]!r}")
    return problems


def check_markdown(rel: str, src_text: str, dst_text: str) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    dst_text = strip_local_sections(dst_text)

    src_fm, src_body = split_frontmatter(src_text)
    dst_fm, dst_body = split_frontmatter(dst_text)
    if (src_fm is None) != (dst_fm is None):
        errors.append("frontmatter 存在性与上游不一致")
    if src_fm is not None and dst_fm is not None:
        s_keys, s_scalars, s_meta = parse_frontmatter(src_fm)
        d_keys, d_scalars, d_meta = parse_frontmatter(dst_fm)
        if s_keys != d_keys:
            errors.append(f"frontmatter key 不一致: 上游={s_keys} 本地={d_keys}")
        for key in FIXED_SCALAR_KEYS:
            if s_scalars.get(key) != d_scalars.get(key):
                errors.append(f"frontmatter `{key}` 值被改动: {s_scalars.get(key)!r} → {d_scalars.get(key)!r}")
        if s_meta != d_meta:
            errors.append("frontmatter metadata 块被改动")
        syntax = frontmatter_syntax_errors(dst_fm)
        if syntax:
            errors.extend(f"frontmatter 语法: {m}" for m in syntax[:5])

    s_fences, d_fences = fences(src_body), fences(dst_body)
    if len(s_fences) != len(d_fences):
        errors.append(f"代码块数量不一致: 上游 {len(s_fences)} → 本地 {len(d_fences)}")
    elif Counter(s_fences) != Counter(d_fences):
        errors.append(f"代码块语言标注不一致: 上游 {s_fences} → 本地 {d_fences}")

    s_links = Counter(LINK_RE.findall(strip_code(src_body)))
    d_links = Counter(LINK_RE.findall(strip_code(dst_body)))
    if s_links != d_links:
        missing = s_links - d_links
        extra = d_links - s_links
        if missing:
            errors.append(f"链接目标缺失/被改: {dict(list(missing.items())[:6])}")
        if extra:
            errors.append(f"多出链接目标: {dict(list(extra.items())[:6])}")

    s_blocks, d_blocks = fence_blocks(src_body), fence_blocks(dst_body)
    if len(s_blocks) == len(d_blocks):
        broken = [i for i, (a, b) in enumerate(zip(s_blocks, d_blocks), 1) if a != b]
        if broken:
            errors.append(f"代码块内容被改动: 第 {broken[:8]} 个代码块（共 {len(s_blocks)} 个）")

    s_heads = len(HEADING_RE.findall(strip_code(src_body)))
    d_heads = len(HEADING_RE.findall(strip_code(dst_body)))
    if s_heads != d_heads:
        errors.append(f"标题数量不一致: 上游 {s_heads} → 本地 {d_heads}")

    s_inline = {m.strip() for m in INLINE_CODE_RE.findall(src_body) if m.strip() and not m.strip().startswith("$")}
    missing_inline = sorted(t for t in s_inline if t not in dst_body)
    if missing_inline:
        warns.append(f"inline code 未保留({len(missing_inline)}): {missing_inline[:6]}")

    # 正文剔除代码块后若无自然语言（纯代码样例文件），"与上游一致"是正确结果，不判失败
    if strip_code(src_body).strip() and src_body.strip() == dst_body.strip():
        errors.append("内容与上游完全一致，未翻译")

    return errors, warns


def upstream_root() -> Path:
    plan = {}
    if PLAN_FILE.exists():
        try:
            plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            plan = {}
    root = Path(plan["upstream_dir"]) if plan.get("upstream_dir") else UPSTREAM_DIR
    if not root.exists():
        print(f"错误: 上游目录不存在 {root}，先运行 python scripts/sync_upstream.py plan", file=sys.stderr)
        raise SystemExit(2)
    return root


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="只校验单个文件（相对仓库根）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    up = upstream_root()
    roots = skill_roots(up)
    files = (
        [args.path]
        if args.path
        else [
            rel
            for rel in walk_files(up)
            if not is_local_only(rel) and not rel.startswith(EXCLUDED_PREFIXES)
        ]
    )

    report = {"checked": 0, "translated": 0, "errors": {}, "warnings": {}}
    for rel in files:
        src, dst = up / rel, REPO / rel
        if not dst.exists():
            report["errors"].setdefault(rel, []).append("本地文件缺失")
            continue
        report["checked"] += 1
        if not should_translate(rel, roots):
            continue
        report["translated"] += 1
        try:
            src_text = src.read_text(encoding="utf-8")
            dst_text = dst.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        errors, warns = check_markdown(rel, src_text, dst_text)
        if errors:
            report["errors"][rel] = errors
        if warns:
            report["warnings"][rel] = warns

    ok = not report["errors"]
    if args.json:
        print(json.dumps({**report, "ok": ok}, ensure_ascii=False, indent=2))
    else:
        print(f"检查文件 {report['checked']}（其中 markdown {report['translated']}）")
        if report["errors"]:
            print(f"\n[error] {len(report['errors'])} 个文件有问题:")
            for rel, msgs in sorted(report["errors"].items())[:60]:
                print(f"  {rel}")
                for m in msgs:
                    print(f"    - {m}")
            if len(report["errors"]) > 60:
                print(f"  … 还有 {len(report['errors']) - 60} 个文件")
        if report["warnings"]:
            print(f"\n[warn] {len(report['warnings'])} 个文件有复核提示:")
            for rel, msgs in sorted(report["warnings"].items())[:25]:
                print(f"  {rel}")
                for m in msgs:
                    print(f"    - {m}")
            if len(report["warnings"]) > 25:
                print(f"  … 还有 {len(report['warnings']) - 25} 个")
        print("\n结论:", "通过" if ok else "失败")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
