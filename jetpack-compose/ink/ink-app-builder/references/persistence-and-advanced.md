关于用 `ink-storage` 把 Ink 笔划持久化到 Room 数据库、把绘制内容导出为离屏 `Bitmap` 或 PNG 文件，
以及把指针输入与兄弟手势处理者共享的参考资料。

## 笔划序列化与 Room 持久化

把每个 `Stroke` 拆成两个组成部分以便紧凑存储：

1. **笔划输入（`StrokeInputBatch`）**：用 `androidx.ink.storage` 中的 `stroke.inputs.encode(outputStream)` 和 `StrokeInputBatch.decode(inputStream)` 编解码二进制输入点。（在 `1.1.0-alpha` 及更高版本中，还可使用直接操作 `ByteArray` 的重载 `stroke.inputs.encode` 和 `StrokeInputBatch.decode(bytes)`。）
2. **笔刷元数据**：存储 `size`、`colorLong`、`epsilon`，以及内置笔刷枚举值或自定义笔刷标识符。绝不要直接调用 `brush.family.clientBrushFamilyId`---该属性是 `@RestrictTo(LIBRARY_GROUP)`。请在应用的 `Map<String, BrushFamily>` 中用结构相等 `==` 查找自定义笔刷。

### 序列化数据类与笔划转换器


```kotlin
@Serializable
data class SerializedStroke(
    val inputs: ByteArray,
    val brush: SerializedBrush,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is SerializedStroke) return false
        return inputs.contentEquals(other.inputs) && brush == other.brush
    }

    override fun hashCode(): Int = 31 * inputs.contentHashCode() + brush.hashCode()
}

@Serializable
data class SerializedBrush(
    val size: Float,
    val color: Long,
    val epsilon: Float,
    val stockBrush: SerializedStockBrush,
    val clientBrushFamilyId: String? = null,
)

@Serializable
enum class SerializedStockBrush {
    MarkerLatest,
    PressurePenLatest,
    HighlighterLatest,
    DashedLineLatest,
}

private val stockBrushToEnum = mapOf(
    StockBrushes.marker() to SerializedStockBrush.MarkerLatest,
    StockBrushes.pressurePen() to SerializedStockBrush.PressurePenLatest,
    StockBrushes.highlighter() to SerializedStockBrush.HighlighterLatest,
    StockBrushes.dashedLine() to SerializedStockBrush.DashedLineLatest,
)

private val enumToStockBrush = stockBrushToEnum.entries.associate { (k, v) -> v to k }

fun serializeStroke(
    stroke: Stroke,
    customBrushes: Map<String, BrushFamily> = emptyMap(),
): String {
    val encodedInputs = ByteArrayOutputStream().use { outputStream ->
        stroke.inputs.encode(outputStream)
        outputStream.toByteArray()
    }
    val customBrushId = customBrushes.entries.firstOrNull { it.value == stroke.brush.family }?.key
    val serializedBrush = SerializedBrush(
        size = stroke.brush.size,
        color = stroke.brush.colorLong,
        epsilon = stroke.brush.epsilon,
        stockBrush = stockBrushToEnum[stroke.brush.family] ?: SerializedStockBrush.MarkerLatest,
        clientBrushFamilyId = customBrushId,
    )
    return Json.encodeToString(SerializedStroke(inputs = encodedInputs, brush = serializedBrush))
}

fun deserializeStroke(
    data: String,
    customBrushes: Map<String, BrushFamily> = emptyMap(),
): Stroke? {
    return try {
        val serialized = Json.decodeFromString<SerializedStroke>(data)
        val inputs = ByteArrayInputStream(serialized.inputs).use { inputStream ->
            StrokeInputBatch.decode(inputStream)
        }
        val family = serialized.brush.clientBrushFamilyId?.let { customBrushes[it] }
            ?: enumToStockBrush[serialized.brush.stockBrush]
            ?: StockBrushes.marker()
        val brush = Brush.createWithColorLong(
            family = family,
            colorLong = serialized.brush.color,
            size = serialized.brush.size,
            epsilon = serialized.brush.epsilon,
        )
        Stroke(brush = brush, inputs = inputs)
    } catch (e: Exception) {
        null
    }
}
```

