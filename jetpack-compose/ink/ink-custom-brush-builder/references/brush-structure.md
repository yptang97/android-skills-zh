用于定义 `BrushFamily` 与 `BrushCoat` 层级结构、配置 `BrushTip` 几何和
`BrushPaint` 混合，以及调节 `InputModel` 笔画平滑的参考（
`androidx.ink` `1.1.0-alpha03` 及更高版本）。

## `BrushFamily` 与 `BrushCoat` 层级结构

    graph TD
        BF["BrushFamily"]
        C0["BrushCoat[0]"]
        C1["BrushCoat[1] ..."]
        T0["BrushTip"]
        P0["BrushPaint[]"]
        BB["BrushBehavior[]"]
        TP["Tip Properties (scaleX, scaleY, cornerRounding, slantDegrees, pinch, rotationDegrees)"]
        SO["SelfOverlap"]
        CF["BrushPaint.ColorFunction[]"]
        TL["TextureLayer[] (TilingTexture / StampingTexture)"]

        BF --> C0
        BF --> C1
        C0 --> T0
        C0 --> P0
        T0 --> TP
        T0 --> BB
        P0 --> SO
        P0 --> CF
        P0 --> TL

| 层级 | 类型 | 作用 |
|---|---|---|
| **BrushFamily** | `BrushFamily` | 顶层不可变画笔定义，包含一个或多个 `BrushCoat` 图层和一个 `InputModel`。 |
| **BrushCoat** | `BrushCoat` | 单次渲染通道，含一个 `BrushTip`，以及 `paint: BrushPaint` 或按优先级排列的备选列表 `paintPreferences: List<BrushPaint>`。`BrushFamily.coats` 中的多个 `BrushCoat` 从索引 `0`（最底层）向上叠加合成。 |
| **BrushTip** | `BrushTip` | 每个点上的几何笔迹形状（`scaleX`、`scaleY`、`cornerRounding`、`slantDegrees`、`pinch`、`rotationDegrees`），加上动态 `BrushBehavior` 节点树。 |
| **BrushPaint** | `BrushPaint` | 视觉外观（`SelfOverlap`、`BrushPaint.ColorFunction` 列表，以及 `BrushPaint.TilingTexture` 或 `StampingTexture` 图层）。 |

### 构造与复制 `BrushFamily` 和 `BrushCoat`

使用多层 `BrushFamily(coats = listOf(...))` 构造函数，或单层
`BrushFamily(tip = ..., paint = ...)` 快捷写法，并用 `.copy(...)` 派生变体（
`BrushPaint` 不提供 `copy`）：


```kotlin
val singleCoatFamily = BrushFamily(
    tip = BrushTip(scaleX = 1f, scaleY = 1f, cornerRounding = 1f),
    paint = BrushPaint(selfOverlap = SelfOverlap.ANY),
)

val multiCoatFamily = BrushFamily(
    coats = listOf(
        // Coat 0: Wider semi-transparent shadow coat rendered underneath
        BrushCoat(
            tip = BrushTip(scaleX = 1.3f, scaleY = 1.3f, cornerRounding = 1f),
            paint = BrushPaint(
                selfOverlap = SelfOverlap.DISCARD,
                colorFunctions = listOf(BrushPaint.ColorFunction.OpacityMultiplier(0.15f)),
            ),
        ),
        // Coat 1: Main opaque stroke coat rendered on top
        BrushCoat(
            tip = BrushTip(scaleX = 1f, scaleY = 1f, cornerRounding = 1f),
            paint = BrushPaint(selfOverlap = SelfOverlap.DISCARD),
        ),
    ),
)

val roundedVariant = singleCoatFamily.copy(
    coats = listOf(
        singleCoatFamily.coats.first().let { coat ->
            coat.copy(tip = coat.tip.copy(cornerRounding = 0.5f))
        }
    ),
)
```

<br />

## `BrushTip` 几何配置

