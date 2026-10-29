---
name: ink-app-builder
description: 使用 Jetpack Ink（androidx.ink）与 Compose 为 Android 应用添加手写与自由绘制能力。
  在实现手写笔或触摸绘制表面、渲染湿墨与干墨笔划、配置内置笔刷（pressure pen、marker、
  highlighter）、实现基于几何的擦除、线性撤销与重做历史，或用 Room 持久化笔划时使用这个 skill。
  给出可运行的 Compose 与 ViewModel 实现。不适用于基于 View（XML）的手写，也不要用于编程式创建
  自定义 BrushFamily。对于自定义 BrushFamily 创建、自定义笔尖形状或行为节点图，建议使用
  ink-custom-brush-builder skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-28'
  keywords:
  - Android
  - Jetpack Ink
  - androidx.ink
  - Compose
  - InProgressStrokes
  - CanvasStrokeRenderer
  - StockBrushes
  - drawing
  - stylus
  - digital ink
  - eraser
  - undo
  - redo
  - persistence
---

Android Ink API（`androidx.ink`）是一个模块化的 Jetpack 库，用于在 Android 上构建高性能、低延迟的自由绘制体验。它采用**湿墨（wet ink）与干墨（dry ink）**两阶段模型：

- **湿墨**：用户绘制过程中的实时、超低延迟渲染，由 `InProgressStrokes` composable 负责。
- **干墨**：已定稿的不可变 `Stroke` 对象，由应用通过 `CanvasStrokeRenderer` 渲染。

## 配置与依赖

Ink API 要求 **`minSdk = 26`**，对应 Android 8.0（API level 26）及更高版本。所有 `androidx.ink` 模块在 `gradle/libs.versions.toml` 中必须使用完全相同的版本。修改项目构建文件前先征得用户同意。

### 版本选择（`1.0.0` 稳定版与 `1.1.0-alpha03` 及更高版本）

- 对于依赖 `StockBrushes` 或依赖用 `BrushFamily.decode` 解码的预序列化 `.brush` 资源的生产应用，使用 **`1.0.0`（稳定版）**。在 `1.0.0` 稳定版中，`BrushFamily.encode`、`BrushFamily.decode`、`AndroidBrushFamilySerialization` 和 `BrushFamilyDecodeCallback` 需要 `@OptIn(ExperimentalInkCustomBrushApi::class)`。
- 当应用在 Kotlin 代码中通过编程方式构建自定义笔刷（`BrushFamily`、`BrushCoat`、`BrushTip`、`BrushPaint`、`BrushBehavior`）时，使用 **`1.1.0-alpha03` 及更高版本**。从 `1.1.0-alpha02` 及更高版本起，`BrushFamily` 序列化不再需要 `@OptIn`（并且在 `1.1.0-alpha05` 及更高版本中，`ExperimentalInkCustomBrushApi` 是 `@RestrictTo(LIBRARY_GROUP)`，所以**绝不**给 `1.1.0-alpha03` 及更高版本的代码加这个注解）。

