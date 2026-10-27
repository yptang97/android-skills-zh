提供可直接复制的自定义 `BrushFamily` 与 `Brush` 实现参考，这些实现基于
Kotlin 构造函数 API 构建（`androidx.ink` `1.1.0-alpha03` 及更高版本）。

## 共享的行为辅助函数

下面所有配方都会用到这两个辅助函数 `smoothedBehavior` 与 `jitterBehavior`：


```kotlin
fun smoothedBehavior(
    source: SourceNode.Source,
    sourceStart: Float,
    sourceEnd: Float,
    target: TargetNode.Target,
    targetStart: Float,
    targetEnd: Float,
    dampingSeconds: Float,
    outOfRange: OutOfRange = OutOfRange.CLAMP,
): BrushBehavior = BrushBehavior(
    terminalNode = TargetNode(
        target = target,
        targetModifierRangeStart = targetStart,
        targetModifierRangeEnd = targetEnd,
        input = DampingNode(
            dampOver = ProgressDomain.TIME_IN_SECONDS,
            strength = dampingSeconds,
            input = SourceNode(
                source = source,
                sourceValueRangeStart = sourceStart,
                sourceValueRangeEnd = sourceEnd,
                sourceOutOfRangeBehavior = outOfRange,
            ),
        ),
    ),
)

fun jitterBehavior(
    target: TargetNode.Target,
    targetStart: Float,
    targetEnd: Float,
    basePeriod: Float,
    seed: Int = 42,
): BrushBehavior = BrushBehavior(
    terminalNode = TargetNode(
        target = target,
        targetModifierRangeStart = targetStart,
        targetModifierRangeEnd = targetEnd,
        input = NoiseNode(
            seed = seed,
            varyOver = ProgressDomain.DISTANCE_IN_CENTIMETERS,
            basePeriod = basePeriod,
        ),
    ),
)
```

<br />

## 配方 1：压感笔

把触控笔压力（`NORMALIZED_PRESSURE`）同时映射到笔画尺寸（`50%` 到
`150%`）和逐顶点不透明度（`30%` 到 `100%`）。使用 `SelfOverlap.ANY`，
让 mesh 渲染器应用逐顶点 `OPACITY_MULTIPLIER`：


```kotlin
fun createPressureResponsiveBrush(): Brush {
    val pressurePenFamily = BrushFamily(
        coats = listOf(
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1f,
                    scaleY = 1f,
                    cornerRounding = 1f,
                    behaviors = listOf(
                        smoothedBehavior(
                            source = SourceNode.Source.NORMALIZED_PRESSURE,
                            sourceStart = 0f,
                            sourceEnd = 1f,
                            target = TargetNode.Target.SIZE_MULTIPLIER,
                            targetStart = 0.5f,
                            targetEnd = 1.5f,
                            dampingSeconds = 0.15f,
                        ),
                        smoothedBehavior(
                            source = SourceNode.Source.NORMALIZED_PRESSURE,
                            sourceStart = 0f,
                            sourceEnd = 1f,
                            target = TargetNode.Target.OPACITY_MULTIPLIER,
                            targetStart = 0.3f,
                            targetEnd = 1.0f,
                            dampingSeconds = 0.1f,
                        ),
                    ),
                ),
                paint = BrushPaint(selfOverlap = SelfOverlap.ANY),
            ),
        ),
    )

    return Brush.createWithComposeColor(
        family = pressurePenFamily,
        color = Color.Black,
        size = 10f,
        epsilon = 0.1f,
    )
}
```

<br />

## 配方 2：倾斜响应的书法笔尖

把不对称、45 度倾斜的窄 `BrushTip`（`scaleX = 0.3f`、
`scaleY = 1.0f`、`rotationDegrees = 45f`）与触控笔倾斜（`TILT_IN_RADIANS` 到
`WIDTH_MULTIPLIER`）以及移动方向（`DIRECTION_IN_RADIANS` 配合
`OutOfRange.REPEAT` 到 `ROTATION_OFFSET_IN_RADIANS`）结合起来：