| 属性 | 类型与默认值 | 范围与说明 |
|---|---|---|
| `scaleX`, `scaleY` | `Float = 1f` | 笔尖的水平与垂直缩放，会乘以 `Brush.size`（`>= 0f`；至少有一个必须 `> 0f`）。 |
| `cornerRounding` | `Float = 1f` | `0f` = 尖锐的矩形或平行四边形；`1f` = 完全圆化的圆形或胶囊形。 |
| `slantDegrees` | `Float = 0f` | 在 `rotationDegrees` 之前应用的静态切变角度，单位为**度**（`[-90f, 90f]`）。 |
| `pinch` | `Float = 0f` | 把顶部两个角捏合到一起（`0f` = 矩形，`1f` = 三角形）。 |
| `rotationDegrees` | `Float = 0f` | 静态旋转偏移，单位为**度**（注意：`BrushTip` 的静态角度使用度，而 `BrushBehavior` 的动态角度使用**弧度**）。 |
| `particleGapDistanceScale` | `Float = 0f` | 离散盖章粒子之间的间距，以画笔尺寸的倍数表示（`0f` = 连续笔画）。 |
| `particleGapDurationMillis` | `Long = 0L` | 离散盖章粒子之间的时间间隔，单位为毫秒（`0L` = 连续笔画）。 |
| `behaviors` | `List<BrushBehavior> = emptyList()` | 挂在这个笔尖上的动态 `BrushBehavior` 节点图。 |

### `BrushTip` 形状示例（书法笔尖与平头马克笔）


```kotlin
// Narrow angled calligraphy nib (static angle in degrees)
val calligraphyTip = BrushTip(
    scaleX = 0.3f,
    scaleY = 1.0f,
    cornerRounding = 0.2f,
    rotationDegrees = 45f,
)

// Wide flat marker tip
val markerTip = BrushTip(
    scaleX = 2.0f,
    scaleY = 0.5f,
    cornerRounding = 0.4f,
)
```

<br />

## `BrushPaint` 混合与 `ColorFunction`

### `SelfOverlap` 模式

`SelfOverlap` 控制**单条笔画**自身交叉处的区域在渲染时如何混合：

| 模式 | 行为与渲染器兼容性 |
|---|---|
| `SelfOverlap.ANY` **(default)** | 在 Android 14（API level 34）及更高版本的硬件 `Canvas` 上使用 `ACCUMULATE`（`CanvasMeshRenderer`），在 Android 13（API level 33）及更低版本或软件 `Canvas(bitmap)` 上使用 `DISCARD`（`CanvasPathRenderer`）。只要某个图层使用逐顶点不透明度（`OPACITY_MULTIPLIER`）或颜色 `BrushBehavior` 实例，就必须使用它。 |
| `SelfOverlap.ACCUMULATE` | 在半透明笔画自身交叉处累积不透明度。需要 `CanvasMeshRenderer`（Android 14（API level 34）及更高版本的硬件 `Canvas`）；除非在 `BrushCoat.paintPreferences` 中提供备选 `BrushPaint`，否则会被 `CanvasPathRenderer` 拒绝。 |
| `SelfOverlap.DISCARD` | 渲染平坦、不透明度均匀的轮廓（`CanvasPathRenderer`）。与 `BrushPaint.StampingTexture`，以及同一 `BrushCoat` 上的逐顶点不透明度或颜色 `BrushBehavior` 实例**不兼容**。 |

### `BrushPaint.ColorFunction`（`OpacityMultiplier` 与 `ReplaceColor`）

用 `BrushPaint.ColorFunction` 设置图层的静态不透明度，或替换某个图层的颜色（
例如固定的黑色阴影图层）。绝不要调用内部的 `ReplaceColor.withComposeColor`
---改用 `withColorLong` 或 `withColorIntArgb`：


```kotlin
val translucentPaint = BrushPaint(
    selfOverlap = SelfOverlap.ANY,
    colorFunctions = listOf(
        BrushPaint.ColorFunction.OpacityMultiplier(0.7f),
    ),
)

val fixedBlackShadowPaint = BrushPaint(
    selfOverlap = SelfOverlap.DISCARD,
    colorFunctions = listOf(
        BrushPaint.ColorFunction.ReplaceColor.withColorLong(Color.Black.value.toLong()),
        BrushPaint.ColorFunction.OpacityMultiplier(0.2f),
    ),
)
```

