## 1. 主线程阻塞、卸载与缓存

把非 UI 工作移出主线程，避免在 Composable 主体里直接分配重量级对象，并用 `remember` 在多次重组之间缓存昂贵的计算。

### 1. 在 composable 主体里缓存昂贵的计算

如果 Composable 主体要对集合做排序、过滤或繁重的字符串操作，就把这段计算包进 `remember`：

- **坏做法（每次重组都重新计算）**：


  ```kotlin
  @Composable
  fun FilteredFeed(rawList: List<Post>, query: String) {
      // Avoid: Heavy filtering and sorting on every recomposition
      val filteredList = rawList
          .filter { it.title.contains(query) }
          .sortedBy { it.timestamp }
      PostList(posts = filteredList)
  }
  ```

  <br />

- **优化做法（用 remember 缓存计算）**：


  ```kotlin
  @Composable
  fun FilteredFeed(rawList: List<Post>, query: String) {
      val filteredList = remember(rawList, query) {
          rawList
              .filter { it.title.contains(query) }
              .sortedBy { it.timestamp }
      }
      PostList(posts = filteredList)
  }
  ```

  <br />

对于元素极少的集合（3 到 5 项），把计算包进 `remember` 会引入分配开销，却没有可衡量的收益。用
Macro benchmark 对缓存改动做基准测试。

### 2. 避免在组合中分配重量级对象

绝不要在 Composable 主体里直接分配或计算重量级对象（例如 `RoundedPolygon`、复杂 path、`Paint`
或日期格式化器）。把它们包进 `remember { ... }`，或提升到 Composable 之外。

- **坏做法（每一帧/每次重组都新建日期格式化器）**：


  ```kotlin
  @Composable
  fun DateBadge(timestamp: Long) {
      val formatter = SimpleDateFormat("MMM dd, yyyy", LocalLocale.current.platformLocale)
      Text(text = formatter.format(Date(timestamp)))
  }
  ```

  <br />

- **优化做法（格式化器只分配一次，在多次时间戳更新间复用）**：


  ```kotlin
  // Reusable formatter allocated once at top-level or remembered
  private val dateFormatter =
      SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())

  @Composable
  fun DateBadge(timestamp: Long) {
      val formattedDate = dateFormatter.format(Date(timestamp))

      Text(text = formattedDate)
  }
  ```

  <br />

`.toShape()` 或 `painterResource()` 这类转换函数本身就是 `@Composable`，内部已处理缓存。

### 3. 用 `produceState` 把 I/O 和繁重工作交给 `Dispatchers.IO`

绝不要在主线程上直接执行阻塞操作（例如数据库查询、磁盘 I/O、繁重的文件解析或阻塞的 binder
事务）。用 `produceState` 把它们交给 `Dispatchers.IO`：

- **坏做法（在主 UI 线程上做阻塞 I/O）**：


  ```kotlin
  @Composable
  fun ProfileScreen(fileUri: Uri) {
      var state by remember { mutableStateOf<Data?>(null) }
      LaunchedEffect(fileUri) {
          val data = parseJsonFromDisk(fileUri) // Blocks main dispatcher!
          state = data
      }
  }
  ```

  <br />

- **优化做法（通过 `produceState` 交给 IO 调度器）**：


  ```kotlin
  @Composable
  fun ProfileScreen(fileUri: Uri) {
      val state by produceState<Data?>(initialValue = null, fileUri) {
          value = withContext(Dispatchers.IO) { parseJsonFromDisk(fileUri) }
      }
  }
  ```

  <br />

## 2. 副作用执行与生命周期规则

组织结构化的副作用：生命周期感知、幂等、作用域正确。
禁止在 Composable 主体里直接写副作用，非挂起操作优先用 `SideEffect`，把 flow 或 receiver 订阅提升到列表项
composable 之外，并始终使用 `collectAsStateWithLifecycle()`。

### 1. 禁止在 composable 主体里直接写副作用

Composable 主体必须保持幂等，并且不含直接的副作用。直接写在组合中的副作用会在每一次重组尝试时执行
（包括推测性、被中断或被丢弃的重组过程）。

- **坏做法（副作用直接在组合过程中执行）**：


  ```kotlin
  @Composable
  fun UserProfile(userId: String, viewModel: ProfileViewModel) {
      // Avoid: Runs on every recomposition and speculative pass
      viewModel.trackProfileImpression(userId)
      Text(text = "User: $userId")
  }
  ```

  <br />

