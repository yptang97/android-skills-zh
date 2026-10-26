---
name: edge-to-edge
description: 使用这个 skill 把 Jetpack Compose 应用迁移为支持自适应 edge-to-edge，
  并排查常见问题。使用这个 skill 修复被导航栏或状态栏遮挡、与之重叠的 UI 组件
  （例如按钮或列表），修复 IME insets，以及修复系统栏图标可读性问题。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-08-24'
  keywords:
  - android
  - compose
  - system bars
  - edge-to-edge
  - status bar
  - navigation bar
---

## 前置条件

- 项目**必须**使用 Android Jetpack Compose。
- 项目**必须**以 SDK 35 或更高版本为目标。如果 SDK 低于 35，请把 SDK 提高到 35。

## 步骤 1：规划

1. 定位并分析所有 Activity 类，判断哪些已经支持 edge-to-edge。对每个尚未支持 edge-to-edge 的 Activity，计划让它实现 edge-to-edge。
2. 在每个 Activity 中定位并分析所有列表和 FAB 组件，判断哪些已经支持 edge-to-edge。对每个尚未支持 edge-to-edge 的组件，计划让这些组件都实现 edge-to-edge。
3. 在每个 Activity 中扫描 `TextField`、`OutlinedTextField` 或 `BasicTextField`。如果找到，你**必须**按照本 skill 的 IME 章节验证 IME 不会遮挡输入框。

## 步骤 2：添加 edge-to-edge 支持

1. 在每个尚未调用 `enableEdgeToEdge` 的 Activity 中，于 `onCreate` 里的 `setContent` 之前添加 `enableEdgeToEdge`。
2. 对所有使用软键盘的 Activity，在 AndroidManifest.xml 中添加 `android:windowSoftInputMode="adjustResize"`。

## 步骤 3：应用 insets

- 应用**必须**应用系统 insets，或把内容对齐到标尺，以保证关键
  UI 仍然可点击。只选择一种方式，避免重复的内边距：

  1. **首选：** 在可用时使用 `Scaffold`，把 `PaddingValues` 传给 content lambda。

  ```kotlin
  Scaffold { innerPadding ->
      // innerPadding accounts for system bars and any Scaffold components
      LazyColumn(
          modifier = Modifier
              .fillMaxSize()
              .consumeWindowInsets(innerPadding),
          contentPadding = innerPadding
      ) { /* Content */ }
  }
  ```

  <br />

  1. **首选：** 在可用时使用 Material 组件自带的 inset 处理或 padding 修饰符。

     - Material 3 组件会为自己的组件管理安全区域，包括：
       - `TopAppBar`
       - `SmallTopAppBar`
       - `CenterAlignedTopAppBar`
       - `MediumTopAppBar`
       - `LargeTopAppBar`
       - `BottomAppBar`
       - `ModalDrawerSheet`
       - `DismissibleDrawerSheet`
       - `PermanentDrawerSheet`
       - `ModalBottomSheet`
       - `NavigationBar`
       - `NavigationRail`
     - 对 Material 2 组件，使用 `windowInsets` 参数为 `BottomAppBar`、`TopAppBar` 和 `BottomNavigation` 手动应用 insets。**不要**给父容器加 padding；而应把 insets 直接传给 App Bar 组件。给父容器加 padding 会阻止 App Bar 背景绘制到系统栏区域。例如对 `TopAppBar`，只选择下列选项之一：
       1. **首选：** `TopAppBar(windowInsets = AppBarDefaults.topAppBarWindowInsets)`
       2. `TopAppBar(windowInsets = WindowInsets.systemBars.exclude(WindowInsets.navigationBars))`
       3. `TopAppBar(windowInsets = WindowInsets.systemBars.add(WindowInsets.captionBar))`
  2. 对于 Scaffold 之外的组件，使用 padding 修饰符，例如 `Modifier.safeDrawingPadding()` 或 `Modifier.windowInsetsPadding(WindowInsets.safeDrawing)`。


     ```kotlin
     Box(
         modifier = Modifier
             .fillMaxSize()
             .safeDrawingPadding()
     ) {
         Button(
             onClick = {},
             modifier = Modifier.align(Alignment.BottomCenter)
         ) {
             Text("Login")
         }
     }
     ```

     <br />

  3. 对于嵌套很深、内边距过多的组件，使用 `WindowInsetsRulers`（例如 `Modifier.fitInside(WindowInsetsRulers.SafeDrawing.current)`）。代码示例见 *IME* 章节。

  4. 当你需要某个元素（例如自定义标题栏或装饰性遮罩）的尺寸与系统栏一致时，
     使用 inset 尺寸修饰符（例如
     `Modifier.windowInsetsTopHeight(WindowInsets.systemBars)`）。
     代码示例见 *列表* 章节。

## 自适应 Scaffold

