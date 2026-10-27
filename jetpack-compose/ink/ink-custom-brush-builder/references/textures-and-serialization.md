用于配合 `TextureBitmapStore` 添加 `BrushPaint.TilingTexture` 与
`BrushPaint.StampingTexture` 图层，以及编解码自定义 `BrushFamily`
定义的参考（`androidx.ink` `1.1.0-alpha03` 及更高版本）。

## `TextureBitmapStore` 与纹理资源

`androidx.ink` 不内置纹理图片资源。生成纹理画笔时，要告知用户把所引用的
PNG 或 WebP 纹理文件加入项目（例如用
`app/src/main/res/drawable-nodpi/pencil_grain.png` 避免密度缩放），
并从 `TextureBitmapStore` 返回它的 `Bitmap`。如果
`TextureBitmapStore[clientTextureId]` 返回 `null`，笔画会静默渲染成平坦、
无纹理的填充。


```kotlin
class CustomBrushTextureStore(context: Context) : TextureBitmapStore {
    private val resources = context.resources
    private val textureResources: Map<String, Int> = mapOf(
        "pencil-grain" to R.drawable.pencil_grain,
        "watercolor-wash" to R.drawable.watercolor_wash,
    )
    private val loadedBitmaps = mutableMapOf<String, Bitmap>()

    private val _generation = MutableStateFlow(0)
    val generation: StateFlow<Int> = _generation.asStateFlow()

    override operator fun get(clientTextureId: String): Bitmap? {
        return loadedBitmaps.getOrPut(clientTextureId) {
            textureResources[clientTextureId]?.let { resId ->
                BitmapFactory.decodeResource(resources, resId)
            } ?: return null
        }
    }

    fun registerBitmap(textureId: String, bitmap: Bitmap) {
        loadedBitmaps[textureId] = bitmap
        _generation.update { it + 1 }
    }
}
```

<br />

动态加载纹理后（例如从解码的 `.brush` 流加载）`generation` 递增时，
用 `remember(textureStore, generation)` 重建 `CanvasStrokeRenderer`，
并用 `key(generation)` 给 `InProgressStrokes` 重新设 key，让缓存的
`BitmapShader` 实例刷新。

## `TextureLayer` 子类（`TilingTexture` 与 `StampingTexture`）

在 `1.1.0-alpha03` 及更高版本中，`BrushPaint.TextureLayer` 是一个抽象类，
有两个具体子类：

- **`BrushPaint.TilingTexture`** ：在笔画几何体上平铺无缝纹理（适合铅笔颗粒、纸张纹理或水彩晕染）。设置 `sizeUnit = BrushPaint.TextureLayer.SizeUnit.BRUSH_SIZE`，让平铺尺寸随 `Brush.size` 缩放。
- **`BrushPaint.StampingTexture`** ：沿笔画把纹理盖章到每个离散粒子上（`BrushTip.particleGapDistanceScale > 0f` 或 `particleGapDurationMillis > 0L`）。在 Android 14（API level 34）及更高版本的硬件 `Canvas` 上需要 `CanvasMeshRenderer`；如果笔画还要在 Android 13（API level 33）及更低版本或软件 `Canvas(bitmap)` 上渲染，请在 `BrushCoat.paintPreferences` 中提供一个与路径渲染器兼容的备选 `BrushPaint`。

### 为纹理图层选择 `BlendMode`

**最后一个（或唯一的）`TextureLayer`** 会拿纹理（`src`）与画笔颜色（
`dst`，它承载边缘抗锯齿和逐顶点
`OPACITY_MULTIPLIER`）做混合。请使用输出 alpha 与
`Alpha_dst` 成正比的混合模式---例如 **`BlendMode.MODULATE`**（默认）、
**`BlendMode.DST_IN`** 、**`BlendMode.DST_OUT`** 、**`BlendMode.SRC_ATOP`** 、
或 **`BlendMode.SRC_IN`** 。绝不要在最后一个 `TextureLayer` 上使用
`BlendMode.SRC_OVER`，因为它在纹理不透明处会覆盖边缘抗锯齿并忽略
`OPACITY_MULTIPLIER`：


```kotlin
fun createTexturedBrushFamily(): BrushFamily {
    val grainPaint = BrushPaint(
        selfOverlap = SelfOverlap.ANY,
        textureLayers = listOf(
            BrushPaint.TilingTexture(
                clientTextureId = "pencil-grain",
                sizeX = 1.0f,
                sizeY = 1.0f,
                sizeUnit = BrushPaint.TextureLayer.SizeUnit.BRUSH_SIZE,
                blendMode = BrushPaint.TextureLayer.BlendMode.MODULATE,
            ),
        ),
        colorFunctions = listOf(BrushPaint.ColorFunction.OpacityMultiplier(0.85f)),
    )

    return BrushFamily(
        tip = BrushTip(scaleX = 1f, scaleY = 1f, cornerRounding = 1f),
        paint = grainPaint,
    )
}
```

