为 XR 设备、头显和 AR 眼镜开发相机功能，需要从 2D 像素处理转向 3D 空间感知。

## 理解 XR 开发思路

| 概念 | 移动端关注点 | **XR 关注点** |
|---|---|---|
| **输入** | 原始相机流 | **空间跟踪（visual-inertial odometry (VIO) 或 simultaneous localization and mapping (SLAM)）** |
| **输出** | 屏幕取景器 | **立体透视与遮挡** |
| **约束** | 电池续航 | **运动到光子延迟（低于 20 ms）** |

*** ** * ** ***

## 遵循实现指南

### API 选择

在 XR 设备上，标准的 `CameraX` 实现往往受限或不够用。应始终使用空间计算的软件开发工具包（SDK）：

- **ARCore**：用 ARCore 做平面检测、深度感知和运动跟踪。
- **OpenXR**：用 OpenXR 作为 VR 与 AR 渲染和输入的跨平台标准。
- **OEM SDK**：用厂商专属库实现硬件加速的透视。

### 处理空间透视

与 2D 视口不同，XR 透视通常由系统管理。

**\[关键要求\] 帧同步**：把应用的帧时钟与头显的头戴式显示器（HMD）位姿同步。


```kotlin
// Example: Querying the spatial pose for the current camera frame
val headPose = xrSession.getHeadPose(frameTime)
val projectionMatrix = headPose.getProjectionMatrix(eyeIndex)
```

<br />

### 管理深度与遮挡

数字内容必须遵循真实世界的深度，才能保证遮挡准确。

- **深度图**：用 `ARCore` 或 `SurfaceProcessor` 访问原始深度数据，生成遮挡蒙版。
- **硬件缓冲区**：用 `HardwareBuffer` 把相机帧直接共享给 GPU，避免 CPU 侧拷贝以降低延迟。

*** ** * ** ***

## XR 陷阱

- **眩晕上限**：任何让取景器延迟超过 20 ms 的处理都会让用户不适。不要在主线程上做图像处理。
- **隐私限制**：某些 XR 设备在你尝试录制「Passthrough」图层时会返回黑帧。检查 `Session.isRecordingSupported`。
- **视场角（FOV）**：相机的 FOV 可能和显示的 FOV 不匹配。使用 SDK 的投影矩阵，而不是手工计算宽高比。
- **前台缓冲区渲染**：如果设备支持，用 `FrontBufferRenderer` 做实时叠加，绕过标准的双缓冲延迟。
