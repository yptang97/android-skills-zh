---
name: ink-custom-brush-builder
description: 为 Android 应用创建基于 Jetpack Ink（androidx.ink 1.1.0-alpha03 及更高版本）的自定义
  BrushFamily 定义。在配置自定义 BrushTip 形状、使用 BrushBehavior 节点图添加压力、倾斜、速度或噪声灵敏度、创建多层
  BrushCoat 分层画笔、应用平铺或粒子盖章纹理、配置 SlidingWindowModel 输入平滑，或序列化画笔时，使用这个 skill。交付完整的 Kotlin
  BrushFamily、BrushCoat、BrushTip、BrushPaint 和 BrushBehavior 实现。不要用于基于 View（XML）的墨迹绘制、Compose
  绘制表面配置或现成画笔选择。Compose 绘制表面配置、InProgressStrokes 湿墨与干墨渲染、橡皮擦或持久化，请推荐
  ink-app-builder skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-28'
  keywords:
  - Android
  - Jetpack Ink
  - androidx.ink
  - BrushFamily
  - BrushCoat
  - BrushTip
  - BrushPaint
  - BrushBehavior
  - TilingTexture
  - StampingTexture
  - ColorFunction
  - SlidingWindowModel
  - custom brush
---

Android Ink API 中的自定义画笔围绕 **`BrushFamily`** 层级结构构建：

    BrushFamily
    ├── InputModel (BrushFamily.InputModel.SlidingWindowModel or PASSTHROUGH_MODEL)
    └── BrushCoat[] (one or more rendering layers)
        ├── BrushTip (shape: scaleX, scaleY, cornerRounding, rotationDegrees, slantDegrees, pinch)
        │   └── BrushBehavior[] (dynamic response to stylus or touch input)
        │       └── Tree: TargetNode(input = [Operators](input = SourceNode))
        └── BrushPaint (visual appearance)
            ├── SelfOverlap (ANY, ACCUMULATE, or DISCARD)
            ├── TextureLayer[] (BrushPaint.TilingTexture or BrushPaint.StampingTexture)
            └── BrushPaint.ColorFunction[] (OpacityMultiplier or ReplaceColor)

把一个自定义 `BrushFamily` 与 Compose 的 `Color`、`size` 和 `epsilon` 组合起来，即可创建 `Brush`：


```kotlin
val brush = Brush.createWithComposeColor(
    family = myCustomFamily,
    color = Color.Black,
    size = 10f,
    epsilon = 0.1f,
)
```

<br />

> **版本与实验性 API 要求** ：
> - **需要 `androidx.ink` `1.1.0-alpha03` 及更高版本** ：在 `1.0.0`（Stable）
> 与 `1.1.0-alpha01`-`alpha02` 中，`BrushFamily(...)`、`BrushCoat`、`BrushTip`、
> `BrushPaint`、`BrushBehavior` 以及 `androidx.ink.brush.behavior.*` 节点
> 都是 `@RestrictTo(LIBRARY_GROUP)`（在 `1.0.0` stable 中，自定义画笔
> 只能通过 `BrushFamily.decode` 从二进制 proto 流加载）。
> 从 **`1.1.0-alpha03` 及更高版本** 开始，以编程方式创建自定义画笔的
> 构造函数升级为公有 API（`BrushPaint.TilingTexture`、
> `BrushPaint.StampingTexture`、`BrushPaint.ColorFunction`、
> `BrushFamily.InputModel.SlidingWindowModel`，以及全部行为节点）。
> - **在 `1.1.0-alpha03` 及更高版本中不需要 `@OptIn`** ：所有公有的自定义
> 画笔类与 `ink-storage` 的 `BrushFamily` 序列化 API
> （`BrushFamily.encode` 与 `decode`、`AndroidBrushFamilySerialization`、
> `BrushFamilyDecodeCallback`）在 `1.1.0-alpha03` 及更高版本中都无需注解
> （`ExperimentalInkCustomBrushApi` 在 `1.1.0-alpha05` 及更高版本中是
> `@RestrictTo(LIBRARY_GROUP)`，仅在 `1.0.0` stable 的 `BrushFamily`
> 序列化上需要）。

## 工作流与任务路由

根据所请求的自定义画笔任务，按以下条件指令执行：

