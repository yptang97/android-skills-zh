---
name: glance-canonical-layouts
description: 使用这个 skill，基于 Android Platform Samples 项目中的 Jetpack Glance 规范布局（Canonical
  Layouts）创建主屏幕小组件；或在被要求实现标准小组件布局模式（包括检查列表、图片网格、吸附滚动与标准
  工具栏）时使用。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - android
  - glance
  - widgets
  - appwidget
  - canonical-layouts
  - platform-samples
  - action-list
  - check-list
  - image-grid
  - image-text-list
  - snap-scrolling
  - full-bleed
  - expressive-toolbar
  - search-toolbar
  - standard-toolbar
---

要按推荐的设计模式实现小组件的规范布局（Canonical Layout）：

1. 项目**必须**使用 Jetpack Glance。
2. 你**必须**在**规范布局参考文件**列表中找到所需的布局。
3. 一次性把布局参考文件复制到你项目的目标应用模块（例如 `src/main/java/` 与 `src/main/res/`），以实现完全一致的设计并减少工具调用次数。
4. 你**必须**在 widget provider 类中设置 override val `sizeMode: SizeMode = SizeMode.Exact`。
5. 确认项目可以编译，并把示例的包声明、import 路径与类名更新为目标应用的包名。
6. 清理项目的 widget 代码，移除未使用的类（例如未使用的按钮）。
7. 你**必须**在 `AndroidManifest.xml` 的 `<application>` 内、`<activity>` 之后注册 widget receiver，并确保 `android:resource="@xml/..."` 与所复制的 Widget Info XML 文件名一致。否则小组件不会出现在小组件选择器中：

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

## 依赖

在应用模块的 `build.gradle.kts`（`dependencies` 块）中添加 Jetpack Glance 依赖：

- `androidx.glance:glance-appwidget:1.2.0` or higher
- `androidx.glance:glance-material3:1.2.0` or higher
- `androidx.glance:glance-appwidget-preview:1.2.0` or higher
- `androidx.glance:glance-preview:1.2.0` or higher

实现吸附滚动（Snap Scrolling）时，使用 `1.3.0-alpha02` 或更高版本，并搭配 `compileSdk = 37` 与
Android Gradle Plugin（AGP）9.1.0 或更高版本（例如 `gradle/libs.versions.toml` 中的
`agp = "9.1.0"`）。

如果要复制用 Coil 加载位图的示例数据仓库（例如
`FakeImageGridDataRepository.kt`、`FakeImageTextListDataRepository.kt` 或
`FakeTextWithImageRepository.kt`），并且项目里还没有图像加载库，则还要添加
`io.coil-kt:coil` 这类依赖（例如 `implementation("io.coil-kt:coil:2.7.0")`）。

## 规范布局参考文件

#### 操作列表布局（`action_list`）

