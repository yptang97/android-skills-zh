## 1. 自定义绘制（`Canvas` 与 `drawWithCache`）

- **避免嵌套 Canvas 节点** ：不要仅仅为了给已有布局添加装饰性绘制而使用 `Canvas` composable。应在已有 Composable 上使用 `Modifier.drawBehind` 或 `Modifier.drawWithCache`，避免在布局树中多创建一个节点。
- **用 `drawWithCache` 缓存分配** ：如果你的绘制逻辑会分配依赖绘制区域尺寸的对象（例如 `Path`、`Brush`、`Shader` 或 `Paint`），使用 **`Modifier.drawWithCache`** 缓存已分配的对象，避免 Draw 阶段的 GC 压力。

### A. 缓存 `Path` 分配

- **错误写法（每个绘制帧或动画 tick 都分配新的 Path）**：


  ```kotlin
  Box(
      modifier = Modifier
          .fillMaxSize()
          .drawBehind {
              val path = Path().apply {
                  moveTo(0f, 0f)
                  lineTo(size.width, size.height)
              }
              drawPath(path, Color.Red)
          }
  )
  ```

  <br />

- **优化写法（缓存 Path，仅在 Box 尺寸变化时重建）**：


  ```kotlin
  Box(
      modifier = Modifier
          .fillMaxSize()
          .drawWithCache {
              val path = Path().apply {
                  moveTo(0f, 0f)
                  lineTo(size.width, size.height)
              }
              onDrawBehind {
                  drawPath(path, Color.Red)
              }
          }
  )
  ```

  <br />

## 2. 在 `drawWithCache` 内限定快速变化的 uniform

- **`RuntimeShader` 用 remember** ：务必在 `drawWithCache` 之外 `remember` `RuntimeShader`（或在顶层/进程作用域中懒初始化一次）。虽然编译后的 shader 由运行时内部缓存，但解析 AGSL shader 源字符串会产生显著的解析开销，绝不应在 `drawWithCache` 的尺寸变化轮次中重复执行。
- **`ShaderBrush` 用 remember** ：`ShaderBrush` 是持有 shader 引用的轻量包装。以 shader 为 key 记住它：`remember(shader) { ShaderBrush(shader) }`。
- **在 `drawWithCache` 初始化块中更新依赖布局和尺寸的 uniform**（例如使用 `size.width, size.height` 的视口尺寸或分辨率），因为尺寸只在布局阶段变化。
- **把动态的逐帧 uniform 更新**（例如用 `shader.setFloatUniform(...)` 更新时间）移到 `onDrawBehind` 或 `onDrawWithContent` 块中，且不重新分配 shader 或 brush：


```kotlin
// RuntimeShader parsed once and cached in Composable scope
val shader = remember { RuntimeShader(SHADER_SRC) }
val brush = remember(shader) { ShaderBrush(shader) }

Box(
    modifier = modifier
        .fillMaxSize()
        .drawWithCache {
            // Layout/size-dependent uniforms updated in cache block (on resize)
            shader.setFloatUniform("u_resolution", size.width, size.height)

            onDrawBehind {
                // Per-frame uniforms updated in draw block without reallocating
                shader.setFloatUniform("u_time", timeState.value)
                drawRect(brush)
            }
        }
)
```

<br />

## 3. 图形 `Path` 性能与对象复用

- **在热绘制循环中优先用 `Path.rewind()` 而非 `Path.reset()`** ：
  - **`rewind()`** ：清除线条和曲线，但**保留内存中的内部缓冲区和已分配容量**。当每帧以稳定复杂度重建 path 时（例如波形监视器或自定义图表），使用 `rewind()` 以避免缓冲区重新分配。
  - **`reset()`** ：清除 path 并**释放内部缓冲区** 。仅当 path 短期内不会复用，或其复杂度急剧下降时才使用 `reset()`。

## 4. 值类、原始类型集合与打包

避免在循环、动画回调、measure 块或 draw 方法中分配短生命周期对象（例如 `Pair<Int, Int>`、`Pair<Float,
Float>`、`Point`、坐标对或尺寸）。

- **避免泛型元组（`Pair`、`Triple`）** ：在热循环中分配 `Pair(row, col)` 或 `Pair(x, y)` 会产生持续的堆分配和 GC 压力（例如 `HashSet<Pair<Int, Int>>` 会分配 `Pair` 对象、装箱两个原始 `Int`，并创建一条 `HashMap.Node` 记录 --- 每个元素合计 3 次以上堆分配）。
- **标准泛型集合会装箱原始类型** ：`HashSet<Long>` 或 `HashSet<Int>` 会把每个原始值装箱为 `java.lang.Long`/`java.lang.Integer` 并分配 `HashMap.Node`。要实现真正的零分配集合，请使用 `androidx.collection:collection` 中的 **`androidx.collection.MutableLongSet`** 或 **`MutableIntSet`**。
- **避免循环中的迭代器分配** ：当 `items` 是标准 `List` 时，`for (item in items)` 会分配一个 `Iterator` 对象。改用索引循环（`for
  (i in items.indices)`）或 `androidx.compose.ui.util` 中的 `items.fastForEach { ... }`。
