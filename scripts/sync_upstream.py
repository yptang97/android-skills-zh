#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""android-skills-zh 上游同步工具。

把上游 android/skills 的内容同步到本中文本地化仓库：
非 markdown 文件直接复制，markdown 文件登记到待翻译清单，由翻译流程产出中文版本。

用法::

    python scripts/sync_upstream.py status                     # 查看当前同步状态与上游差异
    python scripts/sync_upstream.py plan                       # 拉取上游并生成待处理清单
    python scripts/sync_upstream.py plan --no-fetch            # 用已 clone 的上游副本生成清单
    python scripts/sync_upstream.py batches --count 16         # 把待翻译文件按体积切成并行批次
    python scripts/sync_upstream.py finalize                   # 校验翻译结果、写状态、记 SYNC.md
    python scripts/sync_upstream.py finalize --allow-missing   # 允许部分文件未翻译（应急）

退出码：0 成功；1 失败；2 需要人工介入。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYNC_DIR = REPO / ".sync"
STATE_FILE = SYNC_DIR / "state.json"
PLAN_FILE = SYNC_DIR / "plan.json"

UPSTREAM_REPO = os.environ.get("UPSTREAM_REPO", "https://github.com/android/skills.git")
UPSTREAM_LABEL = "android/skills"

_env_upstream = os.environ.get("ANDROID_SKILLS_UPSTREAM", "").strip()
UPSTREAM_DIR = (
    Path(_env_upstream).expanduser().resolve()
    if _env_upstream
    else (REPO.parent / "android-skills-upstream").resolve()
)

# 本仓库自有文件，不属于上游内容，同步时不触碰
LOCAL_ONLY_PREFIXES = (".git/", ".sync/", ".skills/", "scripts/")
LOCAL_ONLY_FILES = {".gitignore", "TRANSLATION-GLOSSARY.md", "SYNC.md"}

# 跟随上游同步但保持英文（GitHub 模板、法律文本）
NO_TRANSLATE_PREFIXES = (".github/",)
NO_TRANSLATE_FILES = {"LICENSE.txt"}
# 官方文档整篇镜像（developer.android.com 原文），保持英文
OFFICIAL_DOC_MIRROR_RE = re.compile(r"/references/android/")

# 插件清单里唯一需要本地化的字段
PLUGIN_DESCRIPTION_ZH = (
    "Android skills 是 Google 官方维护的、面向 AI 优化的模块化指令与资源仓库，"
    "帮助 LLM 更好地理解并执行符合 Android 开发最佳实践与官方指南的特定模式。"
    "Android skills 遵循开放标准的 agent skills 规范——用 markdown 文件（SKILL.md）"
    "给出任务的技术规格，并为 LLM 提供专业领域与工作流知识。"
)
MARKETPLACE_DESCRIPTION_ZH = "Google 官方提供的 Android skills，用于 agent 驱动的 Android 开发。"

