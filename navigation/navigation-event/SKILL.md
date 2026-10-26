---
name: navigation-event
description: 在 Compose Android 中使用 NavigationEvent（androidx.navigationevent）库拦截返回手势
  并运行 Predictive Back 动画。涵盖 Activity 配置、`ViewPagers` 或标签页中的父子 dispatcher
  作用域、Compose 的 `NavigationBackHandler`，以及 SDK 36+ 上从旧 `BackHandler` 的迁移。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-07'
  keywords:
  - Android
  - Navigation Event
  - Jetpack Compose
  - Back Navigation
  - Dispatcher
  - Guidelines
  - Troubleshooting
  - ComponentActivity
  - Dialog
  - ViewPager
---

## 通用指南

- **关于架构概念**：如需了解 Navigation Event 库的基础架构、连续手势事件生命周期或类定义，请阅读 [Navigation Event 概览](references/android/guide/navigation/navigation-event/index.md)。
- **关于 Android 目标平台**：如果 compile SDK 低于 36，请在 `build.gradle.kts` 中设为 `36` 或更高。
- **关于 Compose Android 目标平台**：项目必须使用 Jetpack Compose，才能用到 Compose 专属 API。这个 skill 仅覆盖 Compose Android（不包含 Android Views 和非 Compose 实现）。
- **关于 activity dispatcher**：`ComponentActivity` 开箱即自动实现 `NavigationEventDispatcherOwner`。你必须使用内置的 `navigationEventDispatcher`，不要创建匿名 delegate owner，也不要覆盖成员属性。
- **关于 dialog 作用域**：浮动窗口（Compose `Dialog`、`ModalBottomSheet`、`ComponentDialog`）会自动提供 `NavigationEventDispatcherOwner`。dialog 不需要你手动做 `CompositionLocalProvider` 传播。
- **关于父子 dispatcher 层级**：在 Compose 中把导航处理限定到 `ViewPagers`、标签页界面或嵌套导航容器时，使用 `rememberNavigationEventDispatcherOwner()` 创建关联到父级的子 owner。禁用该 owner（`enabled = false`）会自动级联禁用所有子 handler。
- **关于 Compose handler**：`NavigationEventState` 与 handler 之间强制一对一关系。绝不要把同一个 `NavigationEventState` 绑定到多个活跃的 `NavigationBackHandler` 实例（会抛出 `IllegalArgumentException`）。

## 步骤 1：规划

要完成这一步，你 **必须** 确保以下事项：

1. **确认目标平台**：确认应用面向 Compose Android。如果 `compileSdk` 低于 36，请在 `build.gradle.kts` 中设为 `36` 或更高。
2. **导航检查**：检查是否在用 Navigation 3。如果已在使用，请使用 Navigation 3 内置的返回导航支持，而不要手动实现本 skill 中的底层 dispatcher。
3. **层级检查**：找出需要拦截返回手势、或需要父子 dispatcher 关联的宿主 Activity、`ViewPagers`、标签页界面或嵌套导航宿主。
4. **迁移检查**：检查项目是否正在从旧的返回处理方式（`OnBackPressedCallback`、`BackHandler`、`onBackPresser`）迁移到 `NavigationEvent` 和 `NavigationBackHandler`。
5. **输入拦截**：找出应用在何处拦截来自手势或硬件按键、且需要转换为 `NavigationEvent` 的导航事件。

## 步骤 2：配置依赖

要完成这一步，你 **必须** 确保以下事项：

- 关于配置 compile SDK、声明版本目录条目和添加依赖，请遵循 [配置指南](references/android/guide/navigation/navigation-event/setup.md)。

## 步骤 3：配置 dispatcher 与输入

要完成这一步，你 **必须** 确保以下事项：

- 要配置 dispatcher，请利用 `ComponentActivity` 或 `ComponentDialog` 的 owner 自动解析。
- 在 Compose 中按 [dispatcher 指南](references/android/guide/navigation/navigation-event/dispatcher.md) 关联父子 dispatcher。

## 步骤 4：处理返回导航与 UI 过渡

要完成这一步，你 **必须** 确保以下事项：

- 要创建导航事件处理程序、在 Compose 中集成返回手势拦截、在滑动过程中为 UI 组件添加动画，并从旧的 back handler 迁移，请遵循 [处理返回指南](references/android/guide/navigation/navigation-event/handle-back.md)。

## 步骤 5：清理资源

