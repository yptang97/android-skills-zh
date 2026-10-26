---
name: styles
description: 使用这个 skill 把 Jetpack Compose Styles API 集成到 Android 项目中。这个 skill 引导你升级依赖、配置组件主题、让自定义组件支持样式化，并把现有布局属性迁移到统一样式。迁移自定义设计系统组件、把硬编码参数替换为 Style 属性，并使用 Modifier.styleable 处理交互状态。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-20'
  keywords:
  - Jetpack Compose
  - Styles
  - Theming with Styles
  - Migrate to Styles
  - Modifier.styleable
---

## 限制

- 提醒用户这个 skill 是 EXPERIMENTAL（实验性）的，需要升级到 Compose 的 alpha 版本并选用实验性 API。
- 这个 skill 只支持自定义 UI 组件和自定义主题。
- 这个 skill 不支持 Material Design 组件 Styles。

## 前置条件

### 1. 升级依赖

- 项目必须使用 `compileSdk` 版本 37 或更高。
- 项目必须使用 `androidx.compose.foundation:foundation` 版本 `1.12.0-alpha01` 或更高。
- 或者，项目必须使用 Compose BOM 版本 `2026.04.01` 或更高。
- 该 API 要求精确的包名：`import
  androidx.compose.foundation.style.Style`

### 2. 配置编译器选项以启用实验性 API

你必须在项目级别选用该实验性 API。把下面这个代码块添加到模块的 `build.gradle.kts`：

    kotlin {
        compilerOptions {
            jvmTarget = JvmTarget.fromTarget("17")
            freeCompilerArgs.add("-opt-in=androidx.compose.foundation.style.ExperimentalFoundationStyleApi")
        }
    }

## 核心工作流与指南

参考官方文档来完成具体的开发任务：

- 基本 Style 用法：要在组件上设置背景、尺寸和对齐方式，请遵循 [Compose Styles 基础指南](references/android/develop/ui/compose/styles/fundamentals.md)。
- 状态与过渡：要为状态变化（例如按下或悬停）配置属性变更，请遵循 [动画与基于状态的样式指南](references/android/develop/ui/compose/styles/state-animations.md)。
- 架构取舍：要判断何时使用 Style 而不是标准 Modifier，请遵循 [Styles 与 Modifiers 对比](references/android/develop/ui/compose/styles/styles-vs-modifiers.md)。
- 主题级集成：要把样式定义与自定义主题关联起来，请遵循 [使用 Styles 构建主题](references/android/develop/ui/compose/styles/theming.md) 和 [Compose 中的自定义主题](references/android/develop/ui/compose/designsystems/custom.md)。

## 分步迁移工作流

### 步骤 1：分析主题结构

1. 找到你的中心主题文件（例如 `Theme.kt`）。
2. 识别设计令牌。记录颜色、排版和形状的引用（例如 `LocalColorScheme`、`LocalTypography` 或 `LocalShapes`）。
3. 如果项目缺少 Jetpack Compose 依赖，就停下来。先指示用户迁移到 Jetpack Compose。
4. 如果项目导入了 `androidx.compose.material.MaterialTheme`，建议在继续之前先迁移到 Material 3。

### 步骤 2：建立 `ComponentStyles`

1. 在主题目录中新建一个名为 `ComponentStyles.kt` 的文件。
2. 定义一个顶层 data class 来存放组件样式，例如 Jetsnack 的那一个叫 `JetsnackStyles`：


   ```kotlin
   object ExampleComponentStyles {
       val customButtonStyle: Style = {

       }
       val customTextFieldStyle: Style = {

       }
   }
   ```

   <br />

3. 通过自定义主题以静态引用的方式暴露这个类，这里不要用 `CompositionLocals`，因为并不需要。


   ```kotlin
   @Immutable
   class JetsnackTheme(
       // other Design system properties
   ) {
       companion object {
           val colors: CustomThemingWithStyles.JetsnackColors
               @Composable @ReadOnlyComposable
               get() = LocalJetsnackTheme.current.colors
           // ...

           // add helper static reference
           val styles: ComponentStyles = ComponentStyles
       }
   }
   ```

   <br />