LOCALIZED_JSON = {
    ".claude-plugin/plugin.json": PLUGIN_DESCRIPTION_ZH,
    ".codex-plugin/plugin.json": PLUGIN_DESCRIPTION_ZH,
    ".claude-plugin/marketplace.json": MARKETPLACE_DESCRIPTION_ZH,
}


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str, code: int = 1) -> None:
    print(f"错误: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(git_dir: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(git_dir), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and proc.returncode != 0:
        fail(f"git {' '.join(args)} 失败:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def copy_file(src: Path, dst: Path, attempts: int = 5) -> None:
    """复制文件，容忍 Windows 上短暂的文件占用（索引/杀毒）。"""
    last: Exception | None = None
    for i in range(attempts):
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            shutil.copystat(src, dst)
            return
        except OSError as exc:
            last = exc
            time.sleep(0.4 * (i + 1))
    fail(f"复制 {src} → {dst} 失败: {last}")


def is_local_only(rel: str) -> bool:
    return rel in LOCAL_ONLY_FILES or rel.startswith(LOCAL_ONLY_PREFIXES)


FENCE_LINE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def strip_fences(text: str) -> str:
    """移除 fenced code block，只留正文。"""
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_LINE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]
                continue
            out.append(line)
        elif line.strip().startswith(fence * 3):
            fence = None
    return "\n".join(out)


def has_prose(path: Path) -> bool:
    """正文是否含自然语言（纯代码样例文件返回 False，不需要翻译）。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    body = strip_fences(text)
    if body.lstrip().startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
    return bool(re.search(r"[A-Za-z]{2,}", body))


def should_translate(rel: str, roots: set[str], src: Path | None = None) -> bool:
    """翻译范围：skill 目录内的 markdown + 顶层 README。

    `references/android/` 下是 developer.android.com 的整篇文档镜像，保持英文原样。
    `.github/`、插件清单、LICENSE 等元数据不翻译。
    """
    if not rel.endswith(".md") or rel in NO_TRANSLATE_FILES or rel.startswith(NO_TRANSLATE_PREFIXES):
        return False
    if OFFICIAL_DOC_MIRROR_RE.search(rel):
        return False
    if rel == "README.md":
        return True
    if not any(rel.startswith(root + "/") for root in roots):
        return False
    # 纯代码样例文件（正文剔除代码块后无自然语言）原样跟随上游，不进翻译队列
    if src is not None and not has_prose(src):
        return False
    return True


def skill_roots(up: Path) -> set[str]:
    """上游所有 skill 目录（含 SKILL.md 的目录）。"""
    return {p.parent.relative_to(up).as_posix() for p in up.rglob("SKILL.md")}


def walk_files(root: Path) -> list[str]:
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        base = Path(dirpath)
        for name in filenames:
            out.append((base / name).relative_to(root).as_posix())
    return sorted(out)


def ensure_upstream(fetch: bool) -> Path:
    up = UPSTREAM_DIR
    if up == REPO or REPO in up.parents:
        fail(f"上游目录不能指向本仓库或其子目录: {up}")
    if not (up / ".git").exists():
        if up.exists() and any(up.iterdir()):
            fail(f"上游目录已存在但不是 git 仓库: {up}")
        up.parent.mkdir(parents=True, exist_ok=True)
        log(f"克隆上游 {UPSTREAM_REPO} → {up}")
        proc = subprocess.run(
            ["git", "clone", UPSTREAM_REPO, str(up)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            fail(f"克隆上游失败:\n{proc.stderr.strip()}")
    elif fetch:
        log("拉取上游最新 main…")
        run_git(up, "fetch", "--depth", "1", "origin", "main")
        run_git(up, "reset", "--hard", "FETCH_HEAD")
        run_git(up, "clean", "-fdx")
    return up


def upstream_manifest(up: Path) -> dict[str, str]:
    return {rel: sha256_file(up / rel) for rel in walk_files(up)}


def local_manifest() -> dict[str, str]:
    return {
        rel: sha256_file(REPO / rel)
        for rel in walk_files(REPO)
        if not is_local_only(rel)
    }


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"无法解析 {path}: {exc}")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


L10N_VERSION_FILE = REPO / ".sync" / "l10n-version.json"


def read_l10n_version() -> dict:
    """读取本地发布版本记录（由 scripts/publish.py 写入）。"""
    if not L10N_VERSION_FILE.exists():
        return {}
    try:
        return json.loads(L10N_VERSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def localize_plugin_json(target: Path) -> bool:
    """把插件清单里用户可见的 description 换成中文，并保留本地发布的版本号。"""
    want = LOCALIZED_JSON.get(target.relative_to(REPO).as_posix())
    if not want:
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    changed = False
    if isinstance(data.get("description"), str) and data["description"] != want:
        data["description"] = want
        changed = True
    # 上游刚复制过来的是上游版本号；若已发布过对应的中文本地化版本，恢复本地版本号
    l10n = read_l10n_version()
    if l10n and data.get("version") == l10n.get("upstream_version"):
        if data.get("version") != l10n.get("version"):
            data["version"] = l10n["version"]
            changed = True
    for plugin in data.get("plugins", []) or []:
        if isinstance(plugin, dict) and isinstance(plugin.get("description"), str):
            if plugin["description"] != want:
                plugin["description"] = want
                changed = True
    if changed:
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def cmd_status(args) -> int:
    state = load_json(STATE_FILE, {})
    plan = load_json(PLAN_FILE, {})
    up = ensure_upstream(fetch=not args.no_fetch)
    up_sha = run_git(up, "rev-parse", "HEAD")
    log(f"上游目录   : {up}")
    log(f"上游 HEAD  : {up_sha[:12]}  ({run_git(up, 'log', '-1', '--format=%cI')})")
    log(f"本地 state : {state.get('upstream_sha', '（无）')[:12]}  最后同步 {state.get('synced_at', '（无）')}")
    if plan:
        log(
            f"待处理清单 : {plan.get('upstream_sha', '')[:12]}  "
            f"translate={len(plan.get('translate', []))} copied={len(plan.get('copied', []))} "
            f"removed={len(plan.get('removed', []))}"
        )
    return 0


def cmd_plan(args) -> int:
    up = ensure_upstream(fetch=not args.no_fetch)
    up_sha = run_git(up, "rev-parse", "HEAD")
    up_short = run_git(up, "rev-parse", "--short=7", "HEAD")
    upstream = upstream_manifest(up)
    local = local_manifest()
    roots = skill_roots(up)
    state = load_json(STATE_FILE, {})
    base_files: dict[str, str] = state.get("files", {}) or {}
    base_sha = state.get("upstream_sha", "")

    added, modified = [], []
    for rel, digest in upstream.items():
        if rel not in base_files:
            added.append(rel)
        elif base_files[rel] != digest:
            modified.append(rel)

    deleted = sorted(set(base_files) - set(upstream))
    stale_local = sorted(set(local) - set(upstream))

    translate, copied, removed = [], [], []
    for rel in sorted(added + modified):
        src, dst = up / rel, REPO / rel
        if should_translate(rel, roots, src):
            translate.append({
                "path": rel,
                "src": str(src),
                "dst": str(dst),
                "bytes": src.stat().st_size,
                "action": "add" if rel in added else "modify",
            })
        else:
            copy_file(src, dst)
            copied.append(rel)

    for rel in sorted(set(deleted) | set(stale_local)):
        if rel not in upstream:
            removed.append(rel)

    localized = [rel for rel in LOCALIZED_JSON if (REPO / rel).exists() and localize_plugin_json(REPO / rel)]

    plan = {
        "generated_at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "upstream_repo": UPSTREAM_LABEL,
        "upstream_sha": up_sha,
        "upstream_short": up_short,
        "upstream_dir": str(up),
        "base_sha": base_sha,
        "first_run": not bool(base_sha),
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": deleted,
        "translate": translate,
        "copied": copied,
        "removed": removed,
        "localized_json": localized,
    }
    write_json(PLAN_FILE, plan)

    log(f"上游 {up_short}：新增 {len(added)} / 变更 {len(modified)} / 移除 {len(deleted)}")
    log(f"  待翻译 markdown : {len(translate)} 个（{sum(x['bytes'] for x in translate) / 1024:.0f} KB）")
    log(f"  已复制非 markdown: {len(copied)} 个")
    log(f"  待删除           : {len(removed)} 个")
    if localized:
        log(f"  插件清单本地化   : {', '.join(localized)}")
    if not translate and not copied and not removed:
        log("已是最新，无需处理。")
    log(f"清单已写入 {PLAN_FILE}")
    return 0


def cmd_batches(args) -> int:
    plan = load_json(PLAN_FILE, None)
    if not plan:
        fail("没有待处理清单，先运行 plan")
    items = plan.get("translate", [])
    if not items:
        log("没有待翻译文件。")
        return 0
    count = max(1, min(args.count, len(items)))
    buckets: list[list[dict]] = [[] for _ in range(count)]
    loads = [0] * count
    for item in sorted(items, key=lambda x: -x["bytes"]):
        idx = loads.index(min(loads))
        buckets[idx].append(item)
        loads[idx] += item["bytes"]
    out_dir = SYNC_DIR / "batches"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for i, bucket in enumerate(buckets, 1):
        bucket.sort(key=lambda x: x["path"])
        payload = {
            "batch": i,
            "total": count,
            "upstream_dir": plan["upstream_dir"],
            "upstream_sha": plan["upstream_sha"],
            "files": bucket,
            "bytes": sum(x["bytes"] for x in bucket),
        }
        write_json(out_dir / f"batch-{i:02d}.json", payload)
        log(f"batch-{i:02d}.json: {len(bucket):2d} 个文件, {payload['bytes'] / 1024:6.0f} KB")
    return 0


def cmd_finalize(args) -> int:
    plan = load_json(PLAN_FILE, None)
    if not plan:
        fail("没有待处理清单，先运行 plan")
    missing = [
        item["path"] for item in plan.get("translate", [])
        if not (REPO / item["path"]).exists() or (REPO / item["path"]).stat().st_size == 0
    ]
    if missing:
        log(f"未完成翻译的文件（{len(missing)}）:")
        for rel in missing[:50]:
            log(f"  - {rel}")
        if len(missing) > 50:
            log(f"  … 还有 {len(missing) - 50} 个")
        if not args.allow_missing:
            fail("翻译未全部完成；确认后可加 --allow-missing 强制收尾", 2)
        log("已按 --allow-missing 继续收尾。")

    removed = []
    for rel in plan.get("removed", []):
        target = REPO / rel
        if target.is_file():
            target.unlink()
            removed.append(rel)

    for dirpath, dirnames, filenames in os.walk(REPO, topdown=False):
        p = Path(dirpath)
        if ".git" in p.parts or ".sync" in p.parts:
            continue
        try:
            if p != REPO and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass

    upstream = upstream_manifest(Path(plan["upstream_dir"]))
    state = {
        "upstream_repo": UPSTREAM_LABEL,
        "upstream_sha": plan["upstream_sha"],
        "upstream_short": plan["upstream_short"],
        "synced_at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "files": upstream,
    }
    write_json(STATE_FILE, state)

    kind = "首次全量翻译" if plan.get("first_run") else "上游刷新"
    detail = (
        f"{kind}：新增 {len(plan.get('added', []))} / 变更 {len(plan.get('modified', []))} / "
        f"移除 {len(removed)} 个文件，翻译 {len(plan.get('translate', []))} 个 markdown。"
    )
    append_sync_entry(plan["upstream_short"], detail)
    log(f"已写入 state: upstream {plan['upstream_short']}, 受管文件 {len(upstream)} 个")
    log(f"已删除本地文件 {len(removed)} 个")
    PLAN_FILE.unlink(missing_ok=True)
    return 0


def append_sync_entry(upstream_short: str, detail: str) -> None:
    sync_md = REPO / "SYNC.md"
    today = _dt.date.today().isoformat()
    entry = f"- {today}：已同步上游 `{UPSTREAM_LABEL}@{upstream_short}`，本地 commit 待定。{detail}\n"
    if not sync_md.exists():
        sync_md.write_text("# 同步记录\n\n## 同步记录\n\n" + entry, encoding="utf-8")
        return
    text = sync_md.read_text(encoding="utf-8")
    marker = "## 同步记录"
    if marker not in text:
        text = text.rstrip("\n") + "\n\n" + marker + "\n\n" + entry
    else:
        head, _, tail = text.partition(marker)
        body = tail.lstrip("\n")
        text = f"{head}{marker}\n\n{entry}{body}"
    sync_md.write_text(text, encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="android-skills-zh 上游同步工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="查看同步状态")
    p_status.add_argument("--no-fetch", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_plan = sub.add_parser("plan", help="生成待处理清单并复制非 markdown 文件")
    p_plan.add_argument("--no-fetch", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_batches = sub.add_parser("batches", help="按体积切分待翻译文件")
    p_batches.add_argument("--count", type=int, default=16)
    p_batches.set_defaults(func=cmd_batches)

    p_fin = sub.add_parser("finalize", help="校验并写入同步状态")
    p_fin.add_argument("--allow-missing", action="store_true")
    p_fin.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