<br />

### Room 数据库实体、转换器与仓库

在 Kotlin 中使用 Room 时，始终应用 `com.google.devtools.ksp` 插件并使用
`ksp(libs.androidx.room.compiler)`---绝不要用 `annotationProcessor`。在 `Dispatchers.IO` 上执行笔划
编解码，避免大尺寸绘制阻塞 UI 线程：


```kotlin
@Entity(tableName = "documents")
data class DocumentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "strokes_data")
    val strokesData: List<String> = emptyList(),
)

class RoomConverters {
    private val json = Json { ignoreUnknownKeys = true }

    @TypeConverter
    fun fromStringList(list: List<String>?): String? = list?.let { json.encodeToString(it) }

    @TypeConverter
    fun toStringList(jsonString: String?): List<String> {
        if (jsonString.isNullOrEmpty()) return emptyList()
        return try {
            json.decodeFromString<List<String>>(jsonString)
        } catch (e: Exception) {
            emptyList()
        }
    }
}

@Dao
interface DocumentDao {
    @Query("SELECT * FROM documents WHERE id = :id")
    suspend fun getById(id: Long): DocumentEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DocumentEntity)
}

@Database(entities = [DocumentEntity::class], version = 1)
@TypeConverters(RoomConverters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun documentDao(): DocumentDao
}

class StrokeRepositoryImpl(
    private val dao: DocumentDao,
) : StrokeRepository {
    override suspend fun saveStrokes(documentId: Long, strokes: List<Stroke>) {
        withContext(Dispatchers.IO) {
            val serializedList = strokes.map { serializeStroke(it) }
            dao.upsert(DocumentEntity(id = documentId, strokesData = serializedList))
        }
    }

    override suspend fun loadStrokes(documentId: Long): List<Stroke> =
        withContext(Dispatchers.IO) {
            val doc = dao.getById(documentId) ?: return@withContext emptyList()
            doc.strokesData.mapNotNull { deserializeStroke(it) }
        }
}
```

<br />

## Bitmap 与 PNG 导出

用 `Canvas(bitmap)` 与 `CanvasStrokeRenderer.create(textureStore)` 把已完成的笔划渲染到离屏 `Bitmap`。
用 `Bitmap.CompressFormat.PNG` 压缩 `Bitmap`。在版本 `1.0.0` 及更高版本中，
当绘制到软件 `Canvas(bitmap)` 上时，`CanvasStrokeRenderer.create(textureStore)` 会自动回退到路径
渲染（`CanvasPathRenderer`）。
> **软件 `Canvas(bitmap)` 上的路径渲染注意事项**：仅靠网格渲染的特性
> （`SelfOverlap.ACCUMULATE`、`BrushPaint.StampingTexture`（例如
> `StockBrushes.emojiHighlighter` 的迷你 emoji 轨迹），以及逐顶点不透明度或
> 颜色 `BrushBehavior` 实例）无法由 `CanvasPathRenderer` 绘制，
> 除非提供路径兼容的兜底 `BrushPaint`，否则会被跳过。
> 标准 `StockBrushes`（`pressurePen`、`marker`、`highlighter`、`dashedLine`）
> 导出到软件 `Canvas(bitmap)` 没有问题。


```kotlin
suspend fun exportDrawingToPng(
    width: Int,
    height: Int,
    strokes: List<Stroke>,
    textureStore: TextureBitmapStore,
    outputFile: File,
    backgroundColor: Int = android.graphics.Color.WHITE,
): Uri = withContext(Dispatchers.IO) {
    val exportBitmap = createBitmap(width, height)
    val canvas = Canvas(exportBitmap)
    canvas.drawColor(backgroundColor)

    val renderer = CanvasStrokeRenderer.create(textureStore = textureStore)
    strokes.forEach { stroke ->
        canvas.withSave {
            renderer.draw(
                canvas = this,
                stroke = stroke,
                strokeToScreenTransform = Matrix()
            )
        }
    }

    FileOutputStream(outputFile).use { output ->
        exportBitmap.compress(Bitmap.CompressFormat.PNG, 100, output)
    }
    Uri.fromFile(outputFile)
}
```

