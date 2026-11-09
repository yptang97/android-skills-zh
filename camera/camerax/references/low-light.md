本指南介绍如何使用 **Night mode extensions** 和 **Low Light Boost（LLB）** 实现低光功能。

## 选择合适的工具

| 功能 | 用途 | 实现 | 用户体验影响 |
|---|---|---|---|
| **Night mode** | 高质量静态照片 | `ExtensionsManager` | 可能需要用户保持静止数秒。 |
| **LLB，AE 模式** | 实时预览或视频 | `Camera2Interop`、CameraX 工具 | 硬件会降低帧率来提升亮度。 |
| **LLB，Play services** | 实时预览与视频 | `SurfaceProcessor` | 基于软件提亮；能保持较高帧率。 |

*** ** * ** ***

## Night mode 扩展

CameraX Extensions 提供对设备内置计算摄影管线的访问。

### 基本配置

要配置该扩展，先初始化扩展管理器：


```kotlin
/** Binds Night mode with ExtensionSessionConfig (CameraX 1.6.0 and higher). */
suspend fun bindNightMode(
    context: Context,
    lifecycleOwner: LifecycleOwner,
    cameraProvider: ProcessCameraProvider,
    preview: Preview,
    imageCapture: ImageCapture,
): Boolean {
    // Suspend version of getInstanceAsync (CameraX 1.6.0 and higher).
    val extensionsManager = ExtensionsManager.getInstance(context, cameraProvider)
    val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
    if (!extensionsManager.isExtensionAvailable(cameraSelector, ExtensionMode.NIGHT)) {
        return false // Bind without the extension instead.
    }
    // ImageAnalysis isn't supported in extension sessions.
    val config = ExtensionSessionConfig.Builder(ExtensionMode.NIGHT, extensionsManager)
        .addUseCase(preview)
        .addUseCase(imageCapture)
        .build()
    cameraProvider.unbindAll()
    cameraProvider.bindToLifecycle(lifecycleOwner, cameraSelector, config)
    return true
}
```

<br />

### 完整功能

- **Image postview**：在多帧处理进行期间立即显示一张低分辨率图像。

  ```kotlin
  fun buildPostviewImageCapture(): ImageCapture =
      ImageCapture.Builder()
          .setPostviewEnabled(true)
          .build()
  ```
- **Extension strength**：让用户控制夜景效果的强度。

  ```kotlin
  /** Sets the active extension's strength, from 0 to 100. */
  suspend fun setExtensionStrength(
      context: Context,
      cameraProvider: ProcessCameraProvider,
      camera: Camera,
      strength: Int,
  ) {
      val extensionsManager = ExtensionsManager.getInstance(context, cameraProvider)
      // Null when the bound camera has no active extension.
      extensionsManager.getCameraExtensionsControl(camera.cameraControl)
          ?.setExtensionStrength(strength)
  }
  ```
- **Capture progress**：为长曝光显示 UI 进度条。

  ```kotlin
  /**
   * Captures to a file and reports progress for long exposures. The callbacks
   * fire only when ImageCapture.getImageCaptureCapabilities(cameraInfo) reports
   * support.
   */
  suspend fun captureWithProgress(
      imageCapture: ImageCapture,
      outputOptions: ImageCapture.OutputFileOptions,
      onProgress: (percent: Int) -> Unit,
      onPostview: (Bitmap) -> Unit,
  ) {
      try {
          val result = imageCapture.takePicture(
              outputOptions,
              onCaptureProcessProgressed = onProgress,
              onPostviewBitmapAvailable = onPostview,
          )
          Log.d("CameraX", "Saved ${result.savedUri}")
      } catch (e: ImageCaptureException) {
          Log.e("CameraX", "Capture failed", e)
      }
  }
  ```

*** ** * ** ***

## 低光增强

LLB 面向偏爱高帧率的预览流与视频流。

### AE 模式

