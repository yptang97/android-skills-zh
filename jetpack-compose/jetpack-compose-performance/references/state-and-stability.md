## 1. 阶段延后与 lambda（Composition 与 Layout 与 Draw）

把动画、频繁变化或滚动驱动的状态读取包进 lambda，使其延后到 Layout 或 Draw 阶段。这样完全绕过昂贵的 Composition 阶段，避免不必要的重组。

### A. Modifier 偏移

- **错误写法（每个像素变化都重组）**：


  ```kotlin
  val offset = scrollState.value
  Box(modifier = Modifier.offset(x = offset.dp, y = 0.dp))
  ```

  <br />

- **优化写法（跳过 Composition，直接进入 Layout）**：


  ```kotlin
  Box(modifier = Modifier.offset { IntOffset(scrollState.value, 0) })
  ```

  <br />

### B. alpha 与旋转动画

- **错误写法（每个动画帧都重组）**：


  ```kotlin
  val alpha by animateFloatAsState(targetValue)
  Box(modifier = Modifier.alpha(alpha))
  ```

  <br />

- **优化写法（跳过 Composition 和 Layout，直接进入 Draw）**：


  ```kotlin
  val alpha by animateFloatAsState(targetValue)
  Box(modifier = Modifier.graphicsLayer { this.alpha = alpha })
  ```

  <br />

### C. 自定义 composable 参数

传入 lambda 提供者（`valueProvider: () -> Float`）只有在值于 Layout 或 Draw 阶段被读取时才有收益。如果在 Composition 阶段读取，就直接传原始值，避免 lambda 分配开销。

- **在 Composition 阶段读取（直接传值）**：


  ```kotlin
  @Composable
  fun TitleText(text: String) {
      Text(text = text)
  }
  ```

  <br />

- **在 Layout 或 Draw 阶段读取（传 lambda 提供者）**：


  ```kotlin
  @Composable
  fun FadingBox(alphaProvider: () -> Float) {
      Box(Modifier.graphicsLayer { alpha = alphaProvider() })
  }
  ```

  <br />

## 2. 防止跨帧阶段的反向写入

**反向写入**指的是：Compose `State` 在比它被读取更晚的帧阶段（或在同一组合轮次中更下游的 composable 作用域）被修改。

Compose 按三个严格正向流动的阶段执行帧：**Composition \> Layout \> Drawing**。在更晚的阶段（或在读取之后）修改状态，会迫使 Compose 调度更早的阶段重新运行，形成未优化的重组循环。

### 后果

- **额外帧与掉帧**：在连续帧之间强制多余的组合轮次，浪费 CPU/GPU 资源并掉帧。
- **首帧正确性问题**：最初的帧会用无效、默认或未稳定的数据（例如零尺寸或错误偏移）渲染，导致第二帧渲染时出现可见的布局跳变或闪烁。
- **无限重组循环**：当布局尺寸计算或绘制逻辑持续回写到驱动组合的状态时发生。

### 核心规则

1. **检查先读后写的顺序** ：反向写入**严格要求对该状态的读取发生在状态写入之前**（同一组合轮次中的 `Read -> Write`，或跨帧阶段的 `Composition Read -> Layout or Draw Write`）。状态写入应放在事件回调（`onClick`）、协程（`LaunchedEffect`）或副作用（`SideEffect`）中；布局回调（`onSizeChanged`、`onPlaced`）不算事件。
2. **不要把 `Write -> Read` 与反向写入混淆** ：在 composable 开头、对该状态的任何读取发生**之前**给 `MutableState` 赋值（或在 Composition 阶段写入、稍后在 `Canvas` Draw 阶段读取）**不是**反向写入，因为在写入之前没有任何读观察者记录下当前组合作用域（并且 `Composition Write ->
   Draw Read` 是正向流动的）。应把 `var x by remember {
   mutableStateOf(...) }; x = getValue()` 归类为**冗余状态包装**（不必要的 `MutableState` 与 slot table 分配，而且如果之后有人在写入前加了读取，它就变得脆弱），并用普通的 `val` 替换，或在目标阶段直接读取。
