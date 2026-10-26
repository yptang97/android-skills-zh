---
name: wear-widgets
description: 在 Android 项目中使用 Glance Wear 与 Remote Compose 创建、迁移、更新和验证 Wear OS widget。
  在实现 GlanceWearWidget、GlanceWearWidgetService、WearWidgetDocument、Remote Compose UI 基础组件
  （RemoteColumn、RemoteRow、RemoteBox、RemoteText、RemoteImage、RemoteButton）、
  使用 rememberMutableRemoteInt 与 valueChange 管理本地状态、使用 pendingIntentAction 处理点击操作、
  配置 widget provider XML 容器（SMALL 和 LARGE）、为矩形 widget 选择器准备 PNG 预览图，
  或把遗留的 ProtoLayout TileService tile 迁移为 Wear OS widget 时使用这个 skill。
  不要用于移动端主屏幕的 AppWidgetProvider 或 GlanceAppWidget 实现、表盘 complication，
  或全屏的 Wear OS activity。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-16'
  keywords:
  - Wear OS
  - Widgets
  - GlanceWearWidget
  - Remote Compose
  - TileService
---

Wear OS widget 使用 `androidx.glance.wear`（`GlanceWearWidget` 与
`GlanceWearWidgetService`）配合 `androidx.compose.remote`（Remote Compose）。
它们把声明式 UI 与状态文档序列化到手表端宿主进程。

## 前置条件与配置

