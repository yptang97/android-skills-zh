## 说明

当需要在面向 Android 大屏和桌面环境的 Jetpack Compose 应用中添加或重新设计工具提示（tooltip）时，使用本文档。不要使用 Compose Multiplatform 的 Desktop TooltipArea。

预期输出：

- 简要分析目标与输入方式，然后给出保留无障碍、焦点和设计系统规则的实现。

## 工作流

### 步骤 1：确认工具提示的目标与文本

在实现之前先搜索代码并把每个候选都写下来。目标和措辞由你自行决定。

1. 仅图标控件：`IconButton`、`IconToggleButton`、`FloatingActionButton`、`TopAppBar` 的 `navigationIcon` 和 `actions`、工具栏与工具箱图标、带 `contentDescription` 的 `clickable` `Icon`，以及标签被隐藏的导航项（`NavigationBarItem`、`NavigationRailItem`、`NavigationDrawerItem`、`navigationSuiteItems`、`Tab`），例如 `alwaysShowLabel = false` 或折叠的导航栏（rail）。
2. 含义不清的工具栏操作，以及隐藏了键盘快捷键的控件。
3. 跳过那些通过可见文本已经足够清楚的控件。绝不要把工具提示作为标签、指令、校验错误或禁用状态要求的唯一来源。
4. 检查长按是否已经触发拖拽、选择或上下文菜单。如果冲突，跳过工具提示。

对每个工具提示，使用本地化字符串和简短、句式大小写（sentence-case）的文本：

- 从控件的无障碍标签出发：对于仅图标控件，`Icon` 的 `contentDescription` 通常就是正确的工具提示文本。两者复用同一个字符串资源，以免出现漂移，并保留图标上的 `contentDescription` --- 工具提示永远不替代它。
- 描述动作时优先用动词：`Add column`、`Export CSV`、`Mute track`。
- 纯文本工具提示要保持简短清晰。
- 不要重复按钮上可见的文字，除非工具提示补充了快捷键或后果。
- 只在准确时添加快捷键提示，例如 `Save (Ctrl+S)`。
- 对于禁用状态的控件，说明其要求：`Select a row first`。

### 步骤 2：实现工具提示

遍历已确认的目标，按以下模式为每个目标实现工具提示：

- **复用已有组件：** 对重复出现的工具提示使用共享包装组件，对一次性工具提示使用内联 `TooltipBox`。
- **工具提示类型：** 简短标签使用 `PlainTooltip`。额外细节或单个操作使用 `RichTooltip`。
- **工具提示触发方式：** 使用默认的悬停效果、长按和键盘焦点行为，除非工具提示只应从代码中显示。

- **API：** `TooltipBox(positionProvider, tooltip = { PlainTooltip { Text(...) }
  }, state = rememberTooltipState()) { control }`。先检查 Gradle 文件中的 Material 3 版本：在 1.4.0 或更新版本上使用
  `TooltipDefaults.rememberTooltipPositionProvider(positioning =
  TooltipAnchorPosition.Above)`；在 1.3.x 上该函数不存在，使用
  `TooltipDefaults.rememberPlainTooltipPositionProvider()`。

遵循以下规则：

- 给每个 `TooltipBox` 自己的 `TooltipState`。
- 只包装一个控件。把点击、焦点、启用状态和无障碍都保留在控件上，并让包装边界保持紧凑。
- 带操作的富工具提示要使用 `rememberTooltipState(isPersistent =
  true)`, set `hasAction = true`，并在执行操作后关闭它。
- 结束前重新运行步骤 1 中的搜索：每一处匹配现在都有工具提示，或有明确的跳过理由。不要只处理第一个屏幕就停止。

#### 从代码中显示工具提示（可选）

仅用于简短、非必需的帮助，例如功能引导。

- 在协程中调用 `tooltipState.show()`。
- 不再需要工具提示时直接调用 `tooltipState.dismiss()`。
- 如果不应通过悬停效果、长按和键盘焦点显示它，设置 `enableUserInput = false`。
- 从用户事件或一次性 effect 中触发 `show()`，不要在组合期间直接触发。

## 参考链接

在开始实现之前，先查阅以下参考资料。

- AndroidX Material 3 工具提示[示例](https://android.googlesource.com/platform/frameworks/support/+/androidx-main/compose/material3/material3/samples/src/main/java/androidx/compose/material3/samples/TooltipSamples.kt)
- Material Design 3 工具提示[指南](https://m3.material.io/components/tooltips/guidelines)
