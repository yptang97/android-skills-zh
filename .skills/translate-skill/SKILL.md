---
name: translate-skill
description: 把上游 android/skills 的内容翻译、刷新或复核到简体中文本地化仓库 yptang97/android-skills-zh 时使用这个项目级 skill。适用于 SKILL.md、references 文档、README、SYNC.md、安装说明，以及其他需要保留行为关键标识符的上游用户可见内容。
---

# 翻译 skill

使用这个 skill 把上游 `android/skills` 的内容翻译成简体中文，用于 `yptang97/android-skills-zh`。

这个 skill 用于**内容本地化**，不是 Git 同步。Git 层面的同步由 `scripts/sync_upstream.py` 负责。

## 操作原则

把用户可见的英文说明性文字翻译成自然的简体中文，同时原样保留所有行为关键内容。

本仓库是上游的独立简体中文本地化版本：内容以上游为准（增删改查都跟随上游），但呈现语言为中文。上游的仓库元数据（Git 历史、提交作者、tag）不随内容复制。

## 翻译范围

本仓库只翻译 **skill 本体**，其余内容跟随上游同步但保持英文原样。

可翻译：

```text
各 skill 目录下的 SKILL.md
各 skill 目录下的 references/、resources/、analysis/、recording/ 等说明文档
顶层 README.md
```

保持英文：

```text
references/android/**   developer.android.com 整篇文档镜像
.github/**              GitHub issue / PR 模板
LICENSE.txt             法律文本
.claude-plugin/、.codex-plugin/、.agents/  插件清单（仅 description 由脚本套用中文）
```

范围由 `scripts/sync_upstream.py` 的 `should_translate()` 判定，上游新增的 skill 目录会自动纳入。

本地剔除（不复制、不翻译、同步时自动从本地删除）：

```text
wear/          Wear OS 手表
cars/          Android Auto / Automotive OS 驻车应用
device-ai/     端侧 AI 与 AppFunctions
xr/            Android XR 眼镜与头显
```

排除列表是 `sync_upstream.py` 的 `EXCLUDED_PREFIXES`，`check_translation.py` 里有一份同名常量，改一处必须同步另一处。

## 翻译哪些内容

翻译自然语言文本，包括：

```text
README 说明
SKILL.md 的正文
skill description（frontmatter 里的说明性文本）
references/ 下的文档正文
面向 agent 的操作指引
以说明性文字写成的示例
Markdown 标题（headings）
表格中的说明性单元格
```

### Markdown 标题的翻译规则

标题是说明性文字，翻译成简体中文；标题层级与 Markdown 结构保持不变。标题内嵌的 inline code、标识符原样保留。

- 固定 schema 标题（`What it does`、`When to reach for it`、`Common questions`、`It's working if`、`Where it fits`、`Prerequisites`）与结构性标题（`Steps`、`Reference` 等）必须使用 `TRANSLATION-GLOSSARY.md` 登记的统一译法。
- 其余标题按语境意译。
- 修改标题时，同步更新同一文件内指向该标题的 anchor links（GitHub 按标题文本生成 slug，中文标题生成中文 anchor）。

## 原样保留哪些内容

不要翻译或改写：

```text
目录名与文件名
skill 名称（frontmatter 的 name 值）
slash commands
CLI 命令与参数
代码块（含代码块内的注释）
inline code
文件路径
包名、类名、函数名、资源 ID
tool identifiers / API identifiers
环境变量名
frontmatter keys
JSON/YAML/TOML keys
Markdown 链接目标 URL
行为关键 labels
```

保持 Markdown 结构、标题层级、列表嵌套、表格、链接目标、相对路径和 code fences 不变。

**关键校验约束**（`scripts/check_translation.py` 会强制检查）：

1. frontmatter 的 key 集合与上游完全一致。
2. frontmatter 中 `name`、`license` 等标识性字段的值与上游完全一致。
3. fenced code block 的数量、顺序与语言标注与上游一致。
4. 所有 Markdown 链接目标 `](...)` 的多重集与上游完全一致（URL 一个字都不能改）。
5. 段落数量不必逐段对应，但不得丢失任何代码块、表格或链接。

## 仓库路径本地化

翻译用户可见的安装示例时，把上游仓库路径：

```text
android/skills
```

替换为本地化仓库路径：

```text
yptang97/android-skills-zh
```

只有当命令或说明性文字是在告诉用户如何安装或使用**本仓库**时才做这个替换。不要替换：

