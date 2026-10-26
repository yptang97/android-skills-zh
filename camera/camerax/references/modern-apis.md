始终优先使用这些抽象，而不是旧的 Camera2 或早期 CameraX 实现。

## 对比 API

| 使用场景 | 旧式或繁琐的做法 | 建议 |
|---|---|---|
| 二维码或人脸扫描 | `ImageAnalysis.Analyzer` 和手写 ByteBuffer 计算 | **`MlKitAnalyzer`**，它自动处理坐标映射和多格式支持 |
| 后处理 | 自定义 OpenGL 着色器或 `SurfaceTexture` | **`Media3Effect`**，用于可组合的声明式效果 |
| 双摄 | 手动绑定两个 UseCase | **`ConcurrentCamera`**，CameraX 1.3 及更高版本内置支持 |
| 高动态范围 | 手动配置位深和 profile | **`DynamicRange`**，使用 `DYNAMIC_RANGE_HLG10` 或 `SDR` |
| 变焦与对焦 | 通过 `Camera2Interop` 做 CameraX 到 Camera2 的映射 | **`CameraControl.setZoomRatio`** 或 **`setLinearZoom`** |

## 硬件适配意识

现代 API 会屏蔽硬件多样性的复杂度。

- **`CameraSelector`**：使用 `DEFAULT_BACK_CAMERA` 或 `DEFAULT_FRONT_CAMERA`，而不是硬编码相机 ID。如果需要特定的镜头能力，使用 `filter`。
- **Extensions**：在启用夜景、人像虚化和人脸美化等高级模式之前，先用 `ExtensionsManager` 查询设备是否支持。
- **折叠设备**：观察 `Lifecycle` 和 `Viewport` 的更新，以处理折叠设备上的姿态变化，例如半开姿态。

## 所需依赖

把以下依赖添加到你的 `libs.versions.toml` 文件中：

    # CameraX ML Kit

    androidx-camera-mlkit-vision = { group = "androidx.camera", name =
    "camera-mlkit-vision", version.ref = "camerax" }

    # Media3 effects

    androidx-media3-effect = { group = "androidx.media3", name = "media3-effect",
    version.ref = "media3" }

    # Camera extensions

    androidx-camera-extensions = { group = "androidx.camera", name =
    "camera-extensions", version.ref = "camerax" }

稳定版本请参考官方 [CameraX 版本说明](https://developer.android.com/jetpack/androidx/releases/camera)。
