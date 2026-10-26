---
name: play-billing-library-version-upgrade
description: 当你需要把 Android 项目从任意版本的旧版 Google Play Billing Library（PBL）升级或
  迁移到 PBL 最新稳定版时，使用这个 skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-06'
  keywords:
  - android
  - play billing
  - play billing library
  - pbl
  - upgrade
  - migration
  - deprecation
  - google play
---

## 阶段 0：意图说明

**汇报动作**：在开始操作之前，立即告诉用户：「我将把 Play Billing Library 升级到最新版本。」

## 阶段 1：发现与现状感知

1. **主检查（构建版本）**：在 `build.gradle`、`build.gradle.kts` 或 `libs.versions.toml` 中定位项目的结算依赖（例如 `com.android.billingclient:billing`）。
2. **初次编译测试**：立即尝试同步并构建项目。
3. **兜底发现（实际版本）**：
   - **触发条件**：仅当构建立即失败时，才扫描源码中已废弃的构件。
   - **判断逻辑**：出现已废弃的 API 说明**「实际版本」**是这些 API **最后一次可用**的版本，而不是它们首次引入的版本。
   - **示例**：如果代码中出现 `SkuDetails`，就把基线视为 **PBL v7** 或更早（无论 `build.gradle` 中写的版本号是多少）。
4. **确定目标与路径**：查阅版本工具或版本说明，找到最新稳定版，并基于**实际版本**基线计算 \[直接/分步\] 迁移路径。

- **计算迁移路径**：
  - 如果**实际版本**与目标版本相差不超过 2 个大版本：规划**直接迁移**。
  - 如果落后超过 2 个大版本：规划**分步迁移**。每次跨两个大版本迁移（例如 v4 -\> v6 -\> v8），直到距目标版本不超过两个版本。
- **汇报动作**：在继续之前，告诉用户：「我检测到你实际使用的是 PBL \[当前版本\]，最新版本是 \[目标版本\]。我计划采用 \[直接/分步\] 迁移路径。」

## 阶段 2：文档映射与规划

对你规划的路径中每一次大版本跳跃，你**必须**综合以下来源的说明：

- **[迁移指南](https://developer.android.com/google/play/billing/migrate-gpblv%5BX%5D)**（其中 `[X]` 是目标大版本号）。
- **版本亮点**：相关[版本说明](references/android/google/play/billing/release-notes.md)中的「废弃项」与「破坏性变更」章节。
- **开发者文档**：结合你掌握的 Google Play Billing 文档知识，核对本应用用到的相关功能（例如订阅、一次性商品）。
- **制定计划**：列出所需的每一处具体代码改动（API 移除、类替换、逻辑调整），并打印成检查清单。

## 阶段 3：执行说明

*汇报动作：对下面每个步骤，在执行前简要说明你将要做什么，执行后再简要总结你完成了什么。*

### 步骤 1：SDK 与环境对齐

- **动作**：更新 `build.gradle` 以满足 SDK 要求（例如「PBL 9 要求 `compileSdk` 35」）。
- **Gradle 版本**：确认新库是否需要更新的 Android Gradle Plugin（AGP）或 Kotlin 版本。

### 步骤 2：基于意图的重构

分析现有代码的意图，而不是只做纯文本的字符串替换。

- **动作**：你**必须**同时遵循 [references/migration-logic.md](references/migration-logic.md) 章节中的全部废弃说明与重构模式、官方迁移指南，以及阶段 2 中确定的一般文档页面。
- **验证**：确认你执行了**所有文档中的所有步骤**，并确保遵循了参考资料中检查清单的具体要求。

### 步骤 3：逐步验证（仅适用于分步迁移）

1. **升级**到路径中的第一个中间大版本。
2. **运行 `./gradlew assembleDebug`**，确认没有遗漏中间环节的破坏性变更。
3. **重复**上述过程，直到抵达最终目标版本。

### 步骤 4：最终验证检查清单

1. **智能检查清单验证**：
2. 打开 [references/version-checklist.md](references/version-checklist.md)，找到**按版本区分的智能检查清单**。
3. **动作**：对 \[检测到的实际版本\] 到 \[检测到的新版本\] 之间的每个版本，用「在文件中查找」或结构分析确认每一项都已在代码中处理。
4. **测试**：运行所有单元测试与实现测试（`./gradlew test`）。
5. **干净构建**：确认项目能完成完整的干净构建：`./gradlew clean assembleDebug`。随后运行 `./gradlew sync` 和 `./gradlew build`，以便用户可以立即手动测试新版本。

## 最终报告

向开发者解释「为什么」：

- 「我把你的 SDK 更新到 \[版本\]，因为 PBL \[版本\] 在 \[文档中的原因\] 方面要求如此。」
- 「我移除了你自定义的 `retryConnection()` 逻辑，因为库现在通过 `enableAutoServiceReconnection()` 原生处理了这部分。」
- 「已成功从 PBL \[旧版本\] 升级到 PBL \[新版本\]，并通过单元测试验证。基于对最新库中的功能与本应用当前功能集的分析，我建议试用最新版本中的 \[新功能\]（例如预付方案或分期付款），因为该功能现在已经可用但尚未实现。」
