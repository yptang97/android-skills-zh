当你使用 ML Kit 实现 face mesh、对象检测或姿态
检测等功能时，最常见的失败点是
分析图像与取景器 UI 之间的坐标不一致。

## 坐标映射思路

| 维度 | 分析帧 | 屏幕上的取景器 UI |
|---|---|---|
| 分辨率 | 固定，例如 640x480 | 动态，例如 1080x2400 |
| 旋转 | 原始缓冲区为 0° | 竖屏或横屏模式下为 90° 或 270° |
| 原点 | 缓冲区左上角 (0,0) | 屏幕左上角 (0,0) |

*** ** * ** ***

## 遵循实现指南

### 坐标变换矩阵

Android 提供 `Viewport` 和 `UseCaseGroup` API 来自动计算变换矩阵。
**不要**手动计算宽高比缩放。


```kotlin
val transform = previewView.viewPort?.let { viewPort ->
    // Use CameraX's built-in coordinate mapper
    viewPort.getTransformationMatrix(imageProxy.imageInfo.rotationDegrees)
}
```

<br />

### 处理「双重旋转」bug

ML Kit 的结果（边界框）是相对**旋转后的缓冲区**的。如果
设备处于竖屏，缓冲区往往横向为 480x640，而屏幕
是 1080x1920。

要映射坐标，请使用以下工作流：

1. 查询 `imageProxy.imageInfo.rotationDegrees`。
2. 把这个旋转传入 ML Kit 的 `InputImage`。
3. 使用 `MappingUtils.transformRect` 方法把结果 `Rect` 映射到屏幕。

### face mesh 与姿态归一化

对于高精度空间分析，例如「用户的手是否正位于某个
特定的屏幕按钮上？」，请使用 **0.0 到 1.0 的归一化坐标**。


```kotlin
// Example: Converting a Pose landmark to a Screen Coordinate
val screenX = landmark.position.x / analysisWidth * screenWidth
val screenY = landmark.position.y / analysisHeight * screenHeight
```

<br />

**警告** ：始终要考虑**镜像镜头** 。如果使用了 `LENS_FACING_FRONT`，
你必须翻转 X 坐标：`actualX = screenWidth - screenX`。

### overlay 与 canvas 裁剪

在 `PreviewView` 之上使用自定义 `GraphicOverlay` 视图。

- **缓冲区锁定** ：确保 `GraphicOverlay` 每处理一个新的 `ImageAnalysis` 帧就清空一次自己的 canvas，以避免边界框出现「残影」。

*** ** * ** ***

## 空间映射常见陷阱

- **「盒子被拉伸」bug** ：原因在于假设分析帧的宽高比 4:3 与屏幕宽高比 21:9 一致。请使用 `PreviewView.SCALE_TYPE_FILL_CENTER` 并相应映射坐标。
- **延迟** ：如果 ML 处理耗时超过 50 ms，边界框就会落后于用户的脸部。
  - **修复** ：使用 `ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST` 避免排队处理过期的帧。
- **传感器与显示旋转不一致** ：在某些平板上，传感器是横向安装的。请始终查询 `display.rotation` 和 `cameraInfo.sensorRotationDegrees`。
