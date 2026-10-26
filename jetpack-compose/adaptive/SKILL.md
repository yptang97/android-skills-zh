---
name: adaptive
description: 制作或更新应用的 UI，使其适配手机、平板电脑、可折叠设备、笔记本电脑、桌面设备、TV、Auto 和 XR 等不同 Android 设备的操作指引。涵盖如何使用 Compose MediaQuery API 处理不同的窗口尺寸、指向设备（例如鼠标）和文本输入设备（例如键盘），以及如何在配置变更（例如折叠或展开可折叠设备、旋转设备或调整窗口尺寸）时保留 UI、导航、滚动和媒体播放状态。还涵盖使用 Navigation3 Scene 实现的多窗格布局、具有不同目标尺寸的自适应 UI 组件（例如按钮），以及使用 Compose Grid 和 FlexBox API 实现的自适应布局（包括导航区域——导航栏（nav rail）和底部导航栏）。同时涵盖带键盘快捷键、工具提示和自定义光标的桌面体验。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - android
  - ui
  - adaptive
  - Grid
  - FlexBox
  - MediaQuery
  - navigation
  - foldables
  - state
  - resizability
  - configuration-changes
---

## 前置条件

应用必须：

- 所有屏幕都使用 Compose。如果它仍在使用 Fragment 或 View，建议用 XML 转 Compose skill 迁移这些屏幕。
- 使用 Jetpack Navigation 3。如果没有，建议用 Navigation 3 skill 迁移应用。

## 让应用自适应的流程

要让应用自适应，请遵循以下步骤，或按任务需要选取其中一部分。

- 步骤 1：验证当前 UI
- 步骤 2：让导航栏自适应
- 步骤 3：添加多窗格布局
- 步骤 4：通过改变列数让纵向列表自适应
- 步骤 5：滚动时隐藏应用栏
- 步骤 6：在配置变更间保留 UI 状态
- 步骤 7：添加桌面体验

## 步骤 1. 验证当前 UI

确保已有截图测试，用来验证当前 UI 在不同形态系数（form factor）下的表现。如果没有，添加 [Compose 预览截图测试工具](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)。使用以下注解为所有主要形态系数创建预览。例如：


```kotlin
@Preview(name = "Phone", device = Devices.PHONE, showBackground = true)
@Preview(name = "Foldable", device = Devices.FOLDABLE, showBackground = true)
@Preview(name = "Tablet", device = Devices.TABLET, showBackground = true)
@Preview(name = "Desktop", device = Devices.DESKTOP, showBackground = true)
annotation class FormFactorPreviews

@PreviewTest
@FormFactorPreviews
@Composable
fun FeedScreenPreview() {
    SnippetsTheme {
        Box {
            Text("My Screen")
        }
    }
}
```

<br />

## 步骤 2. 让导航栏自适应

当用户竖屏握持手机时，底部导航栏针对触摸输入做了优化。在更大的手持设备上，例如平板电脑和已展开的可折叠设备，导航区域必须可以从屏幕边缘访问（导航栏（navigation rail））。

如果需要为内容提供更多屏幕空间，可以隐藏导航区域。示例包括：

- 用户向下滚动时隐藏导航栏，向上滚动时再次显示。这里的假设是：用户向下滚动时在消费内容，而向上滚动时想离开这些内容。
- 当导航区域的内容会造成干扰时隐藏它。例如相机预览或全屏显示照片时。

当详情屏幕在移动设备上全屏显示时，在更大屏幕上必须停用全屏模式。

迁移步骤：

- 定位现有的导航栏。
- 把每一项转换为 `NavigationSuiteItem`。
- 判断导航栏的可见性是否会变化。例如，它是否被包在 `AnimatedContent` 或 `AnimatedVisibility` composable 中。如果是，遵循「控制导航区域可见性」中的指引。
- 把承载导航栏的容器（通常是 `Scaffold`）替换为 Material 3 自适应布局库中的 `NavigationSuiteScaffold`。
- 使用 `NavigationSuiteScaffold` 的 `navigationItems` 参数提供导航项。

### 步骤 2.1. 控制导航区域可见性

