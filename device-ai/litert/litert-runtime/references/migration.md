本文件给出 skill 中迁移摘要每一步对应的命令和代码。迁移完成后的应用最终会包含 skill 中步骤 1 到步骤 5 的代码：步骤 2 的 `Classifier` 辅助类、步骤 3 的 executor 与 CPU 回退，以及步骤 4 的 `preprocess`。

本文件中的代码使用以下 import：

    import android.content.Context
    import com.google.ai.edge.litert.Accelerator
    import com.google.ai.edge.litert.CompiledModel
    import com.google.ai.edge.litert.TensorBuffer
    import com.google.ai.edge.litert.support.image.TensorImage
    import com.google.ai.edge.litert.support.tensorbuffer.TensorBufferFloat
    import java.io.File
    import kotlin.math.abs

## 1. 定位运行时

读取 `app/build.gradle.kts`（或 `app/build.gradle`）、
`gradle/libs.versions.toml`，以及 `./gradlew :app:dependencies` 的输出，后者还能显示其他库引入了什么。旧应用会通过以下方式之一获得 Interpreter 运行时：

- **TensorFlow Lite**：`org.tensorflow:tensorflow-lite` 以及其他 `org.tensorflow:tensorflow-lite*` 构件。
- **LiteRT 1.x**：1.x 版本的 `com.google.ai.edge.litert:litert`、`litert-gpu`、`litert-support` 或 `litert-metadata`。

当应用依赖 Google Play 服务中的 LiteRT（`com.google.android.gms:play-services-tflite-java`、`-gpu` 或 `-support`，且代码中有 `TfLite.initialize`），或依赖 TensorFlow Lite Task Library（`org.tensorflow:tensorflow-lite-task-vision`、`-text` 或 `-audio`）时，停下来告知用户。这个 skill 不迁移这两者中的任何一个。

然后找出后续步骤要改动的代码：

    grep -rnE 'org\.tensorflow\.lite\.|Interpreter|GpuDelegate|CompatibilityList|NnApiDelegate|NNAPI|[nN]umThreads|FlexDelegate|TfLite' --include='*.kt' --include='*.java' app/src

记录每条代码路径使用哪个加速器（GPU delegate、NNAPI，还是带线程数的 CPU），以及应用是否使用 TensorFlow Lite Support Library（`ImageProcessor`、`TensorImage`、`TensorLabel`、`MetadataExtractor`）。

## 2. 先抓取一份基准输出

基准输出是旧应用对某个固定输入的输出，要在改动任何依赖之前记录下来。步骤 6 会把迁移后的应用与它对比。任选一条路径：

- **路径 A（已连接设备或模拟器）**：用项目现有的测试设施写一个 instrumented test。该测试在 CPU 上（不使用 GPU 或 NNAPI delegate）把一个确定性输入送入应用自己的推理类和预处理。使用与模型输入尺寸不同的位图，绝不要用相机帧。用 `writeGoldenOutput` 把输出写到 `InstrumentationRegistry.getInstrumentation().targetContext.filesDir` 下的文件中。如果模型带 signature，还要把旧代码里的
  `interpreter.getSignatureInputs(key)` 和 `getSignatureOutputs(key)` 记录到日志：迁移后的按名调用需要这些名字（步骤 5）。如果模型没有 signature，则改为记录 `interpreter.getInputTensor(i).name()` 和
  `getOutputTensor(i).name()`。不要用 `./gradlew connectedDebugAndroidTest` 运行抓取测试：它在测试结束后会卸载应用，从而删掉该文件。安装两个 APK，用
  `am instrument` 运行测试，再从可调试应用中把文件复制出来：

      ./gradlew installDebug installDebugAndroidTest
      adb shell pm list instrumentation  # shows <test package>/<runner> for the app
      adb shell am instrument -w -e class <capture test class> <test package>/<runner>
      mkdir -p app/src/androidTest/assets/golden
      adb shell run-as <application ID> cat files/golden.txt > app/src/androidTest/assets/golden/output.txt

