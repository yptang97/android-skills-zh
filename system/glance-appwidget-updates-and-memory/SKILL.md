---
name: glance-appwidget-updates-and-memory
description: 管理 Android AppWidget 的状态更新、后台同步，以及用 Jetpack Glance
  （androidx.glance:glance-appwidget）和 AppWidgetProvider receiver 在 Android 17（API 37）
  上处理 RemoteViews bitmap 内存限制。在以下情况使用这个 skill：配置 Android 17（API level 37）
  的 compileSdk/targetSdk 与 AndroidManifest.xml widget receiver；在 CoroutineWorker 完成
  DataStore 偏好更新（updateAppWidgetState）后刷新冻结或过期的 Glance widget UI；为
  SizeMode.Responsive、SizeMode.Exact 或 LazyColumn 把图像降采样到 WindowMetrics 内存限制之内；
  用 FileProvider 分享 content:// URI；或用 WorkManager 修复 ActionCallback NoSuchMethodException
  与 AppWidgetProvider ForegroundServiceStartNotAllowedException 崩溃。不要用于 Glance 布局模板
  （建议改用 glance-canonical-layouts skill）或应用内的 Compose 屏幕。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-23'
  keywords:
  - Android
  - AppWidget
  - Glance
  - GlanceAppWidget
  - GlanceAppWidgetReceiver
  - AppWidgetProvider
  - RemoteViews
  - widget memory limit
  - WindowMetrics
  - bitmap memory
  - SizeMode.Responsive
  - LazyColumn
  - ImageProvider
  - updateAppWidgetState
  - ActionCallback
  - NoSuchMethodException
  - R8
  - ForegroundServiceStartNotAllowedException
  - WorkManager
  - CoroutineWorker
  - FileProvider
  - Android 17
  - API 37
---

这个 skill 提供指导，帮你管理状态更新，并让使用 Jetpack Glance（`androidx.glance:glance-appwidget`）或
`RemoteViews` 的 Android AppWidget 不超出 Android 17 的 widget bitmap 内存限制。如果是 widget UI
布局模板，建议改用 `glance-canonical-layouts` skill。

- 配置 Glance widget 时，见 [用 Glance 创建 app widget](references/android/develop/ui/compose/glance/create-app-widget.md)。
- 以 Android 17 为目标（`targetSdk = 37`）时，见 [Android 17 widget 内存限制](references/android/about/versions/17/behavior-changes-17.md)。
- 维护经典 `AppWidgetProvider` 时，见 [创建 app widget](references/android/develop/ui/views/appwidgets/index.md)。

## 前置条件

- Kotlin Android 项目（`minSdk >= 26`），在 `build.gradle.kts` 中设置 `compileSdk = 37`（以 Android 17 为目标时设 `targetSdk = 37`）。
- Jetpack Glance（`1.2.0`，最低 `1.1.1+`），并在模块上启用 Compose 编译器 Gradle 插件。

## 关键要求

- **保留现有包名和工具链版本**：先检查 `build.gradle.kts`、`gradle/libs.versions.toml` 和 Kotlin 文件。保留现有的 `namespace`、`applicationId`、`package`、`targetSdk`（除非正在迁移到 Android 17）、Android Gradle Plugin（AGP）和 Kotlin 版本。
- **把图像降采样到 widget 尺寸并估算内存上限**：Android `system_server` 在启动时按默认显示器的真实尺寸一次性计算 `RemoteViews` bitmap 内存上限（`6 *
  width * height` 字节，或 `1.5 * 4 * width * height`），并且不通过公开 API 暴露该上限。由于启动后展开折叠屏或把显示分辨率切到 `QHD+` 会让活动窗口指标报告比启动时上限更大的值，始终先把每张图像降采样到 widget 的目标尺寸（`maxWidthDp x maxHeightDp`，使用 `RGB_565` 或 `ALPHA_8`），并强制执行单图字节上限（`calculateWidgetMemoryCapBytes(context) /
  distinctImageCount`），该上限在 API 30+ 上按 `WindowManager.currentWindowMetrics.bounds` 估算为 `6 * width * height`（在 API 26-29 或 `WindowManager` 不可用时回退到 `resources.displayMetrics`）。