- **优化做法（包在 SideEffect 或用户事件处理器里）**：


  ```kotlin
  @Composable
  fun UserProfile(userId: String, viewModel: ProfileViewModel) {
      // Compose 1.12+: keyed SideEffect
      SideEffect(userId) {
          viewModel.trackProfileImpression(userId)
      }
      Text(text = "User: $userId")
  }
  ```

  <br />

### 2. 禁止用 `LaunchedEffect` 处理非挂起操作

绝不要把同步的、非挂起的操作包进 `LaunchedEffect`。
即使不发生挂起，`LaunchedEffect` 也会创建一个独立协程、分配协程上下文
机制，并调度到线程上。

- **坏做法（为同步调用做不必要的协程分配）**：


  ```kotlin
  LaunchedEffect(itemId) {
      analyticsTracker.trackScreenView(itemId) // Non-suspend function!
  }
  ```

  <br />

- **优化做法（组合成功时用 `SideEffect` 做同步
  执行）**：


  ```kotlin
  // Compose 1.12+ (supports keys directly):
  SideEffect(itemId) {
      analyticsTracker.trackScreenView(itemId)
  }
  ```

  <br />

- **警告**：绝不要用 `DisposableEffect(keys) { ... onDispose {} }` 搭配空的
  `onDispose` 块来触发带 key 的同步副作用。检查项目在 `gradle/libs.versions.toml` 或
  `build.gradle(.kts)` 里的 Compose 版本：Compose 1.12+ 用 `SideEffect(keys)`，1.12 之前的版本
  用 `SideEffect { ... }` 配合 `remember` 缓存的 key 检查。

### 3. 生命周期感知的 flow 收集（`collectAsStateWithLifecycle`）

在 Android UI 开发中，收集会主动产生后台工作的 Kotlin `Flow` 时，使用 `collectAsStateWithLifecycle()`。
`collectAsStateWithLifecycle`（来自
`androidx.lifecycle:lifecycle-runtime-compose`）会根据 Android `Lifecycle` 状态（默认
`Lifecycle.State.STARTED`）自动订阅和取消 flow 收集，从而避免应用或屏幕停止时的后台 CPU 占用、耗电、
资源泄漏和不必要的 UI 更新。

- **性能细节与何时优先用 `collectAsState()`**：

  - **基准测试开销**：由于 Android `Lifecycle` 观察者注册和生命周期感知状态机的开销，`collectAsStateWithLifecycle()` 的订阅和分发比 `collectAsState()` 慢约 3-4 倍。
  - **内存内与已限定作用域的 StateFlow**：对于轻量的内存内 `StateFlow`（例如已经用 `SharingStarted.WhileSubscribed(5000)` 限定作用域的 ViewModel 发出的 UI 状态），`collectAsState()` 通常性能更好，能避开这部分开销。
  - **何时必须用 `collectAsStateWithLifecycle()`**：把 `collectAsStateWithLifecycle()` 留给冷 flow、数据库观察流、传感器、位置更新，以及屏幕不可见时必须停止发送的外部轮询流。
  - **非 Android 平台**：在没有 Android `Lifecycle` 库的 Compose Multiplatform（Desktop、Web、iOS）中，使用 `collectAsState()`。
  - **无界面／单元测试环境**：在非 UI 作用域或没有 `LifecycleOwner` 的纯单元测试中。
- **坏做法（在 Android 上后台持续收集，泄漏资源和
  CPU 周期）**：


  ```kotlin
  @Composable
  fun HomeFeed(viewModel: FeedViewModel) {
      // Avoid on Android: Flow stays active when activity is stopped
      val uiState by viewModel.feedState.collectAsState()
      FeedContent(uiState = uiState)
  }
  ```

  <br />

- **优化做法（生命周期感知：进入后台时暂停收集）**：


  ```kotlin
  // import androidx.lifecycle.compose.collectAsStateWithLifecycle

  @Composable
  fun HomeFeed(viewModel: FeedViewModel) {
      val uiState by viewModel.feedState.collectAsStateWithLifecycle()
      FeedContent(uiState = uiState)
  }
  ```

  <br />

### 4. 提升 `BroadcastReceiver` 和监听器，避免逐项注册

绝不要在列表项 Composable 里注册 `BroadcastReceiver` 或系统监听器（例如
`ACTION_TIMEZONE_CHANGED` 或网络连接变化）。这会在主线程上为每个可见项注册单独的 receiver，
造成严重的滚动延迟、内存泄漏和掉帧。

在父级或屏幕级 Composable 里用
`DisposableEffect` 注册一个 receiver，并通过参数或
`CompositionLocalProvider` 把状态向下传递。

