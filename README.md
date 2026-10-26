## Android skills

<!-- local:begin -->
> **简体中文本地化版本。** 本仓库是 [android/skills](https://github.com/android/skills) 的社区中文翻译，内容以上游为准并每日自动同步。
> 翻译范围与校验方式见 `SYNC.md`，术语约定见 `TRANSLATION-GLOSSARY.md`。
<!-- local:end -->

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
