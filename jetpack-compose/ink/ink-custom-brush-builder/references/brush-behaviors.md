用于构建能响应触控笔压力、倾斜、速度、方向和程序化噪声的动态 `BrushBehavior` 节点图的参考（`androidx.ink` `1.1.0-alpha03` 及更高版本）。

## 概述与包导入

`BrushBehavior` 是挂在 `BrushTip.behaviors` 上的树状节点图，按每个输入点求值：**Source 或 ValueNode → \[Operators\] → TerminalNode（`TargetNode` 或 `PolarTargetNode`）**。

- 从 **`androidx.ink.brush.*`** 导入 `BrushBehavior` 和 `InputToolType`（绝不要从 `androidx.ink.brush.behavior.BrushBehavior` 导入）。
- 从 **`androidx.ink.brush.behavior.*`** 导入所有节点类与枚举（`SourceNode`、`ConstantNode`、`NoiseNode`、`ToolTypeFilterNode`、`DampingNode`、`ResponseNode`、`IntegralNode`、`BinaryOpNode`、`InterpolationNode`、`TargetNode`、`PolarTargetNode`、`OutOfRange`、`ProgressDomain`、`EasingFunction`）。

## 全部 11 种行为节点类型

### 1. `SourceNode`（输入信号）

读取原始的触控笔或触摸属性，并用 `sourceOutOfRangeBehavior`
（`OutOfRange.CLAMP`、用于周期角度的 `OutOfRange.REPEAT`，或
`OutOfRange.MIRROR`）把它归一化到 `[sourceValueRangeStart, sourceValueRangeEnd]` 区间：


```kotlin
val pressureSource = SourceNode(
    source = SourceNode.Source.NORMALIZED_PRESSURE,
    sourceValueRangeStart = 0f,
    sourceValueRangeEnd = 1f,
    sourceOutOfRangeBehavior = OutOfRange.CLAMP,
)
```

<br />

#### 可用的 `SourceNode.Source` 常量

| 类别 | `SourceNode.Source` 常量 | 典型范围 |
|---|---|---|
| **压力与倾斜** | `NORMALIZED_PRESSURE` (`[0, 1]`), `TILT_IN_RADIANS` (`[0, π/2]`), `TILT_X_IN_RADIANS` (`[-π/2, π/2]`), `TILT_Y_IN_RADIANS` (`[-π/2, π/2]`), `ORIENTATION_IN_RADIANS` (`[0, 2π)`), `ORIENTATION_ABOUT_ZERO_IN_RADIANS` (`(-π, π]`) | `[0, 1]` 或弧度 |
| **速度与速率** | `SPEED_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND`, `VELOCITY_X_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND`, `VELOCITY_Y_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND`, `SPEED_IN_CENTIMETERS_PER_SECOND`, `VELOCITY_X_IN_CENTIMETERS_PER_SECOND`, `VELOCITY_Y_IN_CENTIMETERS_PER_SECOND` | `[0, ∞)` 或 `(-∞, ∞)` |
| **方向** | `DIRECTION_IN_RADIANS` (`[0, 2π)`), `DIRECTION_ABOUT_ZERO_IN_RADIANS` (`(-π, π]`), `NORMALIZED_DIRECTION_X` (`[-1, 1]`), `NORMALIZED_DIRECTION_Y` (`[-1, 1]`) | 角度请用 `OutOfRange.REPEAT` |
| **加速度** | `ACCELERATION_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND_SQUARED`, `ACCELERATION_X_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND_SQUARED`, `ACCELERATION_Y_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND_SQUARED`, `ACCELERATION_FORWARD_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND_SQUARED`, `ACCELERATION_LATERAL_IN_MULTIPLES_OF_BRUSH_SIZE_PER_SECOND_SQUARED`, `ACCELERATION_IN_CENTIMETERS_PER_SECOND_SQUARED`, `ACCELERATION_X_IN_CENTIMETERS_PER_SECOND_SQUARED`, `ACCELERATION_Y_IN_CENTIMETERS_PER_SECOND_SQUARED`, `ACCELERATION_FORWARD_IN_CENTIMETERS_PER_SECOND_SQUARED`, `ACCELERATION_LATERAL_IN_CENTIMETERS_PER_SECOND_SQUARED` | `[0, ∞)` 或 `(-∞, ∞)` |
| **距离与时间** | `DISTANCE_TRAVELED_IN_MULTIPLES_OF_BRUSH_SIZE`, `DISTANCE_TRAVELED_IN_CENTIMETERS`, `DISTANCE_REMAINING_IN_MULTIPLES_OF_BRUSH_SIZE`, `DISTANCE_REMAINING_AS_FRACTION_OF_STROKE_LENGTH` (`[0, 1]`), `PREDICTED_DISTANCE_TRAVELED_IN_MULTIPLES_OF_BRUSH_SIZE`, `PREDICTED_DISTANCE_TRAVELED_IN_CENTIMETERS`, `TIME_OF_INPUT_IN_SECONDS`, `TIME_FROM_INPUT_TO_STROKE_END_IN_SECONDS`, `PREDICTED_TIME_ELAPSED_IN_SECONDS`, `TIME_SINCE_INPUT_IN_SECONDS`, `TIME_SINCE_STROKE_END_IN_SECONDS` | `[0, ∞)` |

