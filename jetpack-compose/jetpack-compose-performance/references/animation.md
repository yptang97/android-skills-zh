## 1. 为动画做相位延迟（跳过 Composition 到 Draw 和 Layout）

为视觉属性（例如 alpha、scale、rotation、color 或 translation）做动画时，绝不要在 Composition 阶段
在 Composable 主体里直接读取动画状态。在组合期间读取状态会让读取所在的 recompose scope
（以及任何不可跳过的子项）在每一次动画 tick 上重组（每秒 60 到 120 次）。

把对动画状态的读取包进 lambda，让求值推迟到 **Draw** 或
**Layout** 阶段。

### A. Alpha、旋转和缩放：用 `graphicsLayer` 推迟到 Draw

- **坏做法（每一动画帧都重组）**：


  ```kotlin
  val alpha by animateFloatAsState(targetValue = targetAlpha, label = "Alpha")
  // Reading alpha here registers a composition dependency on every frame
  Box(modifier = Modifier.alpha(alpha))
  ```

  <br />

- **优化做法（绕过 Composition 和 Layout，在 Draw 阶段求值）**：


  ```kotlin
  val alpha by animateFloatAsState(targetValue = targetAlpha, label = "Alpha")
  // graphicsLayer with lambda skips composition and runs in the draw phase
  Box(
      modifier = Modifier.graphicsLayer {
          this.alpha = alpha
      }
  )
  ```

  <br />

### B. 动画偏移：用 `Modifier.offset` 推迟到 Layout

- **坏做法（每移动一个像素就重组）**：


  ```kotlin
  val animatedOffset by animateDpAsState(
      targetValue = targetOffset,
      label = "Offset",
  )
  Box(modifier = Modifier.offset(x = animatedOffset, y = 0.dp))
  ```

  <br />

- **优化做法（跳过 Composition，直接进入 Layout 阶段）**：


  ```kotlin
  val animatedOffset by animateIntAsState(
      targetValue = targetOffsetPx,
      label = "Offset",
  )
  Box(
      modifier = Modifier.offset {
          IntOffset(x = animatedOffset, y = 0)
      }
  )
  ```

  <br />

### C. 动画尺寸：用 `Modifier.layout` 或 `animateBounds` 推迟到 Layout

在 Composable 主体里直接用 `animateDpAsState` 和 `Modifier.size(...)` 为容器尺寸做动画，会让该
composable 及其子项在每一次动画 tick 上重组。

改用布局阶段的约束动画或 Lookahead 边界动画：

- **坏做法（每一动画帧都重组整个子树）**：


  ```kotlin
  val animatedSize by animateDpAsState(
      targetValue = targetSize,
      label = "Size",
  )
  Box(modifier = Modifier.size(animatedSize))
  ```

  <br />

- **优化做法（用 `Modifier.layout` 做相位延迟）**：在布局过程中为约束做动画，
  不重新触发组合：


  ```kotlin
  val animatedWidth by animateIntAsState(
      targetValue = targetWidthPx,
      label = "Width",
  )
  Box(
      modifier = Modifier.layout { measurable, constraints ->
          val placeable = measurable.measure(
              constraints.copy(
                  minWidth = animatedWidth,
                  maxWidth = animatedWidth
              )
          )
          layout(placeable.width, placeable.height) {
              placeable.placeRelative(0, 0)
          }
      }
  )
  ```

  <br />

- **优化做法（`animateBounds` 搭配 Lookahead Scope）**：在
  `LookaheadScope` 里用 `animateBounds` 平滑地为尺寸变化做动画：


  ```kotlin
  with(lookaheadScope) {
      Box(modifier = Modifier.animateBounds(this, Modifier.size(finalSize)))
  }
  ```

  <br />

### D. 自定义 composable 参数（lambda 提供者）

创建在内部为属性做动画的自定义 composable 时，要传 lambda 提供者
（`alphaProvider: () -> Float` 或 `offsetProvider: () ->
IntOffset`），而不是原始动画值。这样调用方就不必在 Composition 里读取状态，子项也能把读取推迟到
`graphicsLayer` 或 `offset`。

- **坏做法（调用方必须在 Composition 里读取状态才能传 Float）**：


  ```kotlin
  @Composable
  fun AnimatedCard(alpha: Float) {
      Box(modifier = Modifier.graphicsLayer { this.alpha = alpha })
  }
  ```

  <br />

