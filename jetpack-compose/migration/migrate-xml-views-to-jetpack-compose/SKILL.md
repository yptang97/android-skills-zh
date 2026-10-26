---
name: migrate-xml-views-to-jetpack-compose
description: 提供把 Android XML View 迁移到 Jetpack Compose 的结构化工作流。这个 skill 详述从规划、依赖配置，到主题与布局迁移、验证和 XML 清理的逐步流程。当你需要在 Android 项目中把 XML View 迁移到 Jetpack Compose 时使用这个 skill。它解决的问题是把旧式 XML View 的 UI 转换为现代、声明式的 Compose 组件，同时保持互操作性。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-18'
  keywords:
  - Jetpack Compose
  - migration
  - XML
  - Views
  - interoperability
  - incremental adoption
  - UI development
---

这个 skill 指导把现有 Android XML View 迁移到 Jetpack Compose 的过程。它遵循结构化的 10 步方法，完成稳定、安全且视觉一致的过渡。这个 skill 只迁移 UI（XML 到 Jetpack Compose）。

## 目标

系统性地把单个旧式 XML 布局转换为现代、声明式的 Jetpack Compose UI，同时保持像素级视觉一致和功能完整性。

## 10 步迁移流程概要

1. **确定最合适的待迁移 XML 候选**
2. **分析项目与布局**
3. **制定计划**
4. **捕获 XML View 的 UI**
5. **配置 Compose 依赖与编译器**
6. **配置 Compose 主题**
7. **把 XML 布局迁移到 Compose**
8. **验证迁移结果**
9. **替换使用处**
10. **移除 XML 代码**

## 详细步骤

### 步骤 1：确定最合适的待迁移 XML 候选

如果用户已明确指定目标 XML 布局，直接进入步骤 2。否则，按 [references/identify-optimal-xml-candidate.md](references/identify-optimal-xml-candidate.md) 中的逻辑分析代码库，找出最合适的迁移候选。

### 步骤 2：分析项目与布局

分析所确定 XML View 的结构、层级和实现细节。使用 [references/analysis-of-the-project-and-layout.md](references/analysis-of-the-project-and-layout.md) 指导你对布局及周边项目上下文做技术审查。

### 步骤 3：制定计划

使用步骤 1 和步骤 2 的产出与分析，生成一份分步迁移计划。如果你支持用户交互，就展示给用户并在继续之前请求批准。如果不支持用户交互，就按生成的计划进入步骤 4。

### 步骤 4：捕获 XML View 的 UI

**如果**你支持用户交互，请用户上传 XML View UI 的截图，或提供文件的绝对路径。在步骤 7 的布局迁移中，把这张图片作为视觉参照。
**否则如果**你能运行 Android 模拟器，就为这个 XML 候选查找已有的截图测试。如果没有，用项目已有的测试框架创建一个。如果没有任何框架，就用 **UI Automator** 或 **Espresso** 以最小必要配置创建截图测试。运行测试并截取 XML UI 的基线截图。
**否则**进入步骤 5。

### 步骤 5：配置 Compose 依赖与编译器

检查 `build.gradle` 或 `libs.versions.toml` 中的 Compose 依赖和编译器配置。如果缺失，参照[配置 Compose 依赖与编译器](references/android/develop/ui/compose/setup-compose-dependencies-and-compiler.md)。运行一次 sync，确保依赖能无错解析。

### 步骤 6：配置 Compose 主题

如果项目已经配置好 Compose 主题，直接进入步骤 7。如果缺少 Compose 主题，就初始化它。对于基于 Material 的项目，遵循 [Material 3 迁移指南](references/android/develop/ui/compose/designsystems/migrate-xml-theme-to-compose.md)。对于自定义设计系统，运用专业判断迁移 XML 主题并匹配现有样式。
**约束：** 不要迁移整个主题。只实现这个特定 XML 候选所需的最小主题内容。为保持互操作性，保留原有 XML 主题。保持项目既有的代码约定、模式、命名和值。

### 步骤 7：把 XML View 迁移到 Compose

把 XML 候选转换为 Jetpack Compose 代码，参照 [references/xml-layout-migration.md](references/xml-layout-migration.md) 和步骤 4 的图片。你必须为新创建的 composable 加上 **Compose Preview**，以便做视觉验证。

### 步骤 8：替换使用处

把已迁移 XML 布局的使用处改为使用新的 Compose 组件。

- 要在 View 中加入 Compose，使用 [View 中的 Compose](references/android/develop/ui/compose/migrate/interoperability-apis/compose-in-views.md)。
- 要在 Compose 中加入 View，使用 [Compose 中的 View](references/android/develop/ui/compose/migrate/interoperability-apis/views-in-compose.md)。

### 步骤 9：验证迁移结果

把步骤 4 的基线截图与新 composable 渲染出的 Compose Preview 做对比。忽略字符串内容，专注于布局和样式。反复调整 Compose 代码，直到达到视觉一致。验证通过后，为新 composable 编写 Compose UI 测试。

### 步骤 10：移除 XML 代码

删除已迁移的 XML 文件及其关联的旧式测试。**注意：** 只移除没有被项目其他部分引用的代码和资源。
