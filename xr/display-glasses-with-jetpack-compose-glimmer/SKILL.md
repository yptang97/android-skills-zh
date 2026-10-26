---
name: display-glasses-with-jetpack-compose-glimmer
description: 提供使用 Jetpack Compose Glimmer UI 工具包为显示眼镜开发投影式 Android XR
  应用的指南。涵盖眼镜形态下的 Glimmer 设计原则、工作流与交互模型。当你需要用 Jetpack Compose
  Glimmer 构建 Android XR 增强体验应用时，使用这个 skill。不适用于无显示屏的纯音频 AI
  眼镜、非眼镜形态的 Android XR 头显（用 Jetpack Compose for XR 实现的空间面板或 3D 体积），
  以及手机和平板的 Material 3 UI。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - Jetpack Compose Glimmer
  - display glasses
  - Projected Activity
  - GlimmerTheme
  - Additive Display
  - Android XR - Augmented Experiences
---

## 术语表

| 术语 | 定义 |
|---|---|
| **智能眼镜** | 带扬声器、摄像头与麦克风的免手持眼镜（纯音频或带显示屏的眼镜）。 |
| **显示眼镜** | 带私有镜片内显示屏的眼镜，可与音频配合提供一眼可读的视觉信息。 |
| **Jetpack Compose Glimmer** | 为显示眼镜提供组件、主题与焦点行为的 Compose UI 工具包。 |
| **投影式 Activity** | 运行在手机宿主上的 `Activity`，其 UI 与输入被投影到已连接的眼镜。 |
| **投影设备** | 连接到 Android 宿主手机的 XR 眼镜设备，应用内容会投影到该设备。 |
| **GlimmerTheme** | 为 `GlimmerColors`、`GlimmerTypography` 与 `GlimmerShapes` 提供样式的根 provider。 |
| **叠加式显示屏** | 通过向场景叠加光线、使黑色（`#000000`）呈现为 100% 透明的显示屏。 |
| **增强体验** | 轻量、叠加式的 Android XR 体验，帮助用户在移动场景中获得辅助。 |
| **视角** | XR 中的感知尺寸；可读文本的最小值为 0.6 度（1 米处约 18sp）。 |

## 前置条件

- 目标 `compileSdk` 为 37 或更高（`compileSdk = 37` 或 `compileSdk { version
  = release(37) }`）。如果更低，把 `compileSdk` 更新到 37。
