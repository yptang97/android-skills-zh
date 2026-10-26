---
name: leanback-to-compose-tv-migration
description: 提供把 Android TV 应用从旧版 Leanback UI Toolkit、Android Views 或 Support Fragments
  迁移到 Jetpack Compose for TV（androidx.tv）的说明与架构模式。适用于 Leanback 到 Compose
  的迁移，包括浏览屏幕、设置屏幕、认证屏幕、登录屏幕或视频播放屏幕的迁移，或在你需要用现代
  Compose 等价物替换 BrowseSupportFragment、LeanbackSettingsFragment、PreferenceFragment、
  BaseLeanbackPreferenceFragmentCompat、VideoSupportFragment、GuidedStepSupportFragment、
  SearchSupportFragment、VerticalGridSupportFragment、Presenter、ArrayObjectAdapter 或
  CursorMapper 时使用；也适用于实现带焦点记忆的沉浸式轮播、使用 PlayerSurface 的 Media3 视频
  播放，或自定义 10 英尺主视觉布局。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-18'
  keywords:
  - Android TV
  - Jetpack Compose
  - Leanback
  - migration
  - androidx.tv
  - Carousel
  - 10-foot UI
  - PlayerSurface
  - Media3
  - focusRestorer
  - FocusRequester
  - TV development
  - Android Views
  - LeanbackSettingsFragment
  - PreferenceFragment
  - BrowseSupportFragment
---

## 10 英尺 UI

「10 英尺 UI」是面向电视的设计范式，它把界面调整为适合约 3 米（10 英尺）观看距离的形态。设计这类体验时，请考虑以下关键特征：

- **观看距离**：观众坐得离屏幕较远，处于「向后靠」的观看状态。屏幕布局要简洁，文字与 UI 元素要大到能在远处舒适阅读，避免密集的文字块。
- **色彩对比度**：为避免在对比度较低的电视屏幕上出现色彩发白，设计采用高对比度的配色和明确的视觉指示，使聚焦状态在不同电视面板上都清晰可见。
- **D-pad 导航**：交互依赖方向键遥控器，仅支持有限的方向键操作（`Up`、`Down`、`Left`、`Right`），组件按清晰的空间网格与轮播排列，且不出现焦点陷阱。

## 核心架构与库的选择

把 Android TV 应用迁移到 Jetpack Compose 时，你必须使用 `androidx.tv` 库，并遵循以下 10 英尺 UI 模式：

- **UI 现代化**：关注自定义的电影感布局，而不是沿用旧版的 1:1 直接模板。你必须使用 Jetpack Compose for TV 的功能，例如动态渐变主视觉背景、自定义焦点动画、自定义导航抽屉和自定义布局。
- **主设计系统**：你必须始终使用 `androidx.tv.material3.*`（`androidx.tv:tv-material`），而不是移动端的 `androidx.compose.material3.*`。TV Material 3 内置 D-Pad 焦点处理、焦点缩放，以及针对 TV 优化的字体排版与形状。要配置 Compose for TV 依赖，请参阅 [Compose for TV 配置](references/android/training/tv/playback/compose/index.md)。
- **焦点缩放动画**：对可交互卡片，你必须使用 `CompactCard`、`ClassicCard` 或 `WideCardContainer`，并设置 `scale = CardDefaults.scale(focusedScale = 1.1f)`，以提供标准的 TV 焦点动画。
- **Coil 图片加载**：要在不显式传入 `ImageLoader` 参数的情况下使用声明式 `AsyncImage(model, contentDescription, ...)`，你必须在 Gradle 依赖中包含 `io.coil-kt:coil-compose`。
- **显式导入**：你必须始终显式导入 TV Material 3 的类（例如 `import androidx.tv.material3.Surface`、`import androidx.tv.material3.ListItem`），不要使用通配符导入（`import androidx.tv.material3.*`）。
- **文件命名约定**：Composable 屏幕文件必须按屏幕命名（例如把 `BrowseScreen` 命名为 `BrowseScreen.kt`，`PlaybackScreen` 命名为 `PlaybackScreen.kt`，`AuthenticationScreen` 命名为 `AuthenticationScreen.kt`）。不要使用 `Main` 这类泛化前缀。
- **过扫描与屏幕边框**：你必须对根容器、轮播和顶部栏应用水平内边距（例如 `horizontal = 48.dp` 或 `32.dp`、`vertical = 24.dp`），以防内容被裁切。
- **阅读宽度限制**：对长文本，你必须用 `Modifier.widthIn(max = 600.dp)` 限制文字列的最大宽度。
- **Media3 Compose 依赖**：在现代化媒体播放屏幕时，请在 `app/build.gradle` 中包含 `androidx.media3:media3-ui-compose`。
- **禁止使用旧版 AndroidView 包装**：不要用旧版 `AndroidView` 包装把基于 View 的组件嵌入 Jetpack Compose 屏幕。所有迁移后的屏幕必须使用 Compose 组件或 Media3 Compose 表面（`PlayerSurface`）。

