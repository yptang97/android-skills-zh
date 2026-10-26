---
name: jetpack-compose-performance
description: 诊断并优化 Android Jetpack Compose UI 代码。在分析现有代码的性能瓶颈、以减少重组开销并防止掉帧和 UI 卡顿时，使用这个 skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - Jetpack Compose
  - performance
  - UI development
  - optimization
  - recomposition
  - lazy layouts
  - graphics
  - stability
  - memory
  - allocation
  - jank
  - rendering
  - state computation
  - state derivation
  - snapshotFlow
  - produceState
  - derivedStateOf
  - computedStateOf
  - sharedElement
  - sharedBounds
  - CompositionLocal
---

## 基础前置条件

在对 composable 做微观优化之前，先确保标准的生产配置已就位：

1. **Release 构建**：绝不要对可调试构建做性能分析或基准测试；ART 运行时验证会严重拖慢性能。
2. **R8 压缩**：保持 R8 启用，以优化字节码和协程调度。
3. **Baseline Profile**：为关键用户旅程（冷启动、关键滚动信息流）生成 baseline profile，让 ART VM 提前预编译和预加载类。

## 优化审查流程

1. **全面扫描** ：按以下各节的 7 个核心类别扫描目标代码。要针对所有检查清单规则评估每一个 `@Composable` 函数、modifier 链和 lazy 布局数据模型，而不是发现第一个问题就停下。
2. **标记或修改前必读参考资料** ：每当某个文件命中类别 1--7 中的某条规则，你在报告问题或修改代码**之前**，**必须**打开并阅读对应的 `references/*.md` 文件，了解获准的修复模式和完整的范围限定。绝不要只靠摘要要点来编写修复。

## 1. 状态、快照与稳定性（[references/state-and-stability.md](references/state-and-stability.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/state-and-stability.md](references/state-and-stability.md)。

- **阶段延后（lambda）** ：把频繁变化的状态读取包进 lambda（例如 `Modifier.offset` 或 `Modifier.graphicsLayer`），让读取发生在 Layout 或 Draw 阶段而非 Composition 阶段。
- **禁止反向写入（检查先读后写的顺序）** ：绝不要在更晚的阶段修改状态，也不要在一个状态已在同一组合轮次中被读取之后再修改它（`Read -> Write`，或 `Composition Read -> Layout or Draw
  Write`）。避免跨阶段的反向写入，以防首帧跳变、卡顿和无限重组循环（[反向写入](references/android/develop/ui/compose/performance/backwards-write.md)）。**不要**把 composable 开头的状态赋值（`Write ->
  Read` 或 `Composition Write -> Draw Read`）标记为反向写入---反向写入严格要求对该状态的读取发生在写入之前。
- **避免组合中的冗余状态包装（`Write -> Read`）** ：不要仅仅为了在组合开头立即覆盖、然后再读取而把同步值包进 `remember { mutableStateOf(...) }`（例如 `var path by remember { mutableStateOf(Path()) }; path =
  viewModel.getPath()`）。这虽然不算反向写入，却会带来不必要的 slot table 与 `MutableState` 快照开销（而且如果之后在赋值前加了读取，就有变成反向写入的风险）；应改用普通的局部 `val`，或在目标阶段内直接读取该值（例如 `Modifier.drawWithCache`）。
- **显式 `remember` key 与 slot 开销** ：始终把 `remember` 内部引用的所有输入变量和 composable 参数作为计算 key 传入。请记住，`remember` 会在 slot table 中存储 `keys + 1` 个对象，并在每次重组时检查 key 相等性；只有当分配开销大或必须保留对象身份时才使用 `remember`。在包装 `derivedStateOf` 时，**不要**把快照状态值/属性（例如 `state.value`）作为 key 传入（如果实例引用会变化，传入 `State` 实例本身是可以的）。
- **`computedStateOf` 与 `derivedStateOf`（Compose 1.13+）** ：在 Compose 1.13+ 上，对来自快速变化输入的简单条件判断和过滤状态（例如 `scrollState.value > 0`）使用 `computedStateOf`，它的失效处理明显快于 `derivedStateOf`（在 Compose `< 1.13` 上使用 `remember { derivedStateOf { ... } }`）。`derivedStateOf` 留给两类情况：能从多次读取缓存中获益的重计算，或在每次组合中被读取足够频繁（大致为 `10 / numberOfStatesReadPerCalculation` 次，且读取之间不触发失效）从而能弥补失效成本的简单计算。
- **同步状态派生** ：审查观察 Compose 状态（例如滚动位置或集合大小）的异步 `produceState` + `snapshotFlow` 块；把它们替换为同步的 `remember { derivedStateOf
  { ... } }`（或在 Compose 1.13+ 上用 `computedStateOf`）。