- **在 provideContent 之外一次性解码共享 bitmap**：`SizeMode.Exact`（供 `glance-canonical-layouts` 组合当前 span 的竖屏和横屏方向）和 `SizeMode.Responsive`（用于预打包一组 `DpSize` 断点）都会在每次更新时多次调用 `provideContent`。在 `provideContent` 之前的 `provideGlance` 中一次性解码共享 bitmap，并把它们传给 `ImageProvider(bitmap)`，这样在任一模式下 `RemoteViews` 都会跨所有尺寸去重共享的 `Bitmap`。如果 widget 按 `LocalSize.current` 缩放不同的 bitmap，就用不同 bitmap 的数量去除 `calculateWidgetMemoryCapBytes(context)`。
- **降采样 content URI 并授予启动器读取权限**：在 Android 17（`targetSdk >= 37`）上，由 bitmap 支持的 `Icon` 会和 `Bitmap` 一起计入上限。传给 `ImageProvider(uri)` 或 `RemoteViews.setImageViewUri` 的 `content://` URI 不计入进程间通信（IPC）上限，但启动器会以全分辨率解码它们。把文件降采样后写入 `context.cacheDir`，用 `FileProvider.getUriForFile` 暴露它，并把 `Intent.FLAG_GRANT_READ_URI_PERMISSION` 授予 `Intent.CATEGORY_HOME` 包。
- **状态变更后显式触发 widget 更新**：`updateAppWidgetState` 把偏好写入 DataStore，但不会更新 widget UI。改变状态后，调用 `GlanceAppWidget.update(context,
  glanceId)` 或 `GlanceAppWidget.updateAll(context)`。
- **替换图像时使用完整的 updateAppWidget 调用**：在 `AppWidgetProvider` 类中替换 bitmap 或 `Icon` 时，调用 `AppWidgetManager.updateAppWidget` 而不是 `partiallyUpdateAppWidget`。

## 参考实现文件

实现每一步时，读 `references/` 下的配套参考文件，
并把示例的 `package` 声明和类名改成本应用自己的：

- **Bitmap 上限 \& FileProvider 辅助类**：[WidgetBitmapUtils.kt](references/WidgetBitmapUtils.kt)
- **响应式 widget、Receiver \& 错误回退**：[SampleGlanceWidget.kt](references/SampleGlanceWidget.kt)
- **LazyColumn 集合 widget \& 版本缓存**：[FeedCollectionGlanceWidget.kt](references/FeedCollectionGlanceWidget.kt)
- **DataStore 状态推送、CoroutineWorker \& ActionCallback**：[WidgetStateAndActions.kt](references/WidgetStateAndActions.kt)
- **经典 AppWidgetProvider、WorkManager \& 完整更新**：[ClassicWidgetImageUpdater.kt](references/ClassicWidgetImageUpdater.kt)
- **清单、Widget 信息、FileProvider 路径 \& R8 规则**：[AndroidManifest.xml](references/AndroidManifest.xml)、[sample_widget_info.xml](references/res/xml/sample_widget_info.xml)、[file_paths.xml](references/res/xml/file_paths.xml)、[proguard-rules.pro](references/proguard-rules.pro)

## 详细步骤

### 步骤 1：配置 SDK 级别、依赖和清单声明

1. 先读 `gradle/libs.versions.toml`、`app/build.gradle.kts` 和 `app/src/main/AndroidManifest.xml`。如果已有 AGP、Kotlin 或库版本，保留它们；否则把 `glance = "1.2.0"` 以及 `androidx.glance:glance-appwidget` 和 `androidx.glance:glance-material3` 添加到 `gradle/libs.versions.toml`。
2. 在 `app/build.gradle.kts` 中，保留 `namespace`、`applicationId` 以及任何现有的 `minSdk >= 26`、`targetSdk` 或库版本。设置 `compileSdk = 37`（仅当明确把应用迁移到以 Android 17 为目标时才设 `targetSdk = 37`），启用 `buildFeatures { compose = true }`，并添加 `implementation(libs.androidx.glance.appwidget)` 和 `implementation(libs.androidx.glance.material3)`。
3. 在 `AndroidManifest.xml`（见 [AndroidManifest.xml](references/AndroidManifest.xml)）中，声明 `<queries>`，其中包含 `<action android:name="android.intent.action.MAIN" />` 和 `<category
   android:name="android.intent.category.HOME" />`，以便 `queryIntentActivities` 在 API 30+ 上能发现启动器包。注册你的 `GlanceAppWidgetReceiver`（把 `android.appwidget.provider` 指向 `@xml/sample_widget_info`，见 [sample_widget_info.xml](references/res/xml/sample_widget_info.xml)），并注册 `androidx.core.content.FileProvider`，配置 `android:authorities="${applicationId}.fileprovider"`、`android:exported="false"`、`android:grantUriPermissions="true"`，以及指向 `@xml/file_paths` 的 `android.support.FILE_PROVIDER_PATHS`（该文件声明 `<cache-path name="widget_cache" path="widget_images/" />`，见 [file_paths.xml](references/res/xml/file_paths.xml)）：

