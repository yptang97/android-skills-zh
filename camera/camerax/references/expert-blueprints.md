复杂的相机功能如果在单轮对话里一次性尝试，常会因「Agent Stall」或超时而失败。用这些蓝图把任务拆成可管理的阶段。

## 手动控制

### 阶段一：ViewModel 与状态

1. 定义一个 `ManualSettings` 数据类。
2. 在你的 `CameraViewModel` 中添加一个 `MutableStateFlow<ManualSettings>`。
3. 用滑块和开关实现 Jetpack Compose UI，用来更新这个 Flow。

### 阶段二：控制器接线

1. 在 `CameraController.kt` 中新建函数 `updateManualSettings(settings: ManualSettings)`。
2. 把这些设置映射到 `CameraSystem` 层。

### 阶段三：CameraX `Camera2Interop` 接线

1. 在 `CameraSession.kt` 中，用 `Camera2Interop.Extender` 工具访问 Camera2 的捕获请求键。
2. 应用这些硬件键：
   - `CaptureRequest.SENSOR_SENSITIVITY`，用于设置 ISO 感光度。
   - `CaptureRequest.SENSOR_EXPOSURE_TIME`，用于设置曝光时间。
   - `CaptureRequest.LENS_FOCUS_DISTANCE`，用于设置对焦距离。
3. **关键**：如果手动曝光已启用，把 `CaptureRequest.CONTROL_AE_MODE` 设为 `CameraMetadata.CONTROL_AE_MODE_OFF`。 ---

## RAW 与 JPEG 捕获

### 阶段一：输出配置

1. 用 `CameraInfo` 确认设备是否支持 RAW 捕获。
2. 用 `OUTPUT_FORMAT_RAW_JPEG` 或 `OUTPUT_FORMAT_RAW` 配置 `ImageCapture.Builder`。

### 阶段二：实现

1. 为目标存储位置提供 `ImageCapture.OutputFileOptions`。
2. 调用 `takePicture`。CameraX 在内部管理 `DngCreator`，用所需的 `CameraCharacteristics` 和 `CaptureResult` 元数据包装 RAW 数据。

*** ** * ** ***

## 应用图像效果

### 阶段一：选择效果

1. 使用 `androidx.media3:media3-effect` 依赖。
2. 使用 `RgbFilter` 或 `HslAdjustment` 完成常规调色。

### 阶段二：应用

1. 用效果列表配置 `Composition.Builder` 或 `MediaItem.Builder`。
2. 通过 `setEffects` 方法把效果列表注入 CameraX 的 `Recorder` 或 `Preview`。

*** ** * ** ***

## 低光拍摄

关于 Night Mode Extensions 与 Low Light Boost 的指引，见
[low-light.md](https://developer.android.com/agents/skills/camera/camerax/references/low-light)。