3. **如果在 Composition 阶段读取，绝不要在 `onSizeChanged`、`onPlaced` 或 `LayoutModifier`
   中写入状态** ：在 Draw 或 Layout 阶段直接读取尺寸（`Modifier.drawWithCache`、`Modifier.layout`），把窗口级尺寸提升（`WindowWidthSizeClass`），或使用 `FlowRow`/`LazyVerticalGrid`。
4. **绝不要在 Composition 阶段读取状态之后再修改它** ：当你需要在组合中捕获变化的值而不触发重组时，使用 `rememberUpdatedState`。
5. **把状态读取延后到尽可能晚的阶段**：在 Layout 或 Draw 阶段读取状态，可在状态变化时完全跳过 Composition。

### 常见模式：反向写入与事件驱动更新

#### A. Composition 中的直接修改（`Read -> Write` 与 `Write -> Read`）

- **错误写法（`Read -> Write`：读取之后修改状态会立即触发
  重组循环）**：


  ```kotlin
  @Composable
  fun BadCounter() {
      var count by remember { mutableIntStateOf(0) }
      Text("Count: $count") // 1. State read in Composition
      Button(onClick = {}) {
          // 2. State write in Composition AFTER read (Backwards write!)
          count++
      }
  }
  ```

  <br />

- **不是反向写入，但属于冗余/脆弱（Composition 中的 `Write -> Read`）**：


  ```kotlin
  // NOT a backwards write because the write happens BEFORE any read in
  // Composition (and before Canvas reads it in the Draw phase).
  // However, wrapping a synchronous value in mutableStateOf is redundant
  // and error-prone if a read is later added before the write.
  @Composable
  fun RedundantStateWrapper(viewModel: MyViewModel) {
      var path by remember { mutableStateOf(Path()) }
      // 1. Write occurs first (no prior read in scope)
      path = viewModel.getPath()
      Canvas(Modifier.fillMaxSize()) {
          // 2. Read occurs later in Draw phase (Forward flow)
          drawPath(path, Color.Red)
      }
  }

  // Optimized: Remove redundant mutableStateOf wrapper and read in Draw
  @Composable
  fun OptimizedWrapper(viewModel: MyViewModel) {
      Canvas(Modifier.fillMaxSize()) {
          val path = viewModel.getPath()
          drawPath(path, Color.Red)
      }
  }
  ```

  <br />

#### B. 在 Composition 阶段读取、在 Layout 阶段写入（跨阶段反向写入）

- **错误写法（Layout 写入被 Composition 读取的状态，导致首帧
  跳变）**：


  ```kotlin
  @Composable
  fun BadLayout() {
      var componentHeight by remember { mutableStateOf(0.dp) }

      // Composition reads state before Layout measures it
      if (componentHeight > 100.dp) {
          Banner()
      }

      Box(
          modifier = Modifier.onSizeChanged { size ->
              // Backwards write: Layout -> Composition
              componentHeight = size.height.dp
          }
      )
  }
  ```

  <br />

- **优化写法（把尺寸计算延后到 Layout 阶段，或提升到 Window 层）**：


  ```kotlin
  @Composable
  fun OptimizedLayout(modifier: Modifier = Modifier) {
      // Measurement and placement handled in Layout without recomposition
      Box(
          modifier = modifier.layout { measurable, constraints ->
              val placeable = measurable.measure(constraints)
              layout(placeable.width, placeable.height) {
                  placeable.placeRelative(0, 0)
              }
          }
      )
  }
  ```

  <br />

