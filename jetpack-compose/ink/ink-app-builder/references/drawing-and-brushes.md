用于构建无闪烁的 Compose 绘制表面、用 `CanvasStrokeRenderer` 渲染干墨笔划，以及配置或切换
`StockBrushes` 的参考资料。

## `InProgressStrokes` 参数

配置 `InProgressStrokes` 时，传入这些参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `defaultBrush` | `Brush?` | 无（必需） | 笔划开始时所应用的笔刷；传 `null` 则禁用湿墨输入，同时保持渲染资源处于活跃状态。 |
| `nextBrush` | `() -> Brush?` | `{ defaultBrush }` | 返回下一笔所用笔刷的 lambda。 |
| `pointerEventToWorldTransform` | `Matrix` | `IDENTITY_MATRIX` | `androidx.compose.ui.graphics.Matrix`，把指针坐标映射到世界空间或笔划空间。 |
| `strokeToWorldTransform` | `Matrix` | `IDENTITY_MATRIX` | `androidx.compose.ui.graphics.Matrix`，把笔划坐标映射到世界空间。 |
| `maskPath` | `Path?` | `null` | `androidx.compose.ui.graphics.Path`，用于遮罩不渲染湿墨的区域，例如浮动工具栏。 |
| `textureBitmapStore` | `TextureBitmapStore` | `TextureBitmapStore { null }` | 用于纹理笔刷的不可空位图存储（不要传 `null`）。 |
| `onStrokesFinished` | `(List<Stroke>) -> Unit` | 无（必需） | UI 线程回调，在指针抬起时把已完成的 `Stroke` 对象交给应用的干墨状态。 |

## 渲染干墨笔划与荧光笔混合模式

用 `CanvasStrokeRenderer.create(textureStore)` 创建 `CanvasStrokeRenderer`，并在
`nativeCanvas.withSave` 块内把每个 `Stroke` 渲染到 `drawContext.canvas.nativeCanvas`，这样变换与裁剪状态
始终与单个笔划关联。
> **离屏与软件 `Canvas` 注意事项**：自版本 `1.0.0` 起，
> `CanvasStrokeRenderer.create(textureStore)` 会自动检测软件画布
> （`!canvas.isHardwareAccelerated`，例如 `Canvas(bitmap)`），并回退到路径渲染。绝不要调用
> `@RestrictTo(LIBRARY_GROUP)` 的 2 参数重载版本
> `CanvasStrokeRenderer.create(forcePathRendering = true, textureStore)`。

### 用 `BlendMode.Multiply` 渲染荧光笔笔划

要让重叠的高亮在视觉上真实地压暗底层墨迹、又不产生自身混合的瑕疵，使用半透明颜色 alpha
（`< 1f`），并通过 `drawContext.canvas.withSaveLayer` 按笔划合成 `BlendMode.Multiply`：


```kotlin
@Composable
fun StrokeCanvas(
    strokes: List<Stroke>,
    canvasStrokeRenderer: CanvasStrokeRenderer,
    modifier: Modifier = Modifier,
) {
    val multiplyPaint = remember { Paint().apply { blendMode = BlendMode.Multiply } }
    val srcOverPaint = remember { Paint().apply { blendMode = BlendMode.SrcOver } }
    val identityMatrix = remember { Matrix() }

    Canvas(modifier = modifier.fillMaxSize()) {
        val nativeCanvas = drawContext.canvas.nativeCanvas
        val bounds = drawContext.size.toRect()

        strokes.fastForEach { stroke ->
            val paint = if (stroke.brush.family == StockBrushes.highlighter()) {
                multiplyPaint
            } else {
                srcOverPaint
            }

            drawContext.canvas.withSaveLayer(bounds, paint) {
                nativeCanvas.withSave {
                    canvasStrokeRenderer.draw(
                        canvas = this,
                        stroke = stroke,
                        strokeToScreenTransform = identityMatrix,
                    )
                }
            }
        }
    }
}
```

<br />

## 内置笔刷与笔刷配置

`StockBrushes`（来自 `ink-brush`）提供内置的 `BrushFamily` 工厂。

> [!NOTE]
> **注意：** 所有 `StockBrushes` 工厂在 Android 8.0（API level 26）及更高版本上都可用，包括带 `showMiniEmojiTrail = false` 的 `StockBrushes.emojiHighlighter`。网格渲染的特性（例如 `SelfOverlap.ACCUMULATE` 和迷你 emoji 轨迹（`showMiniEmojiTrail = true`））需要 Android 14（API level 34）及更高版本。

| 工厂方法 | 说明 | 典型用途 |
|---|---|---|
| `StockBrushes.pressurePen` | 宽度可变的压感笔 | 主要书写与绘制工具 |
| `StockBrushes.marker` | 等宽马克笔 | 粗体绘制与平涂笔划 |
| `StockBrushes.highlighter(selfOverlap = SelfOverlap.ANY)` | 半透明荧光笔（`SelfOverlap.ANY` 在 Android 14（API level 34）及更高版本上使用 `SelfOverlap.ACCUMULATE`；传 `SelfOverlap.DISCARD` 可抑制自重叠加深） | 在已有内容上做高亮 |
| `StockBrushes.dashedLine` | 虚线段样式 | 边框、辅助线和标注 |
| `StockBrushes.emojiHighlighter(clientTextureId, showMiniEmojiTrail = false, selfOverlap = SelfOverlap.ANY)` | 带 emoji 笔尖的纹理荧光笔（`showMiniEmojiTrail = false` 在所有受支持的 API 级别上都可用；`showMiniEmojiTrail = true` 需要 Android 14（API level 34）及更高版本） | 装饰性高亮 |

