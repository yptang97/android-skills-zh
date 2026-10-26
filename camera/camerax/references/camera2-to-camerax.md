Camera2 提供细粒度控制，但会引入样板代码：管理
`CameraDevice` 状态、`CameraCaptureSession` 生命周期、后台线程、
`HandlerThread`，以及手动的方向计算。

CameraX 通过把 `Preview`、`ImageCapture`、`ImageAnalysis` 这类高层 `UseCase`
直接绑定到 Android 生命周期来简化这些工作，并自动处理线程管理和设备专属的规避方案。

*** ** * ** ***

## 移除 Camera2 样板代码

迁移到 CameraX 后可以删掉手动配置代码：

1. **删除手动线程处理** ：移除专用于相机后台任务的 `HandlerThread`、`Handler` 和 executor。CameraX 自己管理线程。
2. **移除会话与设备回调** ：删除 `CameraDevice.StateCallback` 与 `CameraCaptureSession.StateCallback` 实现。
3. **移除 Surface 管理** ：移除把 `Surface` 对象从 `TextureView` 或 `SurfaceView` 手动路由到相机设备的代码。
4. **移除手动方向逻辑** ：删除为调整预览与拍摄方向而涉及 `CameraCharacteristics.SENSOR_ORIENTATION` 和屏幕旋转的计算。

*** ** * ** ***

## 初始化 `ProcessCameraProvider`

请求 `ProcessCameraProvider`，并把你的 use case 绑定到作为 `LifecycleOwner` 的
Activity 或 Fragment。这取代了
`CameraManager.openCamera` 流程。


```kotlin
val context = LocalContext.current
val lifecycleOwner = LocalLifecycleOwner.current
LaunchedEffect(context, lifecycleOwner) {
  val cameraProvider = ProcessCameraProvider.getInstance(context).await()

  val cameraSelector = CameraSelector.Builder()
    .requireLensFacing(CameraSelector.LENS_FACING_BACK)
    .build()

  val preview = Preview.Builder().build()
  val imageCapture = ImageCapture.Builder()
    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
    .build()

  // ImageAnalysis is common when migrating from Camera2 ImageReader
  val imageAnalysis = ImageAnalysis.Builder()
    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
    .build()

  cameraProvider.unbindAll()

  val camera = cameraProvider.bindToLifecycle(
    lifecycleOwner,
    cameraSelector,
    preview,
    imageCapture,
    imageAnalysis
  )
}
```

<br />

*** ** * ** ***

## 实现预览与点击对焦

CameraX 会自动处理 surface 配置。根据你的 UI 工具包选择：

### 方案 A：用于 Android Views

在布局中使用 `androidx.camera.view.PreviewView`，并把它绑定到
`Preview` use case。


```kotlin
preview.setSurfaceProvider(previewView.surfaceProvider)
```

<br />

### 方案 B：用于 Jetpack Compose

使用 `androidx.camera.compose.CameraXViewfinder`。


```kotlin
var surfaceRequest by remember { mutableStateOf<SurfaceRequest?>(null) }
val preview = remember {
  Preview.Builder().build().apply {
    setSurfaceProvider { request -> surfaceRequest = request }
  }
}
```

<br />

*** ** * ** ***

## 拍摄照片

用 `ImageCapture` use case 取代 `ImageReader` 拍摄流程和
`CaptureRequest.Builder.TEMPLATE_STILL_CAPTURE`。CameraX 会利用返回的 `ImageProxy`
原生处理旋转。


```kotlin
imageCapture.takePicture(
  cameraExecutor,
  object : ImageCapture.OnImageCapturedCallback() {
    override fun onCaptureSuccess(image: ImageProxy) {
      val buffer = image.planes[0].buffer
      val bytes = ByteArray(buffer.remaining())
      buffer.get(bytes)
      val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
      if (bitmap != null) {
        val matrix = Matrix()
        matrix.postRotate(image.imageInfo.rotationDegrees.toFloat())
        if (lensFacing == CameraSelector.LENS_FACING_FRONT) {
          matrix.postScale(-1f, 1f)
        }

        val rotatedBitmap = Bitmap.createBitmap(
          bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
        )
      }

      // MUST close proxy
      image.close()
    }

    override fun onError(exception: ImageCaptureException) {
      Log.e("CameraX", "Capture failed: ${exception.message}", exception)
    }
  }
)
```

<br />

*** ** * ** ***

## 实现图像分析

如果你原本在 Camera2 中使用 `ImageReader` 访问原始帧，例如用于二维码
扫描或 ML，请改用 CameraX 的 `ImageAnalysis` use case。


```kotlin
imageAnalysis.setAnalyzer(cameraExecutor) { imageProxy ->
  try {
    val rotationDegrees = imageProxy.imageInfo.rotationDegrees
    // Process image here (e.g., run object detection)
    // ...
  } finally {
    // MUST close the imageProxy to avoid blocking the pipeline
    imageProxy.close()
  }
}
```

<br />

*** ** * ** ***

## 使用 Camera2 interop

如果你的应用需要 CameraX 未直接暴露的特定 Camera2 配置项，例如自定义
曝光模式或闪光灯设置，可以使用 `Camera2Interop` 把它们应用到你的 CameraX use case 上。


```kotlin
// Use Camera2Interop to set Camera2-specific capture options
val extender = Camera2Interop.Extender(imageCaptureBuilder)
extender.setCaptureRequestOption(
  CaptureRequest.CONTROL_AE_MODE,
  CaptureRequest.CONTROL_AE_MODE_OFF
).setCaptureRequestOption(
  CaptureRequest.FLASH_MODE,
  CaptureRequest.FLASH_MODE_TORCH
)
```

<br />

*** ** * ** ***

## 遵守约束

- **不要手动打开 CameraDevice** ：让 CameraX 通过 `bindToLifecycle` 管理设备的打开与关闭。
- **不要忘记关闭 `ImageProxy`** ：在 `ImageCapture` 和 `ImageAnalysis` 的回调中，你**必须**调用 `image.close()`。否则会阻塞相机流水线。
- **不要阻塞 ImageAnalysis 线程** ：分析器逐帧运行。如果需要执行重量级计算，请把它们转移到后台 worker，并尽快关闭 `ImageProxy`。