1. **确定库版本**：确定 `{GLANCE_WEAR_VERSION}`（`androidx.glance.wear`）、`{COMPOSE_REMOTE_VERSION}`（`androidx.compose.remote`）与 `{WEAR_COMPOSE_REMOTE_VERSION}`（`androidx.wear.compose.remote`）的最新版本。如果还没有稳定版本，就纳入 `-alpha`、`-beta` 或 `-rc` 版本。不要用 `./gradlew dependencies` 来确定版本：
   - 如果有可用的依赖查询工具，就使用它。
   - 否则，从 Google Maven 元数据获取最新版本（[Glance Wear 元数据](https://dl.google.com/dl/android/maven2/androidx/glance/wear/wear/maven-metadata.xml)、[Compose Remote 元数据](https://dl.google.com/dl/android/maven2/androidx/compose/remote/remote-creation-compose/maven-metadata.xml)、[Wear Compose Remote 元数据](https://dl.google.com/dl/android/maven2/androidx/wear/compose/remote/remote-material3/maven-metadata.xml)）。
2. **SDK 与 Compose 编译器要求**：除非用户要求创建 widget、迁移 tile 或配置依赖，否则修改仓库级 Gradle 文件前要先征得许可。设置 `compileSdk = 37` 或更高，并启用 `buildFeatures { compose = true }`。保持项目已有的 Android 与 Kotlin Gradle 插件声明不变。

    dependencies {
        implementation("androidx.glance.wear:wear:{GLANCE_WEAR_VERSION}")
        implementation("androidx.glance.wear:wear-core:{GLANCE_WEAR_VERSION}")
        implementation("androidx.glance.wear:wear-tooling-preview:{GLANCE_WEAR_VERSION}")
        implementation("androidx.compose.remote:remote-creation-compose:{COMPOSE_REMOTE_VERSION}")
        implementation("androidx.compose.remote:remote-creation:{COMPOSE_REMOTE_VERSION}")
        implementation("androidx.compose.remote:remote-core:{COMPOSE_REMOTE_VERSION}")
        implementation("androidx.compose.remote:remote-tooling-preview:{COMPOSE_REMOTE_VERSION}")
        implementation("androidx.wear.compose.remote:remote-material3:{WEAR_COMPOSE_REMOTE_VERSION}")
    }

## 代码库探查

1. 在模块中搜索已有的 `TileService`、`Material3TileService` 或 `GlanceWearWidget` 实现、`app/src/main/AndroidManifest.xml` 中的 `<service>` 条目，以及 `app/src/main/res/` 下的 `@drawable/` 预览资源。
2. 迁移已有 tile 或修改不熟悉的多模块项目时，运行 `./gradlew :app:assembleDebug` 验证基线构建健康状况。

## 工作流

### 步骤 1：配置 AndroidManifest.xml 与 provider XML

在
`app/src/main/AndroidManifest.xml` 中注册 `GlanceWearWidgetService` 子类，声明
`BIND_TILE_PROVIDER` 权限和
`BIND_WIDGET_PROVIDER` intent action。挂上指向
`@xml/` `<wearwidget-provider>` 资源的 `<meta-data>`，该资源包含 `SMALL` 与 `LARGE` 两类 `<container>`
条目。配置 service、provider XML 或迁移遗留 `TileService` 时，
你必须遵循 [Widget service 与清单参考](references/widget-service-and-manifest.md)。

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

### 步骤 2：实现 GlanceWearWidget 与 GlanceWearWidgetService

继承 `GlanceWearWidget` 并重写 `provideWidgetData`，返回
`WearWidgetDocument`。给 `GlanceWearWidgetService` 子类加
`@AssociateWithGlanceWearWidget` 注解，以实现静态 provider 解析：

```kotlin
// WRONG: Mobile GlanceAppWidget API (don't use on Wear OS)
class BrokenWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {}
}

// CORRECT: Wear OS GlanceWearWidget + GlanceWearWidgetService
@AssociateWithGlanceWearWidget(MyWidget::class)
class MyWidgetService : GlanceWearWidgetService() {
    override val widget: GlanceWearWidget = MyWidget()
}

class MyWidget : GlanceWearWidget() {
    override suspend fun provideWidgetData(
        context: Context,
        params: WearWidgetParams,
    ): WearWidgetData =
        WearWidgetDocument(
            background = WearWidgetBrush.color(Color(0xFF1C1B1F).rc)
        ) {
            MyWidgetContent(params = params)
        }
}
```

### 步骤 3：构建 Remote Compose 布局、状态与操作

Remote Compose 在 Wear OS 宿主进程中求值 UI 与状态，
而不是在应用进程中。构建自适应布局或全出血背景时，
你必须遵循 [Remote Compose 布局参考](references/remote-compose-layouts.md)。实现状态
或点击操作时，你必须遵循 [状态与操作参考](references/state-and-actions.md)。

- **远程值包装**：用 `.rs`（`RemoteString`）、`.rc`（`RemoteColor`）、`.rdp`（`RemoteDp`）和 `.ri`（`RemoteInt`）转换基本类型。整数用 `RemoteInt.toRemoteString` 成员方法格式化。
- **自适应容器尺寸**：根据 `params.containerType`（`ContainerInfo.CONTAINER_TYPE_SMALL` 与 `ContainerInfo.CONTAINER_TYPE_LARGE`）分支处理布局密度、排版与条目数量。
- **无遮罩的全出血背景**：在根 `RemoteBox`（`RemoteModifier.fillMaxSize`）中用 `RemoteImage` 和 `RemoteImageBitmap`（`bitmap.asImageBitmap`）渲染背景位图。保持背景图层不被遮蔽（`cornerRadius = 0dp`），不要用 `CircleShape` 或 `RoundedCornerShape` 裁剪。宿主会把边缘裁成手表形状。
- **声明式宿主状态与 PendingIntent 操作**：用 `rememberMutableRemoteInt` 和 `valueChange(state, newValue)` 修改 widget 本地状态，而不是用内存中的 Compose 状态（`mutableStateOf` 或 `mutableIntStateOf`）。用 `pendingIntentAction { ctx -> ... }` 触发页面启动或后台广播（始终传入 `(Context) -> PendingIntent` lambda）。用 `widget.triggerUpdateAll(context)` 刷新活跃 widget。

### 步骤 4：添加 WearWidgetPreview 函数与选择器预览 PNG

1. **Composable 边框预览（`androidx.glance.wear.tooling.preview`）**：从 `androidx.glance.wear.tooling.preview` 导入 `WearWidgetPreview`、`SquircleAllWidgetPreviewParams`、`RoundAllWidgetPreviewParams` 和 `RectangularAllWidgetPreviewParams`（**绝不**从 `androidx.glance.wear.testing` 导入）。定义调用 `WearWidgetPreview(widget, params)` 的 `@Preview` 函数。
2. **矩形选择器 PNG（`res/drawable-nodpi/`）**：为 provider XML 中每个 `<container>` 使用 `320 dpi` 下的 `RectangularAllWidgetPreviewParams`，或渲染非空白、无遮罩的矩形 PNG：
   - `SMALL`（`CONTAINER_TYPE_SMALL`）：**`448x168` px**（320 dpi 下为 `224x84` dp，宽高比 `2.67`）。
   - `LARGE`（`CONTAINER_TYPE_LARGE`）：**`464x288` px**（320 dpi 下为 `232x144` dp，宽高比 `1.61`）。
   - 每张预览 PNG **必须**呈现该 widget 真实的 UI 元素，包括背景、文字标签、图标、头像首字母和按钮。**绝不**使用空白占位图、无标签的空形状或 1:1 的 tile 预览图。添加 composable 预览、选择器 PNG 或单元测试时，你必须遵循 [预览与测试参考](references/previews-and-testing.md)。

## 组件映射

用下面这张示例表查看完整的实现模式与导入：

| 能力或 API 面 | 参考指南 |
|---|---|
| `GlanceWearWidget`、`GlanceWearWidgetService`、`AndroidManifest.xml`、`<wearwidget-provider>`、遗留 `TileService` 迁移 | [Widget service 与清单参考](references/widget-service-and-manifest.md) |
| `RemoteBox`、`RemoteColumn`、`RemoteRow`、`RemoteText`、`RemoteImage`、`ContainerInfo`（`SMALL` 与 `LARGE` 自适应布局） | [Remote Compose 布局参考](references/remote-compose-layouts.md) |
| `RemoteButton`、`rememberMutableRemoteInt`、`valueChange`、`pendingIntentAction`、`BroadcastReceiver`、`triggerUpdateAll` | [状态与操作参考](references/state-and-actions.md) |
| `WearWidgetPreview`、`SquircleAllWidgetPreviewParams`、`RoundAllWidgetPreviewParams`、`RectangularAllWidgetPreviewParams`、选择器 PNG、`captureRawContent` 测试 | [预览与测试参考](references/previews-and-testing.md) |

### 遗留 ProtoLayout 与移动端 Glance 的对应关系

| 遗留或移动端 API | Wear OS widget API | 应采取的操作 |
|---|---|---|
| `androidx.wear.tiles.TileService` | `GlanceWearWidgetService` + `GlanceWearWidget` | 替换 service 并加上 `@AssociateWithGlanceWearWidget`。 |
| `GlanceAppWidget` / `provideGlance` | `GlanceWearWidget` / `provideWidgetData` | 从 `provideWidgetData` 返回 `WearWidgetDocument`。 |
| `LayoutElementBuilders` / `primaryLayout` | `RemoteColumn`、`RemoteRow`、`RemoteBox` | 用 `@RemoteComposable` 函数构建布局。 |
| `mutableStateOf` / `mutableIntStateOf` | `rememberMutableRemoteInt` + `valueChange` | 用 `valueChange` 以声明式方式修改远程状态。 |
| `ModifiersBuilders.Clickable` | `RemoteModifier.clickable(pendingIntentAction { ... })` | 给 `pendingIntentAction` 传入 `(Context) -> PendingIntent` lambda。 |

## 故障排查

| 症状 | 原因 | 修复 |
|---|---|---|
| 找不到符号 `GlanceWearWidget` | 缺少 `androidx.glance.wear:wear:{GLANCE_WEAR_VERSION}` 或 `compileSdk` 过低 | 设置 `compileSdk = 37` 并添加 `androidx.glance.wear:wear:{GLANCE_WEAR_VERSION}`。 |
| 找不到符号 `toRemoteString` | 把 `toRemoteString` 当作顶层扩展导入了 | 移除该导入；以成员方法方式调用 `remoteInt.toRemoteString`。 |
| `pendingIntentAction` 类型不匹配 | 传入了裸 `PendingIntent` 而不是 lambda | 用 lambda 包装：`pendingIntentAction { ctx -> pendingIntent }`。 |
| 迁移后 `wear.tiles` 或 `protolayout` 引用无法解析 | 模块中其他类或 source set 仍在使用遗留 tile API | 在从 `build.gradle.kts` 移除遗留 `wear.tiles` 和 `protolayout` 依赖之前，先迁移或更新剩余的引用。 |

## 验证

1. 运行 `./gradlew :app:assembleDebug`，验证 widget、service、`AndroidManifest.xml` 声明以及 `@xml/` 的 `<wearwidget-provider>` 资源能编译链接且无报错。
2. 如果项目包含单元测试或新的 widget 测试，运行 `./gradlew :app:testDebugUnitTest` 并确认所有测试通过。添加 composable 预览、选择器 PNG 或单元测试时，你必须遵循 [预览与测试参考](references/previews-and-testing.md)。

## 反模式

- **绝不**为 Wear OS widget 继承移动端的 `GlanceAppWidget` 或 `AppWidgetProvider`，也不要使用已废弃的 `GlanceTileService` 或 `TileService`。
- **绝不**为 Remote Compose UI 使用内存中的客户端 Compose 状态（`mutableStateOf`、`mutableIntStateOf`）或进程内点击 lambda。
- **绝不**把裸 `PendingIntent` 实例传给 `pendingIntentAction`；始终传入 `(Context) -> PendingIntent` lambda。
- **绝不**对全出血 widget 背景图层应用 `CircleShape` 或 `RoundedCornerShape` 裁剪。**绝不**把 1:1（`400x400`）的 tile 预览图或空白纯色占位图复用作 widget 选择器 PNG。

## 最佳实践

- **必须**在 `<service>` 上声明 `com.google.android.wearable.permission.BIND_TILE_PROVIDER` 和 `androidx.glance.wear.action.BIND_WIDGET_PROVIDER`。
- **必须**在 `@xml/` 中声明 `SMALL` 和 `LARGE` 的 `<container>` 条目，并在 `res/drawable-nodpi/` 中提供符合领域实际尺寸的 `448x168` 与 `464x288` PNG。
- **必须**让布局内容适配 `params.containerType`，并为 `SquircleAllWidgetPreviewParams` 和 `RoundAllWidgetPreviewParams` 都提供 `@Preview` 函数。