## D-pad 焦点处理与导航

Jetpack Compose for TV（`androidx.tv.material3`）需要显式管理焦点，因为组件不会自动获得初始焦点，且导航基于二维空间坐标。要配置 TV 的 D-pad 导航，请按 [TV Navigation 指南](references/android/training/tv/get-started/navigation.md)中的说明操作。

### 初始焦点

你必须用 `FocusRequester` 把初始焦点分配给每个屏幕上的主要可交互元素（例如第一个操作按钮、卡片或 `ListItem`）。定义 `val focusRequester = remember { FocusRequester() }`，把 `Modifier.focusRequester(focusRequester)` 附加到该主要元素上，并在 `LaunchedEffect(Unit) { focusRequester.requestFocus() }` 中请求焦点：

```kotlin
val focusRequester = remember { FocusRequester() }
val focusManager = LocalFocusManager.current

LaunchedEffect(Unit) {
    focusRequester.requestFocus()
}
```

<br />

*注意：对于状态会变化或包含 pager 的屏幕（例如使用 `HorizontalPager` 的 `OnboardingScreen`），你必须把状态键传给 `LaunchedEffect`（例如 `LaunchedEffect(pagerState.currentPage)`），以便在页面切换时重新应用焦点。*

### 双向焦点路由与避免焦点陷阱

当可交互元素分布在显示区域的两侧时，标准的二维空间导航无法在它们之间找到目标。这会形成焦点陷阱，用户无法用 D-pad 从某个区域导航出去。

要实现对称、双向且没有焦点陷阱的 D-pad 导航，你应尽可能依赖 Compose 的二维空间焦点引擎。当跨越可滚动容器（例如 `LazyColumn` 或 `LazyRow`）连接相邻的 UI 元素时，不要为 lazy 列表内的单个条目设置方向覆盖（`up = ...`、`down = ...`）。当条目在垂直导航过程中滚出屏幕时，它的 `FocusRequester` 会变成未初始化状态，在焦点搜索时抛出 `IllegalStateException`：

```kotlin
Row(
    modifier = Modifier
        .fillMaxWidth()
        .padding(horizontal = 48.dp, vertical = 16.dp),
    horizontalArrangement = Arrangement.End
) {
    Button(
        onClick = { /* Search */ },
        modifier = Modifier.focusRequester(topBarFocusRequester)
    ) { Text("Search") }
}
```

<br />

### 行级焦点记忆（`Modifier.focusRestorer`）

在水平轮播（`LazyRow`）之间垂直导航时，Compose 默认的二维空间焦点引擎会沿当前聚焦条目的 X 坐标搜索。如果用户在 Row 1 中向右滚动（例如滚到 X=800dp 处的 Item 4），然后按 DOWN 想导航到 Row 2，空间路由会聚焦 Row 2 中位于 X=800dp 的那个条目。

要让每一行各自记住卡片的焦点位置（再次访问时把焦点恢复到上次访问的条目），你必须把 **`Modifier.focusRestorer`**（不带参数）直接附加到 `LazyRow` 上。不要在 lazy 容器中传入自定义的兜底 `FocusRequester` lambda，因为在快速 D-pad 滚动时对未附加或已滚出屏幕的条目调用 `requestFocus` 会抛出 `IllegalStateException`。

