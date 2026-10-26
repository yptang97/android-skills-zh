---
name: camerax
description: 为使用 CameraX 进行 Android 相机开发提供技术指导。
  在实现相机功能、处理异步录制生命周期、使用 CameraX 进行低层硬件互操作，
  或集成 ML Kit 或 Media3 效果时使用。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-08'
  keywords:
  - recipe
  - Android
  - Camera
  - Camera1
  - Camera2
  - CameraX
  - migration
  - Compose
  - guide
  - dependencies
  - PreviewView
  - CameraXViewfinder
  - ImageCapture
  - VideoCapture
  - ImageAnalysis.
---

这个 skill 为在 Android 上构建相机应用提供流程式指导与标准模式，重点是
CameraX（包括其 `Camera2Interop` 工具）以及 Media3 集成。

## 核心工作流

### 处理不可变 API 模式

各种 Android 相机与媒体 API，尤其是 CameraX 的 `VideoCapture`，使用一种
**流式、不可变的 builder 风格模式**，其中方法会返回新实例。
如果没有重新赋值这些返回值，像音频这样的设置就会被忽略。

**模式：必须重新赋值**


```kotlin
// WRONG
run {
  val pending = recorder.prepareRecording(context, opts)
  pending.withAudioEnabled() // This returns a new instance which is ignored
  val active = pending.start(exec, listener)
}

// CORRECT
run {
  val pending = recorder.prepareRecording(context, opts)
      .withAudioEnabled() // Chaining works
  val active = pending.start(exec, listener)
}

// ALSO CORRECT
run {
  var pending = recorder.prepareRecording(context, opts)
  pending = pending.withAudioEnabled() // Reassignment
  val active = pending.start(exec, listener)
}
```

<br />

受影响的类清单见[不可变性](references/immutability.md)。

### 迁移到 CameraX

在把遗留相机代码库迁移到 CameraX Jetpack 库时：

- **Camera1 到 CameraX**：迁移遗留的 `android.hardware.Camera` 实现、surface 处理与手动生命周期时，见 [Camera1 迁移指南](references/camera1-to-camerax.md)。
- **Camera2 到 CameraX**：迁移较新但冗长的 `android.hardware.camera2` 实现、会话状态回调与互操作模式时，见 [Camera2 迁移指南](references/camera2-to-camerax.md)。

### 全面的功能蓝图设计

对于涉及多个文件和硬件层接线的多步骤功能，遵循
[结构化蓝图](references/expert-blueprints.md) 方法来避免
系统超时。这类复杂功能包括：

- **手动控制**：拆分为 `ViewModel` 状态、控制器层，以及会话中的 `Camera2Interop` 接线。
- **RAW 拍摄**：把 JPEG 与 RAW 输出配置拆成独立的构建步骤。
- **自定义效果**：优先使用 `Media3Effect` 或 `SurfaceProcessor`，而非手动 OpenGL 管线，除非绝对需要极致性能。
- **低光**：夜视模式与 LLB 的指导见[低光](references/low-light.md)。
- **折叠屏**：处理动态姿态与铰链状态的指导见[折叠屏](references/foldables.md)。
- **XR、AR 与 VR**：空间跟踪、透视同步与延迟护栏的指导见[XR](references/xr.md)。
- **散热与功耗**：管理 `StreamUseCase` 优化与 `PowerManager` 热状态的指导见[散热](references/thermals.md)。
- **测试与模拟**：使用 `FakeCameraConfig`、处理异步生命周期、验证分析管线的指导见[测试](references/testing.md)。
- **ML Kit 空间分析**：坐标映射、旋转逻辑与镜像镜头处理的指导见[ML Kit 空间分析](references/mlkit-spatial.md)。
- **Wear OS 相机遥控**：圆形 UI 约束、Data Layer API 同步与远程触发逻辑的指导见[Wear OS](references/wear-os.md)。

分步指南见 [expert-blueprints](references/expert-blueprints.md)。

### API 发现

始终使用更高层抽象，而不是手动低层接线：

- **分析**：使用 `MlKitAnalyzer`，而不是手写 `ImageAnalysis.Analyzer`。
- **滤镜与效果**：标准后处理使用 `Media3Effect`。
- **多摄像头**：双流配置使用 `ConcurrentCamera` API。

当前建议见 [modern-apis](references/modern-apis.md)。

### 代码质量与架构规则

在构建相机实现时，遵循以下 Android 生态标准模式：

- **测试：用 fake 而非 mock**：避免使用 `Mockito` 这类 mock 库，尤其是针对 `ImageProxy` 这类多步骤 CameraX 接口。构建「Fake」来验证状态，而不是依赖不可靠的实现细节。
- **Google Truth 断言**：优先使用 `assertThat` 而不是 `assertEquals` 这类标准 `JUnit` 断言，以提升可读性。
- **显式测试运行器**：始终为测试类定义显式的 `@RunWith`，确保 CI 环境能正确执行它们。
- **语义 UI 合并**：在 Compose 中构建自定义相机控件时（例如带 `Icon` 和 `Text` 的按钮），使用 `semantics {
  mergeDescendants = true }` 确保屏幕阅读器把它们作为一个连贯整体来播报。

## 硬件与设备多样性

相机应用运行在种类繁多的硬件上，从手机、折叠屏到平板、笔记本，甚至智能家电。
要考虑应用所运行的具体硬件。

- **形态因素**：考虑折叠屏和平板上的屏幕尺寸与方向变化。
- **多摄像头阵列**：有些设备有后置摄像头和前置摄像头。另一些设备有多个后置摄像头，例如广角和长焦镜头。
- **功能对等**：闪光灯或自动对焦这类功能在不同硬件上行为不同。例如，CameraX 同时处理物理闪光灯（背面）和基于屏幕的闪光灯（正面），在实现闪光灯功能时两者都要考虑。

## 常见陷阱

- **异步生命周期**：在尝试停止或暂停之前检查 `isRecording` 状态。UI 状态更新要处理 `VideoRecordEvent.Start`，而不只是初始调用。
- **线程安全**：相机回调通常运行在后台 executor 上。把 UI 更新派发到主线程。
- **权限处理**：检查 `CAMERA` 权限；在 `VideoCapture` 中启用音频时要专门检查 `RECORD_AUDIO`。