CameraX 内置的优先提升亮度的方式。它会修改硬件的自动曝光算法。

- **启用**：使用 `CameraControl.enableLowLightBoostAsync`。
- **实现**：

  ```kotlin
  /**
   * Enables AE-mode Low Light Boost. Requires CameraX 1.5.0 or higher,
   * Android 15 (API level 35) or higher, and device support.
   */
  fun enableLowLightBoost(
      camera: Camera,
      lifecycleOwner: LifecycleOwner,
      executor: Executor,
  ): Boolean {
      // lowLightBoostState is always OFF on unsupported devices, so it can't
      // be used as the availability check.
      if (!camera.cameraInfo.isLowLightBoostSupported) return false

      val future = camera.cameraControl.enableLowLightBoostAsync(true)
      future.addListener({
          try {
              future.get()
          } catch (e: ExecutionException) {
              // IllegalStateException: unsupported or a settings conflict.
              Log.w("CameraX", "Low Light Boost not enabled", e.cause)
          }
      }, executor)

      camera.cameraInfo.lowLightBoostState.observe(lifecycleOwner) { state ->
          val isBoosting = state == LowLightBoostState.ACTIVE
          Log.d("CameraX", "Low Light Boost active: $isBoosting")
      }
      return true
  }
  ```
- **监控**：观察 `CameraInfo.lowLightBoostState`，跟踪硬件何时真正应用该增强。

### Google Play services LLB

这是一个多步实现，使用基于会话的 `SurfaceProcessor`。

**依赖**：`com.google.android.gms:play-services-camera-low-light-boost`

要实现 Google Play services LLB，按以下核心步骤操作：

1. **初始化客户端**：`val client = LowLightBoost.getClient`。
2. **实现 `SurfaceProcessor`**：
   - **管理会话**：调用 `client.createSession`。
   - **转发所需元数据**：观察相机的 `TotalCaptureResult` 流，把每个结果转发给会话：`session.processCaptureResult`。
   - **提供 Surface**：从会话取输入 Surface，`session.getCameraSurface`，并提供给相机的 `SurfaceRequest`。
   - **生命周期**：在处理器关闭或 `SurfaceRequest` 完成时释放会话，`session.release`。
3. **通过 `CameraEffect` 接入**：

   ```kotlin
   /** CameraEffect's constructors are protected, so subclass it. */
   class LowLightBoostEffect(
       surfaceProcessor: SurfaceProcessor,
       executor: Executor,
       onError: Consumer<Throwable>,
   ) : CameraEffect(
       CameraEffect.PREVIEW or CameraEffect.VIDEO_CAPTURE,
       executor,
       surfaceProcessor,
       onError,
   )

   fun buildLowLightBoostUseCaseGroup(
       preview: Preview,
       videoCapture: VideoCapture<Recorder>,
       llbSurfaceProcessor: SurfaceProcessor,
       executor: Executor,
   ): UseCaseGroup {
       val effect = LowLightBoostEffect(llbSurfaceProcessor, executor) { error ->
           Log.e("CameraX", "Low Light Boost effect failed", error)
       }
       // Bind the group with cameraProvider.bindToLifecycle(owner, selector, group).
       return UseCaseGroup.Builder()
           .addUseCase(preview)
           .addUseCase(videoCapture)
           .addEffect(effect)
           .build()
   }
   ```
4. **场景检测**：使用 `session.setSceneDetectorCallback` 接收 `boostStrength` 更新，用于实时 UI 指示。

*** ** * ** ***

## 实现说明

- **线程安全**：始终以异步方式处理 `ExtensionsManager` 和 `LowLightBoostClient` 的初始化。
- **FPS 取舍**：AE 模式的 LLB 往往会大幅降低帧率来提升亮度。
- **兼容性**：Extensions、Night Mode 可能与 `ConcurrentCamera` 冲突。绑定时务必先确认支持情况。
