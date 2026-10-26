相机操作是移动设备上最耗电的任务之一。如果不主动管理，系统会限制硬件、丢帧，或者强制关闭相机应用。

## 热管理策略

| 优先级 | 策略 | 实现 |
|---|---|---|
| **1. 告知** | 用例提示 | 提供 `StreamUseCase`，让系统优化硬件。 |
| **2. 监控** | 热状态监听器 | 观察 `PowerManager.addThermalStatusListener`。 |
| **3. 处置** | 优雅降级 | 动态降低 FPS、分辨率，或禁用 HDR 这类高负载效果。 |

*** ** * ** ***

## 遵循实现指南

### Stream use case 优化

Android 13（API 级别 33）引入 `StreamUseCase`。这是告诉硬件如何权衡画质与功耗的**最有效**方式。


```kotlin
// In CameraX: Set the hint on your Use Case
val preview = Preview.Builder()
    .setTargetName("Preview")
    .apply {
        Camera2Interop.Extender(this).setStreamUseCase(
            CameraMetadata.SCALER_AVAILABLE_STREAM_USE_CASES_VIDEO_CALL.toLong()
        )
    }
    .build()
```

<br />

以下是流优化中的几个关键用例：

- `PREVIEW`：该选项是默认值，提供均衡的配置。
- `STILL_CAPTURE`：该选项为短时连拍提供高质量捕获。
- `VIDEO_RECORD`：该选项保持持续功耗，并针对编码优化。
- `VIDEO_CALL`：该选项为长时间会话最小化功耗。

### 监控热状态

不要等到崩溃。监控 `PowerManager` 状态，在达到 `THERMAL_STATUS_CRITICAL` 之前就做出反应。


```kotlin
val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
powerManager.addThermalStatusListener { status ->
    when (status) {
        PowerManager.THERMAL_STATUS_MODERATE -> {
            // Signal to UI: "Device is warming up"
        }
        PowerManager.THERMAL_STATUS_SEVERE -> {
            // ACTION: Reduce Frame Rate from 60fps to 30fps
            // ACTION: Disable HDR or High-Quality Post-processing
        }
        PowerManager.THERMAL_STATUS_CRITICAL -> {
            // ACTION: Close the camera session to prevent hardware damage
        }
    }
}
```

<br />

### 优雅降级层级

| 层级 | 措施 | 用户影响 |
|---|---|---|
| **轻微** | 停止使用 ML Kit 的后台分析 | 极小 |
| **中等** | 把帧率限制到 30 FPS | 可察觉但流畅 |
| **严重** | 把分辨率从 1080p 降到 720p | 画面明显变化 |
| **危急** | 关闭会话 | 应用处于安全模式，不可用 |

*** ** * ** ***

## 热相关陷阱

- **「双重工作」缺陷**：除非确有必要，不要同时运行两个不同宽高比的高分辨率流——例如预览流和视频捕获流。这会迫使图像信号处理器（ISP）做双倍的缩放工作，产生过多热量。
- **Surface 过载**：在 `THERMAL_STATUS_SEVERE` 期间，不要使用多级 `SurfaceProcessor` 或 `Media3Effect` 链。
- **闪光灯发热**：使用闪光灯或手电筒会产生高热负载。如果热状态为 `SEVERE`，主动关闭闪光灯。
