关于用 MVVM 与 Hilt 组织 Ink Compose 应用、实现线性撤销与重做历史栈，以及添加基于几何的笔划
橡皮擦的参考资料。

## MVVM 架构概述

    Compose UI Layer (DrawingScreen -> DrawingSurface + DrawingToolbox)
      │  Observes StateFlows via collectAsStateWithLifecycle
      ▼
    ViewModel Layer (DrawingViewModel)
      │  Manages uiState, currentBrush, isEraserMode, canUndo/canRedo, history
      ▼
    Repository Layer (StrokeRepository)
      │  Runs serializeStroke / deserializeStroke on Dispatchers.IO
      ▼
    Data Layer (Room AppDatabase + DocumentDao)

定义一个不可变的 UI 状态类，以及一个持有笔划历史、当前笔刷与橡皮擦状态的 `ViewModel`：


```kotlin
data class DrawingUiState(
    val strokes: List<Stroke> = emptyList(),
    val documentTitle: String = "",
)
```

<br />

## 线性撤销与重做历史栈

在 `ViewModel` 内维护一个快照历史列表（`MutableList<List<Stroke>>`）和一个 `historyIndex` 指针。
由于 `Stroke` 实例不可变，每个快照只分配一个轻量的列表引用，不会复制笔划几何数据。

### 带撤销、重做与橡皮擦的 `DrawingViewModel`

当用户在 `undo` 之后新增、擦除或清除笔划时，先截断 `historyIndex` 之后的所有条目，再追加新快照。
用 `maxHistorySize`（例如 `50`）限制长会话中的历史增长，并在每次变更后（`onStrokesFinished`、
`endErase`、`undo`、`redo` 和 `clearStrokes`）于 `Dispatchers.IO` 上持久化笔划：


```kotlin
class DrawingViewModel(
    private val repository: StrokeRepository,
    val textureStore: AppTextureBitmapStore,
    private val documentId: Long = 1L,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DrawingUiState())
    val uiState: StateFlow<DrawingUiState> = _uiState.asStateFlow()

    private val _selectedBrush = MutableStateFlow(
        Brush.createWithComposeColor(
            family = StockBrushes.pressurePen(),
            color = Color.Black,
            size = 5f,
            epsilon = 0.1f,
        )
    )
    val currentBrush: StateFlow<Brush> = _selectedBrush.asStateFlow()

    fun getCurrentBrush(): Brush = _selectedBrush.value

    private val _isEraserMode = MutableStateFlow(false)
    val isEraserMode: StateFlow<Boolean> = _isEraserMode.asStateFlow()

    private val _canUndo = MutableStateFlow(false)
    val canUndo: StateFlow<Boolean> = _canUndo.asStateFlow()

    private val _canRedo = MutableStateFlow(false)
    val canRedo: StateFlow<Boolean> = _canRedo.asStateFlow()

    private val history = mutableListOf<List<Stroke>>()
    private var historyIndex = -1
    private val maxHistorySize = 50

    private var previousPoint: MutableVec? = null
    private val eraserPadding = 50f

    init {
        viewModelScope.launch {
            val initialStrokes = repository.loadStrokes(documentId)
            _uiState.update { it.copy(strokes = initialStrokes) }
            history.clear()
            history.add(initialStrokes)
            historyIndex = 0
            updateUndoRedoState()
        }
    }

    private fun updateStrokes(newStrokes: List<Stroke>) {
        // Truncate any future redo states when a new edit occurs after undo
        if (historyIndex < history.size - 1) {
            history.subList(historyIndex + 1, history.size).clear()
        }
        history.add(newStrokes)
        historyIndex++

        while (history.size > maxHistorySize) {
            history.removeAt(0)
            historyIndex--
        }

        _uiState.update { it.copy(strokes = newStrokes) }
        updateUndoRedoState()
    }

    private fun updateUndoRedoState() {
        _canUndo.value = historyIndex > 0
        _canRedo.value = historyIndex < history.size - 1
    }

    fun onStrokesFinished(finishedStrokes: List<Stroke>) {
        val current = history.getOrElse(historyIndex) { emptyList() }
        updateStrokes(current + finishedStrokes)
        viewModelScope.launch { saveStrokes() }
    }

    fun undo() {
        if (_canUndo.value) {
            historyIndex--
            _uiState.update { it.copy(strokes = history[historyIndex]) }
            updateUndoRedoState()
            viewModelScope.launch { saveStrokes() }
        }
    }

    fun redo() {
        if (_canRedo.value) {
            historyIndex++
            _uiState.update { it.copy(strokes = history[historyIndex]) }
            updateUndoRedoState()
            viewModelScope.launch { saveStrokes() }
        }
    }

    fun clearStrokes() {
        if (_uiState.value.strokes.isNotEmpty()) {
            updateStrokes(emptyList())
            viewModelScope.launch { saveStrokes() }
        }
    }

    fun setEraserMode(enabled: Boolean) {
        _isEraserMode.value = enabled
    }

    fun startErase() {
        previousPoint = null
    }

    fun endErase() {
        previousPoint = null
        viewModelScope.launch { saveStrokes() }
    }

    fun erase(x: Float, y: Float) {
        val strokesBefore = history.getOrElse(historyIndex) { emptyList() }
        val strokesAfter = eraseIntersectingStrokes(x, y, strokesBefore)
        if (strokesAfter.size != strokesBefore.size) {
            updateStrokes(strokesAfter)
        }
    }

    private fun eraseIntersectingStrokes(
        currentX: Float,
        currentY: Float,
        currentStrokes: List<Stroke>,
    ): List<Stroke> {
        val prev = previousPoint
        previousPoint = MutableVec(currentX, currentY)
        if (prev == null) return currentStrokes

        val segment = MutableSegment(prev, MutableVec(currentX, currentY))
        val parallelogram = MutableParallelogram()
            .populateFromSegmentAndPadding(segment, eraserPadding)

        val strokesToRemove = currentStrokes.filter { stroke ->
            stroke.shape.intersects(parallelogram, AffineTransform.IDENTITY)
        }
        return if (strokesToRemove.isNotEmpty()) {
            currentStrokes - strokesToRemove.toSet()
        } else {
            currentStrokes
        }
    }

    private suspend fun saveStrokes() {
        val strokesToSave = history.getOrElse(historyIndex) { emptyList() }
        repository.saveStrokes(documentId, strokesToSave)
    }
}
```