- **步骤 1（依赖）** ：在为以编程方式创建自定义画笔配置 Android 项目时，先征得用户许可再修改构建文件，并确认 `androidx.ink:ink-brush`、`androidx.ink:ink-brush-compose`、`androidx.ink:ink-storage` 和 `androidx.ink:ink-nativeloader` 在 `gradle/libs.versions.toml` 与 `app/build.gradle.kts` 中使用 `1.1.0-alpha03` 或更高版本。
- **步骤 2（层级、笔尖形状、绘制与输入平滑）** ：在定义 `BrushFamily` 与多层 `BrushCoat`、配置 `BrushTip` 几何（`scaleX`、`scaleY`、`cornerRounding`、`rotationDegrees`、`slantDegrees`、`pinch`）、设置 `BrushPaint` 属性（`SelfOverlap`、`ColorFunction`），或用 `BrushFamily.InputModel.SlidingWindowModel` 平滑笔画输入时，你必须遵循 [brush-structure.md](references/brush-structure.md)。基准 `Brush` 创建或 `1.0.0` 资源加载，请查阅 [Brush APIs](references/android/develop/ui/compose/touch-input/stylus-input/ink-api-brush-apis.md)。
- **步骤 3（动态触控笔与触摸行为）** ：在用 `BrushBehavior` 节点树（`SourceNode`、`DampingNode`、`NoiseNode`、`ResponseNode`、`TargetNode`、`PolarTargetNode`）让画笔对触控笔压力、倾斜、速度、方向或程序化噪声做出动态响应时，你必须遵循 [brush-behaviors.md](references/brush-behaviors.md)。
- **步骤 4（纹理与序列化）** ：在添加 `BrushPaint.TilingTexture` 或 `BrushPaint.StampingTexture` 图层、实现 `TextureBitmapStore`，或编解码自定义 `BrushFamily` 定义（`BrushFamily.encode` 与 `decode`、`AndroidBrushFamilySerialization`、`BrushFamilyDecodeCallback`）时，你必须遵循 [textures-and-serialization.md](references/textures-and-serialization.md)。要告知用户需要往项目里添加哪些纹理图片文件（例如 `app/src/main/res/drawable-nodpi/pencil_grain.png`），并在 `TextureBitmapStore` 中注册。
- **步骤 5（完整画笔配方）** ：在从零构建完整的压感笔、书法笔尖、素描铅笔、水彩晕染或多层阴影画笔时，从 [examples.md](references/examples.md) 中可直接复制的实现开始。
- **Compose 绘制表面、橡皮擦或持久化** ：Compose 绘制表面配置、`InProgressStrokes` 湿墨与干墨渲染、基于几何的擦除，或 Room 笔画持久化，请推荐 `ink-app-builder` skill。

## 反模式

- **绝不要用裸 `ink.proto.*` builder 构建画笔**---始终使用公有的 Kotlin 构造函数（`androidx.ink.brush.*` 中的 `BrushFamily`、`BrushCoat`、`BrushTip`、`BrushPaint`、`BrushBehavior`）。
- **绝不要在触摸监听器里手动缩放笔画宽度**来实现压力或倾斜灵敏度---改用 `BrushBehavior`，把 `SourceNode.Source.NORMALIZED_PRESSURE` 或 `TILT_IN_RADIANS` 映射到 `TargetNode.Target.SIZE_MULTIPLIER` 或 `WIDTH_MULTIPLIER`。
- **绝不要用手动 `Canvas` 位图盖章或 `BitmapShader`** 实现纹理画笔---改用 `BrushPaint.TilingTexture` 或 `BrushPaint.StampingTexture` 配合 `TextureBitmapStore`。
- **绝不要在最末（或唯一）的 `TextureLayer` 上使用 `BlendMode.SRC_OVER`** ---改用 `BlendMode.MODULATE`、`DST_IN`、`DST_OUT`、`SRC_ATOP` 或 `SRC_IN`，以免边缘抗锯齿和 `OPACITY_MULTIPLIER` 行为被覆盖。
- **绝不要把 `BrushFamily` 序列化为 JSON、Gson、Moshi 或 `Parcelable`** ---始终使用 `androidx.ink.storage` 中的 `BrushFamily.encode` 与 `BrushFamily.decode` 或 `AndroidBrushFamilySerialization`。
- **绝不要自己实现 Bézier（`quadTo`、`cubicTo`）平滑** ---输入平滑请配置 `BrushFamily.InputModel.SlidingWindowModel`，行为平滑请配置 `DampingNode`。
- **绝不要在绘制循环里用 `Random.nextFloat`** 制造有机的笔画抖动---改为在 `BrushBehavior` 中挂一个随笔画距离变化的 `NoiseNode`。
