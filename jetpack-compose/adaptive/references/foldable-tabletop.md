## 说明

### 步骤 1. 分离观看内容与交互控件

检查目标 composable（例如媒体播放器或相机预览）：

- 分离观看 composable：提取显示在竖起屏幕上的视觉内容（例如视频播放或相机预览）。
- 分离控件 composable：提取交互式触摸元素（例如播放按钮或快门控件）。

### 步骤 2. 选择布局策略

检查这些 composable 在不同配置下是否相同：

- **不要使用 `Grid` --- 改用条件布局分支（方案 A）**：当控件或内容在两种布局间不同，本来就需要两个不同的
  composable 时（例如带简单浮层按钮的平放布局，与带展开控制面板或不同参数控件的桌面布局），
  采用此方案。

- **使用 `Grid`（方案 B）**：当这些 composable（观看内容与控件）在两种配置下完全相同、只是位置
  变化时采用此方案。例如媒体播放器的播放器与控制器 composable 保持不变：平放姿态下这些 composable
  叠放，桌面姿态下分成两行。

### 步骤 3. 实现布局

#### 方案 A：使用条件布局分支（非 Grid）

当控件或内容在不同姿态下不同、每种配置需要不同的 composable 时，采用此方案。

1. 使用 `androidx.compose.ui` 中的 `mediaQuery` 观察 `windowPosture`（`import androidx.compose.ui.mediaQuery` 和 `import androidx.compose.ui.UiMediaScope`）。用 `mediaQuery { windowPosture == UiMediaScope.Posture.Tabletop }`（或 `Posture.Tabletop`）检查是否为桌面姿态。不要直接使用 `windowPosture.isTabletop`。（注意：如果尚未启用，在 `Application` 类中设置 `ComposeUiFlags.isMediaQueryIntegrationEnabled = true`）。
2. 通过 `currentWindowAdaptiveInfoV2().windowPosture`（如果使用较旧版本的库，则用 `currentWindowAdaptiveInfo().windowPosture`）从窗口姿态中获取物理的水平铰链边界。
3. 在父容器中，用 `coordinates.windowToLocal` 把铰链边界从窗口坐标转换到局部坐标（例如在 `onGloballyPositioned` 中转换 `Offset(0f, hinge.top.toFloat())` 和 `Offset(0f, hinge.bottom.toFloat())`）。当周围存在其他 UI 组件时，绝不要假设是 50/50 分割。
4. 暴露局部的铰链上、下边界（例如使用 `HorizontalRuler` 或自定义布局修饰符）：
   - 把观看 composable 约束在折叠线上方（`maxHeight` 以 `hingeTop` 为界）。
   - 把控件约束在折叠线下方并相应偏移（`maxHeight` 以 `containerHeight - hingeBottom` 为界，放置在 `y = hingeBottom`）。
5. 如果不是桌面姿态，返回标准的平放布局（例如观看 composable 填满可用空间，控件以浮层形式呈现）。

#### 方案 B：使用 Grid

1. 用 `enum` 类定义布局区域标识符。
2. 在 `defaultConfig` 中，把所有区域都分配到 `row = 1, column = 1`。`Grid` 使用隐式 z 轴排序，在布局中后声明的 composable 会渲染在先前声明的 composable 之上。
3. 在 `tabletopConfig` 中，定义两行高度为 `0.5f`，并把主内容区域分配到第 1 行、控件分配到第 2 行。
4. 使用 `mediaQuery`（来自 `androidx.compose.ui.mediaQuery`）在桌面姿态下（`windowPosture == UiMediaScope.Posture.Tabletop`）选择 `tabletopConfig`，否则选择 `defaultConfig`。
5. 把 config 传给 `Grid`，并用 `Modifier.gridItem(areaId)` 绑定内容。
6. 在 `Grid` 主体中先声明观看 composable，再声明控件 composable。这样可以验证在平放姿态下控件渲染在观看内容之上。

方案 B 的参考实现见
[桌面姿态 recipe](https://developer.android.com/develop/adaptive-apps/cookbook/tabletop-posture-media-query-grid)。