- **简单原始值** ：对于简单的布尔表达式和属性查找，优先使用普通的自定义 Kotlin getter（`get()`），而不是 `derivedStateOf` 或 `computedStateOf`。
- **集合状态跟踪** ：整表更新应使用标准 `mutableListOf()` 搭配有实际意义的赋值和 `mutableStateOf(list, neverEqualPolicy())`，而不是 `mutableStateListOf()`。
- **快照集合** ：重复查询或迭代时使用 `SnapshotStateList.toList()`，避免逐元素读取的观察开销。
- **重复的状态读取** ：把重复的 Compose `State` 属性读取提取到块顶部的局部变量中。
- **setter 中的状态** ：避免在自定义属性 setter 内读取 Compose `State`；在触发变更副作用时使用原始 backing field，并批量处理多属性更新。
- **稳定性与跳过的权衡（跳过不是免费的）** ：不要执着于稳定性，也不要把 `@Immutable`、`@Stable` 或 `ImmutableList` 当成默认解决方案。跳过一个 composable 不是零成本：每个参数都会像被 remember 一样存入 slot table，重组时必须比较所有输入。[强跳过模式](references/android/develop/ui/compose/performance/stability/strongskipping.md)已经能在实例相等（`===`）匹配时跳过带不稳定参数的 composable（包括标准 `kotlin.collections.List`）。给模型加注解或使用 `ImmutableList` 会强制结构性相等（`.equals()`），对大型集合或复杂类来说，这可能比重组本身昂贵得多。
- **绝不给集合模型添加 `@Stable`、`@Immutable` 或 `ImmutableList`** ：在编写或优化代码时，绝不要给包含集合（`List`、`Set`、`Map`）的模型加 `@Immutable` 或 `@Stable`，并且**绝不**建议把 `kotlin.collections.List<T>` 换成 `ImmutableList<T>`（或把 `ImmutableList` 加进 `stability_config.txt`）。在强跳过模式下，每次重组都对集合做 `O(N)` 的 `.equals()` 比 `O(1)` 的实例相等（`===`）更昂贵。
- **移除既有 `@Stable` / `@Immutable` 注解的范围限定
  （仅限大型 lazy 数据集）** ：
  - **何时移除** ：**只有**在**两个**条件同时满足时，才建议从数据模型上移除已有的 `@Stable` 或 `@Immutable` 注解：(1) 该模型被用在**lazy 布局**（`LazyColumn`、`LazyRow`、`LazyGrid`、`Pager`、`ScalingLazyColumn`）中作为输入流或项目模型，**且** (2) 它包含**大型数据集或深层嵌套
    的集合层级**（例如信息流、大型标签/项目列表，或像 `Post` 含 `List<Paragraph>` 和 `List<Markup>` 这样的多层嵌套列表），此时递归的 `O(N)` `.equals()` 检查会拖慢滚动和重组性能。
  - **何时保持原样** ：对于代码库中所有其他既有的 `@Stable`、`@Immutable` 或 `ImmutableList` 用法---例如非 lazy 的 UI 模型、独立组件，或集合规模较小/有界（例如一张卡片带几个徽标、缩略图或元数据行）而数据集大小较小或未知的模型---**保持现有
    注解不动，也不要标记它们** 。绝不要不经验证就盲目 grep 并标记代码库中所有 `@Stable`/`@Immutable` 类，必须先确认它们是否为大型数据集的 lazy 布局提供输入。