如果导航栏的可见性会变化——在特定场景或特定屏幕上被隐藏——这种行为必须在自适应导航区域中保持。这通过 `NavigationSuiteScaffold` 的 `state` 参数实现。

迁移步骤：

- 确认导航栏被隐藏的场景。通常用一个布尔变量表示可见性。变量名使用 `isNavBarVisible` 或 `shouldShowNavBar`。
- 使用 `rememberNavigationSuiteScaffoldState()` 创建 `NavigationSuiteScaffoldState` 实例，并传给 `NavigationSuiteScaffold`。
- 当导航区域可见性变化时，用 `LaunchedEffect` 调用 `NavigationSuiteScaffoldState` 的 `show` 或 `hide`。

例如：


```kotlin
// Pass this variable to any composable that needs to control the navigation area visibility
var isNavBarVisible by remember { mutableStateOf(true) }
val scaffoldVisibilityState = rememberNavigationSuiteScaffoldState()

NavigationSuiteScaffold(
    navigationSuiteItems = navItems,
    state = scaffoldVisibilityState
) {
    // Main content
}

LaunchedEffect(isNavBarVisible){
    if (isNavBarVisible) {
        scaffoldVisibilityState.show()
    } else {
        scaffoldVisibilityState.hide()
    }
}
```

<br />

## 步骤 3. 使用 Navigation 3 Scene 添加多窗格布局

分析代码库，寻找相互关联的屏幕——在一个屏幕上点击某项会打开另一个屏幕，显示与前者相关的信息。有两种典型的屏幕关系：列表-详情（list-detail）和支撑窗格（supporting pane）。

重要：必须使用 Navigation 3 的 `SceneStrategy` 方式实现多窗格布局。不要使用 `ListDetailPaneScaffold` 或 `SupportingPaneScaffold`。

### 步骤 3.1. 列表-详情

#### 识别列表屏幕与详情屏幕

列表-详情布局显示一个项目列表（即列表屏幕），点击某一项会打开显示该项目更多细节的新屏幕（即详情屏幕）。

典型用法包括邮件、笔记和消息等效率类应用。

除非明确要求，否则当详情内容需要大量屏幕空间时（例如图像或媒体更适合全屏呈现），避免使用这种模式。

#### 添加 Material 列表-详情 SceneStrategy

- 添加 `androidx.compose.material3.adaptive:adaptive-navigation3` 库
- 使用 `rememberListDetailSceneStrategy` 创建 `androidx.compose.material3.adaptive.navigation3.ListDetailSceneStrategy`
- 通过 `NavDisplay` 的 `sceneStrategies` 参数把 `ListDetailSceneStrategy` 传给它

#### 使用 metadata 识别列表屏幕与详情屏幕

- 使用 `ListDetailSceneStrategy.listPane(detailPlaceholder = {
  <placeholder composable> })`，通过 `entry(metadata = ...)` 或 `NavEntry(metadata = ...)` 为列表条目添加 metadata。
- 使用 `detailPlaceholder` 参数在没有选中列表项时给详情屏幕添加占位符。
- 使用 `ListDetailSceneStrategy.detailPane()` 为详情条目添加 metadata。

#### 重要考虑事项

- 当详情屏幕在移动设备上全屏显示内容时（内容填满整个屏幕、应用栏或导航栏被隐藏），如果它属于列表-详情布局，必须停用全屏模式。
- 在列表-详情布局中，详情屏幕不得显示返回箭头。

参考实现见 [Nav3 **Material** 列表-详情配方](references/android/guide/navigation/navigation-3/recipes/material-listdetail.md)。

### 步骤 3.2. 支撑窗格

识别支撑窗格屏幕：主屏幕显示单个项目，选中它会打开一个带更多细节的「支撑屏幕」。支撑屏幕是对主屏幕的补充，显示在支撑窗格中。

#### 添加 Material 支撑窗格 `SceneStrategy`

- 如果还没有，添加 `androidx.compose.material3.adaptive:adaptive-navigation3` 库
- 使用 `rememberSupportingPaneSceneStrategy` 创建 `androidx.compose.material3.adaptive.navigation3.SupportingPaneSceneStrategy`
- 通过 `NavDisplay` 的 `sceneStrategies` 参数把 `SupportingPaneSceneStrategy` 传给它

