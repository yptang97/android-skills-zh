## 1. 布局坐标、矩形与可见性跟踪

`Modifier.onGloballyPositioned` 会在布局阶段之后、该节点的全局窗口位置可能发生变化时对其触发（例如滚动或动画期间祖先节点移动时的每一帧），因此它是掉帧、多余回调和布局反馈循环的常见来源。请改用有针对性的现代 API：

### 1. 视口与停留时长跟踪：使用 `Modifier.onVisibilityChanged`

不要在 `onGloballyPositioned` 内部手工计算视口交集。
使用 **`Modifier.onVisibilityChanged`**（配合 `minFractionVisible` 和可选的
`minDurationMs` 停留阈值）来实现：

- **曝光日志记录**：确保分析事件只在条目真正进入视口并保持可见满最短时长时才触发（防止对预取的懒加载条目过早记录）。
- **延迟 Lookahead 共享过渡**：只在条目进入视口时才附加 `Modifier.sharedBounds` 或 `Modifier.sharedElement`，从而消除屏幕外条目上的 Lookahead 阶段。


```kotlin
// Optimized: Viewport entry with dwell threshold
Box(
    modifier = Modifier.onVisibilityChanged(
        minFractionVisible = 0.5f,
        minDurationMs = 500L,
    ) { isVisible ->
        if (isVisible) {
            analytics.logImpression(itemId)
        }
    }
)
```

<br />

### 2. 本地位置与限流边界：优先使用 `onPlaced` 或 `onLayoutRectChanged`

- **仅需尺寸（`IntSize`）**：如果你只需要宽度和高度，使用 `Modifier.onSizeChanged`。它只在节点尺寸变化时执行，忽略位置移动。
- **放置后的本地坐标（`Modifier.onPlaced`）**：需要在节点放置后获取相对于父级的放置坐标、又不想订阅祖先带来的窗口或屏幕移动时，使用 `Modifier.onPlaced`。
- **限流边界跟踪（`Modifier.onLayoutRectChanged`）**：需要根、窗口或屏幕相对的边界（`RelativeLayoutBounds`）时，优先使用 `Modifier.onLayoutRectChanged` 而不是 `onGloballyPositioned`；它支持内置的 `throttleMillis` 和 `debounceMillis` 参数，避免每帧触发。

### 3. 按需查询坐标：不要用 `MutableState` 跟踪位置

不要只为在某事件发生（例如显示 tooltip、菜单，或处理手势）时把布局坐标缓存进 `MutableState` 备用，而持续监听坐标回调（`onGloballyPositioned` 或
`onPlaced`）。把坐标存入 state 会导致每次布局或滚动阶段都执行多余回调，并有重组抖动或反向写入的风险。

#### A. 在自定义 Modifier 中（`Modifier.Node`）

`requireLayoutCoordinates()` 是 `Modifier.Node`（具体来说是
`DelegatableNode`）上的 API，专为按需拉取坐标而设计：

- **在事件处理器内部查询**：在自定义 modifier 节点（例如 `PointerInputModifierNode` 或 `DrawModifierNode`）中，在事件发生的时刻直接在手势、触摸或绘制回调内部调用 `requireLayoutCoordinates()`。
- **消除持续监听**：你不需要为了实现 `LayoutAwareModifierNode`，或只为了在交互发生时拿到坐标而持续监听 `onGloballyPositioned`。


```kotlin
// In a custom PointerInputModifierNode:
class InteractiveTooltipNode : Modifier.Node(), PointerInputModifierNode {
    override fun onPointerEvent(
        pointerEvent: PointerEvent,
        pass: PointerEventPass,
        bounds: IntSize,
    ) {
        // Query coordinates on-demand at the exact moment of the interaction
        if (isAttached) {
            val coordinates = requireLayoutCoordinates()
            val bounds = coordinates.boundsInRoot()
            showTooltip(bounds)
        }
    }
}
```

<br />

#### B. 在高阶 composable 代码中（相对于 `Modifier.clickable`）

`requireLayoutCoordinates()` 严格来说是 `Modifier.Node` API——它在高阶
composable 中**不可用**，而 `Modifier.clickable` 也不会把坐标传给它的
`onClick: () -> Unit` lambda：

- **普通点击（`Modifier.clickable`）**：如果你的点击处理器不需要精确的屏幕坐标，就直接用 `Modifier.clickable`，不要附加任何坐标监听器。
- **需要位置感知的手势（`Modifier.pointerInput`）**：如果你在 composable 代码中需要精确的点按位置（例如把下拉菜单锚定在触点处），就用 `Modifier.pointerInput` 配合 `detectTapGestures` 在事件上直接接收点按的 `Offset`，而不是把 `onGloballyPositioned` 的边界存进 `MutableState`：


