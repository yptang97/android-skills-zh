# 同步记录

本仓库是 [android/skills](https://github.com/android/skills) 的简体中文本地化版本，由 [yptang97/android-skills-zh](https://github.com/yptang97/android-skills-zh) 维护。

内容以上游为准：目录结构、文件清单、代码与配置都以 `android/skills` 的 `main` 分支为唯一来源，本仓库只做语言本地化。上游的 skill 增删改会通过每日同步任务（每天 03:00）落到本仓库；上游删除的内容在本仓库同样删除。

- 翻译规范：`.skills/translate-skill/SKILL.md`
- 术语表：`TRANSLATION-GLOSSARY.md`
- 同步工具：`scripts/sync_upstream.py`（`plan` → 翻译 → `finalize`）
- 结构校验：`scripts/check_translation.py`
- 英文残留复核：`scripts/audit_english.py`

## 同步记录

- 2026-10-28：已同步上游 `android/skills@45fd173`，本地 commit 待定。上游刷新：新增 34 / 变更 10 / 移除 11 个文件，翻译 21 个 markdown。
- 2026-10-26：已同步上游 `android/skills@4ebabf2`，本地 commit `9b61e67`。上游刷新：新增 0 / 变更 0 / 移除 118 个文件，翻译 0 个 markdown。
- 2026-10-26：已同步上游 `android/skills@4ebabf2`，本地 commit `a341394`。首次全量翻译：新增 428 / 变更 0 / 移除 0 个文件，翻译 151 个 markdown。