<br />

```xml
<receiver android:name=".glance.MyReceiver"
    android:exported="true">
    <intent-filter>
        <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
    </intent-filter>
    <meta-data
        android:name="android.appwidget.provider"
        android:resource="@xml/my_app_widget_info" />
</receiver>
```

<br />

### 步骤 2：估算 widget 内存上限并降采样图像

读 [WidgetBitmapUtils.kt](references/WidgetBitmapUtils.kt) 并实现内存上限与降采样
辅助函数：

1. **估算上限（`calculateWidgetMemoryCapBytes`）**：在 API 30+（`Build.VERSION.SDK_INT >= Build.VERSION_CODES.R`）上，读取 `val bounds =
   context.getSystemService(WindowManager::class.java)?.currentWindowMetrics?.bounds`，并在 `bounds != null && bounds.width() > 0 && bounds.height() > 0` 时返回 `6L * bounds.width().toLong() * bounds.height().toLong()`（在 API 30+ 上，从非 UI 的 widget 或 worker `Context` 调用 `WindowManager` 会记录一条非致命的 `StrictMode` 违规，这对该估算来说是预期行为）。在 API 26-29（或 `WindowManager` 不可用）时，回退到 `context.resources.displayMetrics`（`6L * dm.widthPixels.toLong() *
   dm.heightPixels.toLong()`）。由于 `system_server` 在启动时一次性缓存 `6 * width *
   height`，始终先把图像尺寸限制为 widget 的 `maxWidthDp x
   maxHeightDp`（阶段 1），而不是填满整个屏幕预算。
2. **分两阶段降采样（`decodeDownsampledWidgetBitmap`）**：
   - 先用 `BitmapFactory.Options().apply {
     inJustDecodeBounds = true; inPreferredConfig = config }` 探测尺寸，并在 `(bounds.outWidth / (sampleSize * 2) >=
     targetWidthPx && bounds.outHeight / (sampleSize * 2) >= targetHeightPx) ||
     (bounds.outWidth / sampleSize > targetWidthPx * 2) || (bounds.outHeight /
     sampleSize > targetHeightPx * 2)` 成立时把 `sampleSize *= 2` 加倍（其中 `targetWidthPx = max(1,
     (maxWidthDp * density).toInt())`），这样当某一轴已经放得下时，宽横幅或高截图也不会绕过降采样。
   - 然后在 `(max(1, bounds.outWidth /
     sampleSize).toLong() * max(1, bounds.outHeight / sampleSize).toLong() *
     bytesPerPixel) > perImageCapBytes` 成立时把 `sampleSize *= 2` 加倍，以强制执行单图字节上限（`perImageCapBytes =
     calculateWidgetMemoryCapBytes(context) / max(1, distinctImageCount)`）。对 `Bitmap.Config.RGB_565`（不透明照片）用每像素 `2L` 字节，对 `Bitmap.Config.ALPHA_8` 掩码用 `1L`，以及在 `bounds.outConfig != null && bounds.outConfig !=
     config` 时用 `4L`（因为 `BitmapFactory` 会把半透明 PNG 或 WebP 文件从 `RGB_565` 升级为 4 字节的 `ARGB_8888`）。用 `inSampleSize =
     sampleSize` 和 `inPreferredConfig = config` 解码。