```kotlin
LazyRow(
    modifier = Modifier.focusRestorer(),
    contentPadding = PaddingValues(horizontal = 48.dp),
    horizontalArrangement = Arrangement.spacedBy(16.dp)
) {
    itemsIndexed(videos) { vidIndex, video ->
        CompactCard(
            onClick = { onVideoClick(video) },
            image = {
                AsyncImage(
                    model = video.cardImageUrl,
                    contentDescription = video.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
            },
            title = { Text(video.title) },
            modifier = Modifier
                .then(
                    if (catIndex == 0 && vidIndex == 0) {
                        Modifier.focusRequester(firstCardFocusRequester)
                    } else {
                        Modifier
                    }
                )
                .onFocusChanged { focusState ->
                    if (focusState.isFocused) {
                        focusedVideo = video
                        focusedCategoryIndex = catIndex
                    }
                }
        )
    }
}
```

<br />

### 文本输入、硬件键盘回车拦截与 IME 焦点串联

从 Leanback（`SearchSupportFragment`、`GuidedStepSupportFragment`）迁移搜索栏或登录表单时，不要使用裸 `BasicTextField` 容器或空的 `Surface(onClick = {})` 包装，因为它们会导致 D-pad CENTER 键无法唤起虚拟键盘（IME）。

1. **可点击的 TV 表面包装并拦截返回键（`onPreviewKeyEvent`）**：把标准 M3 `TextField` 包在可聚焦的 TV `Surface(onClick = { focusRequester.requestFocus() }, scale = ClickableSurfaceDefaults.scale(focusedScale = 1.01f), border = ClickableSurfaceDefaults.border(focusedBorder = Border(BorderStroke(2.dp, Color.White))))` 中，以提供聚焦描边和 D-pad 焦点缩放。你必须在文本框或包装层上附加 `Modifier.onPreviewKeyEvent`，拦截 `Key.Back` 和 `Key.Escape`，使用户能在不退出屏幕的情况下移除输入框焦点。
2. **为什么必须拦截返回键**：在 Android TV 上编辑文本框时，按 D-pad 的 **Back** 键通常会返回并退出屏幕。通过在 `onPreviewKeyEvent` 中拦截 `KeyUp` 上的 `Key.Back` 和 `Key.Escape` 来结束编辑（清除焦点），用户就能回到 D-pad 表单导航，而不会被困在文本框里或误退出屏幕。
3. **IME 焦点串联**：对多字段表单（例如认证屏幕中的用户名和密码），在上方字段上附加 `KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) })` 与 `ImeAction.Next`，把焦点向下传递给下一个输入框；在底部字段上使用 `ImeAction.Done`，把焦点直接交给提交按钮：

```kotlin
Surface(
    onClick = { focusRequester.requestFocus() },
    border = ClickableSurfaceDefaults.border(focusedBorder = Border(border = BorderStroke(2.dp, Color.White))),
    modifier = Modifier
        .fillMaxWidth()
        .focusRequester(focusRequester)
) {
    OutlinedTextField(
        value = username,
        onValueChange = { username = it },
        label = { Text("Username") },
        singleLine = true,
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
        keyboardActions = KeyboardActions(onNext = { focusManager.moveFocus(FocusDirection.Down) }),
        modifier = Modifier
            .fillMaxWidth()
            .onPreviewKeyEvent { event ->
                if (event.type == KeyEventType.KeyDown && (event.key == Key.Enter || event.key == Key.NumPadEnter)) {
                    focusManager.moveFocus(FocusDirection.Down)
                    true
                } else false
            }
    )
}

Surface(
    onClick = {},
    border = ClickableSurfaceDefaults.border(focusedBorder = Border(border = BorderStroke(2.dp, Color.White))),
    modifier = Modifier.fillMaxWidth()
) {
    OutlinedTextField(
        value = password,
        onValueChange = { password = it },
        label = { Text("Password") },
        singleLine = true,
        visualTransformation = PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
        keyboardActions = KeyboardActions(onDone = { onLoginSuccess() }),
        modifier = Modifier
            .fillMaxWidth()
            .onPreviewKeyEvent { event ->
                if (event.type == KeyEventType.KeyDown && (event.key == Key.Enter || event.key == Key.NumPadEnter)) {
                    onLoginSuccess()
                    true
                } else false
            }
    )
}
```

