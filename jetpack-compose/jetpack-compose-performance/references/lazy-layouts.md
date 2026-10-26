## 1. Lazy 布局指令

实施严格的 item key 设置、content type 映射和索引查找优化，以免滚动期间出现
不必要的 item 重组、布局 pass 和掉帧。
> **适用范围保护（仅限虚拟化容器）**：本节的指令**严格**适用于 lazy 虚拟化布局
> （`LazyColumn`、`LazyRow`、`LazyVerticalGrid`、`LazyHorizontalGrid`、
> `HorizontalPager`、`VerticalPager`）。使用标准 Kotlin `for` 或 `forEach`
> 循环遍历集合的标准非虚拟化容器（`Column`、`Row`、`Box`）**不是** lazy 布局。
> **不要**因为标准 `Column`/`Row` 循环缺少 `key` 或 `contentType` 参数就标记它们。

### 1. 要求提供 key 和 content type

始终为所有 item 提供稳定的 `key` 和 `contentType`。

- **`key`**：让 Compose 能在重排序和列表更新时保留 item 状态，而无需从头重建 item 组合。
- **`contentType`**：让 Compose 在回收同一视觉类型的 item 时复用 item 组合和节点槽位，显著降低快速滚动时的布局膨胀开销。


```kotlin
LazyColumn {
    items(
        items = itemList,
        key = { item -> item.id },
        contentType = { item -> item.type }
    ) { item ->
        ItemRow(item = item)
    }
}
```

<br />

- **确保 key 可存入 Bundle**：key 必须能保存在 Android `Bundle` 中，因为 `LazyColumn` 内部使用 `rememberSaveable` 在配置变更和进程死亡后保留滚动状态与 item 状态。
  - **不要**使用自定义数据类作为 key，除非它们实现了 `Parcelable` 或 `Serializable`。
  - **要**使用唯一的原始类型（例如 `Int` 或 `Long`）。如有需要，把多个字段组合成唯一字符串：`key = { "${it.id}_${it.timestamp}"
    }`。为把内存和哈希开销降到最低，优先使用 `Int` 和 `Long` 而不是 `String`。
- **避免重复和不稳定的 key**：确保 key 全局唯一且确定。绝不要使用 `hashCode()` 或列表索引作为 key，因为它们在 item 被重排序、插入或过滤时会变化。

### 2. 避免在 item 内进行集合搜索和可观察状态查询

不要在 item 布局块或外层列表 item 作用域内执行集合搜索、线性索引扫描或
可观察状态查询：

- **线性索引扫描（`indexOf`、`find`）**：在布局块内搜索某个 item 的索引
  （例如 `list.indexOf(item)`）会把一次线性布局 pass 变成 `O(N²)` 操作，
  并在异步修改期间引发 `IndexOutOfBoundsException`。请改用
  `itemsIndexed`。

  - **错误做法（每个 item 都做 `O(N²)` 线性扫描）**：


    ```kotlin
    LazyColumn {
        items(items = itemList, key = { it.id }) { item ->
            // O(N) lookup inside each item!
            val index = itemList.indexOf(item)
            ItemRow(index = index, item = item)
        }
    }
    ```

    <br />

  - **优化做法（用 `itemsIndexed` 直接传入索引）**：


    ```kotlin
    LazyColumn {
        itemsIndexed(
            items = itemList,
            key = { _, item -> item.id },
        ) { index, item ->
            ItemRow(index = index, item = item)
        }
    }
    ```

    <br />