#### 使用 metadata 识别主屏幕与支撑屏幕

- 使用 `SupportingPaneSceneStrategy.mainPane()`，通过 `entry(metadata = ...)` 或 `NavEntry(metadata = ...)` 为主条目添加 metadata
- 使用 `SupportingPaneSceneStrategy.supportingPane()` 为支撑条目添加 metadata

### 步骤 3.3. 运行截图测试

如果做了改动，记录新的参考文件。请用户目视确认新布局正确。

## 步骤 4. 通过改变列数让纵向列表自适应

### 步骤 4.1. 让 lazy 列表自适应

查找以下纵向列表 composable：`LazyColumn`、`LazyVerticalGrid`、`LazyVerticalStaggeredGrid`。

迁移步骤：

- 为列选择合适的 dp 最小宽度。在这个宽度下项目必须对用户清晰可见。
- 对于 `LazyColumn`：改为 `LazyVerticalGrid`，然后按后面的指引操作
- 对于 `LazyVerticalGrid`：把 `columns` 参数改为使用 `GridCells.Adaptive(<width>.dp)`
- 对于 `LazyVerticalStaggeredGrid`：把 `columns` 参数改为使用 `StaggeredGridCells.Adaptive(<width>.dp)`

### 步骤 4.2. 把非 lazy 列表迁移到 Grid

警告：Grid 是从 Compose 1.11.0-beta01 起可用的实验性 API。与用户确认他们在代码库中使用实验性 API 没有问题。

查找任何包含多个同类型项目的 `Column`，并用 `Grid` 替换它。不要用 `LazyVerticalGrid` 或其他 lazy 布局替换。不要把 `Grid` 放进现有的 `Column` 里。要完全替换它。

`Grid` 通过向它的 `config` 参数传入一个 lambda（`GridConfigurationScope` 上的扩展函数）来配置。在 lambda 内部，`constraints` 提供网格容器的最小和最大尺寸，可用于根据可用尺寸改变行数和列数。例如，以下代码这样配置 `Grid`：当可用宽度为：

- 小于 800dp 时，使用 2x4 网格
- 800dp 或更大时，使用 4x2 网格


```kotlin
Grid(
    config = {
        val maxWidthDp = constraints.maxWidth.toDp()
        val (cols, rows) = if (maxWidthDp < 800.dp){
            2 to 4
        } else{
            4 to 2
        }

        val gapSizeDp = 8.dp
        val cellSize = ((maxWidthDp - (gapSizeDp * (cols - 1))) / cols).coerceAtLeast(0.dp)
        repeat(cols) { column(cellSize) }
        repeat(rows) { row(cellSize) }
        gap(gapSizeDp)
    }
) { /** items **/ }
```

<br />

`Grid` 是实验性 API，因此要给任何使用它的函数加上 `@OptIn(ExperimentalGridApi::class)` 注解。

## 步骤 5：滚动时隐藏应用栏

在包含多个顶层目的地的应用中，每个屏幕必须独立管理自己的应用栏状态。主要有两种滚动行为：

- `exitUntilCollapsedScrollBehavior`：向下滚动时隐藏，向上滚动时保持隐藏，直到到达最顶部（0 偏移）。
- `enterAlwaysScrollBehavior`：向下滚动时隐藏，向上滚动时立即显示。

## 步骤 6：在配置变更间保留 UI 状态

重要：**绝不**为了抑制 Activity 重建或锁定方向而在 `AndroidManifest.xml` 中添加 `android:configChanges` 或 `android:screenOrientation`。退出重建只会隐藏状态丢失的 bug 而不是修复它们，会破坏自适应资源重新加载，并阻止应用进程重启。

修复配置变更导致的状态丢失时，要系统地审查**所有**屏幕、组件和状态持有者中 `remember` 的**每一处**用法（换言之，不要只搜索 `remember { mutableStateOf(...) }`）：

### 步骤 6.1. 在 Composable 中保留原始类型与自定义 UI 状态