- **在强跳过模式下何时添加 `@Stable` / `@Immutable`** ：Compose 模块中带 `val` 原始类型/`String` 属性的扁平 `data class` **已被编译器推断为稳定**并自动使用 `.equals()`---不要给它们加多余的 `@Immutable` 注解。只有当编译器无法推断稳定性（例如来自非 Compose 模块的类或接口）**并且**某个数据源（例如 Room 或 MVI reducer）每次发射都会为未变更的项目分配新对象实例时才添加 `@Stable` 或 `@Immutable`，**前提**是该类小、扁平、不含集合（`List`、`Set`、`Map`），且它的 `.equals()` 检查是简单的 `O(1)`。
- **让 composable 更廉价，而不是强行跳过**：不要过度看重重组次数。一旦组合已被调度（调度并启动重组轮次占据成本的大头），在一次活跃的重组轮次中跳过一个 composable 省下的时间很少。应专注于让 composable 的执行更廉价、把状态读取延后到 Layout/Draw，并用基准测试验证，而不是假设跳过就能提升性能。

## 2. 布局与测量优化（[references/layouts.md](references/layouts.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/layouts.md](references/layouts.md)。

- **坐标与放置** ：避免 `onGloballyPositioned`；视口跟踪用 `Modifier.onVisibilityChanged`，局部边界用 `Modifier.onPlaced` 或 `Modifier.onLayoutRectChanged`，并需要在 `Modifier.Node` 事件处理器中按需查询 `requireLayoutCoordinates()`。
- **用自定义 `Layout` 锚定浮动内容** ：给组件附加浮动标签或工具提示时，使用自定义 `Layout` 测量并相互相对地放置两个子项。绝不要在 `MutableState` 中跟踪 `onGloballyPositioned` 坐标再用 `offset` 定位浮动内容，这会导致 1 帧延迟并调度第二次组合轮次。
- **偏移量的阶段延后** ：把动态偏移包进 lambda（`Modifier.offset { IntOffset(...) }`），直接从 Composition 跳到 Layout。
- **树深度与装饰性包装** ：避免多余的包装 `Box` 和装饰性 `Canvas` 节点；直接附加 modifier 或使用 `Modifier.drawBehind`。
- **子组合开销** ：在热路径和 lazy 项目中避免 `BoxWithConstraints` / `SubcomposeLayout`；优先使用标准 modifier、`Modifier.layout` 或 `LayoutModifierNode`。
- **固有测量**：谨慎使用固有测量，避免深层嵌套的固有链。

## 3. Lazy 布局优化（[references/lazy-layouts.md](references/lazy-layouts.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/lazy-layouts.md](references/lazy-layouts.md)。

- **Lazy 布局范围限定** ：关于 `key` 和 `contentType` 的指令**严格**适用于 Lazy 容器（`LazyColumn`、`LazyRow`、`LazyGrid`）。绝不要标记在集合上迭代的标准非 lazy 容器（`Column`、`Row`、`Box`）。
- **强制提供 `contentType` 与原始类型 `key`** ：始终为 lazy 布局（`LazyColumn`、`LazyRow`、`LazyGrid`）中的所有项目同时指定原始类型 `key`（`Int`、`Long`、`String`）**和** `contentType`。使用 `items` 或 `itemsIndexed` 时绝不省略 `contentType`：`contentType = { _, item -> item.type }`。省略 `contentType` 会让 Compose 在滚动期间无法复用组合 slot。
- **项目内的索引查找** ：用 `itemsIndexed` 替换 `list.indexOf(item)`，消除布局过程中 `O(N²)` 的查找。
- **可观察的选择与状态查询** ：把选择跟踪从 `mutableStateListOf` 改为 `MutableState` 中的不可变 `Set`（`mutableStateOf(emptySet<String>())`）、`mutableStateSetOf()` 或 Map，以获得 `O(1)` 查找。向叶子 composable 传 lambda 提供者（`isSelected: () -> Boolean`），把重组与父级 `items` 作用域隔离开。
- **在 lazy 项目中传播 CompositionLocal** ：避免在单个 lazy 项目 composable 内查询 `CompositionLocal`（`LocalContext.current`、`LocalDensity.current`、`LocalSharedTransitionScope.current`、各种 scope 等）；在父容器或屏幕中解析一次，然后把解析后的值作为参数向下传递。
- **在 lazy 项目中延后共享转场** ：把 lazy 项目上的 `Modifier.sharedBounds` 或 `Modifier.sharedElement` 放在可见性指示器（例如 `Modifier.onVisibilityChanged` 或视口可见性检查）之后，这样离屏或预取的项目不会实例化转场 scope。
- **项目数量的派生** ：直接读取集合的 `.size`，不要把列表数量包进 `derivedStateOf`。
- **小型与有界列表** ：对于小型或有界集合（例如 1 到 10 个项目），使用标准 `Row` 或 `Column` 配合 `for` 或 `forEach` 循环，以消除 lazy 虚拟化、测量和预取开销。
- **提升共享 Flow** ：在 lazy 布局之前的父容器中只收集一次共享 `Flow`；绝不要对每个可见项目调用 `collectAsStateWithLifecycle()`。
- **避免在预取项目中产生副作用** ：绝不要在 lazy 项目内的 `LaunchedEffect(Unit)` 中触发分析事件；改用带停留阈值的 `Modifier.onVisibilityChanged`。