<br />

## Lazy 容器

在 Jetpack Compose for TV 中实现可滚动列表或网格时，你必须使用 `androidx.compose.foundation.lazy` 和 `androidx.compose.foundation.lazy.grid` 中的标准 `LazyColumn`、`LazyRow` 和 `LazyVerticalGrid`。对于目录浏览布局，请按 [Catalog Browser 指南](references/android/training/tv/playback/compose/browse.md)中的说明操作。

1. **用 `BringIntoViewSpec` 实现轴心滚动**：当使用 `BringIntoViewSpec` 与 `CompositionLocalProvider(LocalBringIntoViewSpec provides ...)` 为目录行定义自定义轴心滚动线时，你必须确保项目基于 Compose Foundation 1.7.0+ 编译，可在 `app/build.gradle` 中添加 `implementation platform('androidx.compose:compose-bom:2024.06.00')`（或更新版本），或添加 `implementation 'androidx.compose.foundation:foundation:1.7.0'`。若没有 Compose Foundation 1.7.0+，`import androidx.compose.foundation.gestures.LocalBringIntoViewSpec` 会失败并报 `Unresolved reference: LocalBringIntoViewSpec`。
2. **行级焦点记忆（`Modifier.focusRestorer`）**：用 `@OptIn(ExperimentalFocusRestorerApi::class, ExperimentalComposeUiApi::class)` 注解你的 composable，并在每个分类 `LazyRow` 上附加 `Modifier.focusRestorer`，以便在目录行之间垂直导航时记住并恢复上次聚焦的卡片。

当用可聚焦的 TV Material 3 组件（`CompactCard`、`ListItem`、`Button`）填充时，标准 Compose lazy 容器会自动处理二维 D-Pad 焦点路由、焦点记忆和边缘滚动：

```kotlin
@Composable
fun CatalogBrowser(
    featuredContentList: List<Movie>,
    sectionList: List<Section>,
    modifier: Modifier = Modifier,
    onItemSelected: (Movie) -> Unit = {},
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        items(sectionList.size) { index ->
            val section = sectionList[index]
            SectionRow(section, onItemSelected = onItemSelected)
        }
    }
}
```

<br />

## Media3 视频播放与播放控制条

迁移旧版 Leanback 视频播放（`VideoSupportFragment` / `PlaybackGlue`）时，请使用 Compose Media3 的 `PlayerSurface`（`androidx.media3.ui.compose.PlayerSurface`），并配合半透明的播放控制覆盖层：

1. **必须包含 Media3 播放控制按钮（`PlayPauseButton`）**：在 `PlayerSurface` 之上，你必须叠加一条半透明底部控制栏（`Box(modifier = Modifier.align(Alignment.BottomCenter))`），其中包含明确的 Media3 UI Compose 按钮：至少要有 `PlayPauseButton`、`SeekBackButton` 和 `SeekForwardButton`。绝不能让播放控制覆盖层为空。要使用这些 composable，你必须在 `app/build.gradle` 依赖中，与 `androidx.media3:media3-ui-compose` 一起添加 `implementation 'androidx.media3:media3-ui-compose-material3:1.6.0'`。
2. **D-pad 方向键快进快退（`onPreviewKeyEvent`）**：要支持用遥控器 D-pad 前进和后退，请在容器或控制覆盖层上附加 `Modifier.onPreviewKeyEvent`，拦截 Compose 的 `Key.DirectionLeft` 和 `Key.DirectionRight`（例如 `keyEvent.key == Key.DirectionLeft`），以 10 秒为单位后退和前进（`exoPlayer.seekTo(exoPlayer.currentPosition - 10000)`）。绝不要使用旧版 Android View 的 keycode（`KeyEvent.KEYCODE_DPAD_LEFT` 或 `nativeKeyEvent.keyCode`）。
3. **禁止使用旧版 AndroidView 包装**：不要用 `AndroidView { ... }` 包装旧版 `PlayerView` 或 `StyledPlayerView`。在 Compose for TV 中，你必须用 `PlayerSurface`（`androidx.media3.ui.compose.PlayerSurface`）配合 `ExoPlayer` 渲染视频。

