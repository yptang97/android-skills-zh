## 说明

在面向 Android 大屏和桌面环境的 Jetpack Compose 应用中添加或修改指针光标行为时，使用本文档。

## 工作流

对下面每一步，先在整个代码库中搜索列出的 API，把每一处匹配都写下来，然后再用 `Modifier.pointerHoverIcon(icon)` 在元素本身上实现。光标类型由你根据这些步骤自行选择。结束前重新运行搜索：每一处匹配要么已处理，要么有明确的跳过理由。

### 步骤 1：找到并处理可拖拽元素（Grab / Grabbing）

走查应用，找出所有能从 `TYPE_GRAB` / `TYPE_GRABBING` 光标中获益的可拖拽元素。

- **搜索：** `dragAndDropSource`、`detectDragGesturesAfterLongPress`、可重排列表项、可移动内容上的 `draggable(`。
- **示例：** 可重排列表项、可移动的浮动窗口、地图表面、可拖拽滑块，以及自定义拖放目标。
- **实现：** 对每一个元素，可移动表面使用 `PointerIcon(android.view.PointerIcon.TYPE_GRAB)` 实现光标，仅在拖拽进行中使用 `PointerIcon(android.view.PointerIcon.TYPE_GRABBING)`。

### 步骤 2：找到并处理手写与绘制元素（Crosshair）

走查应用，找出所有手写或精确绘制元素。

- **搜索：** `Canvas(`、`InProgressStrokesView`、`AndroidView` 中的绘制表面、绘制笔画或图形的 `pointerInput` 块。
- **示例：** Canvas 绘图区域、签名捕获板、图像裁剪工具和空间选择边界框。
- **实现：** 对每一个元素，使用 `PointerIcon.Crosshair` 实现光标。

### 步骤 3：找到并处理可调整尺寸的元素（Resize）

走查应用，找出所有分隔条、可调整的边缘和调整尺寸手柄。

- **搜索：** `VerticalDragHandle`、`paneExpansionDragHandle`、`paneExpansionDraggable`、sheet 的 `dragHandle =`、`anchoredDraggable`、分隔线上的 `draggable(`。
- **示例：** 分割窗格分隔线（横向或纵向）、可调整尺寸的对话框边缘、底部 sheet 的拖拽手柄。
- **实现：** 对每一个元素，实现正确的系统光标（例如纵向分隔条使用 `PointerIcon(android.view.PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW)`）。让光标方向与手柄匹配。

### 步骤 4：找到并处理可点击元素（Hand）

走查应用，找出所有链接、可点击文本和仅图标控件。

- **搜索：** `IconButton`、`IconToggleButton`、`FloatingActionButton`、`NavigationBarItem`、`NavigationRailItem`、`NavigationDrawerItem`、`navigationSuiteItems`、`Tab(`、`Icon` 或 `Text` 上的 `clickable`。
- **示例：** 文本中的超链接、独立图标按钮、导航栏、导航栏（rail）和抽屉项、标签页，以及启用的开关。
- **实现：** 对每一个元素，在元素处于启用状态时使用 `PointerIcon.Hand`。当元素处于非启用或禁用状态时，必须回退到 `PointerIcon.Default`。不要给每一个可点击表面都使用 `Hand`。

### 步骤 5：找到并处理文本选择元素（Text）

走查应用，找出所有自定义的可编辑或可选择文本区域。

- **示例：** 自定义代码编辑器、可选择的日志输出、自定义文本选择浮层。
- **实现：** 对每一个元素，使用 `PointerIcon.Text`。确保不要覆盖标准 Compose 文本框的正确默认光标。

### 步骤 6：找到并处理临时阻塞元素（Wait）

走查应用，找出短暂的、临时阻塞的区域。

- **示例：** 表单提交浮层、本地处理状态、刷新面板。
- **实现：** 对每一个元素，使用 `PointerIcon(android.view.PointerIcon.TYPE_WAIT)` 实现光标。

## 参考链接

在开始实现之前，先查阅以下参考资料。

- [Compose `pointerHoverIcon` API 参考](https://developer.android.com/reference/kotlin/androidx/compose/ui/input/pointer/package-summary#pointerHoverIcon(androidx.compose.ui.Modifier,androidx.compose.ui.input.pointer.PointerIcon,kotlin.Boolean))
- [Compose `PointerIcon` API 参考](https://developer.android.com/reference/kotlin/androidx/compose/ui/input/pointer/PointerIcon)
- [Android 指针输入概览](https://developer.android.com/develop/ui/compose/touch-input/pointer-input)
