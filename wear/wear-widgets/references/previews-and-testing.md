## 1. Composable 预览套件（`Squircle`、`Round` 与 `Rectangular`）

用 `@Preview` 注解预览函数，并把预定义的某个
`PreviewParameterProvider` 套件传给 `@PreviewParameter`。调用
`WearWidgetPreview(widget, params)` 渲染 `SMALL` 与 `LARGE` 容器：

- **`SquircleAllWidgetPreviewParams`**：圆角矩形容器。
- **`RoundAllWidgetPreviewParams`**：胶囊形（pill）容器。
- **`RectangularAllWidgetPreviewParams`**：`320 dpi` 下带显示安全内边距的未裁剪矩形容器，用于生成小组件选择器预览资源。

```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.glance.wear.core.WearWidgetParams
import androidx.glance.wear.tooling.preview.RectangularAllWidgetPreviewParams
import androidx.glance.wear.tooling.preview.RoundAllWidgetPreviewParams
import androidx.glance.wear.tooling.preview.SquircleAllWidgetPreviewParams
import androidx.glance.wear.tooling.preview.WearWidgetPreview

@Preview(
    name = "Squircle",
    device = "spec:width=1000dp,height=1000dp,dpi=320",
)
@Composable
fun MyWidgetSquirclePreview(
    @PreviewParameter(SquircleAllWidgetPreviewParams::class)
    params: WearWidgetParams,
) {
    WearWidgetPreview(MyWidget(), params)
}

@Preview(
    name = "Round",
    device = "spec:width=1000dp,height=1000dp,dpi=320",
)
@Composable
fun MyWidgetRoundPreview(
    @PreviewParameter(RoundAllWidgetPreviewParams::class)
    params: WearWidgetParams,
) {
    WearWidgetPreview(MyWidget(), params)
}

@Preview(
    name = "Widget Preview Asset",
    device = "spec:width=1000dp,height=1000dp,dpi=320",
)
@Composable
fun MyWidgetCatalogPreview(
    @PreviewParameter(RectangularAllWidgetPreviewParams::class)
    params: WearWidgetParams,
) {
    WearWidgetPreview(MyWidget(), params)
}
```

## 2. 小组件选择器预览 PNG（`res/drawable-nodpi/`）

Wear OS 会在系统小组件选择器中，为 `@xml/` provider 配置里声明的每个
`<container>` 显示静态预览图。

### 生成并保存矩形预览资源

1. 渲染使用 `RectangularAllWidgetPreviewParams::class` 与 `device = "spec:width=1000dp,height=1000dp,dpi=320"` 配置的 `@Preview` 函数。该套件会为 `SMALL` 与 `LARGE` 两种容器都生成未裁剪的矩形变体。
2. 从 Android Studio 的 **Design** 面板（**Copy Image** 或保存）或使用 CLI 预览工具导出渲染后的图片。
3. 把 `SMALL` 与 `LARGE` 的 PNG 保存到 `app/src/main/res/drawable-nodpi/`，以避免密度缩放。

### 平台资源要求

- **目录**：把位图 PNG 放在 `app/src/main/res/drawable-nodpi/`，这样系统不会应用密度缩放。
- **尺寸（320 dpi，即 2.0x 手表密度）**：
  - `SMALL`（`CONTAINER_TYPE_SMALL`，`224x84` dp）：**`448x168` px**（宽高比 `2.67`）。
  - `LARGE`（`CONTAINER_TYPE_LARGE`，`232x144` dp）：**`464x288` px**（宽高比 `1.61`）。
- **视觉保真度**：每张预览 PNG **必须**是能体现小组件真实 UI 元素的非空白、未加遮罩的矩形图片。要包含小组件的标题或数值文本、可交互按钮、图标、头像缩写，或合成后的背景 drawable。**严禁**使用纯色占位图、无标签的空形状、原始背景纹理，或 1:1（`400x400`）的方块预览。

## 3. Robolectric 单元测试（`provideWidgetData` 与 `captureRawContent`）

用 JUnit 4 与 Robolectric 对小组件做单元测试时，先调用
`widget.provideWidgetData(context, params)`，再调用
`data.captureRawContent(context, params)`。这会执行
`WearWidgetDocument` composable lambda，并验证 Remote Compose 的
`rcDocument` 载荷能无错误地序列化。由于 alpha 版本中的 `WearWidgetParams` 与
`captureRawContent` 带有 `@RestrictTo(LIBRARY_GROUP)`，需要在测试类上加
`@SuppressLint("RestrictedApi")`：

```kotlin
import android.annotation.SuppressLint
import android.content.Context
import androidx.glance.wear.core.ContainerInfo
import androidx.glance.wear.core.WearWidgetParams
import androidx.glance.wear.core.WidgetInstanceId
import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@SuppressLint("RestrictedApi")
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class MyWidgetTest {
    @Test
    fun provideWidgetData_serializesRemoteComposeDocument() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val widget = MyWidget()
        for (containerType in listOf(
            ContainerInfo.CONTAINER_TYPE_SMALL,
            ContainerInfo.CONTAINER_TYPE_LARGE,
        )) {
            val params = WearWidgetParams(
                instanceId = WidgetInstanceId(namespace = "test", id = 1),
                containerType = containerType,
                widthDp = 220f,
                heightDp = 120f,
                horizontalPaddingDp = 8f,
                verticalPaddingDp = 8f,
                cornerRadiusDp = 16f,
            )
            val data = widget.provideWidgetData(context, params)
            val rawContent = data.captureRawContent(context, params)
            assertNotNull(rawContent.rcDocument)
            assertTrue(rawContent.rcDocument.isNotEmpty())
        }
    }
}
```