## 4. 动画与共享转场（[references/animation.md](references/animation.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/animation.md](references/animation.md)。

- **动画属性的阶段延后** ：把快速变化的动画状态读取（alpha、scale、rotation、color）包进 `Modifier.graphicsLayer { ...
  }`，绕过 Composition 直接在 Draw 阶段求值。
- **偏移量与尺寸的阶段延后** ：把动画偏移包进 `Modifier.offset { IntOffset(...) }`，并用 `Modifier.layout { ... }` 或 `Modifier.animateBounds` 对约束做动画，以在尺寸转场期间绕过重组。
- **在快速滚动列表中延后共享转场** ：只在可见时用 `Modifier.onVisibilityChanged` 附加 `Modifier.sharedBounds` 或 `Modifier.sharedElement`，避免在被丢弃的预取项目上产生 modifier 和观察实例化开销。
- **Lambda 提供者** ：向子 composable 传 lambda 提供者（`() -> Float`）而不是原始动画值，让状态读取保持延后到 Draw 或 Layout。
- **节点中的持久 `Animatable`** ：把 `Animatable` 作为 `Modifier.Node` 上的持久成员属性保存，并在 `onAttach()` 中用 `coroutineScope.launch` 启动。

## 5. effect、生命周期与线程（[effects-and-threading.md](references/effects-and-threading.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/effects-and-threading.md](references/effects-and-threading.md)。

- **禁止在 body 中直接产生副作用** ：绝不要在组合期间直接在 Composable body 中执行副作用；把它们包进 `SideEffect`、`LaunchedEffect` 或用户事件回调。
- **禁止非挂起的 `LaunchedEffect` 与空的 `DisposableEffect`** ：绝不要用 `LaunchedEffect` 执行同步操作（例如打日志或更新对象）。绝不要用 `onDispose {}` 为空的 `DisposableEffect` 作为变通方案。改用 `SideEffect`（在 Compose 1.12+ 中，`SideEffect(keys) { ... }` 直接支持 key；在 Compose `<
  1.12` 上，`SideEffect` 不接受参数，因此要检查项目的 Compose 版本，并在 `SideEffect { ... }` 内用被 `remember` 的持有者跟踪 key 变化）。
- **缓存 body 中的分配** ：把重量级对象分配（例如日期格式化器或复杂 path）和昂贵计算包进 `remember`。
- **合并相关的 `LaunchedEffect`** ：把多个 `LaunchedEffect(Unit)` 调用合并为带嵌套 `launch { ... }` 块的单个 `LaunchedEffect`，以减少 effect 节点分配和协程启动器开销。
- **effect 顺序与拆除成本** ：理解组合变更被应用时 effect 的执行顺序（`DisposableEffect` 先运行，然后是 `SideEffect`，而 `LaunchedEffect` 会在组合的 `CoroutineContext` 上启动协程，该协程异步派发，且不保证等到 Draw 之后）。注意取消 `LaunchedEffect` 会产生协程取消和拆除开销；在动画或滚动期间避免频繁循环 `LaunchedEffect` 的 key。
- **主线程卸载** ：用 `produceState` 把阻塞式 I/O、重型文件解析和数据库操作卸载到 `withContext(Dispatchers.IO)`。
- **lazy 布局中不要有项目级的曝光 effect** ：绝不要在 lazy 项目内用 `LaunchedEffect` 或 `DisposableEffect` 记录曝光。lazy 项目在进入视口之前就会被预组合，造成过早或虚假的曝光。改用带停留阈值的 `Modifier.onVisibilityChanged`。
- **生命周期感知的 Flow 收集** ：对于在 Android 上会主动产生后台工作的 UI Flow 收集，使用 `collectAsStateWithLifecycle()`；对于轻量的内存 StateFlow 或非 Android 作用域，使用 `collectAsState()`。
- **提升接收器与监听器** ：在屏幕层级用 `DisposableEffect` 只注册一次系统监听器和 `BroadcastReceiver`，不要在 lazy 列表项内注册。
- **保护可选 effect** ：启动前用 `if (callback != null)` 保护 effect，避免分配空协程和 effect 节点。
- **防止陈旧捕获** ：当 `LaunchedEffect` 中长时间运行或循环的协程引用回调或参数时，使用 `rememberUpdatedState`。
- **替换旧式定时器** ：用 `LaunchedEffect` 和 `delay()` 替换 `Handler.postDelayed` 或 `TimerTask`。

