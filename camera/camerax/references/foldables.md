折叠屏设备给相机应用带来了独特挑战，包括动态布局变化、多种显示方向，
以及桌面模式和书本模式这类物理设备姿态。

## 管理折叠状态与姿态

| 状态 | 姿态 | 用户交互 | 实现目标 |
|---|---|---|---|
| `FLAT` | 标准 | 全屏预览 | 常规手机布局。 |
| `HALF_OPENED` | 桌面 | 下半屏放控件 | 分屏布局，取景器在上，控件在下。 |
| `HALF_OPENED` | 书本 | 并排 | 一侧面板放取景器，另一侧放图库和控件。 |

*** ** * ** ***

## 遵循实现指南

### 检测姿态变化

使用 Jetpack WindowManager 库观察设备的铰链状态和折叠布局。


```kotlin
lifecycleScope.launch {
    lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
        windowInfoTracker.windowLayoutInfo(activity)
            .collect { layoutInfo ->
                val displayFeature = layoutInfo.displayFeatures
                    .filterIsInstance<FoldingFeature>()
                    .firstOrNull()

                updateCameraLayout(displayFeature)
            }
    }
}
```

<br />

### 处理桌面模式

在桌面模式（横向折叠）下，应把取景器移到屏幕上半部分、控件移到下半部分，
避免用户看到「弯折」的画面。

- **辨别方向：** 检查 `FoldingFeature.orientation`。
- **计算几何：** 使用 `FoldingFeature.bounds` 确定铰链在屏幕上的物理位置。
- **更新 UI：** 通过 padding 或约束把 `PreviewView` 移到铰链上方。

### 坐标映射与 `Viewport`

当折叠导致 UI 布局变化时，你**必须**更新 `Viewport`，
以确保点击对焦和图像拍摄的坐标仍然准确。


```kotlin
val viewport = ViewPort.Builder(Rational(viewfinder.width, viewfinder.height), display.rotation)
    .setScaleType(ViewPort.FILL_CENTER)
    .build()

val useCaseGroup = UseCaseGroup.Builder()
    .addUseCase(preview)
    .setViewPort(viewport)
    .build()
```

<br />

### 后置显示屏模式

有些折叠屏允许在设备展开时用外屏配合后置摄像头拍摄。

- **验证：** 如果 OEM SDK 或 Android 14（API 级别 34）及以上提供支持，检查 `DeviceState.REAR_DISPLAY_STATE`。
- **逻辑：** 处理在不同宽高比的显示表面上预览的分离与重新附加。

*** ** * ** ***

## 折叠屏常见陷阱

- **铰链畸变：** 在 `HALF_OPENED` 状态下不要把相机预览跨过铰链。
- **物理方向：** 折叠或展开设备时，相机传感器相对屏幕的物理方向通常会变化。始终依赖 `CameraInfo.getSensorRotationDegrees`。
- **延迟：** 在折叠事件中重新绑定 `UseCase` 对象代价很高。在执行完整的 `bindToLifecycle` 重配置之前，先使用 `PreviewView` 的内部缩放。