- `NavigationSuiteScaffold` 会为自己的组件（如 `NavigationRail` 或 `NavigationBar`）管理安全区域。但自适应 scaffold（例如 `NavigationSuiteScaffold`、`ListDetailPaneScaffold`）不会把 PaddingValues 传递给其内部内容。你**必须**按 *步骤 3* 所述，对**各个**屏幕或组件（例如列表的 `contentPadding` 或 FAB 的 padding）应用 insets。**不要**给 `NavigationSuiteScaffold` 父级应用 `safeDrawingPadding` 或类似修饰符。这会裁剪内容并阻止屏幕实现 edge-to-edge。

## IME

- 对每个使用软键盘的 Activity，检查 AndroidManifest.xml 中是否设置了 `android:windowSoftInputMode="adjustResize"`。不要使用 `SOFT_INPUT_ADJUST_RESIZE`，因为它已废弃。然后，保持输入框的焦点。选择一种：
  - 1. **首选：** 给内容容器添加 `Modifier.fitInside(WindowInsetsRulers.Ime.current)`。这比 `imePadding()` 更受推荐，因为它能减少卡顿，以及因忘记在层级上层消费 insets 而产生的多余内边距。
  - 2. 给内容容器添加 `imePadding`。该 padding 修饰符**必须**放在 `Modifier.verticalScroll()` 之前。如果父级已通过 `contentWindowInsets` 处理了 IME（例如 `contentWindowInsets =
    WindowInsets.safeDrawing`），就不要使用 `Modifier.imePadding()`。否则会造成双重内边距。

### 带 Scaffold 的 IME 代码模式

#### 正确

这里正确，是因为 `contentWindowInsets` 包含 IME insets，它们会作为 `innerPadding` 传给
content lambda。


```kotlin
// RIGHT
Scaffold(contentWindowInsets = WindowInsets.safeDrawing) { innerPadding ->
    Column(
        modifier = Modifier
            .padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .verticalScroll(rememberScrollState())
    ) { /* Content */ }
}
```

<br />

*** ** * ** ***

这里正确，是因为 `fitInside` 会让内容贴合 IME insets，与
`contentWindowInsets` 无关。


```kotlin
// RIGHT
Scaffold() { innerPadding ->
    Column(
        modifier = Modifier
            .padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .fitInside(WindowInsetsRulers.Ime.current)
            .verticalScroll(rememberScrollState())
    ) { /* Content */ }
}
```

<br />

*** ** * ** ***

这里正确，是因为默认的 `contentWindowInsets` 不包含 IME insets，
而 `imePadding()` 会应用 IME insets：


```kotlin
// RIGHT
Scaffold() { innerPadding ->
    Column(
        modifier = Modifier
            .padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .imePadding()
            .verticalScroll(rememberScrollState())
    ) { /* Content */ }
}
```

<br />

#### 错误

这里错误，是因为 IME 打开时会出现多余的内边距。IME insets 被应用了两次：一次通过 innerPadding（其中包含传入的 `contentWindowInsets` 值带来的 IME insets），一次通过 `imePadding`：


```kotlin
// WRONG
Scaffold(contentWindowInsets = WindowInsets.safeDrawing) { innerPadding ->
    Column(
        modifier = Modifier
            .padding(innerPadding)
            .imePadding()
            .verticalScroll(rememberScrollState())
    ) { /* Content */ }
}
```

<br />

*** ** * ** ***

这里错误，是因为 IME 会盖住内容。Scaffold 默认的
`contentWindowInsets` 不包含 IME insets。


```kotlin
// WRONG
Scaffold() { innerPadding ->
    Column(
        modifier = Modifier
            .padding(innerPadding)
            .verticalScroll(rememberScrollState())
    ) { /* Content */ }
}
```

<br />

### 不带 Scaffold 的 IME 代码模式

#### 正确

以下代码示例不会造成多余的内边距。


```kotlin
// RIGHT
Box(
    // Insets consumed
    modifier = Modifier.safeDrawingPadding() // or imePadding(), safeContentPadding(), safeGesturesPadding()
) {
    Column(
        modifier = Modifier.imePadding()
    ) { /* Content */ }
}
```

<br />

*** ** * ** ***


```kotlin
// RIGHT
Box(
    // Insets consumed
    modifier = Modifier.windowInsetsPadding(WindowInsets.safeDrawing) // or WindowInsets.ime, WindowInsets.safeContent, WindowInsets.safeGestures
) {
    Column(
        modifier = Modifier.imePadding()
    ) { /* Content */ }
}
```

<br />

*** ** * ** ***


```kotlin
// RIGHT
Box(
    // Insets not consumed, but irrelevant due to fitInside
    modifier = Modifier.padding(WindowInsets.safeDrawing.asPaddingValues()) // or WindowInsets.ime.asPaddingValues(), WindowInsets.safeContent.asPaddingValues(), WindowInsets.safeGestures.asPaddingValues()
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .fitInside(WindowInsetsRulers.Ime.current)
    ) { /* Content */ }
}
```

<br />

#### 错误

以下代码示例会造成多余的内边距，因为 IME insets
被应用了两次：


```kotlin
// WRONG
Box(
    // Insets not consumed
    modifier = Modifier.padding(WindowInsets.safeDrawing.asPaddingValues()) // or WindowInsets.ime.asPaddingValues(), WindowInsets.safeContent.asPaddingValues(), WindowInsets.safeGestures.asPaddingValues()
) {
    Column(
        modifier = Modifier.imePadding()
    ) { /* Content */ }
}
```