- 对于用户输入和交互式 UI 状态，例如 `TextField` 草稿文本、搜索查询、滚动位置和开关状态，把 `remember { mutableStateOf(...) }` 替换为 `rememberSaveable { mutableStateOf(...) }`。
- 在合适时把状态按相关标识符做 key（例如 `rememberSaveable(conversationId) { mutableStateOf("") }`）。
- 对于原生不支持 `Bundle` 保存的自定义 data class 或集合（例如 `Set`）：
  - 当通过 `var state by rememberSaveable(...) { mutableStateOf(...) }` 委托 `MutableState<T>` 时，用 **`stateSaver`** 传入你的自定义 `Saver`（当 block 返回 `MutableState<T>` 时**不要**传 `saver = ...`）：


```kotlin
// this Saver implementation converts CustomState object which we don't know how to save
// to List<String> which we can save
private val CustomStateSaver = Saver<CustomState, List<String>>(
    save = { customState -> customState.values.map { it.value } },
    restore = { values -> CustomState(values.map { CustomStateValue.valueOf(it) }.toSet()) }
)

@Composable
fun MyComposable() {
    var customState by rememberSaveable(stateSaver = CustomStateSaver) {
        mutableStateOf(CustomState())
    }
}
```

<br />

- 另一种做法是给类加上 `@Serializable` 注解，并使用 `rememberSerializable`。

### 步骤 6.2. 在 lazy 与可滚动布局中保留滚动状态

朴素的 `remember { LazyListState() }`、`remember { LazyGridState() }` 和 `remember { ScrollState(...) }` **不会**在配置变更间保存滚动位置，因为它们绕过了状态类的 `Saver`。

检查所有屏幕和可复用组件中的所有可滚动容器（`LazyColumn`、`LazyRow`、`LazyVerticalGrid`、`LazyHorizontalGrid`、`LazyVerticalStaggeredGrid`、`Modifier.verticalScroll` 和 `Modifier.horizontalScroll`），把朴素的 `remember` 实例化替换为内置的可保存工厂函数：

- `remember { LazyListState() }` -\> `rememberLazyListState()`
- `remember { LazyGridState() }` -\> `rememberLazyGridState()`
- `remember { LazyStaggeredGridState() }` -\> `rememberLazyStaggeredGridState()`
- `remember { ScrollState(initial = 0) }` -\> `rememberScrollState()`

### 步骤 6.3. 保留 Navigation 3 状态与多个返回栈

详情见 Navigation 3 指南中的[保存和管理导航状态](references/android/guide/navigation/navigation-3/save-state.md)。

### 步骤 6.4. 保留媒体播放状态（`ExoPlayer` / Media3）

当 MediaPlayer（例如 `ExoPlayer`）在 composable 中用 `remember` 创建时，它会在被销毁时释放，并在配置变更时从头重建，导致播放位置重置为 `0:00`，即使用户已暂停视频也会自动播放。

要保留 `ExoPlayer` 的播放状态（`currentPosition` 和 `playWhenReady`）：

1. 使用 `rememberSaveable(videoResId)` 存储 `savedPositionMs`（`mutableLongStateOf(0L)`）和 `savedPlayWhenReady`（`mutableStateOf(true)`）。
2. **在播放过程中保持已保存状态最新 --- 不要只在 `onDispose` 中保存**：在 `Player.Listener`（`onPlayWhenReadyChanged`、`onPositionDiscontinuity`）中**以及**活跃期间在 `LaunchedEffect(player)` 循环里定期更新 `savedPlayWhenReady` 和 `savedPositionMs`。
3. **用恢复的状态初始化播放器**：在 `prepare()` 之前设置 `playWhenReady = savedPlayWhenReady` 并调用 `seekTo(savedPositionMs)`。
4. **保护 `LifecycleStartEffect`，使其不会自动播放已暂停的视频或覆盖 `savedPlayWhenReady`**：
   - 在 `LifecycleStartEffect(player)` 中，只有当 `savedPlayWhenReady` 为 `true` 时才调用 `player.play()`（否则已暂停的视频在恢复后会重新开始播放）。
   - 在 `onStopOrDispose` 中，在调用 `player.pause()` 之前捕获 `val wasPlaying = player.playWhenReady` 和 `savedPositionMs = player.currentPosition`，然后恢复 `savedPlayWhenReady = wasPlaying`，这样停止/销毁时的 `player.pause()` 就不会把 `savedPlayWhenReady` 覆盖为 `false`：


