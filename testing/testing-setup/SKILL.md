---
name: testing-setup
description: 分析并制定 Android 应用的测试策略——安装测试库、搭建测试基础设施、创建单元测试、UI 测试、截图测试和端到端测试所需的 harness。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-28'
  keywords:
  - android
  - testing
  - ui tests
  - screenshot tests
  - coverage
---

## 步骤 1：分析当前测试配置

要了解现有项目的测试配置，在 libs.versions.toml 文件或构建文件中查找这些依赖：

1. 使用的依赖注入框架。例如 Hilt、Koin、Anvil 或原生 Dagger。
2. 这个项目使用的单元（本地）测试框架。例如 JUnit4 或 JUnit5。
3. 单元测试、instrumented 测试和 UI 测试所用的 mocking 框架（如果有）。例如 Mockito 或 Mockk。
4. Robolectric。判断以下三种用途中哪些适用：
   1. 在单元测试中使用，为平台实体提供 fake
   2. 在没有设备或模拟器的情况下运行行为 UI 测试。例如用于运行 Espresso 或 Compose 测试。
   3. 使用 Roborazzi 做截图测试
5. 应用是 100% Compose、Views 还是混合？
6. 行为 UI 测试：
   1. Compose 测试（`androidx.compose.ui:ui-test-*`）
   2. Views 的 Espresso 测试。检查是否有 Kaspresso 之类的封装。依赖：`androidx.test.espresso:espresso-core`、`androidx.test:runner`、`androidx.test:rules`。
7. 截图测试。判断项目使用以下哪种类型：
   1. Instrumented（基于设备）。例如使用 Dropshots。
   2. 基于 Robolectric，因此本地运行。例如使用 Roborazzi。
   3. 基于 LayoutLib，因此本地运行。例如 Paparazzi，或 Compose Preview Screenshot Testing 工具。
8. 端到端测试（也称为 Release Candidate 测试）始终在设备上运行，并使用 UIAutomator、Appium 或 Robotium 等高层框架。
9. 生成一份包含分析结果的 Markdown 报告

## 步骤 2：为测试配置依赖注入框架

如果没有依赖注入框架，就安装一个：如果是多平台应用，询问用户想装 Koin 还是 kotlin-inject。如果不是多平台，就安装 Hilt。

安装测试相关依赖（例如 `com.google.dagger:hilt-compiler`，应通过 `kspAndroidTest` 配置应用）。