更多信息见[反向写入文档](https://developer.android.com/develop/ui/compose/performance/backwards-write)。

## 3. 状态与快照优化

### A. 用 `neverEqualPolicy()` 优化整表更新

`mutableStateListOf` 通过快照系统跟踪每个单独元素的变更。当不需要细粒度的元素跟踪时，用标准 `MutableList` 承载你的集合，把它包在 `mutableStateOf(list,
neverEqualPolicy())` 中，并用有实际意义的赋值（`state.value = list`）触发重组。


```kotlin
class ActiveQueueManager {
    private val list = mutableListOf<Item>()
    val items = mutableStateOf(list, neverEqualPolicy())

    fun enqueue(item: Item) {
        list.add(item)
        items.value = list // Load-bearing assignment triggers recomposition
    }
}
```

<br />

### B. 对重复查询和迭代使用 `SnapshotStateList.toList()`

在 composable 内反复迭代或查询 `SnapshotStateList`（或 `SnapshotStateMap`），会在每个被访问的索引或元素上注册快照读取观察。

当要对快照集合做重复查询（例如在循环中检查 `.contains()`）、过滤、排序或多步处理时，在作用域开头先用 `.toList()`（或 `.toSet()` / `.toMap()`）取一份原子快照，然后在这份只读快照上操作：

- **错误写法（循环内重复的 contains 查询会对每个元素注册细粒度
  依赖）**：


  ```kotlin
  @Composable
  fun ItemSelector(
      items: List<Item>,
      selectedIds: SnapshotStateList<String>,
  ) {
      Column {
          items.forEach { item ->
              // Avoid: Repeatedly querying the snapshot list inside the loop
              val isSelected = selectedIds.contains(item.id)
              ItemRow(item = item, isSelected = isSelected)
          }
      }
  }
  ```

  <br />

- **优化写法（取一次只读快照 Set，实现 `O(1)` 查询）**：


  ```kotlin
  @Composable
  fun ItemSelector(
      items: List<Item>,
      selectedIds: SnapshotStateList<String>,
  ) {
      // Convert to a local Set once per recomposition for fast O(1) lookups
      val selectedSet = selectedIds.toSet()
      Column {
          items.forEach { item ->
              val isSelected = selectedSet.contains(item.id)
              ItemRow(item = item, isSelected = isSelected)
          }
      }
  }
  ```

  <br />

### C. 把重复的状态读取提取到局部变量

在函数中多次读取 Compose `State` 属性（例如 `transition.currentState`、`scrollState.value` 或 `state.value`）会注册冗余的快照查找。把状态读取缓存到块顶部的局部变量中。

- **错误写法（重复的快照状态读取）**：


  ```kotlin
  val label = when (transition.currentState) {
      State.Idle -> "Idle"
      State.Running -> "Running: ${transition.currentState}"
      State.Finished -> "Finished: ${transition.currentState}"
  }
  ```

  <br />

- **优化写法（只读取一次并缓存到局部变量）**：


  ```kotlin
  val currentState = transition.currentState
  val label = when (currentState) {
      State.Idle -> "Idle"
      State.Running -> "Running: $currentState"
      State.Finished -> "Finished: $currentState"
  }
  ```

  <br />

### D. `computedStateOf` 与 `derivedStateOf`（Compose 1.13+）

当从频繁变化的输入派生状态时（例如每个滚动 tick 都检查 `scrollState.value > 0`），在组合中直接读取原始状态会让 composable 每帧失效。

在 Compose 1.13+ 中，与 **`derivedStateOf`** 一同引入了 **`computedStateOf`**：

- **`computedStateOf`** ：在**每次读取**时执行计算，不缓存值。
  - **首次读取** ：略快于 `derivedStateOf`，因为它避免了缓存初始化和快照依赖记账。
  - **第二次读取** ：略慢于 `derivedStateOf`，因为它要重新执行计算。
  - **写后读（失效）** ：明显快于 `derivedStateOf`，因为它没有昂贵的缓存失效路径、缓存回写和快照 apply 监听器派发。
- **`derivedStateOf`** ：缓存计算结果，只要依赖状态未变就返回缓存值。
  - 当依赖状态频繁变化时，由于缓存清除、重新计算、缓存回写，以及推进快照或触发 apply 监听器，其失效路径更慢。

#### 何时用哪个

1. **对于由快速变化状态（例如滚动偏移或滑块位置）驱动的简单条件判断、布尔标志或轻量派生，优先用 `computedStateOf`（Compose 1.13+）或 `remember { derivedStateOf {
   ... } }`（Compose \< 1.13）**。在使用
   `computedStateOf` 之前，检查 `gradle/libs.versions.toml` 或
   `build.gradle(.kts)` 确认项目的 Compose 版本：


   ```kotlin
   @Composable
   fun ScrollToTopButton(scrollState: ScrollState) {
       // Compose 1.13+: Invalidates composition only when > 0 changes,
       // with minimal invalidation overhead compared to derivedStateOf.
       // On Compose < 1.13, use remember { derivedStateOf { ... } }.
       val showButton by remember { computedStateOf { scrollState.value > 0 } }

       if (showButton) {
           FloatingActionButton(onClick = { /* ... */ }) {
               Icon(Icons.Default.ArrowUpward, "Scroll to Top")
           }
       }
   }
   ```

   <br />

2. **当计算本身在计算上很重，且在同一次组合轮次中被读取多次时，使用 `derivedStateOf`**，这样多次读取缓存带来的收益才能超过失效成本。

   - *简单计算的读取频率细节* ：对于简单计算，如果每次组合中被读取得足够频繁，`derivedStateOf` 也可能优于 `computedStateOf`。具体来说，当每次组合中被读取约 `10 / numberOfStatesReadPerCalculation` 次时（假设计算在读取之间从不失效），`derivedStateOf` 开始能弥补失效成本。
3. **对于简单的属性查找或布尔取反，且不需要失效抑制时，优先用普通 Kotlin getter（`get()`）**：


   ```kotlin
   var isLocked by mutableStateOf(false)
   val isReady: Boolean get() = !isLocked
   ```

   <br />

4. **同步派生要避免 `produceState` + `snapshotFlow`**：
   相比 `computedStateOf` 或 `derivedStateOf`，把 `snapshotFlow` 包进 `produceState` 会增加不必要的协程分配、上下文切换和 flow 派发开销。

   - **错误写法（不必要的协程与 flow 派发）**：


     ```kotlin
     val isScrolledToTop by produceState(initialValue = true, scrollState) {
         snapshotFlow { scrollState.firstVisibleItemIndex == 0 }
             .collect { value = it }
     }
     ```

     <br />

   - **优化写法（同步快照派生）**：


     ```kotlin
     // Compose 1.13+:
     val isScrolledToTop by remember {
         computedStateOf { scrollState.firstVisibleItemIndex == 0 }
     }
     // Compose < 1.13:
     val isScrolledToTop by remember {
         derivedStateOf { scrollState.firstVisibleItemIndex == 0 }
     }
     ```

     <br />

## 4. 强跳过模式与稳定性

不要为了强行让每个 composable 都跳过而给一切加 `@Stable` 或 `@Immutable`（或把集合包进 `ImmutableList`）。

**跳过 composable 不是零成本的**。强行制造稳定性实际上可能降低运行时性能，而不是提升。

### A. Compose 在底层如何处理跳过

当一个 composable 变为可跳过时，Compose 编译器会为每个参数生成 slot table 存储和比较逻辑：

    // What you write
    @Composable
    fun ContactCell(contact: Contact) {
        /* Your function body */
    }

    // What the Compose compiler generates (simplified)
    @Composable
    fun ContactCell(
        contact: Contact,
        $composer: Composer?,
        $changed: Int
    ) {
        val $dirty = $changed or $composer.changed(contact)

        if ($dirty) {
            /* Your function body */
        } else {
            $composer.skipToGroupEnd()
        }
    }

传入 composable 的每个参数实际上都会像被 `remember` 过一样存入 slot table。在每次重组轮次中：

1. Compose 从 slot table 读取先前的参数值。
2. 它在旧值与新值之间执行相等性检查。
3. 如果任何检查失败，composable 执行其 body；如果全部检查通过，它调用 `$composer.skipToGroupEnd()`。

这种 slot table 缓存与比较逻辑在每次重组尝试时都会产生内存和 CPU 开销。

### B. 实例相等（`===`）与结构性相等（`.equals()`）

在**强跳过模式**下（现代 Compose 中默认启用）：

- **不稳定参数**使用**实例相等**比较（`===` / `$composer.changedInstance(param)`）。
- **稳定参数**（原始类型、带 `@Stable` / `@Immutable` 注解的类，或所有属性都稳定的类型）使用**结构性相等**比较（`.equals()` / `$composer.changed(param)`）。

#### 为什么 `@Stable`、`@Immutable` 和 `ImmutableList` 可能损害性能

不稳定参数并不会被阻止跳过：如果在多次重组间传入同一个实例（`param === oldParam`），Compose 会通过快速的 `O(1)` 指针检查迅速跳过该 composable。

当你给类加上 `@Stable` 或 `@Immutable`（或把 `kotlin.collections.List` 换成 `ImmutableList`）时，Compose 就从快速的 `===` 指针比较切换到深层的 `.equals()` 结构比较。

- **昂贵的深度比较** ：在复杂模型或大型集合（例如数百个项目）中，每次重组都执行 `equals()` 可能比执行 composable 的 body 昂贵得多。方法跟踪常常显示 `Model.equals` 耗掉了绝大部分帧时间。
- **组合次数不等于基准测试** ：一个虽然跳过、但花 3ms 做深层 `.equals()` 检查的 composable，明显慢于一个用 0.2ms 完成重组的 composable。
- **绝不建议把 `List<T>` 换成 `ImmutableList<T>`** ：绝不要建议在 `@Stable` 或 `@Immutable` 模型上把 `kotlin.collections.List<T>` 属性转换为 `kotlinx.collections.immutable.ImmutableList<T>`（或通过 `stability_config.txt` 使用 Guava `ImmutableList`）。在强跳过模式下，标准 `List<T>` 已通过 `O(1)` 引用相等（`===`）跳过，而 `ImmutableList<T>` 会强制 `O(N)` 的逐元素 `.equals()` 遍历。

#### 范围限定：何时移除既有的 `@Stable` 或 `@Immutable`

在审查或重构既有代码库时，在建议修改现有稳定性注解之前，先套用严格的范围限定：

1. **只建议为 lazy 布局中的大型数据集移除 `@Stable` / `@Immutable`** ：**只有**在**两个**条件都满足时，才强烈建议从数据模型上移除既有的 `@Stable` 或 `@Immutable` 注解：
   - 该模型被用在**lazy 布局**（`LazyColumn`、`LazyRow`、`LazyVerticalGrid`、`LazyHorizontalGrid`、`Pager`、`ScalingLazyColumn`）中作为输入集合容器或项目模型，**且**
   - 它持有**大型数据集或深层嵌套集合树**（例如整屏信息流、数百个项目/标签，或像 `Post` 含 `List<Paragraph>` 和 `List<Markup>` 这样的嵌套列表），此时滚动或重组期间的 `O(N)` 结构相等检查很昂贵。
2. **其他场景保持既有注解不动** ：对于代码库中已有 `@Stable`、`@Immutable` 或 `ImmutableList` 的所有其他用途---例如非 lazy 的屏幕/组件模型、独立 UI 元素，或集合较小/有界（例如一张卡片模型含 2--5 个徽标、缩略图或元数据行）而数据集大小较小或难以静态估算的模型---**保持既有注解不动**。

### C. 参数解包与相等性传播的陷阱（`ImmutableList`）

Compose 编译器包含一项优化：沿 composable 层级向下传播完全相同的对象引用，可让 Compose 复用之前的相等性结果并跳过冗余比较。

当父 `@Composable` 把完全相同的参数引用传给子 `@Composable` 时，Compose 编译器会传播其 dirty 位掩码，让子级可以跳过重新执行 `.equals()`。

然而，当父 `@Composable` 收到一个包含大型 `ImmutableList` 的 `data class`，并把解包后的 `ImmutableList` 传给子 `@Composable` 时，**Compose 会执行两次 `O(N)` 结构相等**：


```kotlin
// Bad: Both HomeScreen (via data class .equals()) and HomeContent evaluate
// O(N) structural equality on the same ImmutableList in a single frame
data class HomeScreenModel(
    val header: String,
    val items: ImmutableList<ItemModel>
)

@Composable
private fun HomeScreen(model: HomeScreenModel) {
    TopAppBar(title = { Text(model.header) })
    // Unwrapping model.items to pass to a child @Composable
    HomeContent(model.items)
}

// Because contentList is an ImmutableList, HomeContent must re-evaluate O(N)
// .equals() on the list itself, even though HomeScreen already compared model
@Composable
private fun HomeContent(contentList: ImmutableList<ItemModel>) {
    LazyColumn {
        items(contentList) { /* ... */ }
    }
}
```

<br />

在上面的示例中，由于 `items` 是 `data class` 内的 `ImmutableList`（编译器将其视为稳定并用 `.equals()` 比较）：

1. `HomeScreen` 执行 `model.equals(oldModel)`，其中以 `O(N)` 时间遍历 `model.items.equals(oldModel.items)`。
2. `HomeContent` 收到的是 `model.items` 而不是 `model`，因此编译器无法传播 `model` 的 `$dirty` 标志，于是第二次调用 `contentList.equals(oldContentList)`（`O(N)`）。

#### 范围限定：何时参数解包 *不* 是问题

除非**以下所有**条件都满足，否则**不要**标记参数解包：

1. **调用方与被调用方都是可跳过的 `@Composable` 函数** ：普通 Kotlin 函数、构建节点的辅助函数，以及 `LazyListScope` / `LazyGridScope` DSL 扩展（例如 `fun verticalGridUi(itemList =
   content.itemList, ...)`）都不是可跳过 composable，不会在 slot table 中生成 `$composer.changed(...)` 相等性检查。
2. **父对象是带结构性 `.equals()` 的 `@Composable` 参数** ：如果容器对象是在函数体内从状态读取（例如 `val content = model.contentState.value`）而不是作为 `@Composable` 参数传入，或者它是一个没有深层 `data class` `.equals()` 实现的普通 `class`，那么一开始就没有发生父级相等性检查。
3. **被解包的属性本身会触发昂贵的 `O(N)` `.equals()`** ：被解包的属性必须是 `ImmutableList`（或在 `stability_config.txt` 中被标记为稳定的集合）。**绝不**标记对标准 `kotlin.collections.List<T>`（`Set<T>`、`Map<K, V>`）或原始类型/值类型属性（`Int`、`Dp`、`String`、`Boolean`、枚举）的解包---在强跳过模式下，标准 `List<T>` 通过 `O(1)` 引用相等（`===`）比较，因此解包 `content.itemList: List<T>` 没有任何深层比较开销。

### D. 不要过度看重重组次数

重组次数不能替代基准测试。一旦某个屏幕的组合被调度，跳过一个中间 composable 省下的时间微乎其微，却仍要承担记住参数和评估相等性检查的开销。与其试图消除每一次单独的重组，不如专注于**整体避免不必要的组合**——把快速变化的状态读取延后到 Layout 或 Draw 阶段（例如使用 lambda modifier 和 `graphicsLayer`），并
**让 composable 保持轻量**，使其在发生重组时能快速执行。

### E. 设计高性能 composable 的指南

1. **优先使用更少、更易比较的参数** ：在可行时传原始类型（`String`、`Int`、`Long`、`Dp`）或标准 `List<T>` 引用（通过快速的 `===` 比较），而不是大型复合对象。
2. **避免对 `ImmutableList` 做两次 `O(N)` 比较** ：不要把大型集合包进 `data class` 模型里的 `ImmutableList`，否则父、子 `@Composable` 函数都会对列表执行 `O(N)` 的 `.equals()`；应使用标准 `List<T>`，让 Compose 使用 `O(1)` 的 `===` 引用相等。
3. **合并相关 effect 与状态**：尽量减少被 remember 的对象数量和派发的 effect 数量，以降低 slot table 开销。
4. **对 `@Stable` / `@Immutable` 保持克制** ：只给来自非 Compose 模块、实例会被频繁重建且 `.equals()` 是廉价 `O(1)` 的小型扁平 UI 模型添加 `@Stable` 或 `@Immutable`。绝不要给大型集合或深层数据图添加 `@Stable`、`@Immutable` 或 `ImmutableList`。审查既有代码时，只从为 lazy 布局（`LazyColumn`、`LazyRow`、`LazyGrid`）提供大型数据集或深层嵌套集合的模型上移除 `@Stable` 或 `@Immutable`；非 lazy 或集合较小的模型上的既有注解保持不动。
5. **始终做基准测试**：使用 Macrobenchmark 或 Microbenchmark 测量真实的帧耗时和 CPU 影响。绝不要仅凭重组次数判断性能。

- **优化写法（移除大型 lazy 布局模型上的 `@Immutable`，改为依赖快速的
  `===` 实例相等，并传轻量原始值）**：


  ```kotlin
  // Unstable model skips using === pointer check when instance is unchanged
  data class FeedState(
      val feedId: String,
      val items: List<FeedItem>
  )

  @Composable
  fun FeedScreen(state: FeedState) {
      // Pass only the primitive ID needed by the header
      FeedHeader(feedId = state.feedId)
      // Pass the state or items directly
      FeedList(items = state.items)
  }
  ```

  <br />

更多信息见[强跳过模式文档](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping)。

## 5. 使用 `remember` 与计算 key

虽然 `remember` 对于在重组之间保留状态、缓存昂贵操作至关重要，但每次调用都会把结果和 key 存入 slot table，并在每次重组时检查 key 相等性。当必须保留对象身份，或需要缓存不平凡的工作（例如格式化器、shader、path 或列表变换）时使用 `remember`，而不是用它包装简单表达式或廉价分配——后者的 key 比较成本可能高于分配本身。

### 要求给 `remember` 显式提供计算 key

无 key 的 `remember { ... }` 只在初始组合时执行，并在 Composable 的生命周期内缓存结果。如果 Composable 带着新参数值重组，省略 key 就会返回陈旧的缓存值。对于标准 Kotlin 计算和对象实例化，始终把 `remember` 块内引用的每个外部变量或参数作为 key 传入。

- **`derivedStateOf` 的例外** ：包装 `derivedStateOf` 时，**不要**
  把计算 lambda 内读取的快照状态属性作为 `remember` key：


  ```kotlin
  // Bad: passing snapshot state property as a key breaks derivedStateOf
  val showButton by remember(scrollState.firstVisibleItemIndex) {
      derivedStateOf { scrollState.firstVisibleItemIndex > 0 }
  }

  // Optimized: derivedStateOf tracks firstVisibleItemIndex internally
  val showButton by remember {
      derivedStateOf { scrollState.firstVisibleItemIndex > 0 }
  }
  ```

  <br />

  `derivedStateOf` 会在内部动态跟踪快照状态读取，并只在派生结果实际变化时失效。把状态值作为 `remember` key 会迫使 `remember` 块在每一次状态变更时重建，彻底破坏 `derivedStateOf` 跳过重组的能力。只有当 `State` 持有者实例本身可能变化时，才把该实例作为 key 传入。
- **错误写法（标准计算省略 key，参数变化后返回陈旧
  值）**：


  ```kotlin
  @Composable
  fun FormattedDateLabel(timestamp: Long, locale: Locale) {
      val formattedDate = remember {
          SimpleDateFormat("yyyy-MM-dd", locale).format(Date(timestamp))
      }
      Text(text = formattedDate)
  }
  ```

  <br />

- **优化写法（把引用的计算参数作为 key 传入）**：


  ```kotlin
  @Composable
  fun FormattedDateLabel(timestamp: Long, locale: Locale) {
      val formattedDate = remember(timestamp, locale) {
          SimpleDateFormat("yyyy-MM-dd", locale).format(Date(timestamp))
      }
      Text(text = formattedDate)
  }
  ```

  <br />
