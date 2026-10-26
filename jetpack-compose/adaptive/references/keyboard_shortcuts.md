## 说明

在 Jetpack Compose 应用中添加、重新设计或向用户公开键盘快捷键时，使用本文档。

## 工作流

### 步骤 1：盘点动作

在编写任何处理逻辑之前，先列出键盘用户可能需要的动作，以及每个动作所属的屏幕或容器：

1. 顶层导航目的地（底部栏、rail、抽屉、标签页），按显示顺序。
2. 每个屏幕的主要动作。按动作计数，而不是按按钮计数：一个「New」按钮打开含两个选项的菜单，算两个动作。
3. 应当扩展而不是重复实现的既有键盘处理：`onKeyEvent` / `onPreviewKeyEvent`、`KeyboardActions`、`onProvideKeyboardShortcuts`，以及用户输入时持有焦点的文本字段。

用步骤 2 的表格为每个条目分配快捷键，并保留这份清单。

### 步骤 2：选择快捷键

- 优先遵循常见的操作系统惯例，在 Android 上以 Ctrl 作为主要修饰键。
- 只为高频、核心的动作添加领域快捷键。
- 不要覆盖标准的文本编辑快捷键。
- 用 Escape 取消或关闭当前临时 UI。不要把它当作通用的返回导航。

当以下快捷键与应用相关时，你必须实现它们。类别一列说明每组适用于哪类应用：

| 类别 | 动作 | 快捷键 | 说明 |
|---|---|---|---|
| 通用 | 保存 | Ctrl+S | 应用有显式保存动作时使用。 |
| 通用 | 查找/搜索 | Ctrl+F | 把焦点移到搜索字段。 |
| 通用 | 新建条目 | Ctrl+N | 主要创建动作（笔记、消息、文档等）。次要创建动作使用 Ctrl+Shift+N。 |
| 通用 | 打开 | Ctrl+O | 用于打开/导入流程。 |
| 通用 | 刷新 | Ctrl+R 或 F5 | 焦点在 Web 内容上时避免使用浏览器重载。 |
| 通用 | 关闭临时 UI | Escape | 关闭当前对话框、菜单、sheet 或搜索模式。 |
| 编辑 | 撤销 / 重做 | Ctrl+Z / Ctrl+Shift+Z | 文档、画布和列表适用；文本字段本身已处理。 |
| 编辑 | 剪切 / 复制 / 粘贴 | Ctrl+X / Ctrl+C / Ctrl+V | 文本字段本身已处理；为自定义选择内容（列表项、画布对象）实现。 |
| 编辑 | 全选 | Ctrl+A | 列表和画布适用；绝不要在文本字段中覆盖它。 |
| 编辑 | 删除选中项 | Delete 或 Backspace | 文本编辑期间绝不触发。 |
| 编辑 | 放大 / 缩小 / 重置 | Ctrl+Plus / Ctrl+Minus / Ctrl+0 | 文档、图片、地图和画布。 |
| 导航 | 导航目的地 | Ctrl+1 到 Ctrl+9 | 按顺序在主要导航项（例如标签页、Navigation Rail 或抽屉项）之间切换。 |
| 导航 | 下一个 / 上一个标签页或文档 | Ctrl+Tab / Ctrl+Shift+Tab | 在当前屏幕的已打开条目间循环。 |
| 通信 | 发送消息或提交表单 | Enter | 聊天式输入。多行文本字段使用 Shift+Enter 换行。 |
| 通信 | 发送长文本内容 | Ctrl+Enter | 邮件、帖子、评论：需要 Enter 换行时使用。 |
| 通信 | 切换当前聊天 | Ctrl+Tab / Ctrl+Shift+Tab | 切换到列表中的下一个 / 上一个会话。 |
| 媒体 | 播放 / 暂停 | Space | 仅当播放器或媒体列表持有焦点时使用。 |
| 媒体 | 快退 / 快进 | 左 / 右方向键 | 步长 5-10 秒；Shift+方向键步长 30 秒到 1 分钟。 |
| 媒体 | 下一个 / 上一个曲目 | Ctrl+Right / Ctrl+Left | 播放列表和队列。 |
| 媒体 | 音量加 / 减 | 上 / 下方向键 | 仅当播放器持有焦点时使用。 |
| 媒体 | 静音 / 取消静音 | M（或 Ctrl+M） | 当 M 会输入到焦点字段时改用 Ctrl+M。 |
| 媒体 | 全屏 | F | Escape 退出全屏。 |

### 步骤 3：确定快捷键作用域

把快捷键分发器挂到 UI 层级中正确的级别：

- **应用级命令：** 把处理逻辑挂到根导航容器或主 scaffold 上（例如用于切换根导航目的地）。
- **屏幕级命令：** 把处理逻辑挂到目标屏幕内容的公共祖先上。
- **模态命令：** 把处理逻辑挂到活动对话框、菜单或 sheet 内部。
- **上下文命令：** 把处理逻辑挂到持有焦点的编辑器、画布、列表或媒体表面上。

### 步骤 4：实现快捷键处理

在相关 Composable 中用 `onPreviewKeyEvent` 处理键盘快捷键。对于必须
在文本字段持有焦点时也能生效的快捷键（Enter 或 Ctrl+Enter 发送、编辑器中的 Ctrl+S），
优先使用它而不是 `onKeyEvent`：字段会先消费这些按键，因此 `onKeyEvent` 处理逻辑
根本收不到它们。

- **过滤 KeyDown：** 检查 `event.type == KeyEventType.KeyDown` 并忽略重复事件（`event.nativeKeyEvent.repeatCount > 0`）；否则动作也会在按键释放时执行，并在按住期间反复执行。
- **管理焦点：** 按键事件只会分发给活动焦点路径。要确保目标容器或组件使用 `Modifier.focusable()` 并主动持有焦点（例如使用 `FocusRequester.requestFocus()`），才能监听这些事件。

### 步骤 5：发布到 Keyboard Shortcut Helper

步骤 1 清单中的每个快捷键都必须通过系统 Keyboard Shortcut Helper 对用户可见，
并以动作的可见名称作为标签（例如「New drawing note」）。完成之前，把
Helper 条目与你编写的处理逻辑对照一遍：相同的键、相同的修饰键，不能遗漏。

遵循 Keyboard Shortcut Helper [指南](https://developer.android.com/develop/ui/compose/touch-input/keyboard-input/keyboard-shortcuts-helper)。

## 常见陷阱

- 为少见动作添加快捷键。
- 在错误的作用域或活动焦点路径之外挂处理逻辑。
- 用不可见的根容器抢走焦点。
- 无意中用 `onPreviewKeyEvent` 拦截持有焦点的子组件的行为。
- 在重复的 `KeyDown` 事件上重复执行一次性命令。
- 消费已禁用或未处理的命令。
- 发布的 Keyboard Shortcut Helper 条目与实际分发行为不一致。

## 参考链接

在开始实现之前，先查阅这些参考资料。

- Compose 键盘输入 [指南](https://developer.android.com/develop/ui/compose/touch-input/keyboard-input/commands)
- Android 桌面键盘交互 [指引](https://developer.android.com/design/ui/desktop/guides/interaction/keyboard)