## 分阶段迁移策略

为了在不破坏编译、不引入循环依赖的前提下干净地完成迁移，请分五个阶段执行：

- **阶段 1**：基础设施与设计系统
- **阶段 2**：叶子屏幕与独立屏幕
- **阶段 3**：核心浏览与发现屏幕
- **阶段 4**：详情与媒体播放
- **阶段 5**：最终统一与清理

### 阶段 1：基础设施与设计系统

- 创建 `TvTheme.kt`，用自定义的 `ColorScheme`、`Typography` 和 `Shapes` 包装 `TvMaterialTheme`。
- 构建原子化的可复用组件：`MovieCard`、`SectionHeader`、`LoadingIndicator`、`ErrorState`。

### 阶段 2：叶子屏幕与独立屏幕

- 先迁移没有出站导航的屏幕，例如错误提示、引导页或设置页，把它们分别替换为 `ErrorDialog`、`OnboardingScreen` 和 `SettingsScreen`。
- 把使用 `BaseLeanbackPreferenceFragmentCompat`、`BaseLeanbackPreferenceFragment` 或 `LeanbackSettingsFragment` 的地方改为 Compose，例如使用直接绑定 `SharedPreferences` 的 `ListItem` + `Switch`，并替换 `findPreference` 的实现。
- 确保每个屏幕用 `FocusRequester` 让该屏幕的第一个或主要组件获得初始 D-pad 焦点，例如聚焦第一个 `ListItem`。
- 用 `ComponentActivity` 类型的 activity 替换旧版 `Fragment` 类，在 Compose 中以声明式方式使用组件。
- 清理 `res/values/styles.xml` 与 `res/values/themes.xml` 中的旧版样式和主题引用（例如移除指向 `@style/PreferenceThemeOverlay.v14.Leanback` 的 `preferenceTheme`），这些在移除 leanback 依赖后不再受支持：

```kotlin
@Composable
fun TvSettingsScreen(
    modifier: Modifier = Modifier
) {
    var autoPlayNext by remember { mutableStateOf(true) }
    var highQualityAudio by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(48.dp)
    ) {
        Text(
            text = "Settings",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item {
                ListItem(
                    selected = false,
                    onClick = { autoPlayNext = !autoPlayNext },
                    headlineContent = { Text("Autoplay Next Video") },
                    supportingContent = { Text("Automatically start playing next item in queue") },
                    trailingContent = {
                        Switch(
                            checked = autoPlayNext,
                            onCheckedChange = null
                        )
                    }
                )
            }

            item {
                ListItem(
                    selected = false,
                    onClick = { highQualityAudio = !highQualityAudio },
                    headlineContent = { Text("High Quality Audio") },
                    supportingContent = { Text("Use spatial audio and multi-channel output when available") },
                    trailingContent = {
                        Switch(
                            checked = highQualityAudio,
                            onCheckedChange = null
                        )
                    }
                )
            }
        }
    }
}
```

<br />

### 阶段 3：核心浏览与发现屏幕

- 迁移 `VerticalGridScreen`（`LazyVerticalGrid`）、`SearchScreen`（带实时列表过滤的 `BasicTextField`）和 `BrowseScreen`（由多个 `LazyRow` 组成的 `LazyColumn`）。
- 彻底清除旧版 `ArrayObjectAdapter`、`ListRowPresenter`、`CardPresenter` 和 `HeaderItem` 类。

### 阶段 4：详情与媒体播放