> [!IMPORTANT]
> **重要：** 始终查阅适用框架的文档来了解测试方式（例如：[Hilt testing guide](references/android/training/dependency-injection/hilt-testing.md)、[Koin Instrumented tests](https://insert-koin.io/docs/reference/koin-android/instrumented-testing)）。

对于 instrumented 测试，创建并配置一个新的 test runner（在构建 gradle 文件中添加 `testInstrumentationRunner`），并应用框架要求的测试规则（例如在 Hilt 中，用 `@HiltAndroidTest` 注解测试类并应用 `HiltAndroidRule`）。其他框架使用其他机制，查阅它们的文档。

## 步骤 3：安装框架

除非另有说明，遵循当前已有的测试框架栈。

如果没有测试框架，且用户没有指定偏好，就安装以下内容：

- JUnit4，用于本地测试和 instrumented 测试
- JaCoCo，用于测试覆盖率
- UI 测试：如果项目使用 views，用 Espresso。如果完全是 Compose，用 Compose Testing APIs。
- Robolectric，用于运行 UI 测试
- Compose Preview Screenshot Testing 工具，用于截图测试。先检查项目的 AGP 版本，再选择匹配的配置方式并严格遵循：

  - **AGP 9.5.0-alpha03 或更高版本（推荐）：** 使用 `testOptions { screenshotTests.create(...) }` 配置 AGP test suite，具体见[使用 test suite 做截图测试](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)。
  - **较低的 AGP 版本：** 使用 `com.android.compose.screenshot` 搭配[旧版独立插件配置](references/android/studio/preview/compose-screenshot-testing.md)，并告知用户该方式已废弃。不要在配置截图测试的过程中升级 AGP。说明 test suite 在 9.5.0-alpha03 或更高版本可用，把升级留作单独的决定。

  不要在同一个模块中同时使用两种配置方式。如果项目已经在用独立插件，而其 AGP 版本支持 test suite，就用[使用 test suite 做截图测试](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)中的任务与路径映射表，提议迁移。
- Dropshots，用于设备截图测试

- 如果确实需要 mocking 框架，安装 Mockk（`io.mockk:mockk`）。除非明显必要，否则不要安装。

如果要求做 instrumented 截图测试，安装 Dropshots。

如果要求做端到端测试，安装 UI Automator。

## 步骤 4：重构并为测试创建 fake

### **为单元测试做重构**

接下来的章节会要求你编写测试。如果存在对 Android framework 类的依赖，或依赖的实体不属于代码库：

- 首先使用 fake。如果不存在，就为该类创建接口，并用现有代码写一个「Default」实现。把 Fake 版本加到测试源集（test 或 androidTest）。

- 如果无法使用 fake（例如无法访问该类或接口），就对依赖做 mock。

### **为 UI 测试做重构**

如果你需要伪造组件，让测试更简单、更快、更可靠，就用 fake 替换缓慢且有问题的依赖。使用已安装的依赖注入框架来做运行时 fake，以：

- **模拟**不同场景：与用户相关的（凭据错误或重置密码流程）、与服务器相关的（无连接、服务器宕机或服务器返回错误 JSON）或与平台组件相关的（权限不足、磁盘空间不足、无前置摄像头）
- **提升**速度和可靠性（用内存数据库替换数据库，用内存 fake 替换仓库以避免访问网络）

## 步骤 5：单元测试

创建一个任务，为每个包含业务逻辑的文件（ViewModel、Repository，以及 DAO 这类数据库相关类）添加或审查单元测试。不要为 Activity、Compose 布局或依赖注入配置文件编写单元测试。

## 步骤 6：UI 测试

Espresso 或 Compose UI 测试放在 `test` 源集中，因为它们会用 Robolectric 运行。如果要求做 instrumented（模拟器或设备）测试，就把它们放在 `androidTest` 源集中。

## 步骤 7：测试数据库

如果数据库使用 SQLite（通过 Room 或 SQLDelight 之类的库），就用内存数据库编写 instrumented 测试，确保它们在设备的 SQLite 引擎上能正常工作。

## 步骤 8：截图测试

无论使用哪个框架，截图测试都聚焦两类测试：

- 屏幕级截图测试，每个屏幕在九种不同尺寸下测试，组合紧凑、中等和扩展宽度（400、610、900 dp）与高度（400、500 和 1000 dp）。
- 屏幕级变体。添加一张移动端（400x500）截图：
  - 所有备选主题（如果使用了）。
  - 字体缩放设置为 1.5。
- 组件级截图测试，每个组件在不同主题和字体缩放下测试。

截图不测试行为，但如果某些常见场景的 UI 会随状态大幅变化，就要测试它们。例如，通过向 UI 注入加载状态或用 fake 模拟加载状态，来测试加载页面。

## 步骤 9：UI 行为测试

用行为测试测试 UI 逻辑，确保 UI 在传入不同状态、以及执行用户操作时按预期响应。

### **Compose UI 行为测试**

- 使用带 `ComponentActivity` 的 ComposeTestRule 来访问字符串之类的资源。
- 始终优先使用语义匹配器。如果匹配器写起来太复杂（查找单个元素用了三个以上匹配器），就使用 `testTag`。
- 始终验证状态恢复。

### **Views（XML）UI 行为测试**

使用 Espresso 匹配视图并与它们交互。

## 步骤 10：导航测试

创建一个测试套件来验证导航逻辑。包含：

- 返回处理
- 深链接
- 「从主页退出」这类带多个返回栈的特殊模式。

## 步骤 11：模拟不同的窗口尺寸和设置

对于 Compose 布局，使用「[UI 测试常见模式](references/android/develop/ui/compose/testing/common-patterns.md)」中描述的 `DeviceConfigurationOverride` 来模拟不同的窗口尺寸和字体缩放

## 步骤 12：端到端测试

编写少量（约占所有测试的 5%）端到端测试，覆盖重要的用户旅程。用 Compose Test API 或 Espresso 来实现。如果必须访问通知或系统 UI 等平台特性，就使用 UI Automator。

如果你需要截取应用在设备上运行的屏幕，使用 [Dropshots](https://raw.githubusercontent.com/dropbox/dropshots/refs/heads/main/README.md)。在验证与系统 UI 的交互（例如 edge-to-edge 渲染、通知、画中画）时，截图测试需要设备。

## 步骤 13：插桩式截图测试

在模块中安装 `com.dropbox.dropshots` 插件和一个 `Dropshots()` JUnit Rule。为应用的某个功能编写一个新的 instrumented 截图测试。

## 步骤 14：安装 JaCoCo

安装 JaCoCo，用于本地测试代码覆盖率。

- 为每个包含测试的模块添加 `jacoco` 插件。

## 收尾

- 询问是否要把分析结论和对测试策略所做的改动记录下来。如果用户同意：

  - 如果项目中存在 AGENTS.md 文件，就用你对测试策略所做的改动更新它。

  - 如果没有 AGENTS.md 文件，就新建一个文件（docs/testing.md），描述测试策略，包括运行各类测试所需的命令，以及截图基准文件所在的位置。同时在根目录新建 AGENTS.md 文件，并添加指向 docs/testing.md 的链接。