<br />

## 运动预测与手势共存

### 低延迟运动预测

把 `implementation("androidx.input:input-motionprediction:<version>")` 加入
`app/build.gradle.kts`，即可让 `InProgressStrokes` 在 classpath 上存在该库时自动预测后续的手写笔与
触摸点---把手写笔的可感知延迟从 20 到 50 ms 降到接近零，无需额外编写 Kotlin 代码。

### 拖拽共存（`pointerInputWithSiblingFallthrough`）

标准 Compose 的 `pointerInput` 修饰符不会与兄弟 composable 共享指针事件。要让长按拖拽处理者与
`InProgressStrokes` 共存，定义一个返回 `sharePointerInputWithSiblings() = true` 的
`PointerInputModifierNode`，并把它的 `Box` 放在父 `Box` 内 `InProgressStrokes` *之后*
（Compose 对 `Box` 子项做命中测试时按声明顺序的倒序，即从最后一个子项到第一个子项）：


```kotlin
internal fun Modifier.pointerInputWithSiblingFallthrough(
    pointerInputEventHandler: PointerInputEventHandler
) = this then PointerInputSiblingFallthroughElement(pointerInputEventHandler)

private class PointerInputSiblingFallthroughModifierNode(
    pointerInputEventHandler: PointerInputEventHandler
) : PointerInputModifierNode, DelegatingNode() {

    var pointerInputEventHandler: PointerInputEventHandler
        get() = delegateNode.pointerInputEventHandler
        set(value) {
            delegateNode.pointerInputEventHandler = value
        }

    val delegateNode = delegate(
        SuspendingPointerInputModifierNode(pointerInputEventHandler)
    )

    override fun onPointerEvent(
        pointerEvent: PointerEvent,
        pass: PointerEventPass,
        bounds: IntSize
    ) {
        delegateNode.onPointerEvent(pointerEvent, pass, bounds)
    }

    override fun onCancelPointerInput() {
        delegateNode.onCancelPointerInput()
    }

    override fun sharePointerInputWithSiblings() = true
}

private data class PointerInputSiblingFallthroughElement(
    val pointerInputEventHandler: PointerInputEventHandler
) : ModifierNodeElement<PointerInputSiblingFallthroughModifierNode>() {

    override fun create() =
        PointerInputSiblingFallthroughModifierNode(pointerInputEventHandler)

    override fun update(node: PointerInputSiblingFallthroughModifierNode) {
        node.pointerInputEventHandler = pointerInputEventHandler
    }

    override fun InspectorInfo.inspectableProperties() {
        name = "pointerInputWithSiblingFallthrough"
        properties["pointerInputEventHandler"] = pointerInputEventHandler
    }
}
```

<br />

## 常见陷阱

- **把笔划栅格化为位图存入数据库**：始终持久化 `StrokeInputBatch` 的二进制字节与笔刷元数据，而不是 PNG，这样笔划才能保持可编辑、可擦除且与分辨率无关。
- **在每次 Room `Flow` 发射时重新反序列化**：如果每笔之后都保存并收集 Room 的 `Flow`，就会在每一笔时重新解码整个文档。在 `init` 时加载一次，并把内存中的 `history` 作为会话的唯一事实来源。
- **把 `pointerInputWithSiblingFallthrough` 放在 `InProgressStrokes` 之前**：把 fallthrough 的 `Box` 放在 `InProgressStrokes` *之后*，这样它会先被命中测试，并向下把事件共享给 `InProgressStrokes`。
