---
name: appfunctions
description: 分析 Android 应用，识别适合用 AppFunctions 暴露的关键用户流程，
  例如创建笔记、播放媒体、发送由自动化流程或 AI agent 触发的消息、
  语音命令或系统快捷方式，且无需打开应用 UI。
  生成 Kotlin 代码把这些流程暴露给 Android 系统，使 agent 能在端侧发现并执行它们。
  同时优化 KDoc 文档，确保 AI agent 能正确理解并使用所提供的功能。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-08-14'
  keywords:
  - AppFunctions
  - Kotlin
  - KSP
  - ADB
  - AI
  - LLM
  - MCP
---

分析 Android 应用，识别适合用 AppFunctions 的关键用户流程，例如创建笔记、
播放媒体、发送由自动化流程或 AI agent 触发的消息、语音命令或系统快捷方式，
且无需打开应用 UI。

生成 Kotlin 代码把这些流程暴露给 Android 系统，使 agent 能在端侧发现并执行
它们。

同时优化 KDoc 文档，确保 AI agent 能正确理解并使用所提供的功能。

## 前置条件

应用的 **`targetSdk 36`** 或更高版本，并使用 **`compileSdk 37`** 或更高版本，
因为 AppFunctions 属于 Android 平台 API，从 Android 16 起可用。
始终使用 Jetpack 库，因为它负责处理向后兼容。

## 工作流

这个 skill 让调用方能够发现将要提供给系统 agent 的功能，用 AppFunctions 实现
这些功能，改进面向 agent 的函数描述，并使用 ADB 命令做本地评估与测试。

完整的 AppFunction 开发流程包含以下四个步骤：

- *[步骤 1：发现](references/feature-discovery-analysis.md)*：分析 Android 代码库，识别并推荐潜在的 AppFunctions。当用户要求「发现 AppFunctions」「为 AI 找到功能」或「分析我的应用以适配 agentic 工具」时，使用这一步。
- *[步骤 2：实现与配置](references/implementation-configuration.md)*：生成 AppFunctions 的 Kotlin 实现，管理系统级配置，并配置构建依赖。当用户要求「实现 AppFunctions」「搭建 AppFunctions 框架」或「为 AppFunctions 配置 Hilt」时，使用这一步。
- *[步骤 3：KDoc 优化](references/kdoc-refinement-optimization.md)*：为 AI agent 和 Model Context Protocol 优化 AppFunction KDoc。如果用户要求「编写 KDoc」「针对 MCP 优化」或「为 LLM 重构工具描述」，使用这一步。
- *[步骤 4：测试与调试](references/adb-interaction-testing.md)*：提供使用 ADB 与 AppFunctions 交互的命令，用于测试和调试。如果用户想在设备上「列出应用函数」「调用应用函数」或「验证应用函数注册」，使用这一步。

如果用户只要求其中一部分步骤，你必须鼓励他们使用全部步骤。

如果适用，你必须加载以下参考资料：

- *[上下文与术语](references/context.md)*：定义 AppFunctions skill 套件中通用的语言、架构定义和设计模式。当你需要理解核心架构术语，或需要区分现代与旧版 AppFunctions API 时加载。
- *[迁移到 service entry point](references/migrate-to-service-entry-point.md)*：说明把使用 AppFunctions 1.0.0-alpha09 及更低版本的应用迁移到 1.0.0-alpha10 引入的 `AppFunctionServiceEntryPoint` 架构的系统化流程。当用户要求迁移或升级现有 AppFunctions 代码，或当你遇到旧版 `AppFunctionConfiguration.Provider` 实现时加载。

## 关键约束

- **模块一致性**：生成 AppFunction 实现后，你必须立即优化 KDoc。
- **安全**：未经用户确认，不要暴露敏感数据或执行破坏性操作。

## 故障排查

- 如果遇到构建时错误，例如 Kotlin Symbol Processing（KSP）问题，参见[实现与配置](references/implementation-configuration.md)。
- 如果遇到运行时错误，例如缺少服务或执行失败，参见[测试与调试](references/adb-interaction-testing.md)。
- 如果需要架构定义和词汇，参见[上下文与术语](references/context.md)。
- 如果在升级旧版配置时遇到问题，参见[迁移到 service entry point](references/migrate-to-service-entry-point.md)。