- **可观察的选中状态与状态查询**：绝不要用 `mutableStateListOf`
  （`SnapshotStateList`）跟踪选中的 ID，因为 `.contains()` 和 `.remove()`
  会执行 `O(N)` 线性扫描；请在 `MutableState` 中使用不可变 `Set`
  （`mutableStateOf(emptySet<String>())`），或使用 `mutableStateSetOf`
  （Compose 1.8+ 中的 `SnapshotStateSet`）来获得 `O(1)` 查找。另外，
  在外层 `items(...) { ... }` 块内读取可观察集合状态（例如
  `selectedIds.contains(item.id)`）会让整个列表或分区订阅该集合的变更。
  切换单个 item 就会使父作用域失效，并强制所有可见 item 完整重组。应把
  状态读取推迟到叶子 item composable，通过传入 lambda 提供器
  （`isSelected: () -> Boolean`）来实现。

  - **错误做法（`mutableStateListOf` 的 `O(N)` 查找，且在外层 `items`
    作用域读取状态，会在切换时触发整个列表或网格重组）**：


    ```kotlin
    @Composable
    fun TopicGrid(sections: List<TopicSection>) {
        val selectedTopicIds = remember { mutableStateListOf<String>() }
        LazyColumn {
            items(sections, key = { it.id }) { section ->
                Column {
                    Text(text = section.title)
                    section.topics.forEach { topic ->
                        // Avoid: O(N) List.contains() read in items() scope
                        // invalidates the whole section!
                        val isSelected = selectedTopicIds.contains(topic.id)
                        TopicChip(
                            topic = topic,
                            isSelected = isSelected,
                            onToggle = {
                                if (isSelected) {
                                    selectedTopicIds.remove(topic.id)
                                } else {
                                    selectedTopicIds.add(topic.id)
                                }
                            }
                        )
                    }
                }
            }
        }
    }
    ```

    <br />

  - **优化做法（用 `Set<String>`（`mutableStateOf(emptySet())` 或
    `mutableStateSetOf()`）实现 `O(1)` 查找，并把 lambda 传给叶子
    composable，把重组限制在被点击的 item 内）**：


    ```kotlin
    @Composable
    fun TopicGrid(sections: List<TopicSection>) {
        var selectedTopicIds by remember {
            mutableStateOf(emptySet<String>())
        }
        LazyColumn {
            items(
                items = sections,
                key = { it.id },
                contentType = { "section" },
            ) { section ->
                Column {
                    Text(text = section.title)
                    section.topics.forEach { topic ->
                        TopicChip(
                            topic = topic,
                            // O(1) Set read deferred to TopicChip's scope
                            isSelectedProvider = {
                                selectedTopicIds.contains(topic.id)
                            },
                            onToggle = {
                                val selected =
                                    selectedTopicIds.contains(topic.id)
                                selectedTopicIds = if (selected) {
                                    selectedTopicIds - topic.id
                                } else {
                                    selectedTopicIds + topic.id
                                }
                            }
                        )
                    }
                }
            }
        }
    }

    @Composable
    fun TopicChip(
        topic: Topic,
        isSelectedProvider: () -> Boolean,
        onToggle: () -> Unit
    ) {
        // Read occurs inside leaf scope
        val isSelected = isSelectedProvider()
        val status = if (isSelected) "Selected" else "Unselected"
        Box(modifier = Modifier.clickable { onToggle() }) {
            Text(text = "${topic.title} ($status)")
        }
    }
    ```

    <br />

### 3. 不要对直接的集合大小和计数使用 `derivedStateOf`

不要对直接的集合属性访问（例如 `list.size` 或 `list.isEmpty()`）套用
`derivedStateOf`。在已有的列表或快照集合上访问属性是 `O(1)` 读取。把它套进
`derivedStateOf` 会分配一个 `DerivedState` 包装对象、快照记录跟踪结构和
观察者订阅，代价远高于直接读取整数属性。

### 4. 小规模或有界集合不要使用 lazy 布局

**提示：** 对小型静态集合或有界动态集合（例如 1 到 10 个 item，如标签、按钮、
表单行或 chip），优先使用标准的 `Row` 或 `Column` 配合 `for` 或 `forEach`
循环，而不是 `LazyRow` 或 `LazyColumn`。对小集合而言，提前组合所有 item 比
lazy 列表虚拟化机制更能减少布局、预取和测量开销。在广泛改动代码之前，先对
这一改动做基准测试。

- **错误做法（为极小的静态列表承担 lazy 虚拟化开销）**：


  ```kotlin
  LazyRow {
      items(items = listOf("Work", "Personal", "Family")) { tag ->
          FilterChip(tag = tag)
      }
  }
  ```

  <br />

- **优化做法（标准 Row 配合 forEach）**：


  ```kotlin
  Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
      listOf("Work", "Personal", "Family").forEach { tag ->
          FilterChip(tag = tag)
      }
  }
  ```

  <br />