> [!WARNING]
> **警告：** Compose API 会自动执行清理。使用 `NavigationBackHandler` 和 `rememberNavigationEventDispatcherOwner()` 这类 Compose API 时，handler 移除与 dispatcher 销毁会在 composable 离开组合时自动发生。

只有在管理自定义 dispatcher 或非 Compose handler 时，你 **必须** 执行显式的手动清理：

- 在清理时对活跃的 handler 调用 `remove()`。
- 调用 `isEnabled = false` 来临时禁用导航子树。
- 在承载组件销毁时对 dispatcher 实例调用 `dispose()`。销毁父 dispatcher 会自动级联到所有子 dispatcher。

## 核心故障排查指南

### 1. Activity dispatcher 配置（StackOverflowError 递归）

`ComponentActivity` 开箱即自动实现 `NavigationEventDispatcherOwner`。不要覆盖
`navigationEventDispatcher`，也不要把它包进匿名 delegate owner。

#### 正确

**为什么这是正确的**：Compose 应用使用 `ComponentActivity` 作为宿主。
`LocalNavigationEventDispatcherOwner.current` 会自动解析 Activity 内置的 dispatcher。


```kotlin
// RIGHT
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationContent()
        }
    }
}
```

<br />

#### 错误

**为什么这是错误的**：在 `MainActivity` 上直接实现 `NavigationEventDispatcherOwner`，并用新
实例覆盖 `navigationEventDispatcher`，会遮蔽库的扩展属性，导致启动时因无限递归而崩溃
（`StackOverflowError`）。创建多余的匿名 delegate owner
（`object : NavigationEventDispatcherOwner`）是不必要的。


```kotlin
// WRONG
class MainActivity : ComponentActivity(), NavigationEventDispatcherOwner {
    override val navigationEventDispatcher = NavigationEventDispatcher() // Shadow loop crash
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationContent()
        }
    }
}
```

<br />

### 2. 浮动窗口与 dialog 作用域（自动的 ComponentDialog owner）

浮动窗口（Compose `Dialog`、`ModalBottomSheet`，以及任何由 `ComponentDialog` 承载的窗口）会
自动提供 `NavigationEventDispatcherOwner`。不要在 dialog 内用 `CompositionLocalProvider`
手动重新提供 `LocalNavigationEventDispatcherOwner`。

#### 正确

**为什么这是正确的**：`ComponentDialog` 会自动处理导航 dispatcher。Compose `Dialog` 组件
开箱即会解析自己的 dispatcher owner，无需手动传播。


```kotlin
// RIGHT
@Composable
fun MyDialog(onDismiss: () -> Unit) {
    Dialog(onDismissRequest = onDismiss) {
        val navigationState = rememberNavigationEventState(currentInfo = NavigationEventInfo.None)
        NavigationBackHandler(
            state = navigationState,
            onBackCompleted = onDismiss
        )
    }
}
```

<br />

#### 错误

**为什么这是错误的**：用手动 `CompositionLocalProvider` 包裹 dialog 内容会产生多余的样板
代码，并掩盖 `ComponentDialog` 提供的自动 dispatcher 解析。


```kotlin
// WRONG
@Composable
fun MyDialog(onDismiss: () -> Unit) {
    val dispatcherOwner = LocalNavigationEventDispatcherOwner.current!!
    Dialog(onDismissRequest = onDismiss) {
        // Redundant: ComponentDialog provides NavigationEventDispatcherOwner automatically
        CompositionLocalProvider( LocalNavigationEventDispatcherOwner provides dispatcherOwner) {
            val navigationState = rememberNavigationEventState(currentInfo = NavigationEventInfo.None)
            NavigationBackHandler(
                state = navigationState,
                onBackCompleted = onDismiss
            )
        }
    }
}
```

<br />

### 3. 父子 dispatcher 层级（`ViewPagers` 与嵌套导航）

在 Compose 中管理 `ViewPagers`、标签页界面或自定义导航容器这类嵌套 UI 层级时，使用
`rememberNavigationEventDispatcherOwner()` 创建关联到组合层级的子 owner。在子 owner 上设置
`enabled = false` 会自动禁用其 dispatcher 和所有已注册的子 handler。

#### 正确

**为什么这是正确的**：使用 `rememberNavigationEventDispatcherOwner(enabled =
isSelected)` 会创建一个限定作用域的子 dispatcher，并关联到 `LocalNavigationEventDispatcherOwner.current`
中的父级。用 `CompositionLocalProvider` 提供它，可以确保不可见的标签页或页面自动停止拦截
返回手势，而不会泄漏 handler。


