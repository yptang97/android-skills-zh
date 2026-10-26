---
name: wear-compose-m3
description: Wear OS Compose Material3（Wear Compose Material 3 / Wear
  Compose Material3）手表与可穿戴应用指南。涵盖使用 androidx.wear.compose.material3、
  androidx.wear.compose.foundation 和 androidx.wear.compose.navigation3 创建、更新和迁移
  项目（Material 2.5 与 Horologist 迁移），包括
  AppScaffold、ScreenScaffold、TransformingLazyColumn、ambient mode 和预览。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - Wear OS
  - Compose
  - Material3
  - Horologist
  - TransformingLazyColumn
  - ScalingLazyColumn
  - AppScaffold
  - ScreenScaffold
  - EdgeButton
  - SwipeDismissableSceneStrategy
  - Material 2.5
  - ambient mode
---

## 前置条件与兼容性

1. **当前在用的 Wear OS Compose 版本：** 要找到已安装的库版本，直接读取 `gradle/libs.versions.toml` 或 `build.gradle.kts`。不要运行 `./gradlew dependencies` 或其他 shell 命令来解析版本。
2. **Wear OS Compose Material3 版本：** 如果有内部工具可以确定 `androidx.wear.compose:compose-material3` 的 **最新稳定版本** `{VERSION}`，就使用该工具。
   - 否则，获取 [官方 Maven metadata XML](https://dl.google.com/dl/android/maven2/androidx/wear/compose/compose-material3/maven-metadata.xml) 来确定 `{VERSION}`（取最大编号，忽略 `-alpha`、`-beta` 或 `-rc`）。
3. **严格遵守：** 如果某个版本被列为稳定版，你必须使用它，除非用户另有指定。不要因为编辑器里最初出现的「Unresolved reference」错误或过时的网页搜索结果而降级。
4. **Kotlin \& Compose 编译器：** 使用 Kotlin **2.0.0+** 和 `org.jetbrains.kotlin.plugin.compose` Gradle 插件。
5. **Min SDK：** 确保 `minSdk` 至少为 **25**。
6. **Compile SDK \& AGP：** 确保 `compileSdk` 和 AGP 满足库的 AAR metadata 下限（`1.6.x` 要求 `compileSdk >= 35` 且 `AGP >= 8.6.0`；`1.7.x` 要求 `compileSdk >= 37` 且 `AGP >= 9.1.0`）。

## 常见陷阱

1. **必须同步并验证：** 在 `libs.versions.toml` 或 `build.gradle.kts` 中更新版本后，重构前先做一次 Gradle 同步（或运行 `./gradlew assembleDebug`），重构后再运行 `./gradlew assembleDebug` 验证构建。
2. **禁止猜测（错误处理协议）：** 如果同步成功后遇到「Unresolved Reference」或 API 不匹配，不要试图通过降级库版本来「修复」它。

## 能力与工具

### 能力 1：迁移、更新与添加功能

在从旧版 Wear OS Compose 或 Horologist 迁移、更新现有的 Wear Compose Material3 项目，或
添加功能时，使用本指南。

1. 除非开发者另有说明，使用 `{VERSION}` 中最新的稳定版 Wear Compose Material3（优先于迁移指南中出现的任何字面版本号）。
2. 从 Material 2.5 或 Horologist 迁移时，阅读[迁移指南](references/android/training/wearables/compose/migrate-to-material3.md)并使用其中官方的组件映射。
3. 重构任何组件前（例如 `Chip` -\> `Button`），检查参数名、slot 类型和「Expressive」设计令牌。
4. 不要使用 Horologist 的 Composables、Compose Layout 或 Compose Material 库；用对应的 Wear Compose M3 组件替换 Horologist 组件（`AppScaffold` -\> M3 `AppScaffold`，`ScreenScaffold` -\> M3 `ScreenScaffold`，`ScalingLazyColumn` -\> `TransformingLazyColumn`，`ResponsiveListHeader` -\> `ListHeader`，`PagerScreen` -\> `HorizontalPagerScaffold`，`Chip` -\> `Button`，`Confirmation` -\> `ConfirmationDialog`）。
5. **始终** 对照能力 3 中的组件指南进行检查。
6. 迁移或更新组件时，要预期截图测试会失败：内边距和定位的预期默认值会发生变化。不要试图人为匹配旧截图，而应优先采用 Material3 的默认值。

### 能力 2：组件示例

使用这张参考表查找 Wear Compose 组件的规范示例。
处理某个 Wear Compose 组件时，你必须使用表中链接的示例，以确保你知道如何正确使用它。

**重要：** 标有 `[alpha]`、`[beta]` 或 `[rc]` 的符号只在对应的预发布轨道中可用，**不在** 稳定版 `{VERSION}` 中。除非项目明确面向该预发布版本，否则不要使用它们。

#### `androidx.wear.compose.material3.*` 中的 Material 3 组件

| 组件 / 符号 | 参考示例 |
|---|---|
| `AlertDialog`, `AlertDialogDefaults` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md) |
| `AnimatedPage`, `HorizontalPagerScaffold`, `VerticalPagerScaffold` | [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md) |
| `AnimatedText`, `rememberAnimatedTextFontRegistry` | [AnimatedTextSample](references/material3/AnimatedTextSample.kt.md) |
| `AppCard` | [CardSample](references/material3/CardSample.kt.md) |
| `AppScaffold` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ArcProgressIndicator`, `ArcProgressIndicatorDefaults`, `CircularProgressIndicator`, `CircularProgressIndicatorDefaults`, `ProgressIndicatorDefaults`, `SegmentedCircularProgressIndicator`, `drawCircularProgressIndicator` | [ProgressIndicatorSample](references/material3/ProgressIndicatorSample.kt.md) |
| `Button` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [AnimatedTextSample](references/material3/AnimatedTextSample.kt.md), [ButtonGroupSample](references/material3/ButtonGroupSample.kt.md), [ButtonSample](references/material3/ButtonSample.kt.md), [DatePickerSample](references/material3/DatePickerSample.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [FadingExpandingLabelSample](references/material3/FadingExpandingLabelSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [PickerSample](references/material3/PickerSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [StepperSample](references/material3/StepperSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TimePickerSample](references/material3/TimePickerSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ButtonDefaults` | [ButtonSample](references/material3/ButtonSample.kt.md), [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [EdgeButtonSample](references/material3/EdgeButtonSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [PlaceholderSample](references/material3/PlaceholderSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [TextButtonSample](references/material3/TextButtonSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ButtonGroup` | [ButtonGroupSample](references/material3/ButtonGroupSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md) |
| `Card` | [CardSample](references/material3/CardSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `CardDefaults` | [CardSample](references/material3/CardSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `CheckboxButton` | [CheckboxButtonSample](references/material3/CheckboxButtonSample.kt.md), [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md) |
| `ChildButton`, `OutlinedButton` | [ButtonSample](references/material3/ButtonSample.kt.md) |
| `ColorScheme`, `dynamicColorScheme` | [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md) |
| `CompactButton`, `CompactButtonDefaults` | [ButtonSample](references/material3/ButtonSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ConfirmationDialog`, `ConfirmationDialogDefaults`, `FailureConfirmationDialog`, `SuccessConfirmationDialog`, `confirmationDialogCurvedText` | [ConfirmationDialogSample](references/material3/ConfirmationDialogSample.kt.md) |
| `CurvedTextDefaults` | [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md) |
| `DatePicker`, `DatePickerType` | [DatePickerSample](references/material3/DatePickerSample.kt.md) |
| `EdgeButton` | [EdgeButtonSample](references/material3/EdgeButtonSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `EdgeButtonSize` | [EdgeButtonSample](references/material3/EdgeButtonSample.kt.md) |
| `FadingExpandingLabel` | [FadingExpandingLabelSample](references/material3/FadingExpandingLabelSample.kt.md) |
| `FilledIconButton`, `FilledTonalIconButton`, `IconButtonColors`, `IconButtonShapes`, `OutlinedIconButton` | [IconButtonSample](references/material3/IconButtonSample.kt.md) |
| `FilledTonalButton` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [ButtonSample](references/material3/ButtonSample.kt.md), [ConfirmationDialogSample](references/material3/ConfirmationDialogSample.kt.md), [OpenOnPhoneDialogSample](references/material3/OpenOnPhoneDialogSample.kt.md), [PlaceholderSample](references/material3/PlaceholderSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md) |
| `HorizontalPageIndicator`, `VerticalPageIndicator` | [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md) |
| `Icon` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [ButtonSample](references/material3/ButtonSample.kt.md), [CardSample](references/material3/CardSample.kt.md), [CheckboxButtonSample](references/material3/CheckboxButtonSample.kt.md), [ConfirmationDialogSample](references/material3/ConfirmationDialogSample.kt.md), [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [DatePickerSample](references/material3/DatePickerSample.kt.md), [EdgeButtonSample](references/material3/EdgeButtonSample.kt.md), [IconButtonSample](references/material3/IconButtonSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [PlaceholderSample](references/material3/PlaceholderSample.kt.md), [ProgressIndicatorSample](references/material3/ProgressIndicatorSample.kt.md), [RadioButtonSample](references/material3/RadioButtonSample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [SwitchButtonSample](references/material3/SwitchButtonSample.kt.md), [TimePickerSample](references/material3/TimePickerSample.kt.md) |
| `IconButton` | [IconButtonSample](references/material3/IconButtonSample.kt.md), [LevelIndicatorSample](references/material3/LevelIndicatorSample.kt.md), [ProgressIndicatorSample](references/material3/ProgressIndicatorSample.kt.md) |
| `IconButtonDefaults` | [IconButtonSample](references/material3/IconButtonSample.kt.md), [ProgressIndicatorSample](references/material3/ProgressIndicatorSample.kt.md) |
| `IconToggleButton`, `IconToggleButtonDefaults` | [IconToggleButtonSample](references/material3/IconToggleButtonSample.kt.md) |
| `LevelIndicator` | [LevelIndicatorSample](references/material3/LevelIndicatorSample.kt.md) |
| `LinearProgressIndicator` | [LinearProgressIndicatorSample](references/material3/LinearProgressIndicatorSample.kt.md) |
| `ListHeader` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ListHeaderDefaults` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ListSubHeader` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md) |
| `LocalOneHandedGestureEnabled`, `OneHandedGestureDefaults`, `OneHandedGestureHorizontalPageIndicator`, `OneHandedGesturePageIndicatorState`, `OneHandedGesturePriority`, `OneHandedGestureScrollIndicator`, `OneHandedGestureScrollIndicatorState`, `OneHandedGestureVerticalPageIndicator` | [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md) |
| `MaterialTheme` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [ButtonSample](references/material3/ButtonSample.kt.md), [CardSample](references/material3/CardSample.kt.md), [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [LinearProgressIndicatorSample](references/material3/LinearProgressIndicatorSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [ProgressIndicatorSample](references/material3/ProgressIndicatorSample.kt.md), [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md) |
| `OneHandedGestureAction`, `OneHandedGestureClickIndicator`, `OneHandedGestureClickIndicatorState`, `oneHandedGesture`, `rememberOneHandedGestureConfiguration` | [ButtonSample](references/material3/ButtonSample.kt.md), [CardSample](references/material3/CardSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md) |
| `OpenOnPhoneDialog`, `OpenOnPhoneDialogDefaults`, `openOnPhoneDialogCurvedText` | [OpenOnPhoneDialogSample](references/material3/OpenOnPhoneDialogSample.kt.md) |
| `OutlinedCard` | [CardSample](references/material3/CardSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `PagerScaffoldDefaults` | [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md) |
| `Picker` | [PickerSample](references/material3/PickerSample.kt.md) |
| `PickerGroup` | [PickerGroupSample](references/material3/PickerGroupSample.kt.md) |
| `RadioButton`, `SplitRadioButton` | [RadioButtonSample](references/material3/RadioButtonSample.kt.md) |
| `ResponsiveTransformationSpec`, `TransformationVariableSpec` | [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md) |
| `RevealValue`, `SwipeToReveal`, `SwipeToRevealDefaults`, `rememberRevealState` | [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md) |
| `ScreenScaffold` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `ScreenScaffoldDefaults`, `ScrollIndicator` | [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md) |
| `ScreenStage`, `scrollAway` | [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md) |
| `Slider`, `SliderDefaults` | [SliderSample](references/material3/SliderSample.kt.md) |
| `SplitCheckboxButton` | [CheckboxButtonSample](references/material3/CheckboxButtonSample.kt.md) |
| `SplitSwitchButton` | [SwitchButtonSample](references/material3/SwitchButtonSample.kt.md) |
| `Stepper`, `StepperLevelIndicator`, `rangeSemantics` | [StepperSample](references/material3/StepperSample.kt.md) |
| `StepperDefaults` | [LevelIndicatorSample](references/material3/LevelIndicatorSample.kt.md), [StepperSample](references/material3/StepperSample.kt.md) |
| `SurfaceTransformation` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `SwipeToDismissBox` | [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md) |
| `SwitchButton` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [SwitchButtonSample](references/material3/SwitchButtonSample.kt.md) |
| `Text` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [AnimatedTextSample](references/material3/AnimatedTextSample.kt.md), [ButtonGroupSample](references/material3/ButtonGroupSample.kt.md), [ButtonSample](references/material3/ButtonSample.kt.md), [CardSample](references/material3/CardSample.kt.md), [CheckboxButtonSample](references/material3/CheckboxButtonSample.kt.md), [ConfirmationDialogSample](references/material3/ConfirmationDialogSample.kt.md), [DatePickerSample](references/material3/DatePickerSample.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [EdgeButtonSample](references/material3/EdgeButtonSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [OpenOnPhoneDialogSample](references/material3/OpenOnPhoneDialogSample.kt.md), [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [PickerGroupSample](references/material3/PickerGroupSample.kt.md), [PickerSample](references/material3/PickerSample.kt.md), [PlaceholderSample](references/material3/PlaceholderSample.kt.md), [RadioButtonSample](references/material3/RadioButtonSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [StepperSample](references/material3/StepperSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [SwitchButtonSample](references/material3/SwitchButtonSample.kt.md), [TextButtonSample](references/material3/TextButtonSample.kt.md), [TextToggleButtonSample](references/material3/TextToggleButtonSample.kt.md), [TimePickerSample](references/material3/TimePickerSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `TextButton` | [TextButtonSample](references/material3/TextButtonSample.kt.md) |
| `TextButtonDefaults` | [TextButtonSample](references/material3/TextButtonSample.kt.md), [TextToggleButtonSample](references/material3/TextToggleButtonSample.kt.md) |
| `TextToggleButton`, `TextToggleButtonDefaults`, `touchTargetAwareSize` | [TextToggleButtonSample](references/material3/TextToggleButtonSample.kt.md) |
| `TimePicker`, `TimePickerType` | [TimePickerSample](references/material3/TimePickerSample.kt.md) |
| `TimeText` | [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md) |
| `TimeTextDefaults`, `timeTextCurvedText` | [TimeTextSample](references/material3/TimeTextSample.kt.md) |
| `TitleCard` | [CardSample](references/material3/CardSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md) |
| `TransformationSpec` | [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md) |
| `curvedText` | [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md) |
| `firstVisibleItemLayoutItemInfo`, `layoutItemInfoOf`, `rememberTransformingLazyColumnFirstLayoutItemProvider` | [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `placeholder`, `placeholderShimmer`, `rememberPlaceholderState` | [PlaceholderSample](references/material3/PlaceholderSample.kt.md) |
| `rememberPickerState` | [PickerGroupSample](references/material3/PickerGroupSample.kt.md), [PickerSample](references/material3/PickerSample.kt.md) |
| `rememberTransformationSpec`, `transformedHeight` | [AlertDialogSample](references/material3/AlertDialogSample.kt.md), [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `timeTextSeparator` | [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md) |

#### `androidx.wear.compose.foundation.*` 中的 Foundation 组件

| 组件 / 符号 | 参考示例 |
|---|---|
| `AmbientMode`, `LocalAmbientModeManager`, `rememberAmbientModeManager` | [AmbientModeSample](references/foundation/AmbientModeSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md) |
| `AmbientTickEffect` | [AmbientModeSample](references/foundation/AmbientModeSample.kt.md) |
| `BasicSwipeToDismissBox` | [SwipeToDismissBoxSample](references/foundation/SwipeToDismissBoxSample.kt.md) |
| `CurvedAlignment`, `CurvedTextStyle`, `angularGradientBackground`, `angularSize`, `basicCurvedText`, `clearAndSetSemantics`, `curvedColumn`, `padding`, `radialGradientBackground`, `radialSize`, `semantics`, `size` | [CurvedWorldSample](references/foundation/CurvedWorldSample.kt.md) |
| `CurvedDirection`, `CurvedLayout`, `angularSizeDp`, `background`, `curvedBox`, `curvedComposable`, `curvedRow` | [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [CurvedWorldSample](references/foundation/CurvedWorldSample.kt.md) |
| `CurvedModifier` | [CurvedTextSamples](references/material3/CurvedTextSamples.kt.md), [CurvedWorldSample](references/foundation/CurvedWorldSample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md) |
| `HorizontalPager`, `VerticalPager`, `rememberPagerState` | [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [PageIndicatorSample](references/material3/PageIndicatorSample.kt.md), [PagerSamples](references/foundation/PagerSamples.kt.md), [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md) |
| `PagerDefaults` | [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md) |
| `RotaryScrollableDefaults` | [PagerScaffoldSample](references/material3/PagerScaffoldSample.kt.md), [RotarySamples](references/foundation/RotarySamples.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md) |
| `RotarySnapLayoutInfoProvider`, `rotaryScrollable` | [RotarySamples](references/foundation/RotarySamples.kt.md) |
| `ScrollInfoProvider` | [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md) |
| `SwipeToDismissValue`, `edgeSwipeToDismiss`, `rememberSwipeToDismissBoxState` | [SwipeToDismissBoxSample](references/foundation/SwipeToDismissBoxSample.kt.md), [SwipeToDismissBoxSample](references/material3/SwipeToDismissBoxSample.kt.md) |
| `TransformingLazyColumn` | [DynamicColorSchemeSample](references/material3/DynamicColorSchemeSample.kt.md), [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `TransformingLazyColumnDefaults` | [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md) |
| `TransformingLazyColumnFirstLayoutItemProvider` | [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `TransformingLazyColumnItemScrollProgress` | [TransformationSpecSample](references/material3/TransformationSpecSample.kt.md) |
| `expandableButton`, `expandableItem`, `expandableItems`, `rememberExpandableState` | [ExpandableSample](references/foundation/ExpandableSample.kt.md) |
| `hierarchicalFocusGroup` | [HierarchicalFocusSample](references/foundation/HierarchicalFocusSample.kt.md) |
| `items` | [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md) |
| `itemsIndexed` | [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `rememberTransformingLazyColumnState` | [ListHeaderSample](references/material3/ListHeaderSample.kt.md), [OneHandedGestureSamples](references/material3/OneHandedGestureSamples.kt.md), [ScaffoldSample](references/material3/ScaffoldSample.kt.md), [ScrollAwaySample](references/material3/ScrollAwaySample.kt.md), [ScrollIndicatorSample](references/material3/ScrollIndicatorSample.kt.md), [SurfaceTransformationSample](references/material3/SurfaceTransformationSample.kt.md), [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md), [SwipeToRevealSample](references/material3/SwipeToRevealSample.kt.md), [TransformingLazyColumnNotificationsSample](references/material3/TransformingLazyColumnNotificationsSample.kt.md), [TransformingLazyColumnSample](references/foundation/TransformingLazyColumnSample.kt.md), [TransformingLazyColumnSample](references/material3/TransformingLazyColumnSample.kt.md) |
| `requestFocusOnHierarchyActive` | [HierarchicalFocusSample](references/foundation/HierarchicalFocusSample.kt.md), [RotarySamples](references/foundation/RotarySamples.kt.md) |
| `weight` | [CurvedWorldSample](references/foundation/CurvedWorldSample.kt.md), [TimeTextSample](references/material3/TimeTextSample.kt.md) |

#### `androidx.wear.compose.navigation3.*` 中的 Navigation 3 组件

| 组件 / 符号 | 参考示例 |
|---|---|
| `rememberSwipeDismissableSceneStrategy` | [SwipeDismissableSceneStrategySample](references/navigation3/SwipeDismissableSceneStrategySample.kt.md) |

### 能力 3：组件指南

**强制要求**：把本能力当作检查清单，用于任何组件使用场景。它提供比组件语法更全面的实践
指南，说明如何在实践中使用每个组件。

1. `AppScaffold` 和 `ScreenScaffold`
   - \[ \] 把 `AppScaffold` 作为外层容器，`ScreenScaffold` 作为其子级。
   - \[ \] 只使用 **一个** `AppScaffold`，`ScreenScaffold` 数量不限。
2. `ScalingLazyColumn` —— 改用 `TransformingLazyColumn`。
3. `TransformingLazyColumn` —— 你需要以下 import：

   ```kotlin
   import androidx.wear.compose.foundation.lazy.TransformingLazyColumn
   import androidx.wear.compose.foundation.lazy.TransformingLazyColumnDefaults
   import androidx.wear.compose.foundation.lazy.rememberTransformingLazyColumnState
   // ...
   import androidx.wear.compose.material3.lazy.rememberTransformationSpec
   import androidx.wear.compose.material3.lazy.transformedHeight
   ```

   <br />

   **规范示例**：

   ```kotlin
   val columnState = rememberTransformingLazyColumnState()
   val transformationSpec = rememberTransformationSpec()
   ScreenScaffold(
       scrollState = columnState
   ) { contentPadding ->
       TransformingLazyColumn(
           state = columnState,
           contentPadding = contentPadding
       ) {
           item {
               ListHeader(
                   modifier = Modifier
                       .fillMaxWidth()
                       .transformedHeight(this, transformationSpec)
                       .minimumVerticalContentPadding(ListHeaderDefaults.minimumTopListContentPadding),
                   transformation = SurfaceTransformation(transformationSpec)
               ) {
                   Text(text = "Header")
               }
           }
           // ... other items
           item {
               Button(
                   modifier = Modifier
                       .fillMaxWidth()
                       .transformedHeight(this, transformationSpec)
                       .minimumVerticalContentPadding(ButtonDefaults.minimumVerticalListContentPadding),
                   transformation = SurfaceTransformation(transformationSpec),
                   onClick = { /* ... */ },
                   icon = {
                       Icon(
                           imageVector = Icons.Default.Build,
                           contentDescription = "build",
                       )
                   },
               ) {
                   Text(
                       text = "Build",
                       maxLines = 1,
                       overflow = TextOverflow.Ellipsis,
                   )
               }
           }
       }
   }
   ```

   <br />

   - \[ \] 用 `TransformingLazyColumn` 而不是 `ScalingLazyColumn`。
   - \[ \] 必须把 `ScreenScaffold` 的 `contentPadding` 参数传给 `TransformingLazyColumn`。
   - \[ \] 使用 `minimumVerticalContentPadding` 修饰符达到所需的上下内边距。
     - 该值应来自 defaults，例如 `ButtonDefaults`、`CardDefaults`、`ListHeaderDefaults`。
     - 注意：这是 `TransformingLazyColumnItemScope` 内可用的作用域修饰符。
   - \[ \] 确保项目能变形和缩放（作用于 `TransformingLazyColumn` **内部** 的组件，而不是列表本身）：
     - \[ \] 使用 `Modifier.transformedHeight(this, transformationSpec)`。
     - \[ \] 使用 `transformation = SurfaceTransformation(transformationSpec)`。
   - \[ \] 如果要把列表配置为吸附，**同时** 使用 `flingBehavior` 和 `rotaryScrollableBehavior`：

   ```kotlin
   val columnState = rememberTransformingLazyColumnState()
   ScreenScaffold(scrollState = columnState) { contentPadding ->
       TransformingLazyColumn(
           state = columnState,
           flingBehavior = TransformingLazyColumnDefaults.snapFlingBehavior(columnState),
           rotaryScrollableBehavior = RotaryScrollableDefaults.snapBehavior(columnState)
       ) {
           // ...
           // ...
       }
   }
   ```

   <br />

4. `ScreenScaffold`

   - \[ \] 用 `!LocalScrollCaptureInProgress.current`（`androidx.compose.ui.platform`）守护 `scrollIndicator`。
5. `EdgeButton`

   - \[ \] **不要** 把它用作 `TransformingLazyColumn` 内的最后一项。而应使用 `ScreenScaffold` 中的 slot。
   - \[ \] 在 `TransformingLazyColumn` 中使用时，添加所需的过度滚动行为：

   ```kotlin
   val columnState = rememberTransformingLazyColumnState()
   ScreenScaffold(
       scrollState = columnState,
       edgeButton = {
           EdgeButton(
               onClick = { /* TODO */ },
               modifier = Modifier.scrollable(
                   columnState,
                   orientation = Orientation.Vertical,
                   reverseDirection = true,
                   // Apply overscroll to the EdgeButton for proper scrolling behavior.
                   overscrollEffect = rememberOverscrollEffect(),
               )
           ) {
               Text("More")
           }
       }
   ) { contentPadding ->
       TransformingLazyColumn(
           contentPadding = contentPadding,
           state = columnState,
       ) {
           // ...
           // ...
       }
   }
   ```

   <br />

6. `Column`

   - \[ \] 如果屏幕 **永不** 滚动（即使系统字体调到最大），可以把 `Column` 用作 `ScreenScaffold` 的直接子级。
   - \[ \] 其他情况改用 `TransformingLazyColumn`。
7. 样式

   - \[ \] **不要** 硬编码文字尺寸，使用 `MaterialTheme` 的 `typography`。
   - \[ \] **不要** 硬编码颜色，使用 `MaterialTheme` 的 `colorScheme`。
8. 使用组件的 defaults：

   - \[ \] `Button` 这类组件都有对应的 `ButtonDefaults` 对象。
   - \[ \] 处理内边距和样式值时，检查并使用任何组件的 `*Defaults` 对象，而不是硬编码值。
9. 使用 Wear 专属的预览注解
   （`androidx.wear.compose.ui.tooling.preview`）：

   - \[ \] `@WearPreviewDevices`
   - \[ \] `@WearPreviewFontScales`
   - \[ \] 确保已包含 `androidx.wear.compose:compose-ui-tooling` 依赖。
10. Ambient mode

    - \[ \] 使用 `LocalAmbientModeManager`（由 `CompositionLocalProvider` 和 `rememberAmbientModeManager()` 提供），而不是 `AmbientLifecycleObserver`。
11. 导航

    - \[ \] 新增导航时，使用 Navigation3（`androidx.wear.compose:compose-navigation3`）。
    - \[ \] 使用 `rememberSwipeDismissableSceneStrategy()` / `SwipeDismissableSceneStrategy`（`androidx.wear.compose.navigation3`）。
12. 注释

    - \[ \] 任何 Kotlin 文件被修改后，确保现有注释是最新的，并准确反映实现的变更。
13. `HorizontalPager` 或 `VerticalPager`

    - \[ \] 按此顺序使用 Composable 层级：`AppScaffold`、`HorizontalPagerScaffold`、`HorizontalPager`、`AnimatedPage`、`ScreenScaffold`。`VerticalPager` 同理。