- **路径 B（没有设备）**：不要抓取。把抓取和步骤 6 的设备对比作为实施后的步骤报告给用户。

    // Before the dependency swap: record the legacy app's output for one fixed
    // input, one value per line.
    fun writeGoldenOutput(file: File, output: FloatArray) {
        file.writeText(output.joinToString("\n"))
    }

    // After the migration: compare the migrated output with the recorded one.
    // A difference smaller than 1e-3 passes for outputs of order 1.
    fun maxAbsDifference(golden: FloatArray, migrated: FloatArray): Float {
        check(golden.size == migrated.size) { "Size ${migrated.size} != ${golden.size}" }
        return golden.indices.maxOf { abs(golden[it] - migrated[it]) }
    }

    // The golden file is an asset of the test APK: pass
    // InstrumentationRegistry.getInstrumentation().context, not targetContext,
    // whose assets throw FileNotFoundException for it.
    fun readGoldenOutput(testContext: Context, path: String = "golden/output.txt"): FloatArray =
        testContext.assets.open(path).bufferedReader().use { reader ->
            reader.readLines().filter { it.isNotBlank() }.map { it.toFloat() }.toFloatArray()
        }

## 3. 替换依赖

移除所有旧构件，即使它是被其他库引入的也要移除。LiteRT 构件以原始名称携带 `org.tensorflow.lite` 运行时类，因此混用新旧构件的构建会因类重复而失败。添加 skill 步骤 1 中的依赖（`litert:2.3.0` 和
`litert-gpu:2.3.0`），并要求 `minSdk` 为 24 或更高。

### Support library

