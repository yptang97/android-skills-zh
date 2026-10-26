---
name: litert-runtime
description: 在 Android 上用 Kotlin 通过 CompiledModel API 在 CPU 和 GPU 上配置并实现
  LiteRT（.tflite）端侧推理。任何 Android LiteRT 或 .tflite 任务都用这个 skill，
  包括 Gradle 配置、图像分类或视觉/音频/嵌入辅助类、TensorBuffer 复用、CPU 内存优化、
  Bitmap 预处理、AndroidViewModel 在单线程调度器上带预热的 GPU 到 CPU 回退、
  Google Play services 中的 LiteRT（play-services-litert）、从旧版
  org.tensorflow.lite.Interpreter、GpuDelegate 或 play-services-tflite 迁移，
  以及延迟基准测试。不要用于运行 .litertlm 文件的生成式文本 LLM，也不用于 Python 模型转换。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - LiteRT
  - CompiledModel
  - tflite
  - Android app
  - GPU
  - TensorBuffer
---

本 skill 逐步指导你构建一个 Android 应用，用 [LiteRT CompiledModel API](https://ai.google.dev/edge/litert/android)
（`com.google.ai.edge.litert:litert` 2.x；[源码仓库](https://github.com/google-ai-edge/litert/blob/main/README.md)）在 CPU 或
GPU 上运行 `.tflite` 模型。不要使用已废弃的 `org.tensorflow.lite.Interpreter` API。对于使用 `.litertlm` 文件的
开放式文本语言模型，建议改用 `litert-lm` skill。

## 前置条件

- 一个 Kotlin Android 项目（`minSdk` 必须为 `24` 或更高，这是 LiteRT 2.3.0 的 AAR 所声明的）。
- 应用级 `build.gradle.kts` 文件中来自 Google Maven 的依赖：`implementation("com.google.ai.edge.litert:litert:2.3.0")` 和 `implementation("com.google.ai.edge.litert:litert-gpu:2.3.0")`。从 2.3.0 起，GPU 加速器是第二个构件：只加 `litert` 时应用能构建，但用 `CompiledModel.Options(Accelerator.GPU)` 调用 `CompiledModel.create` 会抛出 `LiteRtException`，因为 APK 里没有 GPU 加速器库。换成 `CompiledModel.Options(Accelerator.GPU, Accelerator.CPU)` 就不会抛：模型实际在 CPU 上运行，而应用报告的是 GPU，只有 Logcat 会显示出来（`GPU accelerator could not be loaded and registered`）。无需在清单中添加条目：`litert` 依赖的 `litert-api` 在自己的清单里声明了 OpenCL 驱动库（`uses-native-library`）。
- 一个已验证的 `.tflite` 模型及其输入约定（输入维度、均值、标准差、通道顺序和张量布局）。对已有验证配方的模型，查看 [LiteRT 模型配方](https://github.com/google-ai-edge/litert-samples/blob/main/models/README.md)。

## 关键要求

- **单线程限定**：必须由一个单线程 executor 或受限的协程调度器持有 `CompiledModel` 实例。创建、推理和关闭都必须在这同一个后台线程上执行，绝不在主线程上。
- **缓冲区生命周期**：用 `createInputBuffers` 和 `createOutputBuffers` 一次性分配 `TensorBuffer` 实例，在多次推理之间复用，并在关闭 `CompiledModel` 之前关闭所有输入和输出缓冲区。
- **同步计时**：`model.run` 把工作排入 GPU 队列后，会在 GPU 执行完成之前返回。测量时必须把 `model.run` 与输出缓冲区回读（`outputs[0].readFloat`）一起计入。
- **预热与异常安全**：在辅助类构造函数的 `init` 块中执行一次预热推理，让首次运行的 GPU 着色器编译不会阻塞用户的第一次交互；并在 `catch` 中先调用 `close` 再重新抛出，这样缓冲区分配或预热抛异常时，`CompiledModel` 和 `TensorBuffer` 的句柄都不会泄漏。
- **迁移**：如果应用已经在用 `org.tensorflow.lite` 代码，你在改动任何文件之前必须先完整阅读「从旧版 TFLite Interpreter 迁移」章节。迁移后的代码不得导入任何 `org.tensorflow.lite` 类（包括 `DataType`），`GpuDelegate` 改为 `CompiledModel.Options(Accelerator.GPU, Accelerator.CPU)`，NNAPI 选项也映射到同一个 GPU 选项。

## 详细步骤

### 步骤 1：配置 Gradle 并放置模型文件

在改动构建文件之前，先在项目中查找 `libs.versions.toml`、`gradle.properties`、
`app/build.gradle.kts` 以及任何已有的 `org.tensorflow.lite` 导入。配置 `minSdk`，
并在 `app/build.gradle.kts` 中添加 LiteRT 运行时和 GPU 加速器依赖：

    android {
        defaultConfig {
            minSdk = 24
        }
    }

    dependencies {
        implementation("com.google.ai.edge.litert:litert:2.3.0")
        implementation("com.google.ai.edge.litert:litert-gpu:2.3.0")
    }

把随应用打包的模型放在 `app/src/main/assets/model.tflite`（AGP 默认不压缩 `.tflite`
文件）。超过基础 APK 大小限制的模型，通过 [Play for On-Device AI](references/android/google/play/on-device-ai.md) 以 AI pack 形式分发，或下载到
`context.filesDir`（`bundletool --local-testing` 可在没有 Google Play 的情况下本地安装 AI pack）。安装时的 AI pack
通过 `AssetManager` 读取。快速跟进或按需下载的 AI pack，以及已下载的文件，用 `CompiledModel.create(filePath,
CompiledModel.Options(accelerator), environment)` 从其磁盘上的
`filePath` 加载，替代步骤 2 中的 asset 调用。用 AI Delivery 库
（`com.google.android.play:ai-delivery`）通过
`AiPackManagerFactory.getInstance(context).getPackLocation(name)?.assetsPath()` 获取 pack 的目录，
该调用在 pack 下载完成前返回 `null`。

在 2.3.0 上，`gradle.properties` 里不需要添加任何内容：`litert` 2.3.0 声明的
namespace 是 `com.google.ai.edge.litert.impl`，其依赖 `litert-api`
2.3.0 声明的是 `com.google.ai.edge.litert`，因此 AGP 9.x 能构建该项目。在
2.2.0 或 2.1.6 上，两个库都声明 `com.google.ai.edge.litert`，AGP
9.x 会停在 `processDebugMainManifest`（AGP 8.x 只把它报为警告并继续
构建）；对这两个版本，把 `android.uniquePackageNames=false` 加到
`gradle.properties`，升到 2.3.0 时再删掉，因为它同时会掩盖任何其他两个库之间的同类
冲突。改为排除 `litert-api` 不可行：`CompiledModel` 和 `Accelerator` 都在 `litert-api` 里，构建会在
`compileDebugKotlin` 阶段失败。

### 步骤 2：实现推理辅助类

把 `CompiledModel` 及其 `TensorBuffer` 实例隔离在一个专用的
`AutoCloseable` 辅助类中，该类不涉及 Android UI 类型：

    import android.content.Context
    import com.google.ai.edge.litert.Accelerator
    import com.google.ai.edge.litert.CompiledModel
    import com.google.ai.edge.litert.Environment
    import com.google.ai.edge.litert.TensorBuffer

    const val INPUT_SIZE = 224 * 224 * 3
    private val environment by lazy { Environment.create() }

    class Classifier(context: Context, accelerator: Accelerator) : AutoCloseable {
        private val model = CompiledModel.create(
            context.assets,
            "model.tflite",
            CompiledModel.Options(accelerator),
            environment
        )
        private val inputs = mutableListOf<TensorBuffer>()
        private val outputs = mutableListOf<TensorBuffer>()

        init {
            try {
                inputs += model.createInputBuffers()
                outputs += model.createOutputBuffers()
                infer(FloatArray(INPUT_SIZE))
            } catch (e: Exception) {
                close()
                throw e
            }
        }

        fun infer(input: FloatArray): FloatArray {
            inputs[0].writeFloat(input)
            model.run(inputs, outputs)
            return outputs[0].readFloat()
        }

        override fun close() {
            (inputs + outputs).forEach { it.close() }
            model.close()
        }
    }

`Accelerator.CPU` 对设备没有任何要求。`Accelerator.GPU` 会为 GPU
编译计算图；当 GPU 无法执行该模型时，构造函数会抛出 `LiteRtException`（GPU 不支持的算子由 `create` 抛出，
在 Android 模拟器上可能由 `create` 或缓冲区分配抛出）。缺少
asset，或文件不是有效模型，也会由 `create` 抛出 `LiteRtException`。

这些缓冲区随模型一起创建一次，每次推理复用，并在关闭模型之前关闭。一个 `Environment` 服务于进程内的所有模型并
保持打开，因此 LiteRT 只加载一次 GPU 加速器库，而不是每次
`create` 调用都加载。构造函数末尾执行一次预热推理（首次
GPU 运行包含着色器编译），如果 `init` 中任一步抛异常，就关闭模型及其缓冲区。`INPUT_SIZE` 是模型的输入元素个数：
`writeFloat` 在数组过长时抛异常，过短时则静默写入，不做报错，
所以尺寸错误会产生错误结果。对于 `int8` 或 `uint8` 张量，改用
`TensorBuffer` 上的 `writeInt8` 和 `readInt8`，而不是 `writeFloat` 和
`readFloat`。

### 步骤 3：接入 ViewModel 与 Compose 屏幕

在 `AndroidViewModel` 中用单线程 executor 驱动辅助类，GPU
编译失败时回退到 `Accelerator.CPU`，并向 Compose UI 暴露不可变
状态：

    import android.app.Application
    import androidx.lifecycle.AndroidViewModel
    import com.google.ai.edge.litert.Accelerator
    import com.google.ai.edge.litert.LiteRtException
    import java.util.concurrent.Executors
    import kotlinx.coroutines.CoroutineScope
    import kotlinx.coroutines.SupervisorJob
    import kotlinx.coroutines.asCoroutineDispatcher
    import kotlinx.coroutines.cancel
    import kotlinx.coroutines.flow.MutableStateFlow
    import kotlinx.coroutines.flow.StateFlow
    import kotlinx.coroutines.flow.asStateFlow
    import kotlinx.coroutines.flow.update
    import kotlinx.coroutines.launch

    data class UiState(
        val ready: Boolean = false,
        val accelerator: Accelerator = Accelerator.CPU,
        val result: List<Float>? = null,
        val error: String? = null
    )

    class MainViewModel(app: Application) : AndroidViewModel(app) {
        private val executor = Executors.newSingleThreadExecutor()
        private val scope = CoroutineScope(
            SupervisorJob() + executor.asCoroutineDispatcher()
        )
        private var classifier: Classifier? = null
        private val _uiState = MutableStateFlow(UiState())
        val uiState: StateFlow<UiState> = _uiState.asStateFlow()

        fun load(preferred: Accelerator = Accelerator.GPU) {
            scope.launch {
                if (classifier != null) return@launch
                val appContext = getApplication<Application>()
                val selected = try {
                    classifier = Classifier(appContext, preferred)
                    preferred
                } catch (e: LiteRtException) {
                    if (preferred != Accelerator.CPU) {
                        try {
                            classifier = Classifier(appContext, Accelerator.CPU)
                            Accelerator.CPU
                        } catch (cpuError: LiteRtException) {
                            _uiState.value = UiState(error = cpuError.message)
                            return@launch
                        }
                    } else {
                        _uiState.value = UiState(error = e.message)
                        return@launch
                    }
                }
                _uiState.value = UiState(ready = true, accelerator = selected)
            }
        }

        fun classify(input: FloatArray) {
            scope.launch {
                try {
                    classifier?.infer(input)?.let { result ->
                        _uiState.update {
                            it.copy(result = result.toList(), error = null)
                        }
                    }
                } catch (e: LiteRtException) {
                    _uiState.update { it.copy(error = e.message) }
                }
            }
        }

        override fun onCleared() {
            scope.launch { classifier?.close() }.invokeOnCompletion {
                scope.cancel()
            }
            executor.shutdown()
        }
    }

由一个单线程 executor 独占模型：创建、推理和关闭都只在它上面
执行，绝不在主线程上。`ViewModel` 自己维护作用域，因为 `viewModelScope` 在 `onCleared` 运行之前就被取消，
在那里启动的关闭操作不会执行；`onCleared` 会在 `close` 完成后取消 `scope`。
跨配置变更时如果模型已加载，`load` 是空操作；`load`
失败会让 `classifier` 保持 `null`。`classify` 把任何
`LiteRtException`（位于 `com.google.ai.edge.litert` 包中）写入 `error`，并保留
模型。

下面的 Compose 屏幕从照片选择器或 CameraX 取得图片（`bitmap`），
并在点击处理函数中运行 `preprocess`（对 224x224 只需几毫秒；
超过 224x224 的图片请把 `preprocess` 移到 executor 上执行）。
`viewModel` 和 `collectAsStateWithLifecycle` 来自
`androidx.lifecycle:lifecycle-viewmodel-compose` 和
`androidx.lifecycle:lifecycle-runtime-compose`（2.10.0）：

    import android.graphics.Bitmap
    import androidx.compose.foundation.layout.Column
    import androidx.compose.material3.Button
    import androidx.compose.material3.Text
    import androidx.compose.runtime.Composable
    import androidx.compose.runtime.LaunchedEffect
    import androidx.compose.runtime.getValue
    import androidx.lifecycle.compose.collectAsStateWithLifecycle
    import androidx.lifecycle.viewmodel.compose.viewModel
    import com.google.ai.edge.litert.Accelerator

    @Composable
    fun MainScreen(
        bitmap: Bitmap,
        viewModel: MainViewModel = viewModel()
    ) {
        val state by viewModel.uiState.collectAsStateWithLifecycle()
        LaunchedEffect(Unit) { viewModel.load(Accelerator.GPU) }
        Column {
            state.error?.let { Text(it) }
            Button(
                onClick = { viewModel.classify(preprocess(bitmap)) },
                enabled = state.ready
            ) {
                Text("Run (${state.accelerator})")
            }
            state.result?.let { scores ->
                Text("Top class: ${scores.indices.maxBy { i -> scores[i] }}")
            }
        }
    }

### 步骤 4：预处理输入以匹配模型约定

用 `preprocess` 把 `Bitmap` 转换成模型的输入。匹配
模型的精确输入维度、归一化均值和标准差、
通道顺序以及内存布局（本例使用 NHWC、RGB，缩放到
`-1.0..1.0`）。`mean` 或 `std` 取值不匹配会产生错误的预测，
看起来像模型坏了：

    import android.graphics.Bitmap

    fun preprocess(
        bitmap: Bitmap,
        size: Int = 224,
        mean: Float = 127.5f,
        std: Float = 127.5f
    ): FloatArray {
        val scaled = checkNotNull(
            Bitmap.createScaledBitmap(bitmap, size, size, true)
                .copy(Bitmap.Config.ARGB_8888, false)
        )
        val pixels = IntArray(size * size).also {
            scaled.getPixels(it, 0, size, 0, 0, size, size)
        }
        val out = FloatArray(size * size * 3)
        pixels.forEachIndexed { i, p ->
            out[i * 3] = ((p shr 16 and 0xFF) - mean) / std
            out[i * 3 + 1] = ((p shr 8 and 0xFF) - mean) / std
            out[i * 3 + 2] = ((p and 0xFF) - mean) / std
        }
        return out
    }

缩放后的 bitmap 会被复制到 `Bitmap.Config.ARGB_8888`，因为 `ImageDecoder`
在 Android 9 及更高版本上默认返回 `Bitmap.Config.HARDWARE` bitmap
（包括来自照片选择器 `Uri` 的图片），缩放会保留该 config，而
`getPixels` 无法读取 `HARDWARE` bitmap；复制针对的是 224x224 缩放后的
bitmap，而不是整张原图。缩放不保留宽高比；
如果模型需要中心裁剪，先裁剪。音频或嵌入模型
用它自己的输入编码替换 `preprocess`，并保留推理类。

### 步骤 5：在真机上验证输出

在 Android Studio 中把应用运行到一台运行 Android 的真机上。先在
`Accelerator.CPU` 上、再在 `Accelerator.GPU` 上，针对一个固定输入，把
应用的输出与模型的参考输出作比较；在真机上验证模型
输出时，必须遵循[设备验证](references/verify.md)。

## 从旧版 TFLite Interpreter 迁移

已经在用 `org.tensorflow.lite.Interpreter` 的应用（来自
`org.tensorflow:tensorflow-lite*` 或来自 `com.google.ai.edge.litert:litert`
1.x）按以下顺序分七步迁移到步骤 1 至 5 的 `CompiledModel` 代码。
在改动现有应用的任何文件之前，
你必须阅读[迁移](references/migration.md)，其中给出了每一步的命令和代码：

1. **查找运行时**：阅读构建文件和已解析的依赖，记录应用使用的 delegate、线程数以及 Support 库的类。
2. **先采集基准输出**：趁旧版运行时还在项目中，在 CPU 上记录应用针对一个固定输入的输出。这一步需要设备或模拟器。用 `am instrument` 运行采集测试，不要用 `connectedDebugAndroidTest`，后者会卸载应用并删除该文件。
3. **替换依赖**：移除所有旧版构件，并添加步骤 1 的依赖。使用 Support 库的应用把它保留为 `com.google.ai.edge.litert:litert-support:2.3.0`，包名从 `org.tensorflow.lite.support` 改为 `com.google.ai.edge.litert.support`（[LiteRT Support 迁移指南](https://github.com/google-ai-edge/LiteRT/blob/main/litert/support_lib/MIGRATION_GUIDE.md)）。
4. **替换 delegate**：`GpuDelegate` 改为 `CompiledModel.Options(Accelerator.GPU, Accelerator.CPU)`，这样 GPU 不支持的算子由 CPU 执行。应用中的 NNAPI 选项映射到同一个 GPU 选项，而不是单独映射到 `Accelerator.CPU` 或 NPU 加速器。`setNumThreads(n)` 改为新的 CPU 选项：`cpuOptions = CompiledModel.CpuOptions(numThreads = n)`。
5. **重写推理代码**：用步骤 2 的 `Classifier` 辅助类替换 `Interpreter` 和 `FileUtil.loadMappedFile`，只在步骤 3 的单线程 executor 上创建和运行，绝不在主线程调用的构造函数中创建。
6. **分两阶段验证**：构建通过，且搜索旧版引用的结果为空白；然后在设备上确认迁移后的输出与基准输出一致。
7. **报告改了什么、什么没有迁移**：如果应用原先使用 NNAPI，要告诉用户它现在运行在 GPU 上、以 CPU 作为第二加速器，这会改变原先运行在 DSP 或 NPU 上的量化模型的速度和数值结果；并把他们引向 [LiteRT 的 NPU 加速](https://ai.google.dev/edge/litert/next/npu)。
   同时告知用户 Google Play services 中的 LiteRT、TensorFlow Lite Task Library、C++ 模块和 Select TensorFlow 算子这些本 skill 不迁移的内容。

适用于所有迁移应用的强制要求：

- **不得出现 `org.tensorflow.lite` 导入**：迁移后的代码不得导入任何 `org.tensorflow.lite` 类，包括 `org.tensorflow.lite.DataType`；LiteRT 构件保留这些类只是为了向后兼容。把需要 `DataType` 的 Support 调用（`TensorImage(DataType.FLOAT32)`、`TensorBuffer.createFixedSize` 和 `TensorLabel`）替换为步骤 4 的 `preprocess`、`CompiledModel` 缓冲区，以及把标签与输出分数配对。删除每一处已有的 `org.tensorflow.lite` 导入行，不只是你新加的那些。

## 反模式

- **绝不**在 Android 主线程上创建、运行或关闭 `CompiledModel`。
- **绝不**在每次推理调用时分配新的 `TensorBuffer` 实例；不关闭每帧的 `TensorBuffer` 对象会泄漏 C++ 堆内存。
- **绝不**在基准测试 `model.run` 时不计入输出缓冲区回读（`outputs[0].readFloat`）。
- **绝不**把 `org.tensorflow:tensorflow-lite*` 构件（例如 `org.tensorflow:tensorflow-lite-support`）与 `com.google.ai.edge.litert:*` 构件混用；两者都提供 `org.tensorflow.lite.*` 类，会导致重复类构建失败。
- **绝不**在 LiteRT 2.3.0 上使用 `Accelerator.GPU` 而不在 `com.google.ai.edge.litert:litert:2.3.0` 之外再加上 `com.google.ai.edge.litert:litert-gpu:2.3.0` 依赖；以 CPU 作为第二加速器时，模型会静默地在 CPU 上运行。

## 检查清单

- \[ \] `minSdk` 是否设为 `24` 或更高，且 `com.google.ai.edge.litert:litert:2.3.0` 与 `com.google.ai.edge.litert:litert-gpu:2.3.0` 是否都已加到 `app/build.gradle.kts`？
- \[ \] 所有旧版 `org.tensorflow:tensorflow-lite*` 依赖和 `org.tensorflow.lite.*` 导入是否都已移除？
- \[ \] `CompiledModel.create`、`model.run` 和 `close` 是否都在同一个单线程后台调度器上执行？
- \[ \] `TensorBuffer` 实例是否只分配一次、跨调用复用，并在 `model.close` 之前关闭，包括 `init` 或预热抛异常的情况？
- \[ \] `load` 是否执行一次预热推理，并在 `Accelerator.GPU` 抛出 `LiteRtException` 时回退到 `Accelerator.CPU`？
- \[ \] 项目能否用 `./gradlew assembleDebug` 编译通过？