<br />

## `InputModel` 与笔画平滑（`SlidingWindowModel`）

`BrushFamily.inputModel` 会在原始触摸点和触控笔点进入行为图之前先做平滑：

- **`BrushFamily.InputModel.SlidingWindowModel`** ：接收 `(windowDurationMillis, upsamplingFrequencyHz)`，应用滑动平均窗口（`windowDurationMillis`，默认 `20L` 毫秒；典型范围 `10L` 到 `50L` 毫秒）和时间上采样（`upsamplingFrequencyHz`，默认 `180` Hz，取 `0` 则禁用）。`BrushFamily.InputModel.DEFAULT_INPUT_MODEL` 使用 `20L` 毫秒与 `180` Hz。
- **`BrushFamily.InputModel.PASSTHROUGH_MODEL`**：跳过平滑与上采样；仅限用于合成或已建模的输入流。

把 `SlidingWindowModel`（用于路径平滑）与
`BrushBehavior` 中的 `DampingNode`（用于压力等动态属性的平滑）结合使用：


```kotlin
/**
 * Creates a custom [BrushFamily] configured for smooth, low-jitter strokes.
 *
 * @param windowDurationMillis Sliding-window duration in milliseconds (default 30ms)
 *   controlling input path smoothing versus latency.
 * @param upsamplingFrequencyHz Target upsampling frequency in Hz (default 180Hz)
 *   for smooth curve subdivision.
 */
fun createSmoothBrushFamily(
    windowDurationMillis: Long = 30L,
    upsamplingFrequencyHz: Int = 180,
): BrushFamily {
    return BrushFamily(
        coats = listOf(
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1f,
                    scaleY = 1f,
                    cornerRounding = 1f,
                    behaviors = listOf(
                        BrushBehavior(
                            terminalNode = TargetNode(
                                target = TargetNode.Target.SIZE_MULTIPLIER,
                                targetModifierRangeStart = 0.5f,
                                targetModifierRangeEnd = 1.5f,
                                input = DampingNode(
                                    dampOver = ProgressDomain.TIME_IN_SECONDS,
                                    strength = 0.15f,
                                    input = SourceNode(
                                        source = SourceNode.Source.NORMALIZED_PRESSURE,
                                        sourceValueRangeStart = 0f,
                                        sourceValueRangeEnd = 1f,
                                        sourceOutOfRangeBehavior = OutOfRange.CLAMP,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                paint = BrushPaint(selfOverlap = SelfOverlap.ANY),
            ),
        ),
        inputModel = BrushFamily.InputModel.SlidingWindowModel(
            windowDurationMillis = windowDurationMillis,
            upsamplingFrequencyHz = upsamplingFrequencyHz,
        ),
    )
}
```

<br />

## 常见陷阱

- **把 `BrushFamily.coats` 与 `BrushCoat.paintPreferences` 搞混** ：多个 `BrushCoat` 是作为图层彼此叠着渲染；而 `paintPreferences` 中的多个 `BrushPaint` 是备选方案，渲染器只会绘制*第一个*兼容的 `BrushPaint`。
- **混用度与弧度** ：`BrushTip` 的静态角度（`rotationDegrees`、`slantDegrees`）使用**度**（`45f`），而 `BrushBehavior` 的动态目标（`ROTATION_OFFSET_IN_RADIANS`、`SLANT_OFFSET_IN_RADIANS`）和数据源（`TILT_IN_RADIANS`）使用**弧度**（`(Math.PI / 4).toFloat()`）。
- **把 `SelfOverlap.DISCARD` 与不透明度或颜色 `BrushBehavior`
  实例一起使用** ：`DISCARD` 会强制使用 `CanvasPathRenderer`，而它忽略逐顶点不透明度和颜色行为。请改用 `SelfOverlap.ANY`。
- **把 `windowDurationMillis` 设到超过 `50L` 毫秒**：过大的平滑窗口会带来明显的触控笔延迟。