使用 TensorFlow Lite Support Library 的应用继续保留它。该库以 LiteRT Support 的形式发布，类和行为都相同。当应用使用
`ImageProcessor`、`TensorImage`、`TensorLabel` 或 `MetadataExtractor` 时，你必须在替换坐标之前阅读 [LiteRT Support 迁移指南](https://github.com/google-ai-edge/LiteRT/blob/main/litert/support_lib/MIGRATION_GUIDE.md)：

- `org.tensorflow:tensorflow-lite-support` 或 1.x 的 `litert-support` 变为 `com.google.ai.edge.litert:litert-support:2.3.0`。
- `org.tensorflow:tensorflow-lite-support-api` 或 1.x 的 `litert-support-api` 变为 `litert-support-api:2.3.0`，与 `litert:2.3.0` 并列。
- `tensorflow-lite-metadata` 或 1.x 的 `litert-metadata` 变为 `litert-metadata:2.3.0`。它依赖 `com.google.flatbuffers:flatbuffers-java:25.2.10`；如果应用固定了更旧的 `flatbuffers-java`，请升级它。

在构建文件中保留 `litert:2.3.0`。然后重命名源码、R8 与 ProGuard 规则以及任何反射字符串中的包名：

    grep -rl 'org\.tensorflow\.lite\.support' --include='*.java' --include='*.kt' --include='*.pro' app/ \
      | xargs sed -i 's/org\.tensorflow\.lite\.support/com.google.ai.edge.litert.support/g'

从未用过 Support library 的应用不要添加它。没有 Support library 时，从 assets 加载标签：

    // Replaces FileUtil.loadLabels in an app that drops the Support library.
    fun loadLabels(context: Context, name: String = "labels.txt"): List<String> =
        context.assets.open(name).bufferedReader().use { it.readLines() }

### 工具链

2.3.0 构件要求 Gradle 构建使用 JDK 17 或更高、`compileSdk`
35、AGP 8.6.0 或更高，以及 Kotlin 插件 2.3 或更高。它们的类携带
Kotlin 2.4 元数据。在改动 `gradle/libs.versions.toml` 或根目录的 `build.gradle.kts` 之前，先询问用户：

- Kotlin 2.2 会以 `The binary version of its metadata is 2.4.0` 报错停止。仍停留在 Kotlin 2.2 的项目要添加 `freeCompilerArgs += "-Xskip-metadata-version-check"`。
- 使用 Kotlin 2.x 时，Compose 应用要应用 `org.jetbrains.kotlin.plugin.compose` 插件来替代 `composeOptions`。

## 4. 替换 delegate

- **GPU delegate**（`GpuDelegate`、`GpuDelegateFactory`）：用 CPU 作为第二个加速器来创建步骤 2 辅助类的 GPU 选项。`CompatibilityList` 没有对应物；步骤 3 的 CPU 回退可以覆盖 GPU 无法运行该模型的设备。
- **NNAPI**（`NnApiDelegate`、`setUseNNAPI(true)`）：NNAPI 从 Android 15 起已废弃，`CompiledModel` API 也没有 NNAPI 加速器。移除该 delegate，并把应用中的 NNAPI 选择映射到 GPU 选项。你必须在最终报告中告知用户这一变更，因为通过 NNAPI 在 DSP 或 NPU 上运行的量化模型，改到 GPU 上运行后速度和数值结果都会变化。NPU 加速是另一个话题，这个 skill 不涉及（[使用 LiteRT 进行 NPU 加速](https://ai.google.dev/edge/litert/next/npu)）。
- **Select TensorFlow operators**（`FlexDelegate`）：没有任何 LiteRT 2.x 构件包含 Flex delegate。这个 skill 不涉及它。告知用户该模型需要在不带 Select TensorFlow operators 的情况下重新导出。

    // Replaces GpuDelegate: the CPU runs the operators that the GPU doesn't
    // support, as it did with the delegate. Keep the CPU fallback of Step 3 for a
    // model that the GPU can't compile at all.
    val gpuWithCpuFallback = CompiledModel.Options(Accelerator.GPU, Accelerator.CPU)

## 5. 重写推理代码

绝不要对 `Interpreter` 做查找替换。把模型移到 skill 步骤 2 的 `Classifier`
辅助类中，由步骤 3 的单线程 executor 持有。
保留应用自己的类及其公开函数作为调用方。

- **模型加载**：`FileUtil.loadMappedFile` 得到的 `Interpreter`，以及 Support 的 `Model.createModel`，在辅助类中都改为 `CompiledModel.create`。没有任何重载接受 `ByteBuffer`。
- **推理**：对 `ByteBuffer` 对象调用 `run`，改为在辅助类一次性创建的 buffer 上调用 `writeFloat`、`run` 和 `readFloat`。对 int8 和 uint8 张量使用 `writeInt8` 和 `readInt8`。
- **线程数**：`setNumThreads` 改为在新的 CPU 选项上使用 `CpuOptions(numThreads = n)`。
- **张量形状**：`getInputTensor` 及其 `shape` 改为按名字查找。`getInputTensorType` 对 `uint8` 张量会抛 `LiteRtException`；要获取大小，使用 `getInputBufferRequirements(name, signature).bufferSize`，它对每种元素类型都以字节为单位。`resizeInput` 在 2.3.0 中没有对应物。
- **Signature**：`runSignature` 改为带映射的 `run`，映射从 signature 的输入输出名字指向 buffer。所有按名调用（带映射的 `run`、`getInputTensorType`、`getInputBufferRequirements`）都使用 signature 中的名字，例如 `x` 或 `args_0` 与 `output_0`，而不是计算图中的张量名，例如 `serving_default_x:0`。当模型没有 signature 时，这些名字就是它的输入输出张量名（例如 `images` 和 `Softmax`）。`CompiledModel` 没有列出它们的调用，所以要从旧代码中获取（步骤 2）。输出映射中缺失或错误的名字会导致进程崩溃（JNI abort），而不是抛出异常，因此在第一次 `run` 之前先检查名字。
- **关闭**：关闭 interpreter 改为调用辅助类的 `close`。

    // Replaces Interpreter.Options.setNumThreads. Create new options; never change
    // the shared CompiledModel.Options.CPU.
    fun cpuOptionsWithThreads(numThreads: Int): CompiledModel.Options =
        CompiledModel.Options(Accelerator.CPU).apply {
            cpuOptions = CompiledModel.CpuOptions(numThreads = numThreads)
        }

    // Replaces interpreter.getInputTensor(0).shape() for float tensors. Look the
    // tensor up by its signature name; this throws for uint8 tensors.
    fun inputShape(model: CompiledModel, inputName: String): List<Int>? =
        model.getInputTensorType(inputName).layout?.dimensions

    // Replaces interpreter.getInputTensor(0).numBytes() for any element type.
    fun inputSizeBytes(model: CompiledModel, inputName: String, signature: String): Int =
        model.getInputBufferRequirements(inputName, signature).bufferSize

    // Replaces interpreter.runSignature. Create the buffers once with
    // model.createInputBuffers(signature) and model.createOutputBuffers(signature),
    // and reuse them for every call. The map keys are the signature's input and
    // output names (such as "args_0" and "output_0").
    fun runSignature(
        model: CompiledModel,
        signature: String,
        inputs: Map<String, TensorBuffer>,
        outputs: Map<String, TensorBuffer>
    ) {
        model.run(inputs, outputs, signature)
    }

### 搭配 Support library

迁移后的代码不得 import 任何 `org.tensorflow.lite` 类，包括
`org.tensorflow.lite.DataType`。LiteRT 构件保留这些类只是出于
向后兼容。对 Support 相关代码应用以下规则：

- 当调用不需要 `DataType` 时，`ImageProcessor`、`TensorImage` 和 `FileUtil` 仍位于 `com.google.ai.edge.litert.support` 下。
- Support 的 `Model` 类运行在 Interpreter API 上。用 skill 步骤 2 的 `Classifier` 辅助类替换它。
- 把需要 `DataType` 的 Support 调用（例如 `TensorImage(DataType.FLOAT32)`、`TensorBuffer.createFixedSize` 或 `TensorLabel`）替换为步骤 4 的 `preprocess`，或替换为 `CompiledModel` 的 buffer。

下面的代码把处理后的图像写入辅助类的 buffer，并把输出分数与标签配对，全程不使用 `DataType`：

    // Replaces the Support library's Model class. ImageProcessor and TensorImage
    // stay; the processed image goes into the CompiledModel buffers directly, and
    // the scores pair with the labels without TensorLabel.
    fun runWithSupportImage(
        model: CompiledModel,
        inputs: List<TensorBuffer>,
        outputs: List<TensorBuffer>,
        image: TensorImage,
        inputElementCount: Int,
        labels: List<String>
    ): Map<String, Float> {
        // A uint8 image (one that skipped NormalizeOp) in a float input yields NaN.
        val pixels = (image.tensorBuffer as? TensorBufferFloat)?.floatArray
            ?: error("Normalize the image to float first")
        // writeFloat accepts a shorter array without an error.
        check(pixels.size == inputElementCount) { "Input size ${pixels.size}" }
        inputs[0].writeFloat(pixels)
        model.run(inputs, outputs)
        return labels.zip(outputs[0].readFloat().toList()).toMap()
    }

### 不使用 Support library

skill 步骤 4 的 `preprocess` 取代了填充输入
`ByteBuffer` 的那段代码。给它提供模型的输入尺寸和原有的归一化参数：旧 `NormalizeOp(mean, std)` 的 `mean` 与 `std`，或应用自己的公式，并保持相同的通道顺序和布局。

## 6. 分两个阶段验证

**阶段 1，在工作站上**：`./gradlew assembleDebug` 通过，且下面两条命令都不输出任何内容。仅靠构建无法暴露残留的 Interpreter 代码，因为 `litert` 2.3.0 构件仍然包含
`org.tensorflow.lite.Interpreter`：

    grep -rnE 'org\.tensorflow\.lite\.|GpuDelegate|NnApiDelegate|FlexDelegate|support\.model\.Model|org\.tensorflow:tensorflow-lite' --include='*.kt' --include='*.java' --include='*.kts' --include='*.gradle' --include='*.toml' --include='*.pro' --exclude-dir=build --exclude-dir=.gradle .
    ./gradlew :app:dependencies --configuration releaseRuntimeClasspath | grep -E 'org\.tensorflow:tensorflow-lite|com\.google\.ai\.edge\.litert:litert[a-z-]*:1\.'

**阶段 2，在设备上**：任选一条路径：

- **路径 A（步骤 2 已抓取基准输出）**：扩展步骤 2 的 instrumented test。把同一输入送入迁移后的预处理和 `Accelerator.CPU` 上的辅助类，并用 `readGoldenOutput(InstrumentationRegistry.getInstrumentation().context)` 读取基准文件。当 `maxAbsDifference` 达到 1e-3 或更大时，测试必须失败。当基准文件只存一个值时，top-1 索引必须一致；归一化做错常常也能通过这一检查。然后按 skill 步骤 5 对比 CPU 与 GPU；在使用随应用捆绑的运行时的情况下，先检查 Logcat 显示的是 `Dynamically loaded GPU accelerator` 而不是 `GPU accelerator
  could not be loaded`，因为缺少 `litert-gpu` 时 GPU 与 CPU 选项会在 CPU 上运行且不报错。
- **路径 B（没有设备）**：只跑阶段 1，并报告阶段 2 未执行。

## 不在范围内

这个 skill 不迁移 Google Play 服务中的 LiteRT，也不迁移
TensorFlow Lite Task Library（`tensorflow-lite-task-vision`、`-text` 或
`-audio`），后者没有 LiteRT 版本。

这个 skill 不迁移 C++ 代码。当应用中的 `CMakeLists.txt`、
`Android.mk` 或 `.cpp` 文件链接了 `tensorflowlite_jni` 时，告知用户该 C++ 模块需要迁移到 LiteRT C++ SDK，并把他们引导到
[从 LiteRT Maven 使用预构建的 C++ 库](https://ai.google.dev/edge/litert/next/android_cpp_sdk)。