- **坏做法（在 LazyColumn 里为每个可见项注册单独的 BroadcastReceiver）**：


  ```kotlin
  @Composable
  fun TimeZoneListItem(timeZoneId: String) {
      val context = LocalContext.current
      DisposableEffect(Unit) {
          // Avoid: Multiplied BroadcastReceivers per visible item!
          val receiver = object : BroadcastReceiver() {
              // ...
          }
          context.registerReceiver(
              receiver,
              IntentFilter(Intent.ACTION_TIMEZONE_CHANGED),
          )
          onDispose { context.unregisterReceiver(receiver) }
      }
      ItemRow(timeZoneId)
  }
  ```

  <br />

- **优化做法（单个 BroadcastReceiver 提升到父容器）**：


  ```kotlin
  @Composable
  fun TimeZoneList(timeZoneIds: List<String>) {
      val context = LocalContext.current
      var currentTimeZone by remember {
          mutableStateOf(TimeZone.getDefault())
      }

      DisposableEffect(context) {
          val receiver = object : BroadcastReceiver() {
              override fun onReceive(c: Context?, intent: Intent?) {
                  currentTimeZone = TimeZone.getDefault()
              }
          }
          context.registerReceiver(
              receiver,
              IntentFilter(Intent.ACTION_TIMEZONE_CHANGED),
          )
          onDispose { context.unregisterReceiver(receiver) }
      }

      LazyColumn {
          items(timeZoneIds, key = { it }) { id ->
              TimeZoneListItem(
                  timeZoneId = id,
                  currentTimeZone = currentTimeZone,
              )
          }
      }
  }
  ```

  <br />

### 5. 为可选副作用加保护，并让副作用类型匹配工作类型

如果可选回调或触发处理器是 `null`，绝不要无条件地启动 `LaunchedEffect` 或 `DisposableEffect`。
用 `if (callback != null)` 为副作用加保护，避免分配不必要的协程 job 和快照副作用
跟踪结构。此外，要确保副作用 API 与执行类型匹配：

- **同步回调（`() -> Unit`）**：使用 `SideEffect` 或带 key 的 `SideEffect(onInit)`，而不是启动协程 job。
- **挂起回调（`suspend () -> Unit`）**：使用
  `LaunchedEffect(onInit)`，并用 `if (onInit != null)` 加保护。

- **坏做法（回调为 null 或同步时仍启动空协程和副作用节点）**：


  ```kotlin
  // Avoid: Launches coroutine for synchronous work, runs even if null
  LaunchedEffect(onInit) {
      onInit?.invoke()
  }
  ```

  <br />

- **优化做法（同步工作用 SideEffect；可选时加保护）**：


  ```kotlin
  if (onInit != null) {
      SideEffect(onInit) {
          onInit()
      }
  }
  ```

  <br />

### 6. 用 `rememberUpdatedState` 防止捕获过期值

如果 `LaunchedEffect` 里长时间运行、周期性或循环的协程引用了 Composable 参数或回调，就用 `rememberUpdatedState`
确保它始终使用最新值，而不重启副作用：

- **坏做法（循环存活期间 onTick 参数变化时会捕获过期值）**：


  ```kotlin
  @Composable
  fun PeriodicTicker(intervalMs: Long, onTick: () -> Unit) {
      LaunchedEffect(intervalMs) {
          while (isActive) {
              delay(intervalMs)
              onTick() // Stale reference if onTick callback instance changes!
          }
      }
  }
  ```

  <br />

- **优化做法（rememberUpdatedState 提供最新回调，且不取消计时
  循环）**：


  ```kotlin
  @Composable
  fun PeriodicTicker(intervalMs: Long, onTick: () -> Unit) {
      val currentOnTick by rememberUpdatedState(onTick)
      LaunchedEffect(intervalMs) {
          while (isActive) {
              delay(intervalMs)
              currentOnTick()
          }
      }
  }
  ```

  <br />

### 7. 用协程延时代替旧式计时器

避免在 UI 代码里使用 `Handler.postDelayed` 或 `TimerTask` 这类旧式 Android handler。改用
`LaunchedEffect` 搭配 `delay()`，获得干净、生命周期感知的计时，Composable 离开组合时会自动取消。

- **坏做法（旧式 Handler 有内存泄漏和脱离生命周期执行的风险）**：


  ```kotlin
  DisposableEffect(Unit) {
      val handler = Handler(Looper.getMainLooper())
      val runnable = Runnable { showBanner = false }
      handler.postDelayed(runnable, 3000L)
      onDispose { handler.removeCallbacks(runnable) }
  }
  ```

  <br />

- **优化做法（干净、生命周期感知的协程延时）**：


  ```kotlin
  LaunchedEffect(Unit) {
      delay(3000L)
      showBanner = false
  }
  ```

  <br />

