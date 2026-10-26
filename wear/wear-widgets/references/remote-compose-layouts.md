Remote Compose 在 `androidx.compose.remote.creation.compose.*` 中使用专用的
`@RemoteComposable` 布局容器、修饰符和状态包装器，并在
`androidx.wear.compose.remote.material3.*` 中使用 Material 3 组件。

## 1. 自适应容器尺寸（`SMALL` 与 `LARGE`）

在 `provideWidgetData` 中检查 `params.containerType`，区分
`ContainerInfo.CONTAINER_TYPE_SMALL`（`1x1` 卡片）和
`ContainerInfo.CONTAINER_TYPE_LARGE`（`2x1` 卡片）。针对每种容器尺寸调整布局密度、
内边距、可见行数和字体排版：

```kotlin
import androidx.compose.remote.creation.compose.layout.RemoteAlignment
import androidx.compose.remote.creation.compose.layout.RemoteArrangement
import androidx.compose.remote.creation.compose.layout.RemoteColumn
import androidx.compose.remote.creation.compose.layout.RemoteComposable
import androidx.compose.remote.creation.compose.modifier.RemoteModifier
import androidx.compose.remote.creation.compose.modifier.fillMaxSize
import androidx.compose.remote.creation.compose.modifier.padding
import androidx.compose.remote.creation.compose.state.rc
import androidx.compose.remote.creation.compose.state.rdp
import androidx.compose.remote.creation.compose.state.rs
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.wear.compose.remote.material3.RemoteText

@RemoteComposable
@Composable
fun AdaptiveCardContent(
    isLarge: Boolean,
    title: String,
    subtitle: String,
) {
    RemoteColumn(
        modifier = RemoteModifier.fillMaxSize()
            .padding(if (isLarge) 12.rdp else 6.rdp),
        verticalArrangement = RemoteArrangement.Center,
        horizontalAlignment = RemoteAlignment.CenterHorizontally,
    ) {
        RemoteText(
            text = title.rs,
            color = Color(0xFFE6E1E5).rc,
        )
        if (isLarge) {
            RemoteText(
                text = subtitle.rs,
                color = Color(0xFFD0BCFF).rc,
                modifier = RemoteModifier.padding(top = 4.rdp),
            )
        }
    }
}
```

## 2. 未遮罩的全出血背景图

当 widget 展示背景图案或照片时：

1. 在 `provideWidgetData` 中用 `BitmapFactory.decodeResource(context.resources, R.drawable.<bg_res>)` 解码 drawable。
2. 用 `RemoteImageBitmap`（`bitmap.asImageBitmap`）转换 `Bitmap`。把它作为根 `RemoteBox` 的第一个子项，用 `RemoteImage` 搭配 `RemoteModifier.fillMaxSize` 渲染。
3. **绝不** 对全出血背景应用 `CircleShape`、`RoundedCornerShape` 或手动 `cornerRadius` 裁剪。Wear OS 宿主会自动把 widget 表面遮罩成手表的圆形或方圆边框。

```kotlin
import android.graphics.Bitmap
import androidx.compose.remote.creation.compose.layout.RemoteAlignment
import androidx.compose.remote.creation.compose.layout.RemoteArrangement
import androidx.compose.remote.creation.compose.layout.RemoteBox
import androidx.compose.remote.creation.compose.layout.RemoteColumn
import androidx.compose.remote.creation.compose.layout.RemoteComposable
import androidx.compose.remote.creation.compose.layout.RemoteImage
import androidx.compose.remote.creation.compose.modifier.RemoteModifier
import androidx.compose.remote.creation.compose.modifier.fillMaxSize
import androidx.compose.remote.creation.compose.modifier.padding
import androidx.compose.remote.creation.compose.state.RemoteImageBitmap
import androidx.compose.remote.creation.compose.state.rdp
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.asImageBitmap

@RemoteComposable
@Composable
fun FullBleedBackgroundLayout(
    backgroundBitmap: Bitmap?,
    isLarge: Boolean,
    content: @RemoteComposable @Composable () -> Unit,
) {
    RemoteBox(modifier = RemoteModifier.fillMaxSize()) {
        if (backgroundBitmap != null) {
            RemoteImage(
                remoteBitmap =
                    RemoteImageBitmap(backgroundBitmap.asImageBitmap()),
                contentDescription = null,
                modifier = RemoteModifier.fillMaxSize(),
            )
        }
        RemoteColumn(
            modifier = RemoteModifier.fillMaxSize()
                .padding(if (isLarge) 12.rdp else 6.rdp),
            verticalArrangement = RemoteArrangement.Center,
            horizontalAlignment = RemoteAlignment.CenterHorizontally,
        ) {
            content()
        }
    }
}
```