```kotlin
// RIGHT: Scoping child navigation in a ViewPager or Tab interface
@Composable
fun TabPage(isSelected: Boolean) {
    val childOwner = rememberNavigationEventDispatcherOwner(enabled = isSelected)
    CompositionLocalProvider(LocalNavigationEventDispatcherOwner provides childOwner) {
        val navigationState = rememberNavigationEventState(currentInfo = NavigationEventInfo.None)
        NavigationBackHandler(
            state = navigationState,
            onBackCompleted = { /* Handle page back navigation */ }
        )
        // Page content
    }
}
```

<br />

#### 错误

**为什么这是错误的**：创建未关联的独立 dispatcher、在重组之间不 remember 就直接实例化原始
dispatcher，或尝试使用 `.addChild()` 这类不存在的方法，会破坏层级路由，并让子 handler 在
页面不活跃时仍然生效。


```kotlin
// WRONG
@Composable
fun TabPage(isSelected: Boolean) {
    val parentDispatcher = LocalNavigationEventDispatcherOwner.current?.navigationEventDispatcher
    val childDispatcher = NavigationEventDispatcher() // Unlinked and not remembered across recompositions
    // WRONG: Method does not exist
    parentDispatcher?.addChild(childDispatcher)
}
```

<br />

### 4. Compose 多 handler 注册（IllegalArgumentException）

你不能把同一个 `NavigationEventState` 绑定到多个活跃的 `NavigationBackHandler` 实例，因为这
会在运行时抛出 `IllegalArgumentException`。要处理条件分支流程（例如在检查未保存改动与立即
返回之间做判断），你必须注册单个统一的 handler，并在 `onBackCompleted` 内部做逻辑分支。

#### 正确

**为什么这是正确的**：使用单个 `NavigationBackHandler`，并在 `onBackCompleted` 内部做分支
逻辑，可以保持 `NavigationEventState` 与 handler 之间严格的 1:1 映射，避免状态冲突。


```kotlin
// RIGHT
val navigationState = rememberNavigationEventState(currentInfo = NavigationEventInfo.None)
NavigationBackHandler(
    state = navigationState,
    isBackEnabled = true,
    onBackCompleted = {
        if (hasUnsavedChanges) {
            showDiscardDialog()
        } else {
            onNavigateUp()
        }
    }
)
```

<br />

#### 错误

**为什么这是错误的**：把多个 `NavigationBackHandler` composable 挂到同一个 `navigationState`
实例上，相当于试图把重复的 handler 绑定到单个状态对象，运行时会抛出
`IllegalArgumentException`。


```kotlin
// WRONG
val navigationState = rememberNavigationEventState(currentInfo = NavigationEventInfo.None)
NavigationBackHandler(
    state = navigationState,
    isBackEnabled = hasUnsavedChanges,
    onBackCompleted = { /* Discard changes */ }
)
NavigationBackHandler(
    state = navigationState,
    isBackEnabled = !hasUnsavedChanges,
    onBackCompleted = { /* Navigate up */ }
)
```

<br />

## 检查清单

**面向 Compose Android 目标平台：**

- \[ \] compile SDK 是否设为 `36` 或更高？（如果 compile SDK 低于 36，请在 `build.gradle.kts` 中设为 `36` 或更高）。
- \[ \] `AndroidManifest.xml` 中的 `android:enableOnBackInvokedCallback` 是否 **未** 显式设为 `"false"`？（在 API 36+ 上它默认是 `"true"`；在 API 33--35 上请确保设为 `"true"`）。
- \[ \] Activity 是否依赖内置的 `ComponentActivity` dispatcher owner，而没有多余的匿名 delegate 包装？
- \[ \] dialog 或 sheet 是否依赖 `ComponentDialog` 的自动 dispatcher 解析，而没有多余的 `CompositionLocalProvider` 包装？
- \[ \] 管理嵌套层级时，Compose 中的父子 dispatcher 关系是否用 `rememberNavigationEventDispatcherOwner()` 限定了作用域？
- \[ \] 条件返回逻辑是否在单个统一的 `NavigationBackHandler` 内处理，以避免重复注册（`IllegalArgumentException`）？
- \[ \] 旧的 `BackHandler` 用法是否已迁移到支持预测性进度的 `NavigationBackHandler`？
- \[ \] 项目是否能成功构建并通过测试？