- 迁移 `VideoDetailsScreen` 和 `GuidedStepScreen`。
- 迁移 `PlaybackScreen`，使用 Compose Media3 的 `PlayerSurface`（`androidx.media3.ui.compose.PlayerSurface`），并搭配包含 Media3 Compose 播放控制（例如 `PlayPauseButton`、`SeekBackButton`、`SeekForwardButton`）的半透明底部覆盖层。

### 阶段 5：最终统一与清理

- 删除所有剩余旧版 `.java` activity、fragment、presenter 和 XML 布局文件。
- 确保所有 activity 都继承 `ComponentActivity` 或 `FragmentActivity`，并调用 `setContent { ... }`。
- 从 `res/values/styles.xml` 与 `res/values/themes.xml` 中彻底移除旧版 Leanback 主题与样式声明（例如任何继承自 `Theme.Leanback` 或引用 `lb_` 样式的样式）。

## 组件与类映射指南

| 旧版 Leanback / View 类 | 现代 Jetpack Compose 等价物 |
|---|---|
| `BrowseSupportFragment` / `MainFragment` | `BrowseScreen`（包含分类 `LazyRow` 的 `LazyColumn` + 主视觉横幅） |
| `DetailsSupportFragment` | `VideoDetailsScreen`（海报图、文字列、操作按钮、相关推荐 `LazyRow`） |
| `VideoSupportFragment` / `PlaybackGlue` | `PlaybackScreen`（Media3 `ExoPlayer` + Compose `PlayerSurface`） |
| `GuidedStepSupportFragment` | `GuidedStepScreen`（分屏布局：左侧 40% 为引导面板，右侧 60% 为操作面板） |
| `SearchSupportFragment` | `SearchScreen`（`BasicTextField` + 实时过滤 + `LazyVerticalGrid`） |
| `VerticalGridSupportFragment` | `VerticalGridScreen`（`LazyVerticalGrid(columns = GridCells.Fixed(5))`） |
| `ArrayObjectAdapter` / `Presenter` | 观察不可变 `State<List<T>>` 的声明式 `@Composable` 函数 |
| `CursorMapper` / `LoaderManager` / `CursorLoader` | Kotlin 协程 / Repository 对象中的 `withContext(Dispatchers.IO)` |
| `OnboardingSupportFragment` | `OnboardingScreen`（`HorizontalPager` + D-Pad 导航按钮） |
| `LeanbackSettingsFragment` / `PreferenceFragment` | `SettingsScreen`（首个 `ListItem` 上的 `FocusRequester` + 绑定 `SharedPreferences` 的尾部 `Switch`） |

## 参考实现与经过验证的模式

### 现代 TV 沉浸式列表架构（`BrowseScreen`）

构建 10 英尺 TV 浏览屏幕或沉浸式列表时，不要把主视觉横幅放在滚动列表之前或之外，也不要用程序化 `animateScrollToItem` 调用去对抗 Compose 自动的 `BringIntoView` 系统。

改为使用 Compose Foundation 的 `BringIntoViewSpec` 与 `LocalBringIntoViewSpec` 定义精确的 TV 轴心滚动（例如把活动行定位在距显示区域顶部 35% 的位置）。再配合可变形的沉浸式行：当下方行获得焦点（`focusedCategoryIndex > 0`）时，隐藏主视觉文字，并在 Row 0 上显示普通的区块标题：

