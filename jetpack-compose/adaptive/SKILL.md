---
name: adaptive
description: 让应用 UI 适配不同 Android 设备（包括手机、平板、折叠设备、笔记本电脑、桌面端、TV、Auto
  和 XR）的说明。包含如何使用 Compose MediaQuery API 处理不同的窗口尺寸、指针设备（例如鼠标）
  和文本输入设备（例如键盘），以及如何在配置变更（例如折叠/展开折叠设备、旋转设备或调整窗口大小）时
  保留 UI、导航、滚动和媒体播放状态。还涵盖使用 Navigation3 Scenes 的多窗格布局、目标尺寸可变的
  自适应 UI 组件（例如按钮），以及使用 Compose Grid 和 FlexBox API 的自适应布局（包括导航区域：
  nav rail 与 nav bar）。还涵盖带键盘快捷键、工具提示和自定义光标的桌面端体验。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-24'
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

- 所有屏幕都使用 Compose。如果仍在用 Fragment 或 View，建议使用 XML to Compose skill 迁移这些屏幕。
- 使用 Jetpack Navigation 3。如果没有，建议使用 Navigation 3 skill 迁移应用。

## 让应用自适应的工作流

要让应用自适应，按以下步骤或其中的一部分执行，视任务而定。

- 步骤 1：验证当前 UI
- 步骤 2：让导航栏自适应
- 步骤 3：添加多窗格布局
- 步骤 4：通过改变列数让纵向列表自适应
- 步骤 5：滚动时隐藏应用栏
- 步骤 6：在配置变更时保留 UI 状态
- 步骤 7：添加桌面端体验
- 步骤 8：支持折叠设备

## 步骤 1. 验证当前 UI

确保已存在截图测试，用于在不同形态系数（form factor）上验证当前 UI。如果不存在，添加 [Compose Preview Screenshot Testing
工具](references/android/studio/preview/compose-screenshot-testing-with-testsuites.md)。使用下面的注解为所有主要形态系数创建预览。例如：


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

底部导航栏针对用户竖屏握持手机时的触摸输入做了优化。在平板、展开的折叠设备等更大的手持设备上，导航区域必须能从屏幕边缘访问（导航 rail）。

如果需要为内容提供更多屏幕空间，就隐藏导航区域。这类情形包括：

- 用户向下滚动时隐藏导航栏、向上滚动时重新显示。这里的前提假设是：用户向下滚动时在浏览内容，向上滚动时是想离开该内容去导航。
- 导航区域的内容会造成干扰时隐藏它。例如在相机预览中，或显示全屏照片时。

当详情屏幕在移动端以全屏显示时，在更大屏幕上必须停用全屏模式。

迁移步骤：

- 找到现有的导航栏。
- 把每个条目转换为 `NavigationSuiteItem`。
- 判断导航栏的可见性是否会变化。例如它是否被 `AnimatedContent` 或 `AnimatedVisibility` composable 包裹。如果是，遵循「控制导航区域可见性」中的指引。
- 把承载导航栏的容器（通常是 `Scaffold`）替换为 Material 3 自适应布局库中的 `NavigationSuiteScaffold`。
- 使用 `NavigationSuiteScaffold` 的 `navigationItems` 参数提供导航条目。

### 步骤 2.1. 控制导航区域可见性

如果导航栏的可见性会变化——在某些场景或某些屏幕上被隐藏——这一行为必须在自适应导航区域中保留。这通过 `NavigationSuiteScaffold` 的 `state` 参数实现。

迁移步骤：

- 找出导航栏被隐藏的场景。这通常用一个布尔变量表示可见性。变量名使用 `isNavBarVisible` 或 `shouldShowNavBar`。
- 用 `rememberNavigationSuiteScaffoldState()` 创建 `NavigationSuiteScaffoldState` 实例，并传给 `NavigationSuiteScaffold`。
- 导航区域可见性变化时，用 `LaunchedEffect` 调用 `NavigationSuiteScaffoldState` 的 `show` 或 `hide`。

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

## 步骤 3. 使用 Navigation 3 Scenes 添加多窗格布局

分析代码库，找出相互关联的屏幕——在一个屏幕中点击某个对象，会打开另一个显示与该对象相关信息的屏幕。有两种典型的屏幕关系：列表-详情与辅助窗格。

IMPORTANT: 你必须使用 Navigation 3 的 `SceneStrategy` 方式来实现多窗格布局。不要使用 `ListDetailPaneScaffold` 或 `SupportingPaneScaffold`。

### 步骤 3.1. 列表-详情