3. **在内存 `Bitmap` 与 `FileProvider` `Uri`
   （`cacheWidgetImageUri`）之间选择**：在内存中直接传 bitmap 时，用 `decodeDownsampledWidgetBitmap` 配合 `androidx.glance.ImageProvider(bitmap)`。当 widget 把 `content://` `Uri` 传给 `ImageProvider(uri)` 或 `RemoteViews.setImageViewUri` 时，用 `cacheWidgetImageUri`：它把降采样后的 bitmap 写入 `File(context.cacheDir, "widget_images")`，用 `FileProvider.getUriForFile(context,
   "${context.packageName}.fileprovider", outFile)` 取得 `content://` URI，查询 `Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)`，并调用 `context.grantUriPermission(pkg, uri,
   Intent.FLAG_GRANT_READ_URI_PERMISSION)`。

### 步骤 3：去重多尺寸 bitmap 并处理组合错误

读 [SampleGlanceWidget.kt](references/SampleGlanceWidget.kt) 以配置多尺寸 bitmap 去重和
组合错误恢复：

1. **为布局选择 `SizeMode`**：使用 `SizeMode.Exact`（用 `glance-canonical-layouts` 渲染当前网格 span 的竖屏和横屏方向的确切 `LocalSize.current` 尺寸时推荐）、`SizeMode.Responsive(RESPONSIVE_BUCKETS)`（用 `import
   androidx.compose.ui.unit.DpSize` 和 `import androidx.compose.ui.unit.dp` 预打包固定 `DpSize` 断点，例如 `setOf(DpSize(120.dp, 120.dp),
   DpSize(240.dp, 120.dp), DpSize(240.dp, 240.dp))`，这样尺寸变化过渡不会唤醒应用进程），或 `SizeMode.Single`（用于单一布局）。
2. **在 `provideContent` 之前提升共享 bitmap 解码**：由于 `SizeMode.Exact`（`2-4` 个方向尺寸）和 `SizeMode.Responsive`（`N` 个桶）都会在每次更新时多次运行 `provideContent`，在 `provideContent` **之前**的 `provideGlance` 中用 `decodeDownsampledWidgetBitmap` 和 `Bitmap.Config.RGB_565` 一次性解码共享 bitmap（不透明图像用 `distinctImageCount = 1`）。把得到的 `Bitmap` 传给 `androidx.glance.ImageProvider(sharedBitmap)`，这样 `RemoteViews` 会跨所有尺寸去重共享的 `Bitmap`。
3. **提供零 bitmap 的错误回退**：重写 `onCompositionError(context, glanceId, appWidgetId, throwable)`，并用仅文字的 `RemoteViews` 布局（`0` 个 bitmap）调用 `AppWidgetManager.getInstance(context).updateAppWidget(appWidgetId,
   fallback)`。

### 步骤 4：预解码 LazyColumn 集合图像并分配稳定的 itemId

用 `LazyColumn` 渲染集合 widget 时，读 [FeedCollectionGlanceWidget.kt](references/FeedCollectionGlanceWidget.kt)：

1. 把 `import androidx.glance.appwidget.ImageProvider`（接受 `Uri`）换成 `import androidx.glance.ImageProvider`（接受 `Bitmap`）。移除 `Uri.fromFile` 和 `Icon.createWithContentUri` 调用。
2. Glance 会话活跃期间（更新后 \~45 秒），`.update()` 和 `.updateAll()` 不会重启 `provideGlance`。在 `provideContent` 之前的 `provideGlance` 中声明 `var
   cachedRevision = -1` 和 `var cachedThumbnails = emptyMap<String, Bitmap>()`。在 `provideContent` 内部读取 `val revision = currentState<Preferences>()[KEY_REVISION] ?: 0`，并且只在 `revision != cachedRevision` 时更新 `cachedRevision = revision`，并用 `cachedThumbnails =
   feedItems.mapNotNull { item -> decodeDownsampledWidgetBitmap(...,
   distinctImageCount = max(1, feedItems.size), config =
   Bitmap.Config.RGB_565)?.let { item.id to it } }.toMap()` 解码 `feedItems` 缩略图（用 `mapNotNull` 而不是 `associate`，让 map 保持为 `Map<String, Bitmap>` 而不是 `Map<String, Bitmap?>`）。这样在活跃会话期间 DataStore 状态更新时会重新解码，同时在所有 `SizeMode.Responsive` 桶之间共享同一份已解码的 `Map<String, Bitmap>`。