- **Widget Provider**：[ActionListAppWidget.kt](references/collections/ActionListAppWidget.kt)
- **布局 Composable**：[ActionListLayout.kt](references/collections/layout/ActionListLayout.kt)
- **Widget 信息 XML**：[sample_action_list_widget_info.xml](references/res/xml/sample_action_list_widget_info.xml)
- **数据仓库**：[FakeActionListDataRepository.kt](references/collections/data/FakeActionListDataRepository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_action_list_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_action_list_preview.png)、[sample_home_icon.xml](references/res/drawable/sample_home_icon.xml)、[sample_power_settings_icon.xml](references/res/drawable/sample_power_settings_icon.xml)、[sample_bulb_icon.xml](references/res/drawable/sample_bulb_icon.xml)、[sample_thermostat_icon.xml](references/res/drawable/sample_thermostat_icon.xml)、[sample_ac_icon.xml](references/res/drawable/sample_ac_icon.xml)、[sample_door_icon.xml](references/res/drawable/sample_door_icon.xml)、[sample_arrow_right_icon.xml](references/res/drawable/sample_arrow_right_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)
- **组件**：[RoundedScrollingLazyVerticalGrid.kt](references/collections/layout/RoundedScrollingLazyVerticalGrid.kt)、[ListItem.kt](references/collections/layout/ListItem.kt)、[VerticalListItem.kt](references/collections/layout/VerticalListItem.kt)、[RoundedScrollingLazyColumn.kt](references/collections/layout/RoundedScrollingLazyColumn.kt)、[EmptyListContent.kt](references/collections/layout/EmptyListContent.kt)、[NoDataContent.kt](references/collections/layout/NoDataContent.kt)
- **工具类**：[CollectionsKtx.kt](references/CollectionsKtx.kt)、[ActionUtils.kt](references/utils/ActionUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **其他参考**：[CanonicalLayoutActivity.kt](references/CanonicalLayoutActivity.kt)、[ActionDemonstrationActivity.kt](references/ActionDemonstrationActivity.kt)
- **指南**：
  - 用 Glance action 回调处理列表项操作，并确保状态正确更新。

#### 检查列表布局（`check_list`）

- **Widget Provider**：[CheckListAppWidget.kt](references/collections/CheckListAppWidget.kt)
- **布局 Composable**：[CheckListLayout.kt](references/collections/layout/CheckListLayout.kt)
- **Widget 信息 XML**：[sample_check_list_widget_info.xml](references/res/xml/sample_check_list_widget_info.xml)
- **数据仓库**：[FakeCheckListDataRepository.kt](references/collections/data/FakeCheckListDataRepository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_check_list_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_check_list_preview.png)、[sample_pin_icon.xml](references/res/drawable/sample_pin_icon.xml)、[sample_checked_circle_icon.xml](references/res/drawable/sample_checked_circle_icon.xml)、[sample_circle_icon.xml](references/res/drawable/sample_circle_icon.xml)、[sample_delete_icon.xml](references/res/drawable/sample_delete_icon.xml)、[sample_edit_icon.xml](references/res/drawable/sample_edit_icon.xml)、[sample_snooze_icon.xml](references/res/drawable/sample_snooze_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)
- **组件**：[ListItem.kt](references/collections/layout/ListItem.kt)、[VerticalListItem.kt](references/collections/layout/VerticalListItem.kt)、[RoundedScrollingLazyColumn.kt](references/collections/layout/RoundedScrollingLazyColumn.kt)、[EmptyListContent.kt](references/collections/layout/EmptyListContent.kt)、[NoDataContent.kt](references/collections/layout/NoDataContent.kt)
- **工具类**：[CollectionsKtx.kt](references/CollectionsKtx.kt)、[ActionUtils.kt](references/utils/ActionUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 使用 action 参数或回调实现复选框状态切换，以更新集合项。
  - 对 widget 的 onClick 参数使用 Glance action 回调（例如 `actionRunCallback`、`ActionCallback(actionParametersOf(...)` 或 `actionStartActivity(...)`），以处理点击复选框之类的点击事件。

#### 表现力工具栏布局（`expressive_toolbar`）

- **Widget Provider**：[ExpressiveToolbarAppWidget.kt](references/toolbars/ExpressiveToolbarAppWidget.kt)
- **布局 Composable**：[ExpressiveToolbarLayout.kt](references/toolbars/layout/ExpressiveToolbarLayout.kt)
- **Widget 信息 XML**：[sample_expressive_toolbar_widget_info.xml](references/res/xml/sample_expressive_toolbar_widget_info.xml)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_expressive_toolbar_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_expressive_toolbar_preview.png)、[four_side_cookie_background.xml](references/res/drawable/four_side_cookie_background.xml)、[sample_edit_icon.xml](references/res/drawable/sample_edit_icon.xml)、[sample_share_icon.xml](references/res/drawable/sample_share_icon.xml)、[sample_delete_icon.xml](references/res/drawable/sample_delete_icon.xml)、[sample_info_icon.xml](references/res/drawable/sample_info_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)、[sample_file_upload_icon.xml](references/res/drawable/sample_file_upload_icon.xml)、[sample_mic_icon.xml](references/res/drawable/sample_mic_icon.xml)、[sample_camera_icon.xml](references/res/drawable/sample_camera_icon.xml)
- **组件**：[Buttons.kt](references/toolbars/layout/Buttons.kt)、[LayoutComponents.kt](references/toolbars/layout/LayoutComponents.kt)
- **工具类**：[ActionUtils.kt](references/utils/ActionUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 避免 `ColorProvider` 导入错误：导入 `androidx.glance.unit.ColorProvider`，并使用 `androidx.glance.color.ColorProvider(dayColor, nightColor)`。
  - 纯色背景直接使用 `GlanceModifier.background(Color)`，不要用 `ColorProvider`。

#### 图片网格布局（`image_grid`）

- **Widget Provider**：[ImageGridAppWidget.kt](references/collections/ImageGridAppWidget.kt)
- **布局 Composable**：[ImageGridLayout.kt](references/collections/layout/ImageGridLayout.kt)
- **Widget 信息 XML**：[sample_image_grid_widget_info.xml](references/res/xml/sample_image_grid_widget_info.xml)
- **数据仓库**：[FakeImageGridDataRepository.kt](references/collections/data/FakeImageGridDataRepository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_image_grid_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_image_grid_preview.png)、[sample_placeholder_image.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable/sample_placeholder_image.png)、[sample_grid_icon.xml](references/res/drawable/sample_grid_icon.xml)、[sample_refresh_icon.xml](references/res/drawable/sample_refresh_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)
- **组件**：[RoundedScrollingLazyVerticalGrid.kt](references/collections/layout/RoundedScrollingLazyVerticalGrid.kt)、[EmptyListContent.kt](references/collections/layout/EmptyListContent.kt)、[NoDataContent.kt](references/collections/layout/NoDataContent.kt)、[VerticalListItem.kt](references/collections/layout/VerticalListItem.kt)
- **工具类**：[CollectionsKtx.kt](references/CollectionsKtx.kt)、[ImageUtils.kt](references/utils/ImageUtils.kt)、[ImageAspectRatio.kt](references/utils/ImageAspectRatio.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 除非已配置或要求使用图像加载库，否则图片项使用纯色（`GlanceModifier.background`）或本地 drawable。

#### 图文列表布局（`image_text_list`）

- **Widget Provider**：[ImageTextListAppWidget.kt](references/collections/ImageTextListAppWidget.kt)
- **布局 Composable**：[ImageTextListLayout.kt](references/collections/layout/ImageTextListLayout.kt)
- **Widget 信息 XML**：[sample_image_text_list_widget_info.xml](references/res/xml/sample_image_text_list_widget_info.xml)
- **数据仓库**：[FakeImageTextListDataRepository.kt](references/collections/data/FakeImageTextListDataRepository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_image_text_list_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_image_text_list_preview.png)、[sample_placeholder_image.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable/sample_placeholder_image.png)、[sample_image_icon.xml](references/res/drawable/sample_image_icon.xml)、[sample_heart_icon.xml](references/res/drawable/sample_heart_icon.xml)、[sample_refresh_icon.xml](references/res/drawable/sample_refresh_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)
- **组件**：[ListItem.kt](references/collections/layout/ListItem.kt)、[VerticalListItem.kt](references/collections/layout/VerticalListItem.kt)、[RoundedScrollingLazyColumn.kt](references/collections/layout/RoundedScrollingLazyColumn.kt)、[EmptyListContent.kt](references/collections/layout/EmptyListContent.kt)、[NoDataContent.kt](references/collections/layout/NoDataContent.kt)
- **工具类**：[CollectionsKtx.kt](references/CollectionsKtx.kt)、[ImageUtils.kt](references/utils/ImageUtils.kt)、[ImageAspectRatio.kt](references/utils/ImageAspectRatio.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 常见使用场景：新闻流、文章列表、锻炼记录、消息流与纵向缩略图列表。
  - 把缩略图与主文本、次要文本组合时，平衡列表行高与文本截断。

#### 长文本布局（`long_text`）

- **Widget Provider**：[LongTextAppWidget.kt](references/text/LongTextAppWidget.kt)
- **布局 Composable**：[LongTextLayout.kt](references/text/layout/LongTextLayout.kt)
- **Widget 信息 XML**：[sample_long_text_widget_info.xml](references/res/xml/sample_long_text_widget_info.xml)
- **数据仓库**：[FakeLongTextRespository.kt](references/text/data/FakeLongTextRespository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_long_text_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_long_text_preview.png)、[sample_text_icon.xml](references/res/drawable/sample_text_icon.xml)、[sample_refresh_icon.xml](references/res/drawable/sample_refresh_icon.xml)
- **工具类**：[FontUtils.kt](references/utils/FontUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 如果要相乘 Dp（例如 `2 * padding`），导入 `androidx.compose.ui.unit.times`。
  - 遵循尺寸规则：padding 与排版缩放要使用 dimens.xml 中的尺寸。

#### 搜索工具栏布局（`search_toolbar`）

- **Widget Provider**：[SearchToolBarAppWidget.kt](references/toolbars/SearchToolBarAppWidget.kt)
- **布局 Composable**：[SearchToolBarLayout.kt](references/toolbars/layout/SearchToolBarLayout.kt)
- **Widget 信息 XML**：[sample_search_toolbar_widget_info.xml](references/res/xml/sample_search_toolbar_widget_info.xml)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_search_toolbar_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_search_toolbar_preview.png)、[sample_search_icon.xml](references/res/drawable/sample_search_icon.xml)、[sample_refresh_icon.xml](references/res/drawable/sample_refresh_icon.xml)、[sample_mic_icon.xml](references/res/drawable/sample_mic_icon.xml)、[sample_camera_icon.xml](references/res/drawable/sample_camera_icon.xml)、[sample_delete_icon.xml](references/res/drawable/sample_delete_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)、[sample_pin_icon.xml](references/res/drawable/sample_pin_icon.xml)
- **组件**：[Buttons.kt](references/toolbars/layout/Buttons.kt)、[LayoutComponents.kt](references/toolbars/layout/LayoutComponents.kt)
- **工具类**：[ActionUtils.kt](references/utils/ActionUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 避免 `ColorProvider` 导入错误：导入 `androidx.glance.unit.ColorProvider`，并使用 `androidx.glance.color.ColorProvider(dayColor, nightColor)`。
  - 纯色背景直接使用 `GlanceModifier.background(Color)`，不要用 `ColorProvider`。

#### 全出血图片布局与吸附滚动（`snap_scrolling`）

- **Widget Provider**：[FullBleedImageAppWidget.kt](references/text/FullBleedImageAppWidget.kt)
- **布局 Composable**：[FullBleedImageLayout.kt](references/text/layout/FullBleedImageLayout.kt)
- **Widget 信息 XML**：[sample_full_bleed_image_widget_info.xml](references/res/xml/sample_full_bleed_image_widget_info.xml)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_full_bleed_image_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_full_bleed_image_preview.png)、[sample_scrim_gradient.xml](references/res/drawable/sample_scrim_gradient.xml)、[sample_placeholder_image.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable/sample_placeholder_image.png)、[sample_app_logo.xml](references/res/drawable/sample_app_logo.xml)、[sample_info_icon.xml](references/res/drawable/sample_info_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)
- **工具类**：[FontUtils.kt](references/utils/FontUtils.kt)、[ImageAspectRatio.kt](references/utils/ImageAspectRatio.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 要在 `LazyColumn` 上实现吸附滚动（Snap Scrolling），请设置 `verticalScrollMode =
    VerticalScrollMode.SnapScrollMatchHeight(size.height)`。
  - 实现吸附滚动时，需要 Glance 1.3.0-alpha02（或更高）、Compile SDK 37（Baklava）或更高，以及 Android Gradle Plugin（AGP）9.1.0 或更高。
  - 在 widget provider 类中设置 override val sizeMode: SizeMode = SizeMode.Exact。

#### 标准工具栏布局（`standard_toolbar`）

- **Widget Provider**：[ToolBarAppWidget.kt](references/toolbars/ToolBarAppWidget.kt)
- **布局 Composable**：[ToolBarLayout.kt](references/toolbars/layout/ToolBarLayout.kt)
- **Widget 信息 XML**：[sample_toolbar_widget_info.xml](references/res/xml/sample_toolbar_widget_info.xml)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_toolbar_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_toolbar_preview.png)、[sample_app_logo.xml](references/res/drawable/sample_app_logo.xml)、[sample_search_icon.xml](references/res/drawable/sample_search_icon.xml)、[sample_add_icon.xml](references/res/drawable/sample_add_icon.xml)、[sample_edit_icon.xml](references/res/drawable/sample_edit_icon.xml)、[sample_share_icon.xml](references/res/drawable/sample_share_icon.xml)、[sample_mic_icon.xml](references/res/drawable/sample_mic_icon.xml)、[sample_camera_icon.xml](references/res/drawable/sample_camera_icon.xml)、[sample_videocam_icon.xml](references/res/drawable/sample_videocam_icon.xml)
- **组件**：[Buttons.kt](references/toolbars/layout/Buttons.kt)、[LayoutComponents.kt](references/toolbars/layout/LayoutComponents.kt)
- **工具类**：[ActionUtils.kt](references/utils/ActionUtils.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **其他参考**：[CanonicalLayoutActivity.kt](references/CanonicalLayoutActivity.kt)
- **指南**：
  - 参见故障排查以避免 `ColorProvider` 导入错误：使用 androidx.glance.color.ColorProvider(dayColor, nightColor)。
  - 纯色背景直接使用 GlanceModifier.background(Color)，不要用 `ColorProvider`。

#### 文本配图布局（`text_with_image`）

- **Widget Provider**：[TextWithImageAppWidget.kt](references/text/TextWithImageAppWidget.kt)
- **布局 Composable**：[TextWithImageLayout.kt](references/text/layout/TextWithImageLayout.kt)
- **Widget 信息 XML**：[sample_text_with_image_widget_info.xml](references/res/xml/sample_text_with_image_widget_info.xml)
- **数据仓库**：[FakeTextWithImageRepository.kt](references/text/data/FakeTextWithImageRepository.kt)
- **尺寸**：[dimens.xml](references/res/values/dimens.xml)
- **字符串**：[strings.xml](references/res/values/strings.xml)
- **图形资源**：[sample_text_image_preview.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable-nodpi/sample_text_image_preview.png)、[sample_text_icon.xml](references/res/drawable/sample_text_icon.xml)、[sample_refresh_icon.xml](references/res/drawable/sample_refresh_icon.xml)、[sample_placeholder_image.png](https://developer.android.com/static/agents/skills/system/glance-canonical-layouts/references/res/drawable/sample_placeholder_image.png)、[sample_info_icon.xml](references/res/drawable/sample_info_icon.xml)、[sample_no_data_icon.xml](references/res/drawable/sample_no_data_icon.xml)
- **工具类**：[FontUtils.kt](references/utils/FontUtils.kt)、[ImageAspectRatio.kt](references/utils/ImageAspectRatio.kt)、[PreviewAnnotations.kt](references/utils/PreviewAnnotations.kt)
- **主题**：[Color.kt](references/ui/theme/Color.kt)、[Theme.kt](references/ui/theme/Theme.kt)、[Type.kt](references/ui/theme/Type.kt)
- **指南**：
  - 遵循响应式布局尺寸规则，根据可用的 widget 尺寸让文本与图片并排或上下堆叠。

## 故障排查

1. **背景色**：纯色背景直接使用 `GlanceModifier.background(Color)`，不要用 `ColorProvider`，否则背景会变成透明。
2. **在背景色之外使用 `ColorProvider` 时，避免导入错误**：
   1. 导入类型：`import androidx.glance.unit.ColorProvider`
   2. 使用全限定创建函数：`androidx.glance.color.ColorProvider(dayColor, nightColor)`

## 检查清单

- \[ \] 你是否在 AndroidManifest 中注册了小组件？
- \[ \] 你是否复制了对应的 **Widget Info XML** 文件，并保持 `minWidth`、`minHeight` 与 `minResizeHeight` 等给定值不变？
- \[ \] 你是否使用了对应 **Layout Composable** 文件中给定的 Glance 主题颜色值？
- \[ \] 你是否在 appwidget-provider XML 定义中为 `android:minWidth` 与 `android:minHeight` 使用了尺寸资源引用？
- \[ \] 你是否在 widget provider 类中覆盖了 `val sizeMode: SizeMode = SizeMode.Exact`？