- 指向 `developer.android.com` 的上游文档链接；
- `.claude-plugin/plugin.json` 等发布元数据里的 `homepage` / `repository`；
- 对上游项目的署名与致谢。

不要移除对上游项目的署名。

## Frontmatter 规则

原样保留 frontmatter keys 的集合与顺序。

按含义而不仅是字段名，对每个 frontmatter 值分类：

- 保持 `name` 值不变。
- 把用户可见或面向 agent 的自然语言文本翻译成简体中文，包括 `description`。
- 保持 `license`、`metadata.author`、`metadata.last-updated`、`metadata.keywords`、布尔值、数字、路径、URL、工具名不变。
- 在可翻译的值内部，原样保留内嵌的 slash commands、inline code、占位符、路径、URL、package 名、工具名和其他行为关键片段。
- 对有歧义的值打复核标记，不要猜测。

示例：

```yaml
---
name: appfunctions
description: 分析 Android 应用，识别适合用 AppFunctions 暴露的关键用户流程，例如创建笔记、播放媒体、发送由自动化流程或 AI agent 触发的消息、语音命令或系统快捷方式，且无需打开应用 UI。生成 Kotlin 代码把这些流程暴露给 Android 系统，使 agent 能在设备端发现并执行它们。同时优化 KDoc 文档，确保 AI agent 能正确理解并使用所提供的功能。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-08-14'
  keywords:
  - AppFunctions
  - Kotlin
---
```

## 翻译风格

使用满足以下要求的简体中文：

```text
自然
对 Android 开发者友好
简洁
准确
与本仓库现有语气一致
```

如果某个工程术语在开发者中是标准说法，或者翻译它会降低清晰度，就把它保留为英文（见 `TRANSLATION-GLOSSARY.md` 的「保留英文」区）。

### 语气与格式细节

- 使用「你」称呼读者，不使用「您」。
- 祈使句保持祈使：`Run the command` → 「运行该命令」。
- 全角标点用于中文句子；代码块与 inline code 内保持半角。
- 不新增解释性内容，不删减上游信息；只做语言转换。
- 英文术语与中文混排时不额外插入空格，除非原文该处本来就有空格。

## 术语参考

查阅仓库根目录的 `TRANSLATION-GLOSSARY.md`。对已决定的术语，严格使用记录的译法。

## 单文件工作流

翻译单个文件时：

1. 确认文件路径和文件类型。
2. 把文件归类为可翻译的自然语言文本、混合内容、config/metadata 或不可翻译。
3. 翻译前先保护行为关键片段（代码块、inline code、路径、URL、frontmatter 标识字段）。
4. 只翻译自然语言文本。
5. 原样恢复被保护的片段。
6. 检查命令、代码块、路径、URL、identifiers 和 frontmatter keys 保持不变。
7. 检查本地化后的安装命令使用 `yptang97/android-skills-zh`。
8. 把结果直接写回仓库中的对应路径（目录与文件名与上游一致）。
9. 运行 `python scripts/check_translation.py --path <文件>` 做单文件校验。
10. 返回翻译摘要与所有复核标记。

## 仓库刷新工作流

从上游刷新时：

1. 把上游当作内容来源，而不是 Git 历史。
2. 运行 `python scripts/sync_upstream.py plan`，得到新增、变更和移除的文件清单（`.sync/plan.json`）。
3. 翻译 `plan.json` 中 `translate` 列表里的新增和变更文件；原文从 `upstream_dir` 下的对应路径读取。
4. 不可翻译的支持文件（`.kt`、`.xml`、`.json`、`.py`、`.yml`、`LICENSE.txt`、图片等）由脚本自动复制或删除，不要手工改。
5. 保持本仓库的 README 定位和安装路径不变。
6. 运行 `python scripts/check_translation.py` 完成结构、完整性、索引和行为关键内容检查。
7. 运行 `python scripts/fix_anchors.py`：中文标题会让上游的 `](#english-slug)` 页内链接失效，脚本按标题顺序给对应标题补 `<a id="slug"></a>`，保持旧锚点仍可跳转（上游本身就写错的锚点不处理）。
8. 运行 `python scripts/sync_upstream.py finalize`，写入同步状态并在 `SYNC.md` 追加记录。
9. 在 `SYNC.md` 中记录本次验证结果、翻译执行者和翻译策略摘要。
10. 把有歧义的文件、被移除的文件或有风险的转换打上复核标记，交维护者审查。
11. 总结已翻译文件、复制或保留文件、移除文件、跳过文件、验证结果和复核标记。