### 5. 把共享的 `Flow` 和状态集合提升到 lazy item 之外

**关键：** 绝不要在列表 item composable 内用 `collectAsState()` 或
`collectAsStateWithLifecycle()` 直接收集共享的 `Flow`、`StateFlow` 或可观察
计时器。

当共享 flow 在 item composable 内被收集时，`LazyColumn` 或 `LazyRow` 中每个
可见 item 都会对同一 flow 创建独立订阅。当 flow 发出更新（例如空闲计时器
tick 或周期性同步）时，它会同时使所有可见 item 失效并重组，在滚动期间造成
大量 CPU 尖峰和掉帧。

相反，应**把 flow 的收集提升一次**到 `LazyColumn` 之上的父容器，派生出所需的
状态，再把稳定值或原始类型值下传给各个 item composable。

- **错误做法（每个可见 item 都对共享计时器创建独立订阅）**：


  ```kotlin
  @Composable
  fun FeedItem(item: Post) {
      // Avoid: Multiplied subscriptions across all visible items!
      val secondsSinceLastScroll by MainFeedIdleTracker
          .secondsSinceLastScrollFlow
          .collectAsState(0L)
      val isDwellTriggered = secondsSinceLastScroll >= 5L
      PostActions(isDwellTriggered = isDwellTriggered)
  }

  @Composable
  fun FeedList(posts: List<Post>) {
      LazyColumn {
          items(posts, key = { it.id }) { post ->
              FeedItem(post)
          }
      }
  }
  ```

  <br />

- **优化做法（在 LazyColumn 之上把订阅提升一次，把稳定值下传）**：


  ```kotlin
  @Composable
  fun FeedList(posts: List<Post>) {
      // Hoist once: Parent owns the single subscription
      val secondsSinceLastScroll by MainFeedIdleTracker
          .secondsSinceLastScrollFlow
          .collectAsStateWithLifecycle(0L)
      val isDwellTriggered = secondsSinceLastScroll >= 5L

      LazyColumn {
          items(posts, key = { it.id }) { post ->
              FeedItem(post = post, isDwellTriggered = isDwellTriggered)
          }
      }
  }

  @Composable
  fun FeedItem(post: Post, isDwellTriggered: Boolean) {
      PostActions(isDwellTriggered = isDwellTriggered)
  }
  ```

  <br />

### 6. 向下传递 `CompositionLocal`，而不是在 lazy item 中读取

避免在各个 lazy item composable 内直接查询 `CompositionLocal`（例如
`LocalContext.current` 或 `LocalDensity.current`）。

在每个 item 内查询 `CompositionLocal` 会在 item 组合期间增加重复的 map 查找
开销，并让每个 item 都订阅该 CompositionLocal 的更新。相反，应在父屏幕或
列表容器中读取一次 CompositionLocal，再把解析后的值作为参数下传。

- **错误做法（逐 item 查询作用域和 context）**：


  ```kotlin
  @Composable
  fun SnackItem(snack: Snack) {
      val sharedScope = LocalSharedTransitionScope.current
          ?: error("No scope")
      val context = LocalContext.current
      // ...
  }
  ```

  <br />

- **优化做法（把解析好的依赖作为参数下传）**：


  ```kotlin
  @Composable
  fun SnackList(
      snacks: List<Snack>,
      sharedScope: SharedTransitionScope,
  ) {
      val context = LocalContext.current
      LazyColumn {
          items(snacks, key = { it.id }, contentType = { "snack" }) { snack ->
              SnackItem(
                  snack = snack,
                  sharedScope = sharedScope,
                  context = context,
              )
          }
      }
  }
  ```

  <br />

### 7. 把共享转场推迟到可见性指示器之后

为 lazy 布局中的每个 item 附加 `Modifier.sharedBounds` 或
`Modifier.sharedElement` 会增加大量 modifier 分配、共享状态跟踪和快照记录
实例化开销——即使对应 item 位于屏幕外或已被预取、并不可见。

在快速滚动或大型 lazy 列表中，应把共享转场挡在可见性指示器（例如
`Modifier.onVisibilityChanged` 或 viewport 可见性检查）之后，使只有已渲染、
可见的 item 才实例化转场作用域和协调跟踪。