### 2-9. 取值与运算符节点

使用 `ConstantNode`、`NoiseNode`、`ToolTypeFilterNode`、`DampingNode`、
`ResponseNode`、`IntegralNode`、`BinaryOpNode` 和 `InterpolationNode`，在某个
`ProgressDomain`（`TIME_IN_SECONDS`、`DISTANCE_IN_CENTIMETERS` 或
`DISTANCE_IN_MULTIPLES_OF_BRUSH_SIZE`）上生成、过滤、平滑或组合信号：


```kotlin
// 2. ConstantNode: fixed scalar output
val halfConstant = ConstantNode(0.5f)

// 3. NoiseNode: procedural noise over stroke distance or time
val distanceNoise = NoiseNode(
    seed = 42,
    varyOver = ProgressDomain.DISTANCE_IN_CENTIMETERS,
    basePeriod = 0.3f,
)

// 4. ToolTypeFilterNode: pass signal only for selected InputToolType set
val stylusOnlyPressure = ToolTypeFilterNode(
    enabledToolTypes = setOf(InputToolType.STYLUS),
    input = pressureSource,
)

// 5. DampingNode: low-pass smoothing over time or distance
val dampedPressure = DampingNode(
    dampOver = ProgressDomain.TIME_IN_SECONDS,
    strength = 0.15f,
    input = pressureSource,
)

// 6. ResponseNode: non-linear easing (Predefined, CubicBezier, Linear, Steps)
val easedPressure = ResponseNode(
    responseCurve = EasingFunction.Predefined.EASE_IN_OUT,
    input = dampedPressure,
)

// 7. IntegralNode: accumulates input over time or distance
val accumulatedPressure = IntegralNode(
    integrateOver = ProgressDomain.TIME_IN_SECONDS,
    integralValueRangeStart = 0f,
    integralValueRangeEnd = 1f,
    integralOutOfRangeBehavior = OutOfRange.CLAMP,
    input = pressureSource,
)

// 8. BinaryOpNode: PRODUCT, SUM, MIN, MAX, AND_THEN, OR_ELSE, XOR_ELSE
val scaledPressure = BinaryOpNode(
    operation = BinaryOpNode.BinaryOp.PRODUCT,
    firstInput = easedPressure,
    secondInput = halfConstant,
)

// 9. InterpolationNode: LERP or INVERSE_LERP between startInput and endInput
val lerpedNode = InterpolationNode(
    interpolation = InterpolationNode.Interpolation.LERP,
    paramInput = easedPressure,
    startInput = ConstantNode(0.2f),
    endInput = ConstantNode(1.0f),
)
```

<br />

### 10. `TargetNode`（标量终止节点）

把归一化到 `[0, 1]` 的 `ValueNode` 输入映射到
`[targetModifierRangeStart, targetModifierRangeEnd]`（端点必须有限且不相等：
`rangeStart != rangeEnd`）：

| `TargetNode.Target` 常量 | 对笔画的效果 |
|---|---|
| `SIZE_MULTIPLIER`, `WIDTH_MULTIPLIER`, `HEIGHT_MULTIPLIER` | 缩放笔尖整体尺寸、水平宽度或垂直高度 |
| `SLANT_OFFSET_IN_RADIANS`, `ROTATION_OFFSET_IN_RADIANS` | 以**弧度**为单位增加动态切变或旋转偏移 |
| `CORNER_ROUNDING_OFFSET`, `PINCH_OFFSET` | 给笔尖的 `cornerRounding` 或 `pinch` 增加偏移 |
| `OPACITY_MULTIPLIER`, `PAINT_ANIMATION_PROGRESS_OFFSET` | 乘以逐顶点不透明度（需要 `SelfOverlap.ANY` 或 `ACCUMULATE`），或偏移动画纹理进度 |
| `HUE_OFFSET_IN_RADIANS`, `CHROMA_MULTIPLIER`, `LIGHTNESS_OFFSET` | 偏移色相、色度或亮度 |
| `POSITION_OFFSET_X_IN_MULTIPLES_OF_BRUSH_SIZE`, `POSITION_OFFSET_Y_IN_MULTIPLES_OF_BRUSH_SIZE`, `POSITION_OFFSET_FORWARD_IN_MULTIPLES_OF_BRUSH_SIZE`, `POSITION_OFFSET_LATERAL_IN_MULTIPLES_OF_BRUSH_SIZE` | 以画笔尺寸的倍数偏移笔尖位置 |