```kotlin
fun createCalligraphyBrush(): BrushFamily {
    return BrushFamily(
        coats = listOf(
            BrushCoat(
                tip = BrushTip(
                    scaleX = 0.3f,
                    scaleY = 1.0f,
                    cornerRounding = 0.2f,
                    rotationDegrees = 45f,
                    behaviors = listOf(
                        smoothedBehavior(
                            source = SourceNode.Source.TILT_IN_RADIANS,
                            sourceStart = 0f,
                            sourceEnd = (Math.PI / 2).toFloat(),
                            target = TargetNode.Target.WIDTH_MULTIPLIER,
                            targetStart = 1.0f,
                            targetEnd = 2.5f,
                            dampingSeconds = 0.1f,
                        ),
                        smoothedBehavior(
                            source = SourceNode.Source.DIRECTION_IN_RADIANS,
                            sourceStart = 0f,
                            sourceEnd = (2 * Math.PI).toFloat(),
                            target = TargetNode.Target.ROTATION_OFFSET_IN_RADIANS,
                            targetStart = (-Math.PI).toFloat(),
                            targetEnd = Math.PI.toFloat(),
                            dampingSeconds = 0.05f,
                            outOfRange = OutOfRange.REPEAT,
                        ),
                    ),
                ),
                paint = BrushPaint(selfOverlap = SelfOverlap.DISCARD),
            ),
        ),
    )
}
```

<br />

## 配方 3：带噪声抖动的纹理素描铅笔

把基于倾斜的宽度、基于压力的不透明度、程序化切变抖动（
`NoiseNode` 到 `SLANT_OFFSET_IN_RADIANS`），以及 `BrushPaint.TilingTexture`
颗粒图层（在 `TextureBitmapStore` 中注册的 `"pencil-grain"`）结合起来：


```kotlin
fun createShadingPencilBrush(): BrushFamily {
    return BrushFamily(
        coats = listOf(
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1f,
                    scaleY = 1f,
                    cornerRounding = 1f,
                    behaviors = listOf(
                        smoothedBehavior(
                            source = SourceNode.Source.TILT_IN_RADIANS,
                            sourceStart = 0f,
                            sourceEnd = (Math.PI / 2).toFloat(),
                            target = TargetNode.Target.WIDTH_MULTIPLIER,
                            targetStart = 1.0f,
                            targetEnd = 2.5f,
                            dampingSeconds = 0.1f,
                        ),
                        smoothedBehavior(
                            source = SourceNode.Source.NORMALIZED_PRESSURE,
                            sourceStart = 0f,
                            sourceEnd = 1f,
                            target = TargetNode.Target.OPACITY_MULTIPLIER,
                            targetStart = 0.3f,
                            targetEnd = 1.0f,
                            dampingSeconds = 0.1f,
                        ),
                        jitterBehavior(
                            target = TargetNode.Target.SLANT_OFFSET_IN_RADIANS,
                            targetStart = -0.15f,
                            targetEnd = 0.15f,
                            basePeriod = 0.3f,
                        ),
                    ),
                ),
                paint = BrushPaint(
                    selfOverlap = SelfOverlap.ANY,
                    colorFunctions = listOf(BrushPaint.ColorFunction.OpacityMultiplier(0.8f)),
                    textureLayers = listOf(
                        BrushPaint.TilingTexture(
                            clientTextureId = "pencil-grain",
                            sizeX = 1.0f,
                            sizeY = 1.0f,
                            sizeUnit = BrushPaint.TextureLayer.SizeUnit.BRUSH_SIZE,
                            blendMode = BrushPaint.TextureLayer.BlendMode.MODULATE,
                        ),
                    ),
                ),
            ),
        ),
    )
}
```

<br />

## 配方 4：速度敏感的水彩晕染