## 不翻译的内容（本地策略）

以下内容跟随上游同步，但**保持英文原样**：

```text
.github/                 GitHub issue 与 PR 模板，frontmatter 含 title/labels 等平台字段
LICENSE.txt              法律文本，必须逐字一致
references/android/      developer.android.com 整篇文档镜像，翻译收益低于维护成本
.claude-plugin/、.codex-plugin/、.agents/  插件清单的路径、版本、skills 索引
```

插件清单中仅 `description` 字段由 `scripts/sync_upstream.py` 统一套用中文文案，其余字段原样保留。

## 提交信息模板

提交信息一律用中文，两条固定格式：

```text
sync: 首次简体中文本地化，上游 android/skills@<short-sha>

新增 N 个文件、变更 M 个、移除 K 个。
翻译 X 个 markdown（Y 个 SKILL.md 与 skill 内文档）。
references/android/ 下官方文档镜像保留英文原样。

校验：check_translation 全量通过（N 文件 / 0 error）。
```

```text
sync: 同步上游 android/skills@<short-sha>

新增 N / 变更 M / 移除 K；翻译 X 个 markdown。
校验：check_translation 通过。
```

发布版本单独用一条：

```text
release: <上游版本>-zh.<n> 中文技能包
```

配套的文档提交：

```text
docs: 记录 <short-sha> 同步对应的本地 commit
```

## 验证步骤

每次上游内容刷新后，必须完成并记录以下检查：

1. 运行 `python scripts/check_translation.py`，确认 frontmatter、代码块、链接与文件清单没被破坏。
2. 运行 `python scripts/fix_anchors.py --dry-run`，确认没有失效的页内锚点（输出应只剩上游自身写错的锚点）。
3. 检查公开 skill 索引一致性：`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json` 中列出的 skill 目录都存在且各有 `SKILL.md`。
4. 对比上游的 in-scope 文件清单，确认没有缺失上游文件，也没有残留已从上游移除的 stale 文件。
5. 检查共同 Markdown 文件的行为关键内容：frontmatter keys 和 `name` 值不变，fenced code blocks 平衡，路径、命令、URL、identifier 不被误改。
6. 运行 `git diff --check`，确认没有 whitespace 或 patch hygiene 问题。
7. 检查 `SYNC.md` 指向最新 upstream short SHA，并包含本地同步 commit（不能留下「待定」占位）。
8. 扫描 stale install path：README 中不应残留 `/plugin marketplace add android/skills` 这类指向上游的安装命令。
9. 运行 `python scripts/audit_english.py` 作为人工复核队列。该脚本会包含合理的英文术语、命令、示例和 identifiers，因此只作为 review flag，不作为硬性失败门槛。

验证结果应写入顶层 `README.md` 的「同步与验证」小节，使用简短 checklist，不要粘贴完整命令输出。

## SYNC.md 同步记录

每次上游刷新都应在顶层 `SYNC.md` 的同步记录中新增一条简短条目。

条目应包含：

- 刷新日期，使用 `YYYY-MM-DD` 格式
- 上游来源 revision，格式为 `android/skills@<short-sha>`
- 本地同步 commit（如果已存在）；否则先写「待定」，commit 后替换
- 一句话描述本次可见的内容变更（新增/更新/移除的 skill 数）

示例：

```text
- 2026-10-26：已同步上游 `android/skills@4ebabf2`，本地 commit `a1b2c3d`。首次全量翻译：33 个 skill、319 个文档。
```

## 复核输出格式

复核一次翻译刷新时，提供：

```text
改动文件：
- ...

已翻译文件：
- ...

复制或保留文件：
- ...

移除或过时文件：
- ...

复核标记：
- ...

SYNC.md 同步记录：
- ...

验证结果：
- ...

不变量检查：
- 安装命令指向 yptang97/android-skills-zh
- 代码块保持原样
- frontmatter keys 保持原样
- 路径和 identifiers 保持原样
- Markdown 结构保持原样
```

## Fail-closed 规则

拿不准一段文本是否行为关键时，先原样保留并打上复核标记。

不要悄悄改写任何可能影响安装、skill 发现、命令执行、文件引用、API 调用、工具使用或 agent 行为的内容。