### 8. 合并相关的 `LaunchedEffect`（减少副作用数量）

挂在 composable 上的每个 `LaunchedEffect` 都会分配 slot table 记录、
注册协程启动机制，并在拆除时需要取消跟踪。

当多个异步任务共用同一个触发 key（例如首次加载屏幕时的 `Unit`）时，把它们合并成一个
`LaunchedEffect` 块，内部用嵌套的 `launch { ... }` 调用，而不是声明多个独立的
`LaunchedEffect`。

- **坏做法（多个独立 LaunchedEffect 带来重复的副作用开销）**：


  ```kotlin
  @Composable
  fun ShoppingCartScreen(viewModel: CartViewModel) {
      // Avoid: 3 LaunchedEffects allocate 3 effect nodes and launchers
      LaunchedEffect(Unit) { viewModel.loadCart() }
      LaunchedEffect(Unit) { viewModel.loadPaymentMethods() }
      LaunchedEffect(Unit) { viewModel.loadDeliveryAddresses() }

      CartContent()
  }
  ```

  <br />

- **优化做法（单个 LaunchedEffect 管理多个并发
  协程）**：


  ```kotlin
  @Composable
  fun ShoppingCartScreen(viewModel: CartViewModel) {
      // Optimized: 1 LaunchedEffect node launches concurrent jobs
      LaunchedEffect(Unit) {
          launch { viewModel.loadCart() }
          launch { viewModel.loadPaymentMethods() }
          launch { viewModel.loadDeliveryAddresses() }
      }

      CartContent()
  }
  ```

  <br />

### 9. 副作用执行顺序与拆除开销

了解 Compose 副作用的执行生命周期和性能开销，在选择用哪个时至关重要：

#### A. 组合变更被应用时的执行顺序

当组合变更被应用时（`RememberObserver.onRemembered`），Compose
按以下顺序触发副作用：

1. **`DisposableEffect`**：在组合变更被应用时最先同步执行，顺序与在 composable 中声明的一致。
2. **`SideEffect`**：第二个同步执行，在 `DisposableEffect` 运行之后、布局和绘制发生之前。
3. **`LaunchedEffect`**：在组合变更被应用时，在组合的 `CoroutineContext` 上启动协程。由于它是异步调度到该协程调度器上执行的，不会在应用过程中同步运行，也**不**保证在 Layout 和 Draw 之后运行。

> **警告：**
> 不要假设 `LaunchedEffect` 会等到 Layout 和 Draw 之后才执行。
> 如果你的代码需要布局边界或坐标，请通过布局
> modifier（`onPlaced`、`onSizeChanged` 或 `onLayoutRectChanged`）观察它们，而不是
> 依赖副作用调度时机。

#### B. 副作用分配与拆除开销

各种副作用的开销差异很大：

- **`SideEffect`**：最便宜的副作用；在每次成功的组合过程中同步执行，不做生命周期注册，也不分配协程。
- **`DisposableEffect`**：开销中等；注册回调，并在 key 变化或离开组合时同步运行 `onDispose`。
- **`LaunchedEffect`**：开销最高；需要分配协程启动器、在组合调度器上启动新的协程 job，并在 key 变化或 composable 退出时取消或拆除该协程 job。

由于取消 `LaunchedEffect` 会带来协程 job 取消和
拆除开销，要避免在动画或快速滚动期间频繁轮换 `LaunchedEffect` 的 key。对于无需拆除的同步带 key 触发，
始终优先用带 key 的 `SideEffect(keys)`，而不是 `LaunchedEffect(keys)`。

## 3. 副作用 API 选择指南

根据执行上下文和生命周期要求选择合适的副作用 API：

| 使用场景 | 推荐 API | 示例 |
|---|---|---|
| **与 Composable 生命周期绑定的协程** | `LaunchedEffect(keys)` | 在 ID 变化时触发网络调用或动画 |
| **退出时的同步清理** | `DisposableEffect(keys)` | 注册和注销生命周期监听器或观察者 |
| **从 UI 回调启动协程** | `rememberCoroutineScope()` | 在按钮点击或滑动时触发滚动动画 |
| **把 Compose State 转换为 Flow** | `snapshotFlow { state }` | 对由文本输入框状态派生的搜索请求做防抖 |
| **同步的带 key 触发** | `SideEffect` 或 `SideEffect(keys)` | 更新外部命令式管理的视图或非 Compose 状态 |
| **视口可见性或曝光跟踪** | `Modifier.onVisibilityChanged` | 在列表项进入视口时发送分析数据或记录曝光 \| |
