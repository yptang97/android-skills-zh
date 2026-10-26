---
name: testing-setup
description: 分析并制定 Android 应用的测试策略：安装测试库、搭建测试基础设施，
  为单元测试、UI 测试、截图测试和端到端测试创建测试骨架。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-30'
  keywords:
  - android
  - testing
  - ui tests
  - screenshot tests
  - coverage
---

## 步骤 1：分析当前的测试配置

要了解现有项目的测试配置，请在 libs.versions.toml 文件或构建文件中查找这些依赖：

1. 使用的依赖注入框架。例如 Hilt、Koin、Anvil 或原生 Dagger。
2. 本项目使用的单元（本地）测试框架。例如 JUnit4 或 JUnit5。
3. 用于单元测试，以及 instrumented 测试和 UI 测试的 Mock 框架（如果有）。例如 Mockito 或 Mockk。
4. Robolectric。判断下列三种用法中哪些适用：
   1. 在单元测试中使用，为平台实体提供 fake
   2. 在没有设备或模拟器的情况下运行行为 UI 测试。例如用于运行 Espresso 或 Compose 测试。
   3. 配合 Roborazzi 做截图测试
5. 应用是 100% Compose、Views 还是混合？
6. 行为 UI 测试：
   1. Compose 测试（`androidx.compose.ui:ui-test-*`）
   2. 针对 Views 的 Espresso 测试。检查是否有 Kaspresso 这类封装。依赖：`androidx.test.espresso:espresso-core`、`androidx.test:runner`、`androidx.test:rules`。
7. 截图测试。判断项目使用下列哪种类型：
   1. Instrumented（基于设备）。例如使用 Dropshots。
   2. 基于 Robolectric，因此在本地运行。例如使用 Roborazzi。
   3. 基于 LayoutLib，因此在本地运行。例如 Paparazzi，或 Compose Preview Screenshot Testing 工具。
8. 端到端测试（也称 Release Candidate 测试）始终在设备上运行，使用 UIAutomator、Appium 或 Robotium 这类高层框架。
9. 生成一份包含分析结果的 Markdown 报告

## 步骤 2：为测试配置依赖注入框架

如果没有依赖注入框架，就安装一个：如果是多平台应用，询问用户想安装 Koin 还是
kotlin-inject。如果不是多平台，安装 Hilt。

安装测试依赖（例如 `com.google.dagger:hilt-compiler`
应配合 `kspAndroidTest` 配置应用）。

