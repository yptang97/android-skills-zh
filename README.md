<!-- local:begin -->

# Android skills 中文版

[android/skills](https://github.com/android/skills) 的简体中文本地化分支，只做语言转换，内容与结构以上游为准。

- **上游**：`android/skills`（Apache-2.0），每天 03:00 自动同步、翻译、校验、发版
- **本仓库**：`yptang97/android-skills-zh`，24 个 skill，SKILL.md 与说明文档为中文，代码与 API 原样保留
- **剔除**：`wear/`、`cars/`、`device-ai/`、`xr/` 四类 skill 不在此仓库维护（见下文）

## 快速安装

Claude Code：

```text
/plugin marketplace add yptang97/android-skills-zh
/plugin install android-skills@android-skills
```

Codex：

```text
codex plugin marketplace add yptang97/android-skills-zh
codex plugin add android-skills@android-skills
```

只想要某个 skill，直接把目录拷进 agent 的 skills 目录，例如 `cp -r camera/camerax ~/.claude/skills/`。

## 包含的 24 个 skill

| 分组 | skill | 用途 |
| --- | --- | --- |
| 构建与工具 | `build-system/agp/agp-9-upgrade` | AGP 9 升级迁移（kapt→ksp、Paparazzi 等配方） |
| | `devtools/android-cli` | `android` CLI：建项目、装 APK、管模拟器、导出 UI 树 |
| | `testing/testing-setup` | 测试策略与骨架：单测、UI 测试、截图测试、E2E |
| Compose | `jetpack-compose/adaptive` | 一套 UI 适配手机/平板/折叠/桌面/TV，处理窗口尺寸与配置变更 |
| | `jetpack-compose/jetpack-compose-performance` | 诊断重组开销、掉帧、卡顿 |
| | `jetpack-compose/migration/migrate-xml-views-to-jetpack-compose` | XML View 迁 Compose 的完整流程 |
| | `jetpack-compose/theming/styles` | Compose Styles API 与设计系统迁移 |
| 导航 | `navigation/navigation-3` | Navigation 3：深链、多返回栈、场景化导航 |
| | `navigation/navigation-event` | 返回手势拦截与 Predictive Back |
| 性能 | `performance/anr-audit-and-fix` | ANR 风险扫描与堆栈分诊 |
| | `performance/r8-analyzer` | R8 keep 规则冗余与体积优化 |
| | `profilers/android-profiler` | Perfetto trace 录制与分析 |
| 安全 | `security/android-intent-security` | Intent 重定向防护 |
| | `security/android-permissions-security` | 权限与 IPC 组件加固 |
| Play | `play/engage-sdk-integration` | Engage SDK 集成与排障 |
| | `play/play-billing-library-version-upgrade` | Play Billing Library 升级 |
| | `play/play-policy-insights` | 按 Play 政策自动审计并出合规报告 |
| 大屏与小部件 | `tv/leanback-to-compose-tv-migration` | Leanback/Views 迁到 Compose for TV |
| | `system/glance-canonical-layouts` | Glance 主屏小组件规范布局 |
| 系统适配 | `system/edge-to-edge` | 全屏适配，修系统栏遮挡与 IME insets |
| 相机与媒体 | `camera/camerax` | CameraX 相机开发 |
| | `media/media3-cast-integration` | Media3 接入 Google Cast |
| 身份 | `identity/restore-credentials` | 恢复密钥，新设备静默登录 |
| | `identity/verified-email` | Credential Manager 免 OTP 邮箱验证 |

## 不包含的部分

| 目录 | 上游 skill | 剔除原因 |
| --- | --- | --- |
| `wear/` | `wear-compose-m3`、`wear-widgets` | Wear OS 手表，与本仓库使用场景无关（上游这两项占 56 篇文档） |
| `cars/` | `android-for-cars-parked-apps` | Android Auto / Automotive OS 驻车应用 |
| `device-ai/` | `appfunctions`、`litert-lm`、`litert-runtime`、`ml-kit-genai-prompt-api` | 端侧 AI 与 AppFunctions，按需从上游原文取用 |
| `xr/` | `display-glasses-with-jetpack-compose-glimmer`、`projected-hardware` | Android XR 眼镜与头显应用 |

剔除目录在每次同步时自动跳过，上游新增的相邻内容不会回流进来。需要时直接看上游原文。

## 维护方式

| 工具 | 作用 |
| --- | --- |
| `scripts/sync_upstream.py` | `plan` 拉取上游并算出差异 → 翻译 → `finalize` 落状态、删上游已移除的文件 |
| `scripts/check_translation.py` | 结构校验：frontmatter、代码块内容、链接目标、标题数量、YAML 合法性 |
| `scripts/fix_anchors.py` | 中文标题导致英文页内锚点失效时补 `<a id>` |
| `scripts/audit_english.py` | 英文残留的人工复核队列 |
| `scripts/publish.py` | 发布版本，规则为 `<上游版本>-zh.<n>` |

翻译规范见 `.skills/translate-skill/SKILL.md`，术语以 `TRANSLATION-GLOSSARY.md` 为准，同步历史见 `SYNC.md`。

## 原版 README

<!-- local:end -->

## Android skills

**Android skills** 是一个专门维护 **面向 AI 优化的模块化指令**与资源的仓库，帮助 agent 更好地理解并执行符合
Android 开发最佳实践与官方指南的特定模式，内容源自 [developer.android.com](https://developer.android.com)。

Android skills 遵循[开放标准的 agent skills](https://agentskills.io/home) 规范——markdown
文件（SKILL.md）给出任务的技术规格，并用专业领域与工作流的信息**为 LLM 提供依据**。

我们的 Android skill 开发聚焦于**评估显示 LLM 表现欠佳的使用场景与工作流**。
对于 LLM 已经擅长的成熟领域（例如基础的 Jetpack Compose 最佳实践），我们不作为优先项。

了解更多，请阅读官方文档：

- [Android skills](https://developer.android.com/tools/agents/android-skills)
- [Android CLI](https://developer.android.com/tools/agents/android-cli)
- [Android Studio](https://developer.android.com/studio/gemini/skills)

### 安装 Android skills

用 Android CLI 把指定 skill 安装到当前目录：

```
android skills add r8-analyzer --project=.
```

用 Android CLI 把全部 Android skills 安装到所有检测到的 agent 目录：

```
android skills add --all
```

如果没有任何现存的 agent 目录，也没有指定 agent，skills 会安装到 `~/.gemini/antigravity/skills`，供 Gemini 和 Antigravity 使用。

**选项：**

- `--all` - 添加全部 Android skills。省略时只安装 `android-cli` skill。
- `--agent` - 逗号分隔的 agent 列表，用于指定为哪些 agent 安装 skill。省略时安装到所有检测到的 agent。
- `--project` - 用于安装 skills 的项目根目录路径。


更新全部 skill 或指定 skill，运行：

```
android skills update --all
android skills update wear-compose-m3
```

### 以 agent 插件方式安装

**Claude Code**：

```
/plugin marketplace add yptang97/android-skills-zh
/plugin install android-skills@android-skills
```

**Codex：**

```
codex plugin marketplace add yptang97/android-skills-zh
codex plugin add android-skills@android-skills
```

### 激活 skills

agent 会自动激活与你任务相关的 skill。要使用某个 skill，向 agent 提出与该 skill 相关的任务，例如「把我的应用 UI 改成 edge-to-edge」。如果该 skill 已安装，agent 应当能自动找到并使用它。

## 免责声明

AI 可能出错，请务必复核结果。

## 贡献

提交 GitHub issue 反馈问题、报告缺陷，或提出新的 skill 需求与改动。

目前不接受公开贡献。

## 许可

Android Skills 采用 [Apache License 2.0](LICENSE.txt) 许可。详见 `LICENSE.txt` 文件。

## 阅读我们的社区准则

本项目遵循
[Google 开源社区准则](https://opensource.google/conduct/)。