随着触控笔速度（`SPEED_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND`）增加，降低笔画不透明度（
`OPACITY_MULTIPLIER`），并配一个可重复的水彩晕染
`TilingTexture`：


```kotlin
fun createWatercolorBrush(): BrushFamily {
    return BrushFamily(
        coats = listOf(
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1f,
                    scaleY = 1f,
                    cornerRounding = 1f,
                    behaviors = listOf(
                        smoothedBehavior(
                            source = SourceNode.Source.SPEED_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND,
                            sourceStart = 0f,
                            sourceEnd = 8f,
                            target = TargetNode.Target.OPACITY_MULTIPLIER,
                            targetStart = 1.0f,
                            targetEnd = 0.2f,
                            dampingSeconds = 0.3f,
                        ),
                    ),
                ),
                paint = BrushPaint(
                    selfOverlap = SelfOverlap.ANY,
                    colorFunctions = listOf(BrushPaint.ColorFunction.OpacityMultiplier(0.6f)),
                    textureLayers = listOf(
                        BrushPaint.TilingTexture(
                            clientTextureId = "watercolor-wash",
                            sizeX = 2.0f,
                            sizeY = 2.0f,
                            sizeUnit = BrushPaint.TextureLayer.SizeUnit.BRUSH_SIZE,
                            blendMode = BrushPaint.TextureLayer.BlendMode.MODULATE,
                        ),
                    ),
                ),
            ),
        ),
    )
}
```

<br />

## 配方 5：多层分层阴影画笔

在 `BrushFamily.coats` 中使用两个 `BrushCoat` 图层：更宽（`1.3f`）、
低不透明度（`0.15f`）的底层图层（`coats[0]`）渲染在压感响应的不透明顶层图层（
`coats[1]`）之下：


```kotlin
fun createMultiCoatBrush(): BrushFamily {
    return BrushFamily(
        coats = listOf(
            // Coat 0: Wider semi-transparent shadow layer underneath
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1.3f,
                    scaleY = 1.3f,
                    cornerRounding = 1f,
                ),
                paint = BrushPaint(
                    selfOverlap = SelfOverlap.DISCARD,
                    colorFunctions = listOf(
                        BrushPaint.ColorFunction.OpacityMultiplier(0.15f),
                    ),
                ),
            ),
            // Coat 1: Main opaque stroke layer on top
            BrushCoat(
                tip = BrushTip(
                    scaleX = 1f,
                    scaleY = 1f,
                    cornerRounding = 1f,
                    behaviors = listOf(
                        smoothedBehavior(
                            source = SourceNode.Source.NORMALIZED_PRESSURE,
                            sourceStart = 0f,
                            sourceEnd = 1f,
                            target = TargetNode.Target.SIZE_MULTIPLIER,
                            targetStart = 0.5f,
                            targetEnd = 1.5f,
                            dampingSeconds = 0.15f,
                        ),
                    ),
                ),
                paint = BrushPaint(
                    selfOverlap = SelfOverlap.DISCARD,
                    colorFunctions = listOf(
                        BrushPaint.ColorFunction.OpacityMultiplier(1f),
                    ),
                ),
            ),
        ),
    )
}
```

<br />

## 常见陷阱

- **忘记注册纹理** ：如果不通过 `TextureBitmapStore` 提供位图，纹理配方（`"pencil-grain"`、`"watercolor-wash"`）会渲染成平坦的填充。
- **无意中在 `SIZE_MULTIPLIER` 上叠加多个行为** ：乘数类目标按乘法叠加---两个 `0.5f` 到 `1.5f` 的尺寸行为会合成 `0.25f` 到 `2.25f` 的范围。
- **在压力-不透明度或水彩图层上使用 `SelfOverlap.DISCARD`** ：当图层依赖 `OPACITY_MULTIPLIER` 行为或重叠着色时，始终使用 `SelfOverlap.ANY` 或 `SelfOverlap.ACCUMULATE`。