### Emoji 荧光笔要求

`StockBrushes.emojiHighlighter` 需要两项配置：

1. **`showMiniEmojiTrail` 需要 Android 14（API level 34）及更高版本**：迷你 emoji 粒子轨迹使用 `CanvasMeshRenderer`，它需要 Android 14（`Build.VERSION_CODES.UPSIDE_DOWN_CAKE`，API level 34）及更高版本。在 Android 13（API level 33）及更低版本上，设置 `showMiniEmojiTrail = false`。
2. **用户提供的纹理位图**：`androidx.ink` 不包含 emoji 位图文件。请用户添加纹理位图（例如放在 `app/src/main/res/drawable-nodpi/`），并在 `TextureBitmapStore` 中注册其 `clientTextureId`。


```kotlin
val supportsMiniEmojiTrail = Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE

val heartHighlighter = StockBrushes.emojiHighlighter(
    clientTextureId = "emoji-heart",
    showMiniEmojiTrail = supportsMiniEmojiTrail,
)
```

<br />

### 在保留 alpha 的前提下修改并切换笔刷

`Brush` 是不可变的。用 `copy` 与 `copyWithComposeColor` 派生更新后的笔刷，用 `brush.composeColor` 读取
Compose 颜色，并用结构相等（`==`，绝不要用 `===`）比较 `BrushFamily` 实例。
切换到或切离 `StockBrushes.highlighter` 时，为荧光笔应用半透明 alpha（例如 `0.3f`），
为不透明笔刷恢复 `alpha = 1f`：


```kotlin
private const val HIGHLIGHTER_ALPHA = 0.3f

fun switchBrushFamily(currentBrush: Brush, targetFamily: BrushFamily): Brush {
    val baseColor = currentBrush.composeColor
    val adjustedColor = if (targetFamily == StockBrushes.highlighter()) {
        baseColor.copy(alpha = HIGHLIGHTER_ALPHA)
    } else {
        baseColor.copy(alpha = 1f)
    }
    return currentBrush
        .copy(family = targetFamily)
        .copyWithComposeColor(color = adjustedColor)
}

fun recolorStroke(stroke: Stroke, newColor: Color): Stroke {
    val updatedBrush = stroke.brush.copyWithComposeColor(color = newColor)
    return stroke.copy(brush = updatedBrush)
}
```

<br />

## `TextureBitmapStore` 与 generation 失效

提供一个单例 `TextureBitmapStore`，并带有响应式的 `generation` 计数器。
由于 `CanvasStrokeRenderer` 与 `InProgressStrokes` 会在首次绘制时按 `BrushPaint` 缓存
`BitmapShader` 实例，所以要观察 `generation`，以便用 `remember(textureStore, cacheGen)` 重建
`CanvasStrokeRenderer`，并用 `key(cacheGen)` 在纹理动态加载时更新 `InProgressStrokes` 的缓存：


```kotlin
class AppTextureBitmapStore(context: Context) : TextureBitmapStore {
    private val resources = context.resources
    private val textureResources: Map<String, Int> = mapOf(
        "emoji-heart" to R.drawable.emoji_heart,
    )
    private val loadedBitmaps = mutableMapOf<String, Bitmap>()

    private val _generation = MutableStateFlow(0)
    val generation: StateFlow<Int> = _generation.asStateFlow()

    override operator fun get(clientTextureId: String): Bitmap? {
        return loadedBitmaps.getOrPut(clientTextureId) {
            textureResources[clientTextureId]?.let { resId ->
                BitmapFactory.decodeResource(resources, resId)
            } ?: return null
        }
    }

    fun loadTexture(textureId: String, bitmap: Bitmap) {
        loadedBitmaps[textureId] = bitmap
        _generation.update { it + 1 }
    }
}

val LocalTextureStore = staticCompositionLocalOf<AppTextureBitmapStore> {
    error("No AppTextureBitmapStore provided")
}
```

<br />

## 常见陷阱

- **在橡皮擦模式下仍保持 `InProgressStrokes` 活跃**：当 `isEraserMode` 为 `true` 时把它从组合中移除，避免指针事件冲突。
- **省略 `CanvasStrokeRenderer.draw` 外围的 `withSave`**：始终把每次 `draw` 调用包在 `nativeCanvas.withSave { }` 中，防止矩阵或裁剪泄漏（一个笔划的变换或裁剪边界意外溢出并影响后续绘制）。
- **违反 `0f < epsilon <= size`**：把笔刷的 `size` 缩到小于其 `epsilon` 会抛出 `IllegalArgumentException`。保持 `epsilon >= 0.01f`，避免笔划网格数据占用过多内存。
- **荧光笔使用 `BlendMode.SrcOver`**：如果不在 `withSaveLayer` 内使用 `BlendMode.Multiply` 并降低颜色 alpha（`0.3f`），荧光笔会遮挡已有笔划而不是高亮它们。