```kotlin
// Optimized: Captures touch offset on event without onGloballyPositioned
Box(
    modifier = Modifier.pointerInput(Unit) {
        detectTapGestures { offset ->
            showMenuAt(offset)
        }
    }
)
```

<br />

### 4. 禁止布局反馈循环（在 Layout 期间反向写入）

绝不要在 `onPlaced`、`onSizeChanged` 或 `onGloballyPositioned` 内部写入
`MutableState`——如果读取该 state 会使正在测量的节点的布局、尺寸或放置失效，就会出问题。

在 Layout 阶段写入、并在 Composition 阶段读取的 state 会形成**反向写入**，进而触发**首帧正确性问题**：第一帧以无效、默认或未稳定的尺寸（例如零尺寸或错误的偏移）渲染，随后第二帧重组，造成可见的视觉跳变、布局闪烁和掉帧。如果布局尺寸持续把新值写回 state，就会导致无限重组循环。

同样，在 Layout 阶段内部，state 变更也必须单向向前流动：在测量期间更新 state、在放置期间读取是可以接受的，但在放置期间写入、又在测量期间读取的 state 会造成持续重新测量的循环。

如果自定义绘制或放置需要尺寸或坐标，请在 Draw 或 Layout 阶段直接用
`Modifier.drawWithCache` 或
`Modifier.layout` 读取，而不是把它们传回 Composition。关于阶段流转与消除重组循环的更多信息，参见
[Backwards Write 文档](https://developer.android.com/develop/ui/compose/performance/backwards-write)。

## 2. 布局偏移与约束的阶段延迟

通过把读取包进基于 lambda 的布局 modifier，把对动画或滚动驱动的 state 值的读取延迟到 **Layout** 阶段。这样在 state 变化时就能完全跳过 Composition 阶段：

- **坏做法（每次偏移变化都重组）**：


  ```kotlin
  val offset = scrollState.value
  Box(modifier = Modifier.offset(x = offset.dp, y = 0.dp))
  ```

  <br />

- **优化做法（跳过 Composition，在 Layout 阶段求值）**：


  ```kotlin
  Box(modifier = Modifier.offset { IntOffset(scrollState.value, 0) })
  ```

  <br />

## 3. 尽量减少布局树深度和包装节点

Compose 中的每个布局节点都有测量、放置和快照跟踪开销。尽量减少布局层级深度：

- **避免装饰性包装布局**：不要只为应用背景、边框、内边距或可点击 modifier 就把 composable 包进一个额外的 `Box`。把 modifier 直接附加到子 composable 上。
- **避免为装饰性背景使用 Canvas 节点**：不要只为在内容后面添加装饰性绘制而使用 `Canvas` composable。在已有的布局节点上使用 `Modifier.drawBehind` 或 `Modifier.drawWithCache`，以免给布局树增加额外节点。

## 4. 子组合开销（`SubcomposeLayout` 与 `BoxWithConstraints`）

`SubcomposeLayout`（以及构建在其之上的 composable，例如
`BoxWithConstraints`）会把组合推迟到测量阶段，把 Compose 标准的单趟布局流水线拆成多个子组合
阶段：

- **不要为简单的响应式适配使用 `BoxWithConstraints`**：当标准 modifier（`Modifier.fillMaxWidth()`、`Modifier.weight()` 或 `Modifier.aspectRatio()`）或流式布局能实现相同的视觉布局时，不要使用 `BoxWithConstraints`。
- **不要在 Lazy 条目内使用 `BoxWithConstraints`**：在 `LazyColumn` 或 `LazyRow` 的条目内使用 `BoxWithConstraints` 会给每个被回收和预取的条目引入子组合开销，加剧滚动卡顿。
- **优先使用 `Modifier.layout` 或 `LayoutModifierNode`**：当自定义测量或放置规则依赖于传入的约束时，优先使用 `Modifier.layout { measurable, constraints -> ... }` 或实现 `LayoutModifierNode`，而不是新建一个 `SubcomposeLayout` 或 `BoxWithConstraints`。

## 5. 固有测量

固有测量（`IntrinsicSize.Min`、`IntrinsicSize.Max`）会在最终测量阶段之前向子节点查询其首选尺寸，实际上相当于跑了两趟布局：

- 审慎使用固有测量，只在兄弟节点必须尺寸匹配时使用（例如一个 `Divider` 要与相邻文本的高度一致）。
- 避免在深层级中链式嵌套固有测量。