- **优化做法（调用方传 lambda；读取推迟到子项的 Draw
  阶段）**：


  ```kotlin
  @Composable
  fun AnimatedCard(alphaProvider: () -> Float) {
      Box(modifier = Modifier.graphicsLayer { this.alpha = alphaProvider() })
  }
  ```

  <br />

## 2. 共享转场与共享元素（`SharedTransitionScope`）

`SharedTransitionScope` 让边界与元素转场能够跨布局和跨导航目的地协同进行。

### 1. 在快速滚动的列表里推迟 `sharedBounds` 和 `sharedElement`

**建议：** 对于很长或快速滚动的列表（`LazyColumn`、`LazyRow`、
`LazyVerticalGrid`、`HorizontalPager`），考虑只在列表项通过
`Modifier.onVisibilityChanged` 进入可见视口时才挂上
`Modifier.sharedBounds` 或 `Modifier.sharedElement`。

虽然空间坐标跟踪只在找到匹配项时才启用，但无条件挂上共享转场 modifier 会给**快速拖拽滚动期间可能
永远不会出现在屏幕上的预取项**带来 modifier 实例化和状态观察的开销。推迟到可见时再挂上，
可以避免屏幕外项承担这部分实例化开销。
> **注意：**
> 这条建议适用于当前版本的 Compose。上游平台正在积极开发性能优化，让 `Modifier.sharedBounds` 和
> `Modifier.sharedElement` 更轻量，并避免预取开销。

- **改前（实例化会在所有预取项上执行，即使从未显示）**：


  ```kotlin
  @Composable
  fun FeedItemRow(
      item: FeedItem,
      sharedTransitionScope: SharedTransitionScope,
      animatedVisibilityScope: AnimatedVisibilityScope,
  ) {
      with(sharedTransitionScope) {
          ItemContent(
              modifier = Modifier
                  .fillMaxWidth()
                  .sharedBounds(
                      rememberSharedContentState(key = item.id),
                      animatedVisibilityScope = animatedVisibilityScope,
                  )
          )
      }
  }
  ```

  <br />

- **优化后（共享转场 modifier 推迟到列表项进入
  视口）**：


  ```kotlin
  @Composable
  fun FeedItemRow(
      item: FeedItem,
      sharedTransitionScope: SharedTransitionScope,
      animatedVisibilityScope: AnimatedVisibilityScope,
  ) {
      var isVisibleInWindow by remember { mutableStateOf(false) }

      with(sharedTransitionScope) {
          val sharedBoundsModifier = if (isVisibleInWindow) {
              Modifier.sharedBounds(
                  rememberSharedContentState(key = item.id),
                  animatedVisibilityScope = animatedVisibilityScope,
              )
          } else {
              Modifier
          }

          ItemContent(
              modifier = Modifier
                  .fillMaxWidth()
                  .onVisibilityChanged(
                      minFractionVisible = 0.001f,
                  ) { visible ->
                      isVisibleInWindow = visible
                  }
                  .then(sharedBoundsModifier)
          )
      }
  }
  ```

  <br />

## 3. 在自定义 modifier 里持久化 `Animatable`（`Modifier.Node`）

构建自定义动画 modifier 时，不要用 `composed { ... }` 搭配
`remember { Animatable(...) }` 和 `LaunchedEffect`。

把 `Animatable` 直接作为 `Modifier.Node` 的成员属性保存，并在 `onAttach()` 里用节点自带的
`coroutineScope` 启动动画：


```kotlin
private class FadeRevealNode(
    var targetAlpha: Float,
    var durationMillis: Int
) : Modifier.Node(), DrawModifierNode {
    // Persistent node property (avoids remember overhead)
    private val alpha = Animatable(0f)

    override fun onAttach() {
        // Launches animation tied directly to node lifecycle
        coroutineScope.launch {
            alpha.animateTo(targetAlpha, tween(durationMillis))
        }
    }

    override fun ContentDrawScope.draw() {
        drawContext.canvas.saveLayer(
            bounds = size.toRect(),
            paint = Paint().apply {
                this.alpha = this@FadeRevealNode.alpha.value
            }
        )
        drawContent()
        drawContext.canvas.restore()
    }
}
```

<br />