4. 如果主题令牌是通过 `CompositionLocals` 暴露的，就在 `StyleScope` 上提供扩展来直接引用它们。例如：


   ```kotlin
   val StyleScope.colors: JetsnackColors
       get() = LocalJetsnackTheme.currentValue.colors

   val StyleScope.typography: androidx.compose.material3.Typography
       get() = LocalJetsnackTheme.currentValue.typography

   val StyleScope.shapes: Shapes
       get() = LocalJetsnackTheme.currentValue.shapes
   ```

   <br />

### 步骤 3：把组件迁移到 Styles API

对每个自定义组件（例如 `CustomButton`），按以下顺序完成操作：

1. **建立视觉基线（如果有可用的模拟器）：**
   - **如果你无法运行 Android 模拟器：** 完全跳过这一步，直接进入步骤 2。
   - **如果你可以运行 Android 模拟器：** 执行以下操作来截取基线截图：
     - **方案 A：** 找到并运行该组件已有的截图测试。
     - **方案 B（如果没有现成测试）：** 使用项目已有的测试框架创建一个测试，然后运行它。
     - **方案 C（如果没有测试框架）：** 使用 UI Automator 或 Espresso 创建一个最小化的截图测试，然后运行它。
2. **移除各自的样式参数**：从签名中移除 `backgroundColor`、`shape`、`textStyle` 和 `contentPadding` 这类样式参数，也就是 `StyleScope` 支持的所有内容。
3. **添加 style 参数**：在函数签名中添加 `style: Style = Style`。始终确保默认值精确为 `Style`（例如 `style:
   Style = Style`），而不是 `ChipStyleDefault` 之类的具体样式默认值或任何其他值。
4. **声明状态跟踪**：如果组件可交互，就使用 interaction source 创建 `MutableStyleState`。在 Composable 内部更新状态字段（例如 `isEnabled`），以正确跟踪状态。
5. **应用 styleable 修饰符**：把根元素上具体的布局修饰符替换为 `Modifier.styleable()`。
6. **把默认值移到 ComponentStyles**：把组件定义中的硬编码值移到 `ComponentStyles.kt` 中专门的 `Style` 实例。
7. **验证组件：** 把开始时截取的基线截图与新 composable 渲染出的 Compose Preview 做对比。忽略字符串内容，专注于布局和样式。反复调整 Compose 代码，直到视觉一致。验证通过后，为新 composable 编写一个 Compose UI 测试。

#### 迁移示例

迁移前：


```kotlin
@Composable
fun CustomButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    backgroundColor: Color = JetsnackTheme.colors.brandLight,
    disabledBackgroundColor: Color = JetsnackTheme.colors.brandSecondary,
    shape: Shape = JetsnackTheme.shapes.extraLarge,
    textStyle: TextStyle = JetsnackTheme.typography.labelLarge,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) {
    val interactionSource = remember { MutableInteractionSource() }
    Row(
        modifier
            .clickable(onClick = onClick, indication = null, interactionSource = interactionSource)
            .background(if (enabled) backgroundColor else disabledBackgroundColor, shape)
            .defaultMinSize(58.dp, 40.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
        content = content,
    )
}
```

<br />

迁移后：


```kotlin
// Exposed via ComponentStyles.kt
object ComponentStyles {
    val buttonStyle = Style {
        background(colors.brandLight)
        shape(shapes.extraLarge)
        minWidth(58.dp)
        minHeight(40.dp)
        textStyle(typography.labelLarge)
        disabled {
            background(colors.brandSecondary)
        }
    }
}

@Composable
fun CustomButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    style: Style = Style,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val styleState = rememberUpdatedStyleState(interactionSource) {
        it.isEnabled = enabled
    }
    Row(
        modifier
            .clickable(onClick = onClick, indication = null, interactionSource = interactionSource)
            .styleable(styleState, JetsnackTheme.styles.buttonStyle, style),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
        content = content,
    )
}
```

<br />

### 步骤 4：验证改动

1. 构建项目。确认没有编译错误。
2. 运行模块的截图测试。
3. 对比改动前后组件的整个应用的视觉输出。确认没有出现视觉布局回归。