```kotlin
@UnstableApi
@Composable
private fun rememberExoPlayer(@RawRes videoResId: Int, fromUri: Unit.(Uri) -> MediaItem): ExoPlayer {
    val context = LocalContext.current
    var savedPositionMs by rememberSaveable(videoResId) { mutableLongStateOf(0L) }
    var savedPlayWhenReady by rememberSaveable(videoResId) { mutableStateOf(true) }

    val player = remember(videoResId) {
        ExoPlayer.Builder(context.applicationContext).build().apply {
            setMediaItem(MediaItem.fromUri(RawResourceDataSource.buildRawResourceUri(videoResId)))
            repeatMode = Player.REPEAT_MODE_ONE
            playWhenReady = savedPlayWhenReady
            seekTo(savedPositionMs)
            prepare()
        }
    }

    DisposableEffect(player) {
        val listener = object : Player.Listener {
            override fun onPlayWhenReadyChanged(playWhenReady: Boolean, reason: Int) {
                savedPlayWhenReady = playWhenReady
                savedPositionMs = player.currentPosition
            }
            override fun onPositionDiscontinuity(
                oldPosition: Player.PositionInfo,
                newPosition: Player.PositionInfo,
                reason: Int
            ) {
                savedPositionMs = newPosition.positionMs
            }
        }
        player.addListener(listener)
        onDispose {
            player.removeListener(listener)
            player.release()
        }
    }

    LaunchedEffect(player) {
        while (isActive) {
            savedPositionMs = player.currentPosition
            delay(200)
        }
    }

    LifecycleStartEffect(player) {
        if (savedPlayWhenReady) {
            player.play()
        }
        onStopOrDispose {
            val wasPlaying = player.playWhenReady
            savedPositionMs = player.currentPosition
            player.pause()
            savedPlayWhenReady = wasPlaying
        }
    }

    return player
}
```

<br />

## 步骤 7：添加桌面体验

### 步骤 7.1：确认所需的桌面功能

查看用户的提示词、需求或上传的文件，确定需要实现哪项桌面功能。

### 步骤 7.2：运行针对具体功能的处理

根据识别出的功能，你必须阅读对应的参考文件并遵循其中的指引：

- **键盘快捷键** -\> 阅读 [`references/keyboard_shortcuts.md`](references/keyboard_shortcuts.md)
- **工具提示** -\> 阅读 [`references/tooltips.md`](references/tooltips.md)
- **自定义光标** -\> 阅读 [`references/custom_cursors.md`](references/custom_cursors.md)

每个参考文件都先在整个应用中搜索该功能的目标。先把这份清单写下来，全部实现（不只是你打开的第一个屏幕），并在结束前重新检查清单。

## 最后一步：构建与测试

构建应用并运行本地测试。如果项目有截图测试，运行它们，但不要更新参考图像。请用户在查看截图差异之后再做这件事。

## 实验性自适应 API 的补充文档

以下 API 从 Compose 1.11.0 起可用。

### FlexBox

查看 FlexBox 文档：

- [概述](references/android/develop/ui/compose/layouts/adaptive/flexbox/index.md)
- [快速开始 - 配置](references/android/develop/ui/compose/layouts/adaptive/flexbox/get-started.md)
- [设置容器行为](references/android/develop/ui/compose/layouts/adaptive/flexbox/container-behavior.md)
- [设置项目行为](references/android/develop/ui/compose/layouts/adaptive/flexbox/item-behavior.md)

## MediaQuery

当你需要查询设备的屏幕尺寸、指针精度、键盘类型、是否有摄像头或麦克风以及其他设备能力时，查看 [MediaQuery 文档](references/android/develop/ui/compose/layouts/adaptive/mediaquery/index.md)。

## Grid

当你需要在网格布局中显示固定数量的项目时，查看 Grid 文档：

- [概述](references/android/develop/ui/compose/layouts/adaptive/grid/index.md)
- [快速开始 - 配置](references/android/develop/ui/compose/layouts/adaptive/grid/get-started.md)
- [设置容器属性](references/android/develop/ui/compose/layouts/adaptive/grid/container-properties.md)
- [设置项目属性](references/android/develop/ui/compose/layouts/adaptive/grid/item-properties.md)