### 版本目录（`gradle/libs.versions.toml`）

    [versions]
    ink = "<latest_version>"
    inputMotionPrediction = "<latest_version>"

    [libraries]
    # Core Ink modules
    androidx-ink-authoring         = { module = "androidx.ink:ink-authoring",         version.ref = "ink" }
    androidx-ink-brush             = { module = "androidx.ink:ink-brush",             version.ref = "ink" }
    androidx-ink-geometry          = { module = "androidx.ink:ink-geometry",          version.ref = "ink" }
    androidx-ink-nativeloader      = { module = "androidx.ink:ink-nativeloader",      version.ref = "ink" }
    androidx-ink-rendering         = { module = "androidx.ink:ink-rendering",         version.ref = "ink" }
    androidx-ink-strokes           = { module = "androidx.ink:ink-strokes",           version.ref = "ink" }
    androidx-ink-storage           = { module = "androidx.ink:ink-storage",           version.ref = "ink" }

    # Compose integration modules
    androidx-ink-authoring-android = { module = "androidx.ink:ink-authoring-android", version.ref = "ink" }
    androidx-ink-authoring-compose = { module = "androidx.ink:ink-authoring-compose", version.ref = "ink" }
    androidx-ink-brush-compose     = { module = "androidx.ink:ink-brush-compose",     version.ref = "ink" }
    androidx-ink-geometry-compose  = { module = "androidx.ink:ink-geometry-compose",  version.ref = "ink" }

    # Motion prediction (required for low-latency stylus tracking)
    androidx-input-motionprediction = { module = "androidx.input:input-motionprediction", version.ref = "inputMotionPrediction" }

    # Persistence (kotlinx.serialization + Room with KSP)
    kotlinx-serialization-json = { module = "org.jetbrains.kotlinx:kotlinx-serialization-json", version.ref = "kotlinxSerialization" }
    androidx-room-runtime      = { module = "androidx.room:room-runtime",  version.ref = "room" }
    androidx-room-ktx          = { module = "androidx.room:room-ktx",      version.ref = "room" }
    androidx-room-compiler     = { module = "androidx.room:room-compiler", version.ref = "room" }

    [plugins]
    kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
    ksp                  = { id = "com.google.devtools.ksp",                   version.ref = "ksp" }

### 应用模块配置（`app/build.gradle.kts`）

    plugins {
        alias(libs.plugins.android.application)
        alias(libs.plugins.kotlin.compose)
        alias(libs.plugins.kotlin.serialization)
        alias(libs.plugins.ksp) // Mandatory when using Room in Kotlin
    }

    android {
        defaultConfig {
            minSdk = 26
        }
        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
        }
        buildFeatures {
            compose = true
        }
    }

    dependencies {
        implementation(libs.androidx.ink.authoring)
        implementation(libs.androidx.ink.brush)
        implementation(libs.androidx.ink.geometry)
        implementation(libs.androidx.ink.nativeloader)
        implementation(libs.androidx.ink.rendering)
        implementation(libs.androidx.ink.strokes)
        implementation(libs.androidx.ink.storage)

        implementation(libs.androidx.ink.authoring.android)
        implementation(libs.androidx.ink.authoring.compose)
        implementation(libs.androidx.ink.brush.compose)
        implementation(libs.androidx.ink.geometry.compose)

        implementation(libs.androidx.input.motionprediction)

        implementation(libs.kotlinx.serialization.json)
        implementation(libs.androidx.room.runtime)
        implementation(libs.androidx.room.ktx)
        ksp(libs.androidx.room.compiler) // NEVER use annotationProcessor in Kotlin
    }

## 核心绘制表面与默认笔刷

用 `Brush.createWithComposeColor`（来自 `ink-brush-compose`）创建一个标准的压感笔 `Brush`。`epsilon` 参数定义两个输入点之间被视为视觉上可区分的最小距离（以笔划空间为单位；一般绘制用 `0.1f`，精细工具用 `0.01f`；`Brush` 强制要求 `0f < epsilon <= size`）：


```kotlin
/**
 * Creates a default pressure-sensitive pen [Brush].
 *
 * The `epsilon` parameter sets the geometric tolerance (minimum point distance
 * in stroke units) controlling how far a stroke can be zoomed before triangle
 * artifacts appear (`0f < epsilon <= size`).
 */
fun createDefaultPenBrush(): Brush {
    return Brush.createWithComposeColor(
        family = StockBrushes.pressurePen(),
        color = Color.Black,
        size = 5f,
        epsilon = 0.1f,
    )
}
```

<br />

在 `Box` 中为绘制表面叠放两层：下层是 Compose `Canvas`，在 `nativeCanvas.withSave` 内用 `CanvasStrokeRenderer` 渲染已定稿的干墨 `Stroke` 对象；上层是 `InProgressStrokes` composable，用于低延迟捕获湿墨。在 `DrawingSurface` 内部封装一个同步的 `pendingStrokes` Compose Snapshot State 缓冲区，使干墨 `Canvas` 在 `onStrokesFinished` 触发时于同一个 UI 线程运行循环内失效，从而避免一帧的湿墨到干墨闪烁：