<br />

## 序列化与反序列化自定义 `BrushFamily` 定义

`androidx.ink.storage` 提供两套等价的 gzip+protobuf 序列化
API（在 `1.1.0-alpha02` 及更高版本中无需注解；仅在 `1.0.0` stable 上需要
`@OptIn(ExperimentalInkCustomBrushApi::class)`）：

1. **Kotlin 扩展函数** ：`brushFamily.encode(outputStream, textureBitmapStore)` 与 `BrushFamily.decode(inputStream, maxVersion, getClientTextureId)`。
2. **便于 Java 调用的 `@JvmStatic` 方法** ：`AndroidBrushFamilySerialization.encode` 与 `AndroidBrushFamilySerialization.decode`。

### 保存与加载带内嵌纹理的 `BrushFamily`

在 `1.1.0-alpha` 中用纹理回调解码时，始终把 lambda 包进
**`BrushFamilyDecodeCallback { textureId, bitmap -> ... }`**，以便与多平台的
`OnDecodeTexturePngBytes` 重载区分。生产画笔传
`maxVersion = Version.MAX_SUPPORTED`，测试实验性画笔特性时传
`Version.DEVELOPMENT`：


```kotlin
suspend fun saveCustomBrushToFile(
    context: Context,
    uri: Uri,
    brushFamily: BrushFamily,
    textureBitmapStore: TextureBitmapStore,
) = withContext(Dispatchers.IO) {
    context.contentResolver.openOutputStream(uri)?.use { outputStream ->
        brushFamily.encode(outputStream, textureBitmapStore)
    }
}

suspend fun loadCustomBrushFromFile(
    inputStream: InputStream,
    textureStore: CustomBrushTextureStore,
    allowDevelopmentFeatures: Boolean = false,
): BrushFamily = withContext(Dispatchers.IO) {
    val maxVersion = if (allowDevelopmentFeatures) {
        Version.DEVELOPMENT
    } else {
        Version.MAX_SUPPORTED
    }
    inputStream.use { stream ->
        BrushFamily.decode(
            input = stream,
            maxVersion = maxVersion,
            getClientTextureId = BrushFamilyDecodeCallback { textureId, bitmap ->
                if (bitmap != null) {
                    textureStore.registerBitmap(textureId, bitmap)
                }
                textureId
            },
        )
    }
}
```

<br />

### 把自定义画笔存入 Room 数据库（`BLOB`）

把编码后的 `BrushFamily` 字节持久化到 `ColumnInfo.BLOB` 的 `ByteArray` 列中：


```kotlin
@Entity(tableName = "custom_brushes")
data class CustomBrushEntity(
    @PrimaryKey val name: String,
    @ColumnInfo(typeAffinity = ColumnInfo.BLOB)
    val brushBytes: ByteArray,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is CustomBrushEntity) return false
        return name == other.name && brushBytes.contentEquals(other.brushBytes)
    }

    override fun hashCode(): Int = 31 * name.hashCode() + brushBytes.contentHashCode()
}

fun encodeBrushForDatabase(
    brushFamily: BrushFamily,
    textureBitmapStore: TextureBitmapStore = TextureBitmapStore { null },
): ByteArray {
    return ByteArrayOutputStream().use { stream ->
        brushFamily.encode(stream, textureBitmapStore)
        stream.toByteArray()
    }
}
```

<br />

## 常见陷阱

- **直接实例化抽象的 `BrushPaint.TextureLayer`** ：在 `1.1.0-alpha03` 及更高版本中，要实例化 `BrushPaint.TilingTexture` 或 `BrushPaint.StampingTexture`（`SizeUnit`、`BlendMode` 和 `Wrap` 仍嵌套在 `BrushPaint.TextureLayer.*` 上，而 `Origin` 嵌套在 `BrushPaint.TilingTexture.Origin` 上）。
- **给 `BrushFamily.decode` 传未指定类型的尾随 lambda** ：Kotlin 无法区分 `BrushFamilyDecodeCallback`（`Bitmap?`）与 `OnDecodeTexturePngBytes`（`ByteArray?`）。始终用 `BrushFamilyDecodeCallback { id, bitmap -> ... }` 包装。
- **纹理位图过大** ：把 `res/drawable-nodpi/` 中的平铺纹理控制在 256×256 或 512×512 像素左右，避免不必要的 GPU 内存占用。