## 3. 响应式多项目网格与行

把 `RemoteColumn` 和 `RemoteRow` 与 `RemoteArrangement.spacedBy` 结合，用于
排列头像、快捷操作或状态徽章，并配一个底部操作按钮。
在 `SMALL` 容器中显示更少的项目，在 `LARGE` 容器中显示完整网格。
把每个项目包进 `.clickable(onItemClick)` 容器，让 `RemoteImage`
和回退的 `RemoteText` 两个分支都能响应点击：

```kotlin
import android.graphics.Bitmap
import androidx.compose.remote.creation.compose.action.Action
import androidx.compose.remote.creation.compose.layout.RemoteAlignment
import androidx.compose.remote.creation.compose.layout.RemoteArrangement
import androidx.compose.remote.creation.compose.layout.RemoteBox
import androidx.compose.remote.creation.compose.layout.RemoteColumn
import androidx.compose.remote.creation.compose.layout.RemoteComposable
import androidx.compose.remote.creation.compose.layout.RemoteImage
import androidx.compose.remote.creation.compose.layout.RemoteRow
import androidx.compose.remote.creation.compose.modifier.RemoteModifier
import androidx.compose.remote.creation.compose.modifier.background
import androidx.compose.remote.creation.compose.modifier.clickable
import androidx.compose.remote.creation.compose.modifier.fillMaxSize
import androidx.compose.remote.creation.compose.modifier.padding
import androidx.compose.remote.creation.compose.modifier.size
import androidx.compose.remote.creation.compose.state.RemoteImageBitmap
import androidx.compose.remote.creation.compose.state.rc
import androidx.compose.remote.creation.compose.state.rdp
import androidx.compose.remote.creation.compose.state.rs
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.wear.compose.remote.material3.RemoteButton
import androidx.wear.compose.remote.material3.RemoteText

@RemoteComposable
@Composable
fun GridWithBottomActionLayout(
    items: List<Pair<String, Bitmap?>>,
    isLarge: Boolean,
    onItemClick: Action,
    onMoreClick: Action,
) {
    val visibleItems = if (isLarge) items.take(6) else items.take(3)
    val rows = visibleItems.chunked(3)

    RemoteColumn(
        modifier = RemoteModifier.fillMaxSize().padding(8.rdp),
        verticalArrangement = RemoteArrangement.Center,
        horizontalAlignment = RemoteAlignment.CenterHorizontally,
    ) {
        for (rowItems in rows) {
            RemoteRow(
                horizontalArrangement = RemoteArrangement.spacedBy(8.rdp),
                verticalAlignment = RemoteAlignment.CenterVertically,
            ) {
                for ((label, avatar) in rowItems) {
                    RemoteBox(
                        modifier = RemoteModifier.size(36.rdp)
                            .background(Color(0xFF4F378B).rc)
                            .clickable(onItemClick),
                        contentAlignment = RemoteAlignment.Center,
                    ) {
                        if (avatar != null) {
                            RemoteImage(
                                remoteBitmap =
                                    RemoteImageBitmap(avatar.asImageBitmap()),
                                contentDescription = label.rs,
                                modifier = RemoteModifier.fillMaxSize(),
                            )
                        } else {
                            RemoteText(text = label.rs, color = Color.White.rc)
                        }
                    }
                }
            }
        }
        RemoteButton(
            onClick = onMoreClick,
            modifier = RemoteModifier.padding(top = 6.rdp),
        ) {
            RemoteText(text = "More".rs)
        }
    }
}
```