- **值类装箱陷阱** ：Kotlin 的 `@JvmInline value class` 和原始类型在被用作泛型类型参数（例如 `Set<Point>`）、声明为可空（`Point?`）、或转换为 `Any`/接口类型时会装箱为堆对象。
- **使用 Compose 内置打包工具** ：优先使用 `androidx.compose.ui.util` 中的内置原始类型打包函数（`packInts`、`unpackInt1`、`unpackInt2`、`packFloats`、`unpackFloat1`、`unpackFloat2`）或 Compose 值类（`IntOffset`、`Offset`、`IntSize`、`Size`），而不是自己写位运算。

### A. 用 `MutableLongSet` 做原始类型打包（网格或布局计算）

- **错误写法（每个元素分配 Pair、装箱的 Int、迭代器和
  HashMap.Node）**：


  ```kotlin
  val occupied = HashSet<Pair<Int, Int>>()
  for (item in items) {
      occupied.add(Pair(item.row, item.col))
  }
  ```

  <br />

- **优化写法（使用 MutableLongSet、packInts 和
  fastForEach 实现 0 堆分配）**：


  ```kotlin
  // import androidx.collection.MutableLongSet
  // import androidx.compose.ui.util.fastForEach
  // import androidx.compose.ui.util.packInts

  val occupied = MutableLongSet()
  items.fastForEach { item ->
      occupied.add(packInts(item.row, item.col))
  }
  ```

  <br />

### B. 用于坐标的值类

- **错误写法（每次迭代都创建堆上的 Point 对象）**：


  ```kotlin
  class Point(val x: Float, val y: Float)
  var acc = Point(0f, 0f)
  for (i in 0 until 1000) {
      acc = Point(acc.x + i, acc.y - i)
  }
  ```

  <br />

- **优化写法（0 堆分配，把 2 个 float 打包进一个 Long 原始类型
  值类）**：


  ```kotlin
  // import androidx.compose.ui.util.packFloats
  // import androidx.compose.ui.util.unpackFloat1
  // import androidx.compose.ui.util.unpackFloat2

  @JvmInline
  value class Point private constructor(val packedValue: Long) {
      constructor(x: Float, y: Float) : this(packFloats(x, y))

      val x: Float get() = unpackFloat1(packedValue)
      val y: Float get() = unpackFloat2(packedValue)
  }

  var acc = Point(0f, 0f)
  for (i in 0 until 1000) {
      acc = Point(acc.x + i, acc.y - i)
  }
  // Alternatively, use Compose's built-in Offset class, which implements
  // this exact @JvmInline Long packing pattern under the hood.
  ```

  <br />

## 5. 图片加载与解码（`AsyncImage` 与 `painterResource`）

避免用 `Image(painter = painterResource(resId))` 渲染位图照片或大型位图资源---尤其是在滚动列表（`LazyColumn`、`LazyRow`、`LazyGrid`）中。`painterResource` 严格只用于矢量 drawable（`xml`）和小型 UI 图标。

- **主线程同步解码** ：`painterResource` 在组合期间于主线程同步解码位图（`Compose:recompose` -\> `ImageDecoder`），包括在 lazy 列表预取期间（`lazy:prefetch:compose`）。即便 APK 中一个很小的压缩 JPEG（例如 159 KB）也可能解压成 `2760x1840` 的大位图，阻塞主线程并导致掉帧。
- **不按目标尺寸降采样** ：`painterResource` 不感知布局尺寸（例如 `Modifier.size(160.dp)`），会以完整的原始分辨率解码图片。
- **优先使用 Coil 的 `AsyncImage` 这类异步图片加载（来自
  `io.coil-kt.coil3:coil-compose`，或 Asynchronous Downsampling）** ：
  - **卸载解码** ：`AsyncImage` 在后台线程异步解码图片，让主线程在滚动和预取期间保持空闲。
  - **自动降采样（`ImageDecoder.setTargetSize`）** ：`AsyncImage` 会测量目标布局边界，并自动配置 `ImageDecoder.setTargetSize()`，从而只解码实际显示的像素并上传到 GPU。
  - **提供尺寸合适的资源**：如果要在 APK 中打包静态缩略图，应提供与显示档位匹配的预缩放缩略图资源，而不是全分辨率相机照片。

### A. 在固定尺寸容器中加载位图资源或照片

- **错误写法（在主线程同步解码完整的 `2760x1840` 位图，并把整张
  纹理上传到 GPU 用于一个 `160.dp` 的盒子）**：


  ```kotlin
  Image(
      painter = painterResource(id = R.drawable.donut),
      contentScale = ContentScale.Fit,
      modifier = Modifier.size(160.dp),
      contentDescription = stringResource(id = R.string.attached_image),
  )
  ```

  <br />

- **优化写法（在主线程之外解码，通过 `ImageDecoder.setTargetSize` 自动降采样到
  `160.dp` 的目标尺寸，并缓存结果）**：


  ```kotlin
  // import coil3.compose.AsyncImage

  AsyncImage(
      model = R.drawable.donut,
      contentScale = ContentScale.Fit,
      modifier = Modifier.size(160.dp),
      contentDescription = stringResource(id = R.string.attached_image),
  )
  ```

  <br />
