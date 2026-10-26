## 移除 `Camera1` 实现

1. 删除所有 `android.hardware.Camera` 实例。
2. 删除 `SurfaceView` 和 `SurfaceHolder.Callback` 中 `surfaceCreated`、`surfaceChanged` 和 `surfaceDestroyed` 的实现。
3. 移除在 `onResume` 或 `onPause` 中打开或释放相机的自定义生命周期处理。
4. 移除针对方向的手动矩阵计算。

## 初始化 `ProcessCameraProvider`

请求 `ProcessCameraProvider`，并把使用场景绑定到 Activity 或 Fragment 的生命周期。


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

  cameraProvider.unbindAll() // Unbind before rebinding

  val camera = cameraProvider.bindToLifecycle(
    lifecycleOwner,
    cameraSelector,
    preview,
    imageCapture
  )
  val cameraControl = camera.cameraControl
}
```

<br />

## 实现预览与点击对焦

根据应用的 UI 工具包，从下列模式中只选一种：

### 方案 A：面向 Android Views

使用 `androidx.camera.view.PreviewView`。

1. **配置预览**：


   ```kotlin
   preview.setSurfaceProvider(previewView.surfaceProvider)
   ```

   <br />

2. **处理点击对焦**：


   ```kotlin
   val factory = previewView.meteringPointFactory
   val point = factory.createPoint(x, y) // x, y from touch event
   val action = FocusMeteringAction.Builder(point, FocusMeteringAction.FLAG_AF).build()
   cameraControl?.startFocusAndMetering(action)
   ```

   <br />

### 方案 B：面向 Jetpack Compose

使用 `androidx.camera.compose.CameraXViewfinder`。

1. **配置预览与 SurfaceRequest**：


   ```kotlin
   var surfaceRequest by remember { mutableStateOf<SurfaceRequest?>(null) }
   val preview = remember {
     Preview.Builder().build().apply {
       setSurfaceProvider { request -> surfaceRequest = request }
     }
   }
   ```

   <br />

2. **渲染取景器**：


   ```kotlin
   surfaceRequest?.let { request ->
     CameraXViewfinder(
       surfaceRequest = request,
       coordinateTransformer = coordinateTransformer,
       modifier = Modifier
     )
   }
   ```

   <br />

3. **在 Compose 中处理点击对焦**：


   ```kotlin
   // Inside your tap gesture handler...
   val surfaceCoords = with(coordinateTransformer) { offset.transform() }
   val factory = SurfaceOrientedMeteringPointFactory(
     request.resolution.width.toFloat(),
     request.resolution.height.toFloat()
   )
   val point = factory.createPoint(surfaceCoords.x, surfaceCoords.y)
   val action = FocusMeteringAction.Builder(point, FocusMeteringAction.FLAG_AF).build()
   cameraControl?.startFocusAndMetering(action)
   ```

   <br />

4. **为 Compose 更新目标旋转**：


   ```kotlin
   LaunchedEffect(configuration) {
     if (!view.isInEditMode) {
       val rotation = view.display?.rotation ?: Surface.ROTATION_0
       imageCapture.targetRotation = rotation
       preview.targetRotation = rotation
     }
   }
   ```

   <br />

## 拍摄照片

使用 `ImageCapture` 使用场景拍照。`ImageProxy` 会直接处理旋转。


```kotlin
imageCapture.takePicture(
  cameraExecutor,
  object : ImageCapture.OnImageCapturedCallback() {
    override fun onCaptureSuccess(image: ImageProxy) {
      val buffer = image.planes[0].buffer
      val bytes = ByteArray(buffer.remaining())
      buffer.get(bytes)
      val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)

      // Adjust rotation natively via ImageProxy
      val matrix = Matrix()
      matrix.postRotate(image.imageInfo.rotationDegrees.toFloat())
      if (lensFacing == CameraSelector.LENS_FACING_FRONT) {
        matrix.postScale(-1f, 1f) // Mirror for front camera
      }

      val rotatedBitmap = Bitmap.createBitmap(
        bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
      )

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

## 切换摄像头

要在前置和后置摄像头之间切换，更改 `CameraSelector` 并重新触发 `ProcessCameraProvider` 逻辑。


```kotlin
lensFacing = if (lensFacing == CameraSelector.LENS_FACING_BACK) {
  CameraSelector.LENS_FACING_FRONT
} else {
  CameraSelector.LENS_FACING_BACK
}
```

<br />

## 遵循约束

- **不要手动管理相机生命周期**：通过 `ProcessCameraProvider` 把相机绑定到 `LifecycleOwner`。避免在 `onResume` 或 `onPause` 中手动打开或关闭相机的逻辑。
- **不要手动计算对焦矩阵**：`MeteringPointFactory` 会处理坐标变换，包括设备旋转偏移。避免自定义矩阵实现。
- **不要忘记关闭 `ImageProxy`**：记得在拍摄回调中调用 `image.close()`。跳过这次调用会锁住拍摄管线并中断后续拍照。
- **不要在 Compose 代码中把 `PreviewView` 包进 `AndroidView`**：对于 Compose UI 布局，使用 `CameraXViewfinder`。在 `AndroidView` 中编译 `PreviewView` 是较早的兜底方案，会引入尺寸调整问题。