```kotlin
@Composable
fun ImmersiveBrowseScreen(
    categories: Map<String, List<Video>>,
    onVideoClick: (Video) -> Unit
) {
    var focusedVideo by remember { mutableStateOf<Video?>(null) }
    var focusedCategoryIndex by remember { mutableStateOf(0) }
    val listState = rememberLazyListState()
    val topBarFocusRequester = remember { FocusRequester() }
    val firstCardFocusRequester = remember { FocusRequester() }

    Box(modifier = Modifier.fillMaxSize()) {
        AsyncImage(
            model = focusedVideo?.bgImageUrl,
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )

        PositionFocusedItemInLazyLayout(parentFraction = 0.35f, childFraction = 0.5f) {
            LazyColumn(
                state = listState,
                contentPadding = PaddingValues(top = 36.dp, bottom = 64.dp),
                verticalArrangement = Arrangement.spacedBy(28.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 48.dp, vertical = 16.dp),
                        horizontalArrangement = Arrangement.End
                    ) {
                        Button(
                            onClick = { /* Search */ },
                            modifier = Modifier.focusRequester(topBarFocusRequester)
                        ) { Text("Search") }
                    }
                }

                itemsIndexed(categories.entries.toList()) { catIndex, (categoryName, videos) ->
                    Column {
                        if (catIndex == 0 && focusedCategoryIndex == 0) {
                            Column(
                                modifier = Modifier
                                    .heightIn(min = 200.dp)
                                    .padding(horizontal = 48.dp)
                            ) {
                                Text(
                                    text = focusedVideo?.title ?: "",
                                    style = MaterialTheme.typography.displayMedium
                                )
                                Text(
                                    text = focusedVideo?.description ?: "",
                                    style = MaterialTheme.typography.bodyLarge
                                )
                            }
                        } else {
                            Text(
                                text = categoryName,
                                style = MaterialTheme.typography.titleMedium,
                                modifier = Modifier.padding(horizontal = 48.dp, vertical = 8.dp)
                            )
                        }

                        LazyRow(
                            modifier = Modifier.focusRestorer(),
                            contentPadding = PaddingValues(horizontal = 48.dp),
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            itemsIndexed(videos) { vidIndex, video ->
                                CompactCard(
                                    onClick = { onVideoClick(video) },
                                    image = {
                                        AsyncImage(
                                            model = video.cardImageUrl,
                                            contentDescription = video.title,
                                            contentScale = ContentScale.Crop,
                                            modifier = Modifier.fillMaxSize()
                                        )
                                    },
                                    title = { Text(video.title) },
                                    modifier = Modifier
                                        .then(
                                            if (catIndex == 0 && vidIndex == 0) {
                                                Modifier.focusRequester(firstCardFocusRequester)
                                            } else {
                                                Modifier
                                            }
                                        )
                                        .onFocusChanged { focusState ->
                                            if (focusState.isFocused) {
                                                focusedVideo = video
                                                focusedCategoryIndex = catIndex
                                            }
                                        }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun PositionFocusedItemInLazyLayout(
    parentFraction: Float = 0.35f,
    childFraction: Float = 0.5f,
    content: @Composable () -> Unit,
) {
    val bringIntoViewSpec = remember(parentFraction, childFraction) {
        object : BringIntoViewSpec {
            override fun calculateScrollDistance(
                offset: Float,
                size: Float,
                containerSize: Float
            ): Float {
                if (offset >= 0f && offset <= containerSize * 0.45f) {
                    return 0f
                }
                val initialTargetForLeadingEdge = parentFraction * containerSize - (childFraction * size)
                val targetForLeadingEdge = if (size <= containerSize && (containerSize - initialTargetForLeadingEdge) < size) {
                    containerSize - size
                } else {
                    initialTargetForLeadingEdge
                }
                return offset - targetForLeadingEdge
            }
        }
    }
    CompositionLocalProvider(LocalBringIntoViewSpec provides bringIntoViewSpec, content = content)
}
```

<br />

### Compose TV 中的 Media3 播放（`PlaybackScreen`）

用 `androidx.media3.ui.compose.PlayerSurface` 作为视频渲染画布实现自定义播放屏幕。把 Material3 播放控制（`androidx.media3:media3-ui-compose-material3` 中的 `SeekBackButton`、`PlayPauseButton`、`SeekForwardButton`）放在半透明底部覆盖层中叠加到表面之上，并用自动隐藏超时处理 D-pad 遥控按键事件：