3. 在 `LazyColumn` 中，给 `items(items = feedItems,
   itemId = { item -> item.id.hashCode().toLong() })` 传入稳定的 `Long` `itemId`（有持久数字 ID 时优先用它），并只在 `bitmap !=
   null` 时渲染 `Image(provider =
   ImageProvider(bitmap), contentDescription = item.title)`（绝不要在 `else` 分支回退到 `Uri.fromFile`）。

### 步骤 5：推送状态更新、配置 ActionCallback 并使用 WorkManager

读 [WidgetStateAndActions.kt](references/WidgetStateAndActions.kt)、[proguard-rules.pro](references/proguard-rules.pro) 和
[ClassicWidgetImageUpdater.kt](references/ClassicWidgetImageUpdater.kt) 以实现以下模式：

1. **推送 DataStore 更新**（需要 `androidx.datastore:datastore-preferences-core:1.2.1` 以及 `import
   androidx.glance.appwidget.GlanceAppWidgetManager`、`import
   androidx.glance.appwidget.state.updateAppWidgetState` 和 `import
   androidx.glance.appwidget.updateAll`）：在 `pushWidgetRevisionUpdate(context)`（见 [WidgetStateAndActions.kt](references/WidgetStateAndActions.kt)）中，遍历 `for (glanceId in
   GlanceAppWidgetManager(context).getGlanceIds(Widget::class.java))`，在 `updateAppWidgetState(context, glanceId) { prefs -> ... }` 内部变更状态（同时传 `context` 和 `glanceId`），并立刻调用 `widget.update(context, glanceId)`（或 `widget.updateAll(context)`）。
2. **使用零参数 `ActionCallback` 类，配合 `ActionParameters.Key`，并在 R8 下保留 `<init>()`**（调度后台工作时需要 `androidx.work:work-runtime-ktx:2.12.0`）：`RunCallbackAction` 用 `Class.getDeclaredConstructor().newInstance()` 实例化 `ActionCallback` 类，因此带构造参数在任何构建中都会失败。移除 `ActionCallback` 实现里的构造参数，用 `ActionParameters.Key` 和 `actionParametersOf` 传值（见 [WidgetStateAndActions.kt](references/WidgetStateAndActions.kt) 中的 `RefreshWidgetAction`），并把 `-keep class * implements
   androidx.glance.appwidget.action.ActionCallback { public <init>(); }` 加到 `proguard-rules.pro`（见 [proguard-rules.pro](references/proguard-rules.pro)）。在 `SyncWidgetWorker.doWork()` 内调用 `pushWidgetRevisionUpdate(applicationContext)`，让后台工作更新 DataStore 并刷新 widget。
3. **避免在 `AppWidgetProvider.onUpdate` 中无条件入队一次性
   `WorkManager` 任务，并对图像使用完整的 `updateAppWidget`**（见 [ClassicWidgetImageUpdater.kt](references/ClassicWidgetImageUpdater.kt)）：绝不要从 `AppWidgetProvider.onReceive` 或 `onUpdate` 调用 `context.startForegroundService`（会抛 `ForegroundServiceStartNotAllowedException`）。`GlanceAppWidgetReceiver` 内部已经保持一个延迟 10 年的会话 worker 处于入队状态，所以 WorkManager 的 `RescheduleReceiver` 永远不会切换。在经典 `AppWidgetProvider` 中，避免直接在 `onUpdate` 里入队 `OneTimeWorkRequest`：即使使用 `ExistingWorkPolicy.KEEP`，一旦一次性 worker 结束（`SUCCEEDED`），`UnfinishedWorkListener` 就会禁用 `RescheduleReceiver`，而后者会广播 `ACTION_PACKAGE_CHANGED` 并循环重新触发 `onUpdate`。改为在 `onUpdate` 中用 `enqueueUniquePeriodicWork(...,
   ExistingPeriodicWorkPolicy.KEEP, ...)` 调度周期性同步（它在多次运行之间保持 `ENQUEUED`），对 `< 10s` 的短更新使用 `goAsync()`，或仅在 `onReceive` 中由特定 action 广播时入队一次性工作（`enqueueUniqueWork(..., ExistingWorkPolicy.KEEP, ...)`）。在经典 `RemoteViews` widget 上更新 `Bitmap` 或 `Icon` 时，调用 `appWidgetManager.updateAppWidget` 而不是 `partiallyUpdateAppWidget`。