#### 识别列表屏幕与详情屏幕

列表-详情布局显示一个条目列表（即列表屏幕），点击某个条目会打开一个显示该条目更多详情的新屏幕（即详情屏幕）。

典型用法包括邮件、笔记和消息这类效率类应用。

除非明确要求，否则当详情内容需要大量屏幕空间时（例如图片或适合全屏呈现的媒体），避免使用这种模式。

#### 添加 Material 列表-详情 SceneStrategy

- 添加 `androidx.compose.material3.adaptive:adaptive-navigation3` 库
- 用 `rememberListDetailSceneStrategy` 创建 `androidx.compose.material3.adaptive.navigation3.ListDetailSceneStrategy`
- 通过 `NavDisplay` 的 `sceneStrategies` 参数把 `ListDetailSceneStrategy` 传给 `NavDisplay`

#### 用 metadata 识别列表屏幕与详情屏幕

- 使用 `ListDetailSceneStrategy.listPane(detailPlaceholder = {
  <placeholder composable> })`，通过 `entry(metadata = ...)` 或 `NavEntry(metadata = ...)` 为列表 entry 添加 metadata。
- 使用 `detailPlaceholder` 参数在没有选中任何列表条目时于详情屏幕添加占位符。
- 使用 `ListDetailSceneStrategy.detailPane()` 为详情 entry 添加 metadata。

#### 重要注意事项

- 当详情屏幕在移动端以全屏显示内容时（内容占满整个屏幕，栏或 rail 被隐藏），如果它属于列表-详情布局，必须停用全屏模式。
- 处于列表-详情布局时，详情屏幕不得显示返回箭头。

参考实现见 [Nav3 **Material** List Detail
recipe](references/android/guide/navigation/navigation-3/recipes/material-listdetail.md)。

### 步骤 3.2. 辅助窗格

找出辅助窗格屏幕：主屏幕显示单个条目，选中它会打开一个含更多详情的「辅助屏幕」。辅助屏幕补充主屏幕的内容，并显示在辅助窗格中。

#### 添加 Material 辅助窗格 `SceneStrategy`

- 如果尚未添加，先添加 `androidx.compose.material3.adaptive:adaptive-navigation3` 库
- 用 `rememberSupportingPaneSceneStrategy` 创建 `androidx.compose.material3.adaptive.navigation3.SupportingPaneSceneStrategy`
- 通过 `NavDisplay` 的 `sceneStrategies` 参数把 `SupportingPaneSceneStrategy` 传给 `NavDisplay`

#### 用 metadata 识别主屏幕与辅助屏幕

- 使用 `SupportingPaneSceneStrategy.mainPane()`，通过 `entry(metadata = ...)` 或 `NavEntry(metadata = ...)` 为主 entry 添加 metadata
- 使用 `SupportingPaneSceneStrategy.supportingPane()` 为辅助 entry 添加 metadata

### 步骤 3.3. 运行截图测试

如果做了改动，记录新的参考文件。请用户目视确认新布局是否正确。

## 步骤 4. 通过改变列数让纵向列表自适应

### 步骤 4.1. 让懒加载列表自适应

查找以下纵向列表 composable：`LazyColumn`、`LazyVerticalGrid`、`LazyVerticalStaggeredGrid`。

迁移步骤：

- 为列选择一个合适的最小宽度（dp）。条目在该宽度下必须对用户清晰可见。
- 对于 `LazyColumn`：改为 `LazyVerticalGrid`，并按后面的说明操作
- 对于 `LazyVerticalGrid`：把 `columns` 参数改为使用 `GridCells.Adaptive(<width>.dp)`
- 对于 `LazyVerticalStaggeredGrid`：把 `columns` 参数改为使用 `StaggeredGridCells.Adaptive(<width>.dp)`

### 步骤 4.2. 把非懒加载列表迁移到 Grid

WARNING: Grid 是自 Compose 1.11.0-beta01 起可用的实验性 API。请先与用户确认他们愿意在代码库中使用实验性 API。

查找任何包含多个同类型条目的 `Column`，并用 `Grid` 替换它。不要替换成 `LazyVerticalGrid` 或任何其他懒加载布局。不要把 `Grid` 放进现有的 `Column` 里。要完全替换它。

`Grid` 通过向其 `config` 参数提供一个 lambda（`GridConfigurationScope` 的扩展函数）来配置。在该 lambda 内，`constraints` 提供网格容器的最小与最大尺寸，可用于根据可用尺寸改变行数与列数。例如，下面的代码配置 `Grid`，使得当可用宽度：

