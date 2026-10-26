## 1. GlanceWearWidget 与 GlanceWearWidgetService

每个 Wear OS widget 都需要两个类：

1. 一个 `GlanceWearWidget` 子类，重写 `provideWidgetData(context, params)` 并返回 `WearWidgetDocument`。
2. 一个带 `@AssociateWithGlanceWearWidget` 注解的 `GlanceWearWidgetService` 子类，使构建工具、linter 和 `GlanceWearWidgetManager` 能以静态方式解析 widget provider，而不必通过反射实例化。

```kotlin
import android.content.Context
import androidx.compose.remote.creation.compose.state.rc
import androidx.compose.ui.graphics.Color
import androidx.glance.wear.AssociateWithGlanceWearWidget
import androidx.glance.wear.GlanceWearWidget
import androidx.glance.wear.GlanceWearWidgetService
import androidx.glance.wear.WearWidgetBrush
import androidx.glance.wear.WearWidgetData
import androidx.glance.wear.WearWidgetDocument
import androidx.glance.wear.color
import androidx.glance.wear.core.ContainerInfo
import androidx.glance.wear.core.WearWidgetParams


@AssociateWithGlanceWearWidget(MyWidget::class)
class MyWidgetService : GlanceWearWidgetService() {
    override val widget: GlanceWearWidget = MyWidget()
}

class MyWidget : GlanceWearWidget() {
    override suspend fun provideWidgetData(
        context: Context,
        params: WearWidgetParams,
    ): WearWidgetData {
        val isLarge = params.containerType == ContainerInfo.CONTAINER_TYPE_LARGE
        return WearWidgetDocument(
            background = WearWidgetBrush.color(Color(0xFF1C1B1F).rc)
        ) {
            MyWidgetContent(isLarge = isLarge)
        }
    }
}
```

## 2. AndroidManifest.xml 注册

在
`app/src/main/AndroidManifest.xml` 中注册 `GlanceWearWidgetService` 子类。`<service>` 标签**必须**声明
`com.google.android.wearable.permission.BIND_TILE_PROVIDER` 权限和
`androidx.glance.wear.action.BIND_WIDGET_PROVIDER` intent filter。还要包含指向 `@xml/`
provider 配置文件的
`androidx.glance.wear.widget.provider` `<meta-data>`：

```xml
<service
    android:name=".snippets.widget.skill.MyWidgetService"
    android:exported="true"
    android:permission="com.google.android.wearable.permission.BIND_TILE_PROVIDER">
    <intent-filter>
        <action android:name="androidx.glance.wear.action.BIND_WIDGET_PROVIDER" />
    </intent-filter>
    <meta-data
        android:name="androidx.glance.wear.widget.provider"
        android:resource="@xml/my_widget_info" />
</service>
```

## 3. Provider XML（`res/xml/<widget_name>_info.xml`）

在 `app/src/main/res/xml/` 中创建 `<wearwidget-provider>` XML 资源，
声明 `SMALL` 和 `LARGE` 两个 `<container>` 元素，并使用 `@drawable/` 选择器
预览图：

```xml
<wearwidget-provider
    xmlns:android="http://schemas.android.com/apk/res/android"
    label="@string/app_name"
    description="@string/app_name"
    preferredType="LARGE">
    <container
        type="SMALL"
        previewImage="@drawable/my_widget_preview_small" />
    <container
        type="LARGE"
        previewImage="@drawable/my_widget_preview_large" />
</wearwidget-provider>
```

## 4. 迁移遗留的 ProtoLayout TileService

把遗留的 `androidx.wear.tiles.TileService`（或
`Material3TileService`）迁移为 Glance Wear widget 时：

1. **替换 service 与清单注册**：如果做完整替换式迁移，删除遗留的 `TileService` 类。把 `app/src/main/AndroidManifest.xml` 里遗留的 `<service>` 注册（`BIND_TILE_PROVIDER` 和 `androidx.wear.tiles.PREVIEW`）替换为 `GlanceWearWidgetService` 声明。不要删除已有的 `res/drawable*/` 图像资源，例如遗留 tile 的预览 PNG。在已有 drawable 旁边新增 `448x168` 和 `464x288` 的 `res/drawable-nodpi/` widget 选择器 PNG。要描绘迁移后 widget 的实际 UI 布局，例如带头像首字母徽章的联系人以及底部操作按钮。**绝不**用通用的 `"Small"` 或 `"Large"` 文字标签作为预览图。若要与遗留 tile 向后兼容并存，在 `<wearwidget-provider>` 上设置 `group="<FullyQualifiedLegacyTileService>"` 并添加 `androidx.wear.tiles.GROUP` `<meta-data>`。
2. **移除遗留 tile 依赖**：迁移完遗留的 `TileService` 与 ProtoLayout 代码后，从 `app/build.gradle.kts` 中移除未使用的 `androidx.wear.tiles` 和 `androidx.wear.protolayout.*` 依赖。保持现有 Android 与 Kotlin Gradle 插件配置不变。如果其他 tile、预览或 source set 仍依赖 ProtoLayout，则保留这些依赖或限定其作用范围。验证 `./gradlew :app:assembleDebug` 能在不删除无关应用功能的情况下编译通过，无报错。