## 常见错误与修复

| 症状或异常 | 根本原因 | 修复 |
|---|---|---|
| `IllegalArgumentException: RemoteViews for widget update exceeds maximum bitmap memory usage` | `RemoteViews` 的 bitmap 或图标内存超过了 `6 * W * H` 字节。 | 用 `inSampleSize` 和 `RGB_565`（掩码用 `ALPHA_8`）降采样到 widget 的 `maxWidthDp x maxHeightDp`，强制执行 `calculateWidgetMemoryCapBytes(context) / distinctImageCount`，并在 `provideContent` 之前一次性解码共享 bitmap。 |
| `SecurityException: Permission Denial: opening provider` 或 widget 的 `content://` 图像空白 | Home 启动器对该 `FileProvider` 的 `content://` URI 缺少读取权限，或应用用 `Uri.fromFile` 传了 `file://`。 | 用 `FileProvider` 暴露文件，为 `CATEGORY_HOME` 添加 `<queries>`，并用 `Intent.FLAG_GRANT_READ_URI_PERMISSION` 调用 `context.grantUriPermission`。 |
| 调用 `updateAppWidgetState` 后 widget UI 一直不动 | `updateAppWidgetState` 写入 DataStore 但不重组，或 `provideGlance` 在活跃会话期间未被重新触发。 | 在 `updateAppWidgetState` 之后调用 `.update(context, glanceId)` 或 `.updateAll(context)`，并在 `provideContent` 内观察版本状态。 |
| 点击 action 时出现 `NoSuchMethodException: <Class>.<init> []` | `ActionCallback` 声明了构造参数，或 R8 剥离了 `<init>()`。 | 使用公开的零参数构造函数，用 `ActionParameters.Key` 传值，并在 ProGuard 中保留 `<init>()`。 |
| receiver 中出现 `ForegroundServiceStartNotAllowedException` | `AppWidgetProvider` 在后台调用了 `startForegroundService`。 | 在 `onUpdate` 中用 `enqueueUniquePeriodicWork`（`ExistingPeriodicWorkPolicy.KEEP`）调度周期性同步，或在 `onReceive` 中由自定义 action 广播时入队一次性工作（`enqueueUniqueWork`）。 |
| `Unresolved reference: ImageProvider`、`DpSize`、`updateAppWidgetState` 或 `updateAll` | Glance 与 Compose 的包导入缺失或不匹配，或调用 `updateAppWidgetState(context)` 时没传 `glanceId`。 | 导入 `androidx.glance.ImageProvider`（用于 `Bitmap`）、`androidx.compose.ui.unit.DpSize` 和 `androidx.compose.ui.unit.dp`（用于 `SizeMode.Responsive`）、`androidx.glance.appwidget.state.updateAppWidgetState`（同时传 `context` 和 `glanceId`），以及 `androidx.glance.appwidget.updateAll`。 |

## 反模式

- **绝不**在 `provideContent` 内按尺寸桶用 `SizeMode.Responsive` 或 `SizeMode.Exact` 解码或缩放 `Bitmap`。
- **绝不**把 widget bitmap 的尺寸设为填满整个屏幕内存上限（`6 * width *
  height`）；始终先降采样到 widget 的目标 `maxWidthDp x maxHeightDp`，这样启动后展开折叠屏或切换显示分辨率不会超出启动时上限。
- **绝不**把未缩放的 `content://` `Uri` 或 `Uri.fromFile` 传给 `ImageProvider(uri)` 或 `RemoteViews.setImageViewUri`，也不要漏掉针对 `Intent.CATEGORY_HOME` 的 `context.grantUriPermission`。
- **绝不**调用 `updateAppWidgetState` 却不调用 `GlanceAppWidget.update(context, glanceId)` 或 `GlanceAppWidget.updateAll(context)`。
- **绝不**在替换 widget 图像时调用 `partiallyUpdateAppWidget`。
