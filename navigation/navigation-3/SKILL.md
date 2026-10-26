---
name: navigation-3
description: 学习如何安装并迁移到 Jetpack Navigation 3，以及如何实现深链接、多返回栈、场景
  （对话框、底部面板、列表-详情、双栏、辅助栏）、条件导航
  （例如已登录导航与匿名导航）、从 flow 返回结果、与 Hilt、ViewModel、Kotlin 集成，以及 view 互操作
  等特性与模式。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - recipe
  - Android
  - Navigation 2
  - Navigation 3
  - migration
  - Compose
  - guide
  - dependencies
  - NavKey
  - NavHost
  - NavDisplay
  - BottomSheet
  - list-detail
  - scenes
  - two-pane
  - supporting pane
  - multiple backstacks
  - dialog
  - Hilt
  - ViewModel
  - View interop.
---

*** ** * ** ***

## 迁移指南

- *[Navigation 2 到 Navigation 3 迁移指南](references/android/guide/navigation/navigation-3/migration-guide.md)*：把 Android 应用从 Navigation 2 迁移到 Navigation 3 的分步指南，涵盖依赖更新、路由变更、状态管理和 UI 组件替换。

### 要求

- *[指南：在 Compose 中迁移到类型安全导航](references/android/guide/navigation/type-safe-destinations.md)*：把 Android 应用从基于字符串的导航迁移到 Jetpack Compose 中**类型安全导航**（使用 Jetpack Navigation 2）的分步指南。

## 开发者文档

- *[Navigation 3](references/android/guide/navigation/navigation-3/index.md)*。在文档中搜索更多信息：基础用法、保存与管理导航状态、模块化导航代码、使用 Scenes 创建自定义布局、在目的地之间添加动画，或为目的地应用逻辑或包装。

## 示例方案

展示常见模式的代码示例。

### 基础 API 用法

- *[基础](references/android/guide/navigation/navigation-3/recipes/basic.md)*：演示最基本的 API 用法。
- *[可保存的返回栈](references/android/guide/navigation/navigation-3/recipes/basicsaveable.md)*：演示带持久返回栈的基础 API 用法。
- *[Entry provider DSL](references/android/guide/navigation/navigation-3/recipes/basicdsl.md)*：演示使用 entryProvider DSL 的基础 API 用法。

### 通用 UI

- *[通用 UI](references/android/guide/navigation/navigation-3/recipes/common-ui.md)*：演示如何实现带底部导航栏和多个返回栈的常见导航 UI 模式，其中导航栏的每个标签都有自己的导航历史。

### 深链接

- *[静态 URI](references/android/guide/navigation/navigation-3/recipes/deeplinks-staticuri.md)*：演示如何处理简单的静态 URI 深链接。
- *[带参数的 URI](references/android/guide/navigation/navigation-3/recipes/deeplinks-uriarguments.md)*：演示如何从深链接中解析路径参数和查询参数。
- *[合成 BackStack](references/android/guide/navigation/navigation-3/recipes/deeplinks-syntheticbackstack.md)*：演示如何处理带合成返回栈的深链接。
- *[自定义匹配器](references/android/guide/navigation/navigation-3/recipes/deeplinks-custommatcher.md)*：演示如何实现自定义深链接匹配逻辑。

### 场景

#### 使用内置 Scenes

- *[Dialog](references/android/guide/navigation/navigation-3/recipes/dialog.md)*：演示如何创建 Dialog。

#### 创建自定义 Scenes

- *[BottomSheet](references/android/guide/navigation/navigation-3/recipes/bottomsheet.md)*：演示如何创建 BottomSheet 目的地。
- *[列表-详情场景](references/android/guide/navigation/navigation-3/recipes/scenes-listdetail.md)*：演示如何使用 Navigation 3 Scenes API 实现自适应的列表-详情布局。
- *[双栏场景](references/android/guide/navigation/navigation-3/recipes/scenes-twopane.md)*：演示如何使用 Navigation 3 Scenes API 实现自适应的双栏布局。

### Material Adaptive

- *[Material 列表-详情](references/android/guide/navigation/navigation-3/recipes/material-listdetail.md)*：演示如何使用 Material 3 Adaptive 实现自适应的列表-详情布局。
- *[Material 辅助栏](references/android/guide/navigation/navigation-3/recipes/material-supportingpane.md)*：演示如何使用 Material 3 Adaptive 实现自适应的辅助栏布局。

### 动画

- *[动画](references/android/guide/navigation/navigation-3/recipes/animations.md)*：演示如何为所有目的地和单个目的地覆盖默认动画。
- *[条件转场](references/android/guide/navigation/navigation-3/recipes/conditional-transitions.md)*：演示如何实现条件转场动画。

### 常见返回栈行为

- *[多返回栈](references/android/guide/navigation/navigation-3/recipes/multiple-backstacks.md)*：演示如何创建多个顶层路由，每个都有自己的返回栈。顶层路由显示在导航栏中，让用户可以在它们之间切换。每个顶层路由的状态都会保留，导航状态在配置变更和进程死亡后依然存在。

### 条件导航

- *[条件导航](references/android/guide/navigation/navigation-3/recipes/conditional.md)*：满足条件时切换到另一条导航流程。例如用于身份验证或首次使用引导。

### 生命周期

- *[Lifecycle Owner](references/android/guide/navigation/navigation-3/recipes/lifecycle-owner.md)*：演示在 Navigation 3 中如何使用和观察 Lifecycle。

### 架构

- *[模块化导航代码（Hilt）](references/android/guide/navigation/navigation-3/recipes/modular-hilt.md)*：演示如何使用 Hilt 或 Dagger 做依赖注入，把导航代码解耦到独立模块中。
- *[模块化导航代码（Koin）](references/android/guide/navigation/navigation-3/recipes/modular-koin.md)*：演示如何使用 Koin 做依赖注入，把导航代码解耦到独立模块中。

### 配合 ViewModel 使用

#### 传递导航参数

- *[基础 ViewModel](references/android/guide/navigation/navigation-3/recipes/passingarguments.md)*：导航参数会传给用 `viewModel()` 构造的 `ViewModel`

### 返回结果

- *[以事件形式返回结果](references/android/guide/navigation/navigation-3/recipes/results-event.md)*：把结果作为事件返回给另一个 `NavEntry` 中的内容
- *[以状态形式返回结果](references/android/guide/navigation/navigation-3/recipes/results-state.md)*：把结果作为存储在 `CompositionLocal` 中的状态返回