- 小于 800dp 时，使用 2x4 网格
- 大于等于 800dp 时，使用 4x2 网格


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

`Grid` 是实验性 API，因此要在任何使用它的函数上添加 `@OptIn(ExperimentalGridApi::class)` 注解。

## 步骤 5：滚动时隐藏应用栏

在包含多个顶层目的地的应用中，每个屏幕必须独立管理自己的应用栏状态。主要有两种滚动行为：

- `exitUntilCollapsedScrollBehavior`：向下滚动时隐藏，向上滚动时保持隐藏，直到滚动到最顶部（偏移量为 0）。
- `enterAlwaysScrollBehavior`：向下滚动时隐藏，向上滚动时立即显示。

## 步骤 6：在配置变更时保留 UI 状态

IMPORTANT: **绝不**在 `AndroidManifest.xml` 中添加 `android:configChanges` 或 `android:screenOrientation` 来抑制 Activity 重建或锁定方向。退出重建只会掩盖状态丢失缺陷而不是修复它，还会破坏自适应资源重新加载，并阻止应用进程重启。

修复配置变更导致的状态丢失时，要系统地审查所有屏幕、组件和状态持有者中**每一处** `remember` 用法（换句话说，不要只搜索 `remember { mutableStateOf(...) }`）：

### 步骤 6.1. 在 Composable 中保留基础类型与自定义 UI 状态

- 对于用户输入和交互式 UI 状态（例如 `TextField` 的草稿文本、搜索查询、滚动位置和开关状态），把 `remember { mutableStateOf(...) }` 替换为 `rememberSaveable { mutableStateOf(...) }`。
- 适当时用相关标识符作为状态的 key（例如 `rememberSaveable(conversationId) { mutableStateOf("") }`）。
- 对于无法由 `Bundle` 原生保存的自定义数据类或集合（例如 `Set`）：
  - 通过 `var state by rememberSaveable(...) { mutableStateOf(...) }` 委托 `MutableState<T>` 时，用 **`stateSaver`** 传入自定义 `Saver`（当该 block 返回 `MutableState<T>` 时**不要**传 `saver = ...`）：


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

- 另一种做法是给类加上 `@Serializable` 注解并使用 `rememberSerializable`。

### 步骤 6.2. 在懒加载与可滚动布局中保留滚动状态

朴素的 `remember { LazyListState() }`、`remember { LazyGridState() }` 和 `remember { ScrollState(...) }` **不会**在配置变更时保存滚动位置，因为它们绕过了状态类的 `Saver`。

检查所有屏幕和可复用组件中的所有可滚动容器（`LazyColumn`、`LazyRow`、`LazyVerticalGrid`、`LazyHorizontalGrid`、`LazyVerticalStaggeredGrid`、`Modifier.verticalScroll` 和 `Modifier.horizontalScroll`），把朴素的 `remember` 实例化替换为内置的可保存工厂函数：

- `remember { LazyListState() }` -\> `rememberLazyListState()`
- `remember { LazyGridState() }` -\> `rememberLazyGridState()`
- `remember { LazyStaggeredGridState() }` -\> `rememberLazyStaggeredGridState()`
- `remember { ScrollState(initial = 0) }` -\> `rememberScrollState()`

### 步骤 6.3. 保留 Navigation 3 状态与多个返回栈

详见 Navigation 3 指南中的[保存与管理导航状态](references/android/guide/navigation/navigation-3/save-state.md)。

### 步骤 6.4. 保留媒体播放状态（`ExoPlayer` / Media3）

当 MediaPlayer（例如 `ExoPlayer`）在 composable 内用 `remember` 创建时，它会在销毁时被释放，并在配置变更时从头重建，导致播放位置重置为 `0:00`，并且即使用户此前已暂停视频也会自动开始播放。

要保留 `ExoPlayer` 的播放状态（`currentPosition` 和 `playWhenReady`）：