- 添加依赖时，遵循 [为智能眼镜创建第一个
  Activity](https://developer.android.com/develop/xr/jetpack-xr-sdk/ai-glasses/first-activity)：
  - `androidx.xr.glimmer:glimmer`（最低 `1.0.0-alpha21`，或 catalog 别名 `libs.androidx.glimmer`）
  - `androidx.xr.glimmer:glimmer-google-fonts`（最低 `1.0.0-alpha21`，或 catalog 别名 `libs.androidx.glimmer.google.fonts`）
  - `androidx.xr.projected:projected`（最低 `1.0.0-alpha13`，或 catalog 别名 `libs.androidx.xr.projected`、`libs.androidx.projected`）
  - 先检查 `gradle/libs.versions.toml`；如果已有 catalog 条目，就在 `app/build.gradle.kts` 中使用它们，并确认其版本满足最低要求。不要为 `glimmer-google-fonts` 猜测 `1.0.0-alpha01`。

## 核心约束与限制

- **不要**：在投影式 Activity 或 Glimmer UI 内使用 `MaterialTheme` 或 Material 3 组件（`androidx.compose.material3.*`）。
- **要**：使用 `GlimmerTheme` 与 Glimmer 组件（`androidx.xr.glimmer.*`）。
- **要**：始终把 `androidx.xr.glimmer.googlefonts` 的 `createGoogleSansFlexTypography()` 作为 `typography` 传给 `GlimmerTheme`。
- 不逐一说明具体的硬件设备型号或特有功能。
- **Elevation**：不支持 Material 3 的阴影或 elevation 修饰符。请使用 Jetpack Compose Glimmer 的 `ShadowScope` 或 `Depth` 令牌。
- **排版限制**：可读文本最小字号为 18sp（0.6°）。避免使用 "Thin" 或 "Hairline" 字重，它们在叠加式镜片上会闪烁。

## 1. 配置依赖

- **配置投影式 Activity**：创建投影式 Activity 时，遵循
  [为智能眼镜创建第一个 Activity](https://developer.android.com/develop/xr/jetpack-xr-sdk/ai-glasses/first-activity) 与
  [projectedcontext-source.md](references/projectedcontext-source.md)。在 `AndroidManifest.xml` 中把 `android:requiredDisplayCategory` 设为
  `android.hardware.display.category.XR_PROJECTED`：


  ```xml
  <activity
      android:name="com.example.xr.projected.ProjectedMainActivity"
      android:exported="true"
      android:requiredDisplayCategory="android.hardware.display.category.XR_PROJECTED">
      <intent-filter>
          <action android:name="android.intent.action.MAIN" />
          <category android:name="android.intent.category.XR_PROJECTED_LAUNCHER"/>
      </intent-filter>
  </activity>
  ```

  <br />

- **手机应用集成**：在宿主手机应用里添加一个按钮，显示
  `Text("Launch on Glasses")`。用
  `collectAsStateWithLifecycle(initialValue = false)`
  观察
  `ProjectedContext.isProjectedDeviceConnected(context, coroutineContext)`，以设置按钮的
  `enabled` 状态，使眼镜断开连接时按钮不可用。点击时，用
  `ProjectedContext.createProjectedActivityOptions(context).toBundle()` 在眼镜显示屏上启动 `GlassesMainActivity`，
  如以下代码片段所示：


  ```kotlin
  val options = ProjectedContext.createProjectedActivityOptions(context)
  val intent = Intent(context, ProjectedMainActivity::class.java)
  context.startActivity(intent, options.toBundle())
  ```

  <br />

- **UI 库与字体**：在 `app/build.gradle.kts` 中声明 Glimmer、Google Fonts 与
  Projected 构件时，遵循 [声明 Jetpack
  Compose Glimmer 依赖](https://developer.android.com/jetpack/androidx/releases/xr-glimmer)，并在用 `createGoogleSansFlexTypography` 配置 Google Sans Flex 时，
  遵循 [glimmersansflextypography-source.md](references/glimmersansflextypography-source.md)。

- **主题、初始焦点与黑色背景**：在叠加式显示屏上，纯黑（`Color.Black` 或 `GlimmerTheme.colors.background`）会呈现为 100%
  透明。在 `onCreate` 中（标注
  `@OptIn(ExperimentalComposeUiApi::class)`），设置
  `ComposeUiFlags.isInitialFocusOnFocusableAvailable = true`
  （`androidx.compose.ui.ComposeUiFlags`），用
  `GlimmerTheme(typography = createGoogleSansFlexTypography())` 包裹内容，并对
  根容器应用 `Modifier.background(Color.Black)`（或 `GlimmerTheme.colors.background`）：


  ```kotlin
  @OptIn(ExperimentalProjectedApi::class)
  class ProjectedMainActivity : ComponentActivity() {

      private var displayController: ProjectedDisplayController? = null
      private var isVisualUiSupported by mutableStateOf(false)
      private var areVisualsOn by mutableStateOf(true)

      override fun onCreate(savedInstanceState: Bundle?) {
          super.onCreate(savedInstanceState)

          lifecycle.addObserver(object : DefaultLifecycleObserver {
              override fun onDestroy(owner: LifecycleOwner) {
                  displayController?.close()
                  displayController = null
              }
          })

          initializeGlassesFeatures()

          setContent {
              GlimmerTheme {
                  HomeScreen(
                      areVisualsOn = areVisualsOn,
                      isVisualUiSupported = isVisualUiSupported,
                      onClose = { finish() }
                  )
              }
          }
      }

      private fun initializeGlassesFeatures() {
          lifecycleScope.launch {
              // Check device capabilities
              val projectedDeviceController = ProjectedDeviceController.create(this@ProjectedMainActivity)
              isVisualUiSupported = projectedDeviceController.capabilities.contains(CAPABILITY_VISUAL_UI)

              val controller = ProjectedDisplayController.create(this@ProjectedMainActivity)
              displayController = controller
              val observer = GlassesLifecycleObserver(
                  context = this@ProjectedMainActivity,
                  controller = controller,
                  onVisualsChanged = { visualsOn -> areVisualsOn = visualsOn }
              )
              lifecycle.addObserver(observer)
          }
      }
  }
  ```

  <br />

- **硬件能力、权限与访问**：检查硬件能力、请求权限或访问眼镜硬件时，遵循
  [在运行时检查设备能力](https://developer.android.com/develop/xr/jetpack-xr-sdk/ai-glasses/check-capabilities)、[请求硬件
  权限](references/android/develop/xr/jetpack-xr-sdk/request-hardware-permissions.md)，以及 [用投影上下文访问硬件](references/android/develop/xr/jetpack-xr-sdk/access-hardware-projected-context.md)。

## 2. 精简并转换 UI

- 用 Jetpack Compose Glimmer 组件构建 UI，并用深度表达优先级。
- 自下而上设计，并始终把 UI 底部对齐（`Alignment.BottomCenter`）。
- **一次一件事**：同一时刻只展示一条主要信息（例如使用 `VerticalStack`），避免同时出现多张卡片。
- **颜色对比度**：选择颜色时，遵循 [material-hct-source.md](references/material-hct-source.md)，在 HCT 中保持前景与背景至少 70% 的色调差。

## 3. 映射输入控件

- 把点按与滑动交互映射到眼镜触控板。输入是一维的，避免嵌套滚动控件。
- 用系统返回关闭临时状态或详情视图。
- 实现焦点导航与硬件输入处理时，遵循 [Jetpack Compose Glimmer 中的焦点](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/focus.md) 与 [显示
  眼镜的硬件控件](references/android/design/ui/ai-glasses/guides/interaction/inputs.md)。可滚动容器的焦点移动是连续的，按钮行这类元素则是离散的。

## 4. 用 Jetpack Compose Glimmer 构建

### 实现 Glimmer 样式

使用 `GlimmerTheme` 访问主题令牌时，遵循
[glimmertheme-source.md](references/glimmertheme-source.md)。

| 类别 | 令牌 | 取值 / 作用 |
|---|---|---|
| **颜色** | primary / secondary | `#9BBFFF` / `#4C88E9`（焦点色） |
| **颜色** | positive / negative | `#7AD48F`（确认）/ `#F57082`（警告） |
| **颜色** | background | `#000000`（纯黑，呈现为 100% 透明） |
| **颜色** | surface | `#262626`（边框使用 `SurfaceDefaults.border`） |
| **形状** | Standard / Small | `RoundedCornerShape(36.dp)` / `RoundedCornerShape(12.dp)` |

#### 排版比例（Google Sans Flex）与深度层级

使用 Google Sans Flex，可变轴为 `ROND` = `100f`、`wdth` = `100f`、`opsz`
= `9f`，`wght` 按角色设置：

| 样式 | 字号 / 行高 | 字重 |
|---|---|---|
| **Title Large / Medium / Small** | 30/36.sp，24/32.sp，20/28.sp | 725 |
| **Body Large / Medium / Small** | 30/36.sp，24/32.sp，20/28.sp | 520 |
| **Caption** | 18.sp / 28.sp | 650 |

用 `DepthEffect` 与 `DepthEffectLevels` 模拟深度时，遵循
[deptheffect-source.md](references/deptheffect-source.md) 与 [deptheffectlevels-source.md](references/deptheffectlevels-source.md)：静止卡片与背景 UI 用 `level1`，
聚焦或按下的交互 UI 用 `level2`。

### 实现 Jetpack Compose Glimmer 组件

#### Card、ActionCard、ImageCard 与 ButtonGroup

Card（`androidx.xr.glimmer.Card`）把相关内容聚合成一个视觉
焦点。不要在 `ListItem` 内嵌 `Card`。实现卡片时，遵循
[Jetpack Compose Glimmer：Card](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/cards.md)、[card-source.md](references/card-source.md)
与 [card-samples-source.md](references/card-samples-source.md) 中的说明。

- **可点击与不可点击的卡片**：如果整张 `Card` 作为触发器，就传 `onClick = { ... }`；如果只是信息展示，就省略 `onClick`。用 `focusable: Boolean = true`（例如 `Card(focusable = false)`）控制不可点击卡片的焦点。
- **单一主操作（`ActionCard`）**：当卡片只有一个锚定在底边的主
  按钮操作时，改用
  `androidx.xr.glimmer.ActionCard`，不要把 `Button` 放进
  `Card` 内。它的 `action` 按钮会直接获得焦点：


  ```kotlin
  ActionCard(
      action = {
          Button(onClick = {}, trailingIcon = { Icon(FavoriteIcon, "Localized description") }) {
              Text("Send")
          }
      }
  ) {
      Text("This is a card with a title, leading icon, header image, and action")
  }
  ```

  <br />

- **多个操作（`Card` 与 `ButtonGroup`）---避免焦点争用**：
  当卡片需要搭配多个操作按钮时，使用
  `androidx.xr.glimmer.ButtonGroup`（可选配
  `rememberButtonGroupState`）。**绝不要把 `ButtonGroup` 嵌在 `Card { ...
  }` 内。** 把不可聚焦的 `Card(focusable = false)`（不带 `onClick`）作为
  `ButtonGroup` 的兄弟节点放在 **其上方**（同一 `Column` 中），这样卡片与按钮
  不会争抢焦点：


  ```kotlin
  ButtonGroup(modifier = Modifier.fillMaxWidth()) {
      Button(onClick = {}) { Text("Button 1") }
      Button(onClick = {}) { Text("Button 2") }
      Button(onClick = {}) { Text("Button 3") }
      Button(onClick = {}) { Text("Button 4") }
      Button(onClick = {}) { Text("Button 5") }
  }
  ```

  <br />

- **图片卡片**：用 `ImageCard`、`LeadingImageCard` 或 `TrailingImageCard`
  在卡片文字旁展示醒目的图片。

#### Button 与 ToggleButton

实现按钮或开关按钮时，遵循 [Jetpack
Compose Glimmer：Button](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/buttons.md)、[button-source.md](references/button-source.md) 与
[button-samples-source.md](references/button-samples-source.md) 中的说明。

- **标准按钮与图标按钮**：文本操作使用 `Button`（可带 `leadingIcon`/`trailingIcon`），仅图标触发器使用 `IconButton`（例如媒体的下一曲或上一曲按钮）。
- **开关按钮（`ToggleButton` 与 `IconToggleButton`）**：对需要根据 `checked` 变形的有状态开/关或播放/暂停
  控件，使用 `ToggleButton` 或 `IconToggleButton`：


  ```kotlin
  @Composable
  fun ToggleButtonWithLeadingIconSample() {
      var checked by remember { mutableStateOf(false) }

      ToggleButton(
          checked = checked,
          leadingIcon = {
              Icon(
                  if (checked) FavoriteIcon else OutlinedFavoriteIcon,
                  contentDescription = "Toggle favorite"
              )
          },
          onCheckedChange = { checked = it }
      ) {
          Text(if (checked) "On" else "Off")
      }
  }
  ```

  <br />

#### 标题 chip

`TitleChip`（`androidx.xr.glimmer.TitleChip`）是不可交互的胶囊形标题
（不超过三个词，单行）。实现标题 chip 时，遵循
[Jetpack Compose Glimmer：Title Chip](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/title-chips.md)、
[titlechip-source.md](references/titlechip-source.md) 与 [titlechip-samples-source.md](references/titlechip-samples-source.md) 中的说明。

- **空间间距**：把独立的 `TitleChip` 放在 `Card` 或
  `ActionCard` 上方时，让 `TitleChip` 水平居中，并用
  `TitleChipDefaults.associatedContentSpacing` 把它与卡片分隔（使用 `Spacer` 或
  `Arrangement.spacedBy(TitleChipDefaults.associatedContentSpacing)`）：


  ```kotlin
  @Composable
  fun TitleChipWithCardSample() {
      Column(horizontalAlignment = Alignment.CenterHorizontally) {
          TitleChip { Text("Title Chip") }

          Spacer(Modifier.height(TitleChipDefaults.associatedContentSpacing))

          Card(
              title = { Text("Title") },
              subtitle = { Text("Subtitle") },
              leadingIcon = { Icon(FavoriteIcon, "Localized description") },
          ) {
              Text("Card Content")
          }
      }
  }
  ```

  <br />

#### 图标

添加图标或图标按钮时，遵循 [Jetpack Compose
Glimmer：图标](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/icons.md)、[icon-source.md](references/icon-source.md)、[iconbutton-source.md](references/iconbutton-source.md) 与
[iconsizes-source.md](references/iconsizes-source.md) 中的说明。

- **尺寸与交互性**：用 `GlimmerTheme.iconSizes`（`small`、`medium`、`large`）设置图标尺寸。触发器使用 `IconButton` 或 `IconToggleButton`，状态指示使用 `Icon`。
- **对比度与图标库**：**绝不要**用纯黑（`Color.Black`）给图标着色；黑色会渲染成透明。使用 [Material Symbols](https://fonts.google.com/icons?icon.style=Rounded)（600 字重、Rounded、Unfilled）。如果 `app/build.gradle.kts` 中没有 `androidx.compose.material:material-icons-*`，就用 `ImageVector.Builder` 或 `painterResource` 构建矢量图，不要导入 `androidx.compose.material.icons.*`。

#### 列表

同类的可滚动项使用 `GlimmerLazyColumn`（`androidx.xr.glimmer.list.GlimmerLazyColumn`）。
构建可滚动列表与列表项时，遵循 [list-source.md](references/list-source.md)、[listitem-source.md](references/listitem-source.md)
与 [liststate-source.md](references/liststate-source.md) 中的 API 定义。

- **始终使用 `GlimmerLazyColumn`**：绝不要用 foundation 的 `LazyColumn`。从 `androidx.xr.glimmer.list` 导入 `GlimmerLazyColumn`、`rememberGlimmerLazyListState` 与 `items`（`item` 是作用域成员，无需导入）。要用代码滚动到第一项，先上提 `val listState =
  rememberGlimmerLazyListState()`，再调用 `listState.scrollToItem(0)` 或 `listState.animateScrollToItem(0)`。
- **内建标题、间距与行**：用 `title = {
  TitleChip { Text("...") } }` 直接在 `GlimmerLazyColumn` 上传入标题（不要放在
  外面），设置 `verticalArrangement = Arrangement.spacedBy(20.dp)`，并用
  `androidx.xr.glimmer.ListItem(onClick = { ... }, supportingLabel =
  { Text(...) }) { Text(...) }` 渲染行
  （把主标签作为末尾的 `content` lambda 传入，而不是 `headlineContent`，且绝不要在
  `ListItem` 内嵌 `Card`）：


  ```kotlin
  @Composable
  fun GlimmerLazyColumnWithTitleChipSample() {
      val ingredientItems =
          listOf("Milk", "Flour", "Egg", "Salt", "Apples", "Butter", "Vanilla", "Sugar", "Cinnamon")
      GlimmerLazyColumn(title = { TitleChip { Text("Ingredients") } }) {
          items(ingredientItems) { text -> ListItem { Text(text) } }
      }
  }
  ```

  <br />

#### 堆叠

用 `VerticalStack`（`androidx.xr.glimmer.stack.VerticalStack`）一次显示一张不同类型的
卡片（例如日历、通勤与天气
卡片）。**绝不要**把 `TitleChip` 与 `VerticalStack` 一起使用。实现
`VerticalStack` 时，遵循 [stack-source.md](references/stack-source.md)、
[stackstate-source.md](references/stackstate-source.md) 与 [stackitemscope-source.md](references/stackitemscope-source.md) 中的 API 定义。

- **底部对齐、高度（+66.dp）与 `itemDecoration`**：把
  `VerticalStack` 对齐到 `Alignment.BottomCenter`，把高度设为**比最高的卡片高 `66.dp`**
  （`maxCardHeight + 66.dp`），并对每个
  `item { ... }` 块内的 `Card` 应用 `Modifier.itemDecoration(CardDefaults.shape)`，使背景卡片被裁剪并遮罩：


  ```kotlin
  @Composable
  fun VerticalStackSample() {
      VerticalStack {
          item {
              Card { Text("Top Card") }
          }
          item {
              Card { Text("Second Card") }
          }
          item {
              Card { Text("Third Card") }
          }
      }
  }
  ```

  <br />

#### 横向分页器与动画文本

横向卡片浏览使用 `GlimmerHorizontalPager`
（`androidx.xr.glimmer.pager.GlimmerHorizontalPager`）搭配
`rememberGlimmerPagerState(pageCount = { ... })`（绝不要用 foundation 的 `HorizontalPager`）。

- **平滑文本运动**：在分页页面内，为 Glimmer 的 [`Text`](references/android/develop/xr/jetpack-xr-sdk/jetpack-compose-glimmer/text.md)
  （`androidx.xr.glimmer.Text`，绝不要用 `androidx.compose.material3.Text`）配置
  `textMotion = TextMotion.Animated`（使用 `.copy(textMotion =
  TextMotion.Animated)`），让吸附切换时的渲染更平滑：


  ```kotlin
  // Hoist the pager state, specifying the total page count with a lambda.
  val pagerState = rememberGlimmerPagerState(pageCount = { 10 })

  GlimmerHorizontalPager(
      state = pagerState,
      modifier = Modifier.fillMaxSize(),
  ) { page ->
      // Use Glimmer components like Card and Text for optimized glasses styling.
      Card(modifier = Modifier.fillMaxWidth()) {
          Text(
              text = "Page: $page",
              // Recommended: use TextMotion.Animated for smooth transitions in a pager.
              style = LocalTextStyle.current.copy(textMotion = TextMotion.Animated),
          )
      }
  }
  ```

  <br />

#### Surface

`Modifier.surface`（`androidx.xr.glimmer.surface`）用于构建自定义交互
组件（例如不用 `Card` 或 `Button` 的状态徽标）。创建
自定义 surface 时，遵循 [surface-source.md](references/surface-source.md) 中的 API 定义。

- **共用 `MutableInteractionSource` 与链式顺序**：创建一个 `remember {
  MutableInteractionSource() }`，同时传给
  `Modifier.surface(interactionSource = interactionSource, ...)` 与
  `.clickable(interactionSource = interactionSource, ...)`（或 `.focusable`），
  并把 `.surface(...)` 链在 `.clickable(...)` **之前**：


  ```kotlin
  @Composable
  fun FocusableSurfaceSample() {
      val interactionSource = remember { MutableInteractionSource() }
      Box(
          modifier = Modifier
              .size(100.dp)
              .surface(interactionSource = interactionSource)
              .focusable(interactionSource = interactionSource),
          contentAlignment = Alignment.Center
      ) {
          Text("Focusable")
      }
  }

  @Composable
  fun ClickableSurfaceSample() {
      val interactionSource = remember { MutableInteractionSource() }
      Box(
          modifier = Modifier
              .size(100.dp)
              .surface(interactionSource = interactionSource)
              .focusable(interactionSource = interactionSource)
              .clickable(
                  interactionSource = interactionSource,
                  indication = null
              ) { /* Handle click action */ },
          contentAlignment = Alignment.Center
      ) {
          Text("Clickable")
      }
  }
  ```

  <br />

#### 语音输入指示器与间接指针手势

- **`VoiceInputIndicator` 与 `ContainedVoiceInputIndicator`**：传入一个 `level`
  lambda，返回归一化到 `0.0f..1.0f` 的 `Float`。当由
  `SpeechRecognizer`（`RecognitionListener.onRmsChanged(rmsdB: Float)`）驱动时，
  用 `.coerceIn(0f, 1f)` 归一化并钳制 `rmsdB`：


  ```kotlin
  // Example state variable to hold the normalized level (0.0 to 1.0)
  // that the VoiceInputIndicator component expects.
  val audioLevel = MutableStateFlow(0f)

  // Initialize the Android SpeechRecognizer
  val speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)

  // Listener to capture speech events and audio level changes
  val listener = object : RecognitionListener {
      override fun onRmsChanged(rmsdB: Float) {
          // Normalize raw dB level to a 0.0-1.0 range.
          // Android SpeechRecognizer's rmsdB typically ranges from 0 to ~10.
          audioLevel.value = ((rmsdB - 1f) / 9f).coerceIn(0f, 1f)
      }

      // ... Implement other required RecognitionListener methods ...
      override fun onReadyForSpeech(params: Bundle?) {}
      override fun onBeginningOfSpeech() {}
      override fun onEndOfSpeech() {}
      override fun onError(error: Int) {}
      override fun onResults(results: Bundle?) {}
      override fun onPartialResults(partialResults: Bundle?) {}
      override fun onEvent(eventType: Int, params: Bundle?) {}
      override fun onBufferReceived(buffer: ByteArray?) {}
  }

  // Attach the listener to the recognizer
  speechRecognizer.setRecognitionListener(listener)

  // Create an intent to specify the recognition model and behavior
  val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
      putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
  }
  // Begin listening for audio input
  speechRecognizer.startListening(intent)
  ```

  <br />


  ```kotlin
  @Composable
  fun VoiceInputExample(modifier: Modifier) {
      // Collect the flow as Compose State so the UI reacts to changes in real-time.
      val currentLevel by audioLevel.collectAsState()

      VoiceInputIndicator(
          // The VoiceInputIndicator component provides a visual "pulse" or indicator
          // that changes based on the 'level' lambda, which returns a Float between 0.0 and 1.0.
          level = { currentLevel },
          modifier = modifier
      )
  }
  ```

  <br />

- **`Modifier.onIndirectPointerGesture`**：在设为
  **可聚焦**的容器上（使用 `focusTarget`、`focusable` 或 `surface(focusable =
  true)`），用 `androidx.xr.glimmer.onIndirectPointerGesture` 处理底层触控板点按
  （`onClick`）、前滑（`onSwipeForward`）与后滑
  （`onSwipeBackward`）手势：


  ```kotlin
  @Composable
  fun OnIndirectPointerGestureSample() {
      var lastGesture by remember { mutableStateOf("None") }

      Box(
          modifier =
              Modifier.fillMaxSize()
                  .onIndirectPointerGesture(
                      enabled = true,
                      onSwipeForward = { lastGesture = "Forward" },
                      onSwipeBackward = { lastGesture = "Backward" },
                      onClick = { lastGesture = "Click" },
                  )
                  .focusTarget(),
          contentAlignment = Alignment.Center,
      ) {
          Text("Last Gesture: $lastGesture")
      }
  }
  ```

  <br />

## 5. 与系统 UI 集成

- 处理通知或从通知启动投影式 Activity 时，遵循 [了解智能眼镜的
  通知行为](https://developer.android.com/develop/xr/jetpack-xr-sdk/ai-glasses/notifications/behavior) 与 [从通知在显示
  眼镜上启动眼镜 Activity](https://developer.android.com/develop/xr/jetpack-xr-sdk/ai-glasses/notifications/start-activity) 中的说明。