### 11. `PolarTargetNode`（二维向量终止节点）

把极坐标向量（`angleInput` + `magnitudeInput`）应用到二维位置偏移目标（
`POSITION_OFFSET_ABSOLUTE_IN_RADIANS_AND_MULTIPLES_OF_BRUSH_SIZE` 或
`POSITION_OFFSET_RELATIVE_IN_RADIANS_AND_MULTIPLES_OF_BRUSH_SIZE`）：


```kotlin
val polarScatterBehavior = BrushBehavior(
    terminalNode = PolarTargetNode(
        target = PolarTargetNode.PolarTarget.POSITION_OFFSET_ABSOLUTE_IN_RADIANS_AND_MULTIPLES_OF_BRUSH_SIZE,
        angleRangeStart = 0f,
        angleRangeEnd = (2 * Math.PI).toFloat(),
        angleInput = NoiseNode(
            seed = 101,
            varyOver = ProgressDomain.DISTANCE_IN_CENTIMETERS,
            basePeriod = 0.2f,
        ),
        magnitudeRangeStart = 0f,
        magnitudeRangeEnd = 0.5f,
        magnitudeInput = SourceNode(
            source = SourceNode.Source.NORMALIZED_PRESSURE,
            sourceValueRangeStart = 0f,
            sourceValueRangeEnd = 1f,
        ),
    ),
)
```

<br />

## 可复用的行为模式与示例

为直接映射（`Source` 到 `Target`）、平滑（`Source` 到 `Damping` 到 `Target`）
和程序化噪声（`Noise` 到 `Target`）行为编写可复用的辅助函数，并把它们挂到
`BrushTip(behaviors = listOf(...))` 上：


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

// 1. Pressure -> Size (50% to 150% with 150ms damping)
val pressureToSize = smoothedBehavior(
    source = SourceNode.Source.NORMALIZED_PRESSURE,
    sourceStart = 0f,
    sourceEnd = 1f,
    target = TargetNode.Target.SIZE_MULTIPLIER,
    targetStart = 0.5f,
    targetEnd = 1.5f,
    dampingSeconds = 0.15f,
)

// 2. Stylus Tilt -> Width (1x to 2.5x as tilt increases to pi/2)
val tiltToWidth = smoothedBehavior(
    source = SourceNode.Source.TILT_IN_RADIANS,
    sourceStart = 0f,
    sourceEnd = (Math.PI / 2).toFloat(),
    target = TargetNode.Target.WIDTH_MULTIPLIER,
    targetStart = 1.0f,
    targetEnd = 2.5f,
    dampingSeconds = 0.1f,
)

// 3. Organic distance-based wobble using NoiseNode -> lateral position offset
fun createWobblyBrush(): BrushFamily {
    val wobbleBehavior = BrushBehavior(
        terminalNode = TargetNode(
            target = TargetNode.Target.POSITION_OFFSET_LATERAL_IN_MULTIPLES_OF_BRUSH_SIZE,
            targetModifierRangeStart = -0.25f,
            targetModifierRangeEnd = 0.25f,
            input = NoiseNode(
                seed = 12345,
                varyOver = ProgressDomain.DISTANCE_IN_CENTIMETERS,
                basePeriod = 0.4f,
            ),
        ),
    )
    return BrushFamily(
        tip = BrushTip(
            scaleX = 1f,
            scaleY = 1f,
            cornerRounding = 1f,
            behaviors = listOf(wobbleBehavior),
        ),
        paint = BrushPaint(selfOverlap = SelfOverlap.ANY),
    )
}
```

<br />

## 常见陷阱

- **弄反节点嵌套顺序** ：`TargetNode` 或 `PolarTargetNode` 必须是最外层的 `terminalNode`，由它包裹运算符 `ValueNode` 实例，再由这些实例包裹 `SourceNode` 或 `NoiseNode`。
- **把区间端点设成相等（`rangeStart == rangeEnd`）** ：`SourceNode`、`TargetNode` 和 `PolarTargetNode` 的区间端点必须不相等（`start != end`）；端点相等会抛 `IllegalArgumentException`。固定值请用 `ConstantNode`。
- **在周期性的方向或朝向源上使用 `OutOfRange.CLAMP`** ：`DIRECTION_IN_RADIANS` 和 `ORIENTATION_IN_RADIANS` 在 2π 处回绕---始终传 `OutOfRange.REPEAT`。
- **把 `OPACITY_MULTIPLIER` 淡到 `0f` 却没有把 `SIZE_MULTIPLIER` 降到
  `0f`** ：同时把 `SIZE_MULTIPLIER` 收到 `0f`，这样不可见的笔画 mesh 几何体才会被裁剪掉。
