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
/**
 * Use cases shared by both UI options. Each UI option builds its own Preview
 * with a surface provider and passes it to [bindUseCases].
 */
class CameraUseCases {
    val imageCapture: ImageCapture = ImageCapture.Builder()
        .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
        .build()

    // Replaces a Camera2 ImageReader that was used for frame processing.
    val imageAnalysis: ImageAnalysis = ImageAnalysis.Builder()
        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
        .build()
}

/**
 * Replaces CameraManager.openCamera and the session callbacks. Returns null
 * when the device has no camera for [lensFacing].
 */
suspend fun bindUseCases(
    context: Context,
    lifecycleOwner: LifecycleOwner,
    preview: Preview,
    useCases: CameraUseCases,
    lensFacing: Int = CameraSelector.LENS_FACING_BACK,
): Camera? {
    val cameraProvider = ProcessCameraProvider.awaitInstance(context)
    val cameraSelector = CameraSelector.Builder()
        .requireLensFacing(lensFacing)
        .build()
    if (!cameraProvider.hasCamera(cameraSelector)) return null

    cameraProvider.unbindAll()
    return cameraProvider.bindToLifecycle(
        lifecycleOwner,
        cameraSelector,
        preview,
        useCases.imageCapture,
        useCases.imageAnalysis,
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
fun startCamera(
    activity: ComponentActivity,
    previewView: PreviewView,
    useCases: CameraUseCases,
) {
    // Attach the surface provider before binding, or the preview stays blank.
    val preview = Preview.Builder().build()
    preview.setSurfaceProvider(previewView.surfaceProvider)

    activity.lifecycleScope.launch {
        val camera = bindUseCases(activity, activity, preview, useCases)
            ?: return@launch

        // Tap-to-focus: meteringPointFactory handles rotation and scaling.
        previewView.setOnTouchListener { view, event ->
            if (event.action == MotionEvent.ACTION_UP) {
                val point = previewView.meteringPointFactory.createPoint(event.x, event.y)
                camera.cameraControl.startFocusAndMetering(
                    FocusMeteringAction.Builder(point, FocusMeteringAction.FLAG_AF).build()
                )
                view.performClick()
            }
            true
        }
    }
}
```

<br />

### 方案 B：用于 Jetpack Compose

使用 `androidx.camera.compose.CameraXViewfinder`。


```kotlin
@Composable
fun CameraXPreview(useCases: CameraUseCases, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var surfaceRequest by remember { mutableStateOf<SurfaceRequest?>(null) }
    var cameraControl by remember { mutableStateOf<CameraControl?>(null) }
    val coordinateTransformer = remember { MutableCoordinateTransformer() }

    // Build the Preview once, with its surface provider attached.
    val preview = remember {
        Preview.Builder().build().apply {
            setSurfaceProvider { request -> surfaceRequest = request }
        }
    }

    LaunchedEffect(lifecycleOwner) {
        cameraControl =
            bindUseCases(context, lifecycleOwner, preview, useCases)?.cameraControl
    }

    surfaceRequest?.let { request ->
        CameraXViewfinder(
            surfaceRequest = request,
            coordinateTransformer = coordinateTransformer,
            modifier = modifier.pointerInput(request, cameraControl) {
                detectTapGestures { offset ->
                    val surfaceCoords = with(coordinateTransformer) { offset.transform() }
                    val point = SurfaceOrientedMeteringPointFactory(
                        request.resolution.width.toFloat(),
                        request.resolution.height.toFloat(),
                    ).createPoint(surfaceCoords.x, surfaceCoords.y)
                    cameraControl?.startFocusAndMetering(
                        FocusMeteringAction.Builder(point, FocusMeteringAction.FLAG_AF).build()
                    )
                }
            },
        )
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
/**
 * Replaces an ImageReader and TEMPLATE_STILL_CAPTURE flow. CameraX still
 * needs an app-supplied [executor] for the callback, for example
 * `ContextCompat.getMainExecutor(context)` or an app-owned background
 * executor.
 */
fun capturePhoto(
    imageCapture: ImageCapture,
    executor: Executor,
    lensFacing: Int,
    onPhoto: (Bitmap) -> Unit,
) {
    imageCapture.takePicture(
        executor,
        object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                image.use { proxy ->
                    val buffer = proxy.planes[0].buffer
                    val bytes = ByteArray(buffer.remaining())
                    buffer.get(bytes)
                    val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                        ?: return
                    val matrix = Matrix()
                    matrix.postRotate(proxy.imageInfo.rotationDegrees.toFloat())
                    if (lensFacing == CameraSelector.LENS_FACING_FRONT) {
                        matrix.postScale(-1f, 1f)
                    }
                    onPhoto(
                        Bitmap.createBitmap(
                            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
                        )
                    )
                }
            }

            override fun onError(exception: ImageCaptureException) {
                Log.e("CameraX", "Capture failed", exception)
            }
        },
    )
}
```

<br />

*** ** * ** ***

## 实现图像分析

如果你原本在 Camera2 中使用 `ImageReader` 访问原始帧，例如用于二维码
扫描或 ML，请改用 CameraX 的 `ImageAnalysis` use case。


```kotlin
/**
 * For raw frame access only. For ML Kit barcode, face, or text detection,
 * use MlKitAnalyzer instead. [analysisExecutor] is app-owned, for example
 * `Executors.newSingleThreadExecutor()`; shut it down when the camera closes.
 */
fun setUpAnalysis(imageAnalysis: ImageAnalysis, analysisExecutor: Executor) {
    imageAnalysis.setAnalyzer(analysisExecutor) { imageProxy ->
        // use {} closes the ImageProxy so the next frame can arrive.
        imageProxy.use { proxy ->
            val rotationDegrees = proxy.imageInfo.rotationDegrees
            val yPlane = proxy.planes[0].buffer
            Log.d("CameraX", "Frame ${proxy.width}x${proxy.height}, " +
                "rotation=$rotationDegrees, bytes=${yPlane.remaining()}")
        }
    }
}
```

<br />

*** ** * ** ***

## 使用 Camera2 interop

如果你的应用需要 CameraX 未直接暴露的特定 Camera2 配置项，例如自定义
曝光模式或闪光灯设置，可以使用 `Camera2Interop` 把它们应用到你的 CameraX use case 上。


```kotlin
/**
 * Applies Camera2 manual exposure to ImageCapture. Camera2Interop.Extender is
 * deprecated from CameraX 1.7.0 in favor of the camera2Interop Kotlin builder.
 */
@OptIn(ExperimentalCamera2Interop::class)
fun buildManualExposureImageCapture(
    exposureTimeNs: Long,
    iso: Int,
): ImageCapture {
    val builder = ImageCapture.Builder()
    @Suppress("DEPRECATION") // Deprecated in CameraX 1.7.0; see the note in the guide.
    Camera2Interop.Extender(builder)
        // AE off: the app supplies exposure time and sensitivity.
        .setCaptureRequestOption(
            CaptureRequest.CONTROL_AE_MODE,
            CaptureRequest.CONTROL_AE_MODE_OFF,
        )
        .setCaptureRequestOption(CaptureRequest.SENSOR_EXPOSURE_TIME, exposureTimeNs)
        .setCaptureRequestOption(CaptureRequest.SENSOR_SENSITIVITY, iso)
    return builder.build()
}
```

<br />

*** ** * ** ***

## 遵守约束

- **不要手动打开 CameraDevice** ：让 CameraX 通过 `bindToLifecycle` 管理设备的打开与关闭。
- **不要忘记关闭 `ImageProxy`** ：在 `ImageCapture` 和 `ImageAnalysis` 的回调中，你**必须**调用 `image.close()`。否则会阻塞相机流水线。
- **不要阻塞 ImageAnalysis 线程** ：分析器逐帧运行。如果需要执行重量级计算，请把它们转移到后台 worker，并尽快关闭 `ImageProxy`。