```kotlin
@OptIn(UnstableApi::class)
@Composable
fun Media3PlaybackScreen(
    video: Video,
    onFinish: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val exoPlayer = remember(context) { ExoPlayer.Builder(context).build() }
    var showControls by remember { mutableStateOf(true) }
    val focusRequester = remember { FocusRequester() }
    val coroutineScope = rememberCoroutineScope()
    var autoHideJob by remember { mutableStateOf<Job?>(null) }

    fun scheduleAutoHide() {
        autoHideJob?.cancel()
        autoHideJob = coroutineScope.launch {
            delay(5000)
            showControls = false
        }
    }

    DisposableEffect(exoPlayer) {
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {
                if (playbackState == Player.STATE_ENDED) {
                    onFinish()
                }
            }
        }
        exoPlayer.addListener(listener)
        onDispose {
            autoHideJob?.cancel()
            exoPlayer.removeListener(listener)
            exoPlayer.release()
        }
    }

    LaunchedEffect(video) {
        focusRequester.requestFocus()
        scheduleAutoHide()

        val mediaItem = MediaItem.fromUri(video.videoUrl)
        exoPlayer.setMediaItem(mediaItem)
        exoPlayer.prepare()
        exoPlayer.playWhenReady = true
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black)
            .focusRequester(focusRequester)
            .focusable()
            .onPreviewKeyEvent { event ->
                if (event.type == KeyEventType.KeyDown) {
                    when (event.key) {
                        Key.DirectionCenter, Key.Enter, Key.NumPadEnter, Key.MediaPlayPause, Key.Spacebar -> {
                            if (exoPlayer.isPlaying) exoPlayer.pause() else exoPlayer.play()
                            showControls = true
                            scheduleAutoHide()
                            true
                        }
                        Key.DirectionLeft, Key.MediaRewind -> {
                            val newPos = (exoPlayer.currentPosition - 10_000L).coerceAtLeast(0L)
                            exoPlayer.seekTo(newPos)
                            showControls = true
                            scheduleAutoHide()
                            true
                        }
                        Key.DirectionRight, Key.MediaFastForward -> {
                            val duration = exoPlayer.duration.coerceAtLeast(0L)
                            val newPos = (exoPlayer.currentPosition + 10_000L).coerceAtMost(duration)
                            exoPlayer.seekTo(newPos)
                            showControls = true
                            scheduleAutoHide()
                            true
                        }
                        Key.DirectionUp, Key.DirectionDown -> {
                            showControls = !showControls
                            if (showControls) scheduleAutoHide() else autoHideJob?.cancel()
                            true
                        }
                        else -> false
                    }
                } else false
            },
        contentAlignment = Alignment.Center
    ) {
        PlayerSurface(
            player = exoPlayer,
            modifier = Modifier.fillMaxSize()
        )

        if (showControls) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color(0x80000000))
                    .padding(48.dp),
                contentAlignment = Alignment.BottomCenter
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(24.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    SeekBackButton(player = exoPlayer)
                    PlayPauseButton(player = exoPlayer)
                    SeekForwardButton(player = exoPlayer)
                }
            }
        }
    }
}
```

<br />

### 用响应式协程 Flow 替换 CursorLoader

用返回 `Flow` 的 repository 替换旧版 `LoaderManager.LoaderCallbacks<Cursor>` 和 `CursorObjectAdapter`，该 `Flow` 观察数据库变化，并在为空时触发异步拉取：

```kotlin
object VideoFlowRepository {
    fun getVideosFlow(context: Context, contentUri: Uri): Flow<List<Video>> = callbackFlow {
        val contentObserver = object : ContentObserver(Handler(Looper.getMainLooper())) {
            override fun onChange(selfChange: Boolean) {
                trySend(queryVideos(context, contentUri))
            }
        }

        context.contentResolver.registerContentObserver(
            contentUri,
            true,
            contentObserver
        )

        val initialVideos = queryVideos(context, contentUri)
        trySend(initialVideos)

        awaitClose {
            context.contentResolver.unregisterContentObserver(contentObserver)
        }
    }.flowOn(Dispatchers.IO)

    private fun queryVideos(context: Context, uri: Uri): List<Video> {
        // Query database or ContentProvider
        return emptyList()
    }
}
```

<br />