<br />

## 基于几何的笔划橡皮擦详解

橡皮擦会检测每个笔划的 `PartitionedMesh`（`stroke.shape`）是否与在相邻拖拽点
（`MutableSegment`）之间扫出的、带 padding 的 `MutableParallelogram` 相交。

- **橡皮擦 padding（`eraserPadding`）**：精确擦除用 `10f` 到 `30f`；手指或手写笔擦除用 `40f` 到 `60f`（默认 `50f`）；大面积擦除用 `80f` 及以上。
- **生命周期**：在 `startErase` 和 `endErase` 中都要重置 `previousPoint = null`，这样新的拖拽不会连到上一次拖拽的终点。

### 几何转换与平移或缩放下的擦除

使用 `ink-geometry-compose` 与 `ink-geometry` 的扩展函数，在 Compose 或 Android 类型与 Ink 几何类型之间
转换，或在画布被平移或缩放时变换橡皮擦的命中测试：


```kotlin
fun populatePointFromOffset(reusableVec: MutableVec, offset: Offset): Offset {
    reusableVec.populateFrom(offset)
    return reusableVec.toOffset()
}

fun eraseWithPanZoom(
    strokes: List<Stroke>,
    screenEraserBox: MutableParallelogram,
    worldToScreenAndroidMatrix: AndroidMatrix,
    worldToScreenComposeMatrix: ComposeMatrix? = null,
): List<Stroke> {
    val meshToEraserTransform: AffineTransform =
        if (worldToScreenComposeMatrix != null) {
            ImmutableAffineTransform.from(worldToScreenComposeMatrix) ?: AffineTransform.IDENTITY
        } else {
            MutableAffineTransform().populateFrom(worldToScreenAndroidMatrix)
        }

    return strokes.filterNot { stroke ->
        stroke.shape.intersects(screenEraserBox, meshToEraserTransform)
    }
}

fun getStrokeBounds(stroke: Stroke): Pair<Rect?, RectF?> {
    val boundingBox = stroke.shape.computeBoundingBox() ?: return null to null
    return boundingBox.toRect() to boundingBox.toRectF()
}
```

<br />

## Composable 屏幕接线与仓库接口

用 `collectAsStateWithLifecycle` 观察 `ViewModel` 的 flow，使应用进入后台时暂停收集；并在
`textureStore.generation` 变化时于 composable 层重建 `CanvasStrokeRenderer`：


```kotlin
interface StrokeRepository {
    suspend fun saveStrokes(documentId: Long, strokes: List<Stroke>)
    suspend fun loadStrokes(documentId: Long): List<Stroke>
}

@Composable
fun DrawingScreen(
    viewModel: DrawingViewModel,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val currentBrush by viewModel.currentBrush.collectAsStateWithLifecycle()
    val isEraserMode by viewModel.isEraserMode.collectAsStateWithLifecycle()

    val textureStore = viewModel.textureStore
    val cacheGen by textureStore.generation.collectAsStateWithLifecycle()
    val renderer = remember(textureStore, cacheGen) {
        CanvasStrokeRenderer.create(textureStore)
    }

    CompositionLocalProvider(LocalTextureStore provides textureStore) {
        DrawingSurface(
            strokes = uiState.strokes,
            canvasStrokeRenderer = renderer,
            currentBrush = currentBrush,
            onGetNextBrush = { viewModel.getCurrentBrush() },
            onStrokesFinished = { viewModel.onStrokesFinished(it) },
            isEraserMode = isEraserMode,
            modifier = modifier,
            onErase = { x, y -> viewModel.erase(x, y) },
            onEraseStart = { viewModel.startErase() },
            onEraseEnd = { viewModel.endErase() },
        )
    }
}
```

<br />

## 常见陷阱

- **在 `ViewModel.onCleared` 中启动 `saveStrokes`**：`onCleared` 运行时 `viewModelScope` 已被取消，因此在那里启动的协程会立即取消。应在每次变更后持久化笔划。
- **在 `startErase` 和 `endErase` 中未重置 `previousPoint`**：残留的 `previousPoint` 会在下次触摸按下时生成横跨整个画布的长线段，误擦掉不该擦的笔划。
- **橡皮擦手势中未调用 `change.consume`**：未被消费的拖拽事件会传播到父级或兄弟手势处理者。
- **忘记在 `init` 中为 `history` 填入初始值**：始终添加 `initialStrokes`（即使为空），并设置 `historyIndex = 0`，这样用户的第一笔才能被撤销。