<br />

## 导航栏对比度 \& 系统栏图标

- 如果 Activity 使用 `WindowCompat` 的 `enableEdgeToEdge`，对于同时支持浅色和深色主题的应用，
  你**必须**把 `isAppearanceLightNavigationBars` 和 `isAppearanceLightStatusBars` 设为
  与设备主题相反的值，以便系统栏图标清晰可读。建议在主题文件中做这个设置。
  如果 Activity 使用 `ComponentActivity` 的 `enableEdgeToEdge`，就不要这样做，
  因为它会自动处理图标颜色。


  ```kotlin
  // Only use if calling `enableEdgeToEdge` from `WindowCompat`.
  // Apply to your theme file.
  @Composable
  fun MyTheme(
      darkTheme: Boolean = isSystemInDarkTheme(),
      content: @Composable () -> Unit
  ) {
      val view = LocalView.current
      if (!view.isInEditMode) {
          SideEffect {
              val window = (view.context as? Activity)?.window ?: return@SideEffect
              val controller = WindowCompat.getInsetsController(window, view)

              // Dark icons for Light Mode (!darkTheme), Light icons for Dark Mode
              controller.isAppearanceLightStatusBars = !darkTheme
              controller.isAppearanceLightNavigationBars = !darkTheme
          }
      }

      MaterialTheme(content = content)
  }
  ```

  <br />

- 如果任何屏幕使用了带底栏（例如 `BottomAppBar`、`NavigationBar`）的 `Scaffold` 或
  `NavigationSuiteScaffold`，在 SDK 29+ 上于对应 Activity 中设置
  `window.isNavigationBarContrastEnforced = false`。这可以阻止系统给导航栏添加
  半透明背景，从而确保你的底栏颜色延伸到屏幕底部。

## 列表

- 把 inset 内边距（如 `Scaffold` 的 `innerPadding`）应用到可滚动组件（例如 `LazyColumn`、`LazyRow`）的 `contentPadding` 参数上。不要把它作为 `Modifier.padding()` 应用到列表的父容器，因为这会裁剪内容并阻止内容滚动到系统栏后面。
- 创建一个覆盖系统栏的半透明 composable，使图标仍然清晰可读。


```kotlin
class SystemBarProtectionSnippets : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // enableEdgeToEdge sets window.isNavigationBarContrastEnforced = true
        // which is used to add a translucent scrim to three-button navigation
        enableEdgeToEdge()

        setContent {
            MyTheme {
                // Main content
                MyContent()

                // After drawing main content, draw status bar protection
                StatusBarProtection()
            }
        }
    }
}

@Composable
private fun StatusBarProtection(
    color: Color = MaterialTheme.colorScheme.surfaceContainer,
) {
    Spacer(
        modifier = Modifier
            .fillMaxWidth()
            .height(
                with(LocalDensity.current) {
                    (WindowInsets.statusBars.getTop(this) * 1.2f).toDp()
                }
            )
            .background(
                brush = Brush.verticalGradient(
                    colors = listOf(
                        color.copy(alpha = 1f),
                        color.copy(alpha = 0.8f),
                        Color.Transparent
                    )
                )
            )
    )
}
```

<br />

## 对话框

如果以下两个条件都成立，则该 Dialog 是全屏的，
必须把它做成 edge-to-edge：
1. `DialogProperties` 包含 `usePlatformDefaultWidth = false`。
2. Dialog 调用了 `Modifier.fillMaxSize()`。

要把全屏 Dialog 做成 edge-to-edge，在 `DialogProperties` 中设置 `decorFitsSystemWindows = false`。


```kotlin
Dialog(
    onDismissRequest = { /* Handle dismiss */ },
    properties = DialogProperties(
        // 1. Allows the dialog to span the full width of the screen
        usePlatformDefaultWidth = false,
        // 2. Allows the dialog to draw behind status and navigation bars
        decorFitsSystemWindows = false
    )
) { /* Content */ }
```

<br />

## 检查清单

- \[ \] 每个 `Activity` 都调用了 `enableEdgeToEdge()` 吗？
- \[ \] `AndroidManifest.xml` 中设置了 `adjustResize` 吗？
- \[ \] 每个 `TextField`、`OutlinedTextField` 或 `BasicTextField` 的父级都设置了 `imePadding()`、`fitInside`、`Modifier.safeDrawingPadding()`、`Modifier.safeContentPadding()`、`Modifier.safeGesturesPadding()`，或把 `contentWindowInsets` 设为 `WindowInsets.safeDrawing` 或 `WindowInsets.ime` 吗？
- \[\ ] 列表的第一项和最后一项是否通过把 insets 传给 `contentPadding` 而避开了系统栏？
- \[\ ] FAB 是否通过位于 Scaffold 内或应用 `Modifier.safeDrawingPadding()` 而绘制在导航栏之上？
- \[\ ] 项目能构建吗？运行 `./gradlew build` 确认。