1. 用 `rememberSaveable(videoResId)` 存储 `savedPositionMs`（`mutableLongStateOf(0L)`）和 `savedPlayWhenReady`（`mutableStateOf(true)`）。
2. **在播放过程中持续更新已保存状态 --- 不要只在 `onDispose` 中保存**：在 `Player.Listener`（`onPlayWhenReadyChanged`、`onPositionDiscontinuity`）中更新 `savedPlayWhenReady` 与 `savedPositionMs`，**并且**在活跃期间于 `LaunchedEffect(player)` 循环内周期性更新。
3. **用恢复的状态初始化播放器**：设置 `playWhenReady = savedPlayWhenReady`，并在 `prepare()` 之前调用 `seekTo(savedPositionMs)`。
4. **用 `LifecycleStartEffect` 做保护，避免自动播放已暂停的视频或覆盖 `savedPlayWhenReady`**：
   - 在 `LifecycleStartEffect(player)` 中，仅当 `savedPlayWhenReady` 为 `true` 时才调用 `player.play()`（否则暂停的视频在恢复后会重新开始播放）。
   - 在 `onStopOrDispose` 中，先捕获 `val wasPlaying = player.playWhenReady` 和 `savedPositionMs = player.currentPosition`，再调用 `player.pause()`，然后把 `savedPlayWhenReady = wasPlaying` 恢复回去，这样停止/销毁时的 `player.pause()` 就不会把 `savedPlayWhenReady` 覆盖为 `false`：


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

## 步骤 7：添加桌面端体验

### 步骤 7.1：确定所需的桌面端功能

查看用户的提示词、需求或上传的文件，确定需要实现哪项桌面端功能。

### 步骤 7.2：执行针对该功能的处理

根据识别出的功能，你必须阅读对应的参考文件并遵循其中的说明：

- **Keyboard Shortcuts** -\> 阅读 [`references/keyboard_shortcuts.md`](references/keyboard_shortcuts.md)
- **Tooltips** -\> 阅读 [`references/tooltips.md`](references/tooltips.md)
- **Custom Cursors** -\> 阅读 [`references/custom_cursors.md`](references/custom_cursors.md)

每个参考文件都从在整个应用中搜索该功能的目标开始。先把这份清单写下来，实现全部条目（不要只做你打开的第一个屏幕），并在完成前重新核对清单。

## 步骤 8. 支持折叠设备

桌面模式（tabletop mode）允许用户把折叠设备放在平坦表面上时查看并操作内容。上屏以一个便于观看的角度倾斜，用于呈现视觉内容。下屏平放在表面上，为该内容提供控件。

要支持折叠设备，找出提供以下体验的屏幕：

- 媒体与音频播放或流式播放：视频或音频内容渲染在竖起的上屏。评论、详情与播放进度条控件渲染在平放的下屏表面。
- 视频通话：远端参与者显示在竖起的屏幕上。麦克风与摄像头开关、参与者列表和聊天控件位于平放的下屏表面。
- 相机拍摄：相机取景器显示在竖起的屏幕上。快门按钮、变焦控件与曝光滑块位于平放的下屏表面，便于免手持拍摄。
- 照片编辑：图像画布无遮挡地显示在竖起的屏幕上。滑块、预设调色板和曲线仍可在平放的下屏表面访问。
- 音频混音：波形与分轨控件显示在竖起的屏幕上。唱盘与打击垫位于平放的下屏表面。
- 烹饪：在竖起的屏幕上免手持查看食谱步骤，同时把计时器或步骤导航放在下屏。
- 幻灯片放映：在上屏查看演示文稿幻灯片，在屏幕下方显示演讲者备注或导航。

要在这些屏幕上为折叠设备创建布局，你必须阅读
[桌面姿态](references/foldable-tabletop.md)。

## 最后一步：构建并测试

构建应用并运行本地测试。如果项目有截图测试，运行它们，但不要更新参考图。请用户在查看截图差异后再执行更新。

## 实验性自适应 API 的补充文档

以下 API 从 Compose 1.11.0 起可用。

### FlexBox

查阅 FlexBox 文档：

- [概述](references/android/develop/ui/compose/layouts/adaptive/flexbox/index.md)
- [入门 - 配置](references/android/develop/ui/compose/layouts/adaptive/flexbox/get-started.md)
- [设置容器行为](references/android/develop/ui/compose/layouts/adaptive/flexbox/container-behavior.md)
- [设置条目行为](references/android/develop/ui/compose/layouts/adaptive/flexbox/item-behavior.md)

## MediaQuery

当你需要查询设备的屏幕尺寸、指针精度、键盘类型、是否具备摄像头或麦克风以及其他设备能力时，查阅 [MediaQuery 文档](references/android/develop/ui/compose/layouts/adaptive/mediaquery/index.md)。

## Grid

当你需要在网格布局中显示固定数量的条目时，查阅 Grid 文档：

- [概述](references/android/develop/ui/compose/layouts/adaptive/grid/index.md)
- [入门 - 配置](references/android/develop/ui/compose/layouts/adaptive/grid/get-started.md)
- [设置容器属性](references/android/develop/ui/compose/layouts/adaptive/grid/container-properties.md)
- [设置条目属性](references/android/develop/ui/compose/layouts/adaptive/grid/item-properties.md)