> [!IMPORTANT]
> **重要：** 始终查阅适用框架的文档来了解测试（例如：[Hilt 测试指南](references/android/training/dependency-injection/hilt-testing.md)、[Koin instrumented 测试](https://insert-koin.io/docs/reference/koin-android/instrumented-testing)）。

对于 instrumented 测试，创建并配置（在 build gradle 文件中添加
`testInstrumentationRunner`）一个新的测试 runner，并应用框架要求的测试规则（例如在 Hilt 中，用
`@HiltAndroidTest` 注解测试类并应用 `HiltAndroidRule`）。
其他框架使用其他机制，请查阅它们的文档。

## 步骤 3：安装框架

除非另有说明，沿用当前的测试框架栈。

如果没有测试框架，且用户没有指定任何偏好，安装以下内容：

- JUnit4，用于本地和 instrumented 测试
- Jacoco，用于测试覆盖率
- UI 测试：如果项目使用 views，用 Espresso。如果完全用 Compose，用 Compose Testing API。
- Robolectric，用于运行 UI 测试
- Compose Preview Screenshot Testing 工具，用于截图测试。先检查
  项目的 AGP 版本，然后选择匹配的配置并严格遵守：

  - **AGP 9.5.0-alpha03 或更高版本（推荐）：** 用 `testOptions { screenshotTests.create(...) }` 配置 AGP 测试套件，如[使用测试套件做截图测试](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)所述。
  - **较低的 AGP 版本：** 使用[旧式独立插件配置](references/android/studio/preview/compose-screenshot-testing.md)搭配 `com.android.compose.screenshot`，并告知用户该方式已废弃。不要在配置截图测试的过程中升级 AGP。说明测试套件在 9.5.0-alpha03 或更高版本才可用，把升级留作单独的决定。

  不要在同一模块里混用两种配置。如果项目已经在用独立插件，且其 AGP 版本支持测试套件，
  可以提议用[使用测试套件做截图测试](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)中的任务与路径映射表进行迁移。
- Dropshots，用于设备上的截图测试

- 如果确实需要 Mock 框架，安装 Mockk（`io.mockk:mockk`）。除非明确需要，
  否则不要安装。

如果要求 instrumented 截图测试，安装 Dropshots。

如果要求端到端测试，安装 UI Automator。

## 步骤 4：重构并为测试创建 fake

### **为单元测试重构**

接下来的小节会要求你创建测试。如果你依赖 Android 框架类，或不在代码库中的实体：

- 首先使用 fake。如果不存在，为该类创建一个接口，并用现有代码写一个「Default」实现。把 Fake 版本
  加到测试 sourceset（test 或 androidTest）。

- 如果无法使用 fake（例如无法访问该类或接口），就 mock 这些依赖。

### **为 UI 测试重构**

如果你需要 fake 组件来让测试更简单、更快、更可靠，就用 fake 替换慢或有问题的依赖。使用已安装的
依赖注入框架提供运行时 fake，以便：

- 与用户（错误凭据或密码重置流程）、与服务器（无连接、服务器宕机或服务器返回错误 JSON）或与平台组件（权限不足、磁盘空间不足、没有可用前置摄像头）**模拟**不同场景
- **改善**速度和可靠性（用内存数据库替换数据库，用内存 fake 替换仓库以避免访问网络）

## 步骤 5：单元测试

为每个包含业务逻辑的文件创建添加或审查单元测试的任务（ViewModels、Repositories，以及 DAO
这类与数据库相关的类）。不要为 Activity、Compose 布局或依赖注入配置文件创建单元测试。

## 步骤 6：UI 测试

Espresso 或 Compose UI 测试放在 `test` sourceset，因为它们会用 Robolectric 运行。如果要求
instrumented（模拟器或设备）测试，把它们放在 `androidTest` sourceset。

## 步骤 7：测试数据库

如果数据库使用 SQLite（通过 Room 或 SQLDelight 这类库），用内存数据库创建 instrumented 测试，
确保它们在设备上与 SQLite 引擎配合正常。

## 步骤 8：截图测试

无论使用哪个框架，截图测试都聚焦两类测试：

- 屏幕级截图测试：每个屏幕在九种不同尺寸下测试，组合 compact、medium 和 expanded 宽度（400、610、900 dp）与高度（400、500 和 1000 dp）。
- 屏幕级变体。添加以下内容的移动端（400x500）截图：
  - 所有备选主题（如果使用）。
  - 字体缩放设为 1.5。
- 组件级截图测试：每个组件在不同主题和字体缩放下测试。

截图不测试行为，但如果常见场景的 UI 会随状态大幅变化，就要测试这些场景。例如通过向 UI 注入加载状态
或用 fake 模拟来测试加载屏幕。

## 步骤 9：UI 行为测试

用行为测试检查 UI 逻辑，确保 UI 在不同状态被传入、以及用户执行操作时按预期响应。

### **Compose UI 行为测试**

- 使用带 `ComponentActivity` 的 ComposeTestRule 访问字符串这类资源。
- 始终先用语义匹配器匹配。如果匹配器太复杂（查找单个元素要用三个以上匹配器），就用 `testTag`。
- 始终验证状态恢复。

### **Views（XML）UI 行为测试**

用 Espresso 匹配视图并与它们交互。

## 步骤 10：导航测试

创建一个测试套件来验证导航逻辑。包含：

- 返回处理
- 深链接
- 多返回栈下「通过 home 退出」这类特殊模式。

## 步骤 11：模拟不同的窗口尺寸和设置

对于 Compose 布局，使用「[UI 测试常用模式](references/android/develop/ui/compose/testing/common-patterns.md)」中介绍的 `DeviceConfigurationOverride` 来模拟不同窗口尺寸和字体缩放

## 步骤 12：端到端测试

创建少量（约占全部测试的 5%）覆盖大型用户旅程的端到端测试。用 Compose Test API 或 Espresso 编写。如果
必须访问通知或系统 UI 这类平台功能，使用 UI Automator。

如果需要截取在设备上运行的应用的截图，使用
[Dropshots](https://raw.githubusercontent.com/dropbox/dropshots/refs/heads/main/README.md)。验证与系统 UI 的交互时（例如 edge-to-edge 渲染、通知、画中画），截图测试需要真机

### 步骤 13：instrumented 截图测试

在模块中安装 `com.dropbox.dropshots` 插件和一个 `Dropshots()`
JUnit Rule。为应用的某个功能创建一个新的 instrumented 截图测试。

### 步骤 14：安装 jacoco

安装 jacoco 以获取本地测试的代码覆盖率。

- 为每个包含测试的模块添加 `jacoco` 插件。

## 收尾

- 询问是否需要记录分析结论和对测试策略所做的改动。如果用户同意：

  - 如果项目中存在 AGENTS.md 文件，把你对测试策略所做的改动更新进去。

  - 如果没有 AGENTS.md 文件，新建一个文件（docs/testing.md），描述测试策略，包括运行每种测试
    所需的命令以及截图参考文件的位置。
    同时在根目录新建 AGENTS.md 文件，并链接到 docs/testing.md。