```kotlin
@Composable
fun DrawingSurface(
    strokes: List<Stroke>,
    canvasStrokeRenderer: CanvasStrokeRenderer,
    currentBrush: Brush,
    onGetNextBrush: () -> Brush,
    onStrokesFinished: (List<Stroke>) -> Unit,
    isEraserMode: Boolean,
    modifier: Modifier = Modifier,
    textureStore: AppTextureBitmapStore = LocalTextureStore.current,
    onErase: (Float, Float) -> Unit = { _, _ -> },
    onEraseStart: () -> Unit = {},
    onEraseEnd: () -> Unit = {},
) {
    val cacheGen by textureStore.generation.collectAsStateWithLifecycle()

    // Holds newly finished strokes synchronously for the single frame before
    // asynchronous StateFlow collection delivers the updated strokes list.
    var pendingStrokes by remember { mutableStateOf<List<Stroke>>(emptyList()) }

    SideEffect {
        if (pendingStrokes.isNotEmpty()) {
            pendingStrokes = if (strokes.isEmpty()) {
                emptyList()
            } else {
                pendingStrokes.filter { pending -> strokes.none { it === pending } }
            }
        }
    }

    val strokesToDraw = remember(strokes, pendingStrokes) {
        if (pendingStrokes.isEmpty()) {
            strokes
        } else {
            strokes + pendingStrokes.filter { pending -> strokes.none { it === pending } }
        }
    }
    val identityMatrix = remember { Matrix() }

    val currentOnErase by rememberUpdatedState(onErase)
    val currentOnEraseStart by rememberUpdatedState(onEraseStart)
    val currentOnEraseEnd by rememberUpdatedState(onEraseEnd)

    Box(modifier = modifier) {
        // Layer 1: Dry ink - completed strokes + same-frame pending handoff strokes
        Canvas(modifier = Modifier.fillMaxSize()) {
            val nativeCanvas = drawContext.canvas.nativeCanvas
            strokesToDraw.fastForEach { stroke ->
                nativeCanvas.withSave {
                    canvasStrokeRenderer.draw(
                        canvas = this,
                        stroke = stroke,
                        strokeToScreenTransform = identityMatrix,
                    )
                }
            }
        }

        // Layer 2: Eraser touch handler OR Wet ink (InProgressStrokes)
        if (isEraserMode) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .pointerInput(Unit) {
                        detectDragGestures(
                            onDragStart = { currentOnEraseStart() },
                            onDragEnd = { currentOnEraseEnd() },
                            onDragCancel = { currentOnEraseEnd() },
                            onDrag = { change, _ ->
                                currentOnErase(change.position.x, change.position.y)
                                change.consume()
                            },
                        )
                    }
            )
        } else {
            key(cacheGen) {
                InProgressStrokes(
                    defaultBrush = currentBrush,
                    nextBrush = onGetNextBrush,
                    onStrokesFinished = { newStrokes ->
                        pendingStrokes = pendingStrokes + newStrokes
                        onStrokesFinished(newStrokes)
                    },
                    textureBitmapStore = textureStore,
                )
            }
        }
    }
}
```

<br />

## 工作流与任务分流

根据所请求的任务，遵循这些条件式指令：