## 6. 图形与自定义绘制（[references/graphics-performance.md](references/graphics-performance.md)）

**强制要求** ：在标记或修复本类别的任何问题之前，你**必须**阅读 [references/graphics-performance.md](references/graphics-performance.md)。

- **缓存绘制分配** ：用 `Modifier.drawWithCache` 替换装饰性 `Canvas` 节点，以缓存 `Path`、`Paint` 和 `Brush` 分配。
- **优先用 AsyncImage 而非 Image** ：从网络加载图片时使用 Coil 的 `AsyncImage`，drawable 使用 `painterResource`。`Image` 没有针对缓存和图片加载做优化，可能引起性能问题。
- **限定快速变化的 uniform** ：在组合中 `remember` `RuntimeShader` 和 `ShaderBrush`，在 `drawWithCache` 中更新尺寸相关的 uniform，在 `onDrawBehind` 中更新逐帧 uniform。
- **图形 Path 对象复用** ：在热绘制循环中优先用 `Path.rewind()` 而非 `reset()`，以保留已分配的缓冲区而不重新分配。
- **值类与原始类型集合** ：避免泛型元组（`Pair`、`Triple`）和泛型集合（`HashSet<Long>`）；使用 `androidx.collection.MutableLongSet` 和 `androidx.compose.ui.util.packInts`。

## 7. 自定义 modifier：`Modifier.Node`（[自定义 modifier 指南](references/android/develop/ui/compose/custom-modifiers.md)）

- **Modifier.Node 迁移** ：把旧式 `Modifier.composed` 迁移到
  `ModifierNodeElement` + `Modifier.Node`（或在委托给子节点（例如 `SuspendingPointerInputModifierNode`）时用 `DelegatingNode`），
  并配以能力接口（`DrawModifierNode`、`LayoutModifierNode`、
  `SemanticsModifierNode`、使用 `currentValueOf(...)` 的 `CompositionLocalConsumerModifierNode`），
  以消除每个节点的子组合开销并支持节点复用（见[用 Modifier.Node 创建自定义 modifier](references/android/develop/ui/compose/custom-modifiers.md)）：


  ```kotlin
  // Modifier factory
  fun Modifier.circle(color: Color) = this then CircleElement(color)

  // ModifierNodeElement
  private data class CircleElement(
      val color: Color
  ) : ModifierNodeElement<CircleNode>() {
      override fun create() = CircleNode(color)

      override fun update(node: CircleNode) {
          node.color = color
      }
  }

  // Modifier.Node
  private class CircleNode(
      var color: Color
  ) : DrawModifierNode, Modifier.Node() {
      override fun ContentDrawScope.draw() {
          drawCircle(color)
      }
  }
  ```

  <br />

- **按需获取坐标** ：在 `Modifier.Node` 的指针或绘制处理器中按需查询 `requireLayoutCoordinates()`，
  而不是实现 `GlobalPositionAwareModifierNode.onGloballyPositioned`。

**重要** ：关于如何把常见 modifier 迁移到 Modifier.Node 的更多示例，你必须阅读[用 Modifier.Node 创建自定义 modifier](references/android/develop/ui/compose/custom-modifiers.md)。