- **步骤 1（依赖与 SDK 配置）**：在添加 Ink API 依赖或配置 `minSdk` 时，遵循本文件中的配置代码块以及 [Ink API 配置指南](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-setup.md)。确认 `ink-nativeloader`、`ink-authoring-android` 和 `androidx.input:input-motionprediction` 都已存在。
- **步骤 2（绘制表面与笔划渲染）**：在创建包含湿墨（`InProgressStrokes`）与干墨（`CanvasStrokeRenderer`）的 Compose 绘制屏幕时，实现本文件中的 `DrawingSurface`，并阅读[绘制笔划](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-draw-stroke.md)。关于 `InProgressStrokes` 的参数细节、`BlendMode.Multiply` 荧光笔图层合成，以及 `TextureBitmapStore` 的 generation 失效机制，你**必须**遵循 [drawing-and-brushes.md](references/drawing-and-brushes.md)。
- **步骤 3（内置笔刷与笔刷切换）**：在创建、修改或切换内置笔刷（`StockBrushes.pressurePen`、`marker`、`highlighter`、`dashedLine` 或 `emojiHighlighter`）时，阅读[笔刷 API](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-brush-apis.md)，并且关于 `epsilon` 几何约束、荧光笔 alpha 保留和 Android 14（API level 34）的 `emojiHighlighter` 规则，你**必须**遵循 [drawing-and-brushes.md](references/drawing-and-brushes.md)。
- **步骤 4（橡皮擦、撤销与重做，以及 MVVM 架构）**：在实现基于几何的笔划橡皮擦、线性撤销与重做历史栈，或使用 MVVM 的 `ViewModel` 与 Hilt 装配时，阅读[几何 API](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-geometry-apis.md)，并且你**必须**遵循 [editing-and-architecture.md](references/editing-and-architecture.md)。
- **步骤 5（持久化、位图导出与手势共存）**：在用 Room 保存和加载笔划（`StrokeInputBatch.encode` 与 `decode`）、在配置变更时保留 UI 状态、把绘制内容导出为 `Bitmap` 或 PNG 文件，或把长按拖动手势与绘制结合（`pointerInputWithSiblingFallthrough`）时，阅读[状态保留与持久化存储](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-state-preservation.md)，并且你**必须**遵循 [persistence-and-advanced.md](references/persistence-and-advanced.md)。
- **编程式自定义笔刷**：对于自定义 `BrushFamily` 创建、自定义笔尖形状或行为节点图，建议使用 `ink-custom-brush-builder` skill。

## 反模式

- **绝不要在 Compose 屏幕中使用 `InProgressStrokesView`** ---那是基于 View 的 API。请改用 `InProgressStrokes` composable。
- **绝不要省略 `ink-nativeloader` 或 `ink-authoring-android`** ---缺少 `ink-nativeloader` 会抛出 `UnsatisfiedLinkError`，缺少 `ink-authoring-android` 会在运行时抛出 `ClassNotFoundException`。
- **绝不要直接使用 `View.OnTouchListener` 或 `MotionEvent`** ---`InProgressStrokes` composable 会在内部捕获并处理触摸与手写笔输入。
- **绝不要手动绘制笔划**（用 `Canvas.drawPath` 或遍历笔划点）---始终调用 `CanvasStrokeRenderer.draw(canvas, stroke, transform)`。
- **绝不要调用 `CanvasStrokeRenderer.create(forcePathRendering = true)`** ---带 `forcePathRendering` 的 2 参数重载是 `@RestrictTo(LIBRARY_GROUP)`。请使用公开的 `CanvasStrokeRenderer.create(textureStore)` 工厂方法，它会自动检测软件 `Bitmap` 画布并回退到路径渲染。
- **绝不要只依赖 `onStrokesFinished` 中的异步 `StateFlow` 收集** ---`InProgressStrokes` 在 `onStrokesFinished` 于 UI 线程返回后立即移除已完成的湿墨笔划，而 `collectAsStateWithLifecycle` 要到之后的运行循环才更新，从而造成一帧的湿墨到干墨闪烁。始终像 `DrawingSurface` 那样使用 `pendingStrokes` 缓冲区，在同一个 UI 线程运行循环内同步修改 Compose Snapshot State。
- **绝不要把笔划存成位图**用于撤销、重做或数据库持久化---把 `Stroke` 对象保存在内存中，并把 `StrokeInputBatch` 字节连同笔刷元数据序列化到磁盘。
- **绝不要在 Kotlin 中为 Room 使用 `annotationProcessor`** ---始终应用 `com.google.devtools.ksp` 插件并使用 `ksp(libs.androidx.room.compiler)`，以避免启动时 `AppDatabase_Impl does not exist` 崩溃。
