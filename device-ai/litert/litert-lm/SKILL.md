---
name: litert-lm
description: 构建一个在设备端（CPU 或 GPU 上）运行开源文本 LLM 的 Android 应用，使用
  LiteRT-LM Kotlin API（com.google.ai.edge.litertlm:litertlm-android）。当你要用 Hugging Face
  litert-community 中的 .litertlm 模型（Gemma、Qwen、Llama、Phi）实现聊天、摘要或信息提取功能
  时使用这个 skill，涵盖 Gradle 依赖、GPU 清单条目、把模型文件放到设备上、在主线程之外初始化
  Engine、用 sendMessageAsync 进行流式多轮 Conversation，以及 AndroidViewModel 和 Compose
  屏幕。不要用于以 CompiledModel API 运行 .tflite 视觉、音频或嵌入模型，也不用于图像或音频
  输入、工具调用、NPU 后端，或转换模型。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-20'
  keywords:
  - LiteRT-LM
  - litertlm
  - Gemma
  - on-device LLM
  - Android app
  - GPU
---

这个 skill 提供分步指导，用于构建通过 LiteRT-LM Kotlin API
（`com.google.ai.edge.litertlm`）在 CPU 或 GPU 上运行开源文本 LLM 的 Android 应用。模型就是一个
`.litertlm` 文件。不涵盖图像、音频、工具调用和 NPU 后端。
对于使用 `.tflite` 文件的视觉和音频模型，建议改用 `litert-runtime`
skill。

当这个 skill 使用的 LiteRT-LM 类或方法无法编译时，你必须先阅读 [LiteRT-LM Android 指南](https://ai.google.dev/edge/litert-lm/android) 和 [LiteRT-LM README](https://github.com/google-ai-edge/LiteRT-LM/blob/main/README.md)，再
修改代码。

## 前置条件

- 一个 Kotlin Android 项目（Android Studio 的 Empty Activity 模板就够用）。`litertlm-android` 0.18.0 的 AAR 声明 `minSdk` 为 24。
- 应用级 `build.gradle.kts` 文件中来自 Google Maven 的依赖：`implementation("com.google.ai.edge.litertlm:litertlm-android:0.18.0")`。Google Maven 上列出了后续版本。
- 使用 GPU 后端时，需要在 `AndroidManifest.xml` 的 `<application>` 内添加两个 `uses-native-library` 条目。如果应用要下载模型，还要添加 `INTERNET` 权限。
- 模型文件存放在设备的文件系统中（从数百 MB 到数 GB），绝不要放在 `assets/` 或 APK 中。

## 关键要求

- **依赖优先**：在编写导入 `com.google.ai.edge.litertlm` 的代码之前，如果项目缺少 `litertlm-android` 依赖，先按步骤 1 加上。用 `./gradlew assembleDebug` 验证。
- **后台初始化**：`Engine(config).initialize()` 会加载权重并阻塞数秒。要在后台线程调用，绝不要在主线程调用。
- **单一所有者**：由一个单线程 executor 持有 `Engine` 和 `Conversation`。创建、流式传输、取消和关闭都在它上面执行。
- **只关闭一次**：`Engine` 和 `Conversation` 都是 `AutoCloseable`。对其中任一个再次调用 `close` 都会抛出 `IllegalStateException`。对 `initialize` 抛出过异常的 engine 调用 `close` 同样如此。只有在 `initialize` 返回之后才保存 engine。
- **模型不放进 APK**：向 `EngineConfig` 传绝对路径。绝不要把 `.litertlm` 文件打包进 `assets/`。

## 详细步骤

### 步骤 1：配置 Gradle 与清单

修改构建文件之前，先在项目中查找 `libs.versions.toml`、`app/build.gradle.kts` 和
`AndroidManifest.xml`。在 `app/build.gradle.kts` 中配置 `minSdk` 并添加 LiteRT-LM 依赖：

<br />

    android {
        defaultConfig {
            minSdk = 24
        }
    }

    dependencies {
        implementation("com.google.ai.edge.litertlm:litertlm-android:0.18.0")
    }

如果项目使用 Hilt，先检查 Dagger 版本。`litertlm-android`
0.18.0 带有 Kotlin 2.4 元数据，Hilt 2.59.2 无法读取。构建会在 `hiltJavaCompileDebug` 阶段失败，报
`Provided Metadata instance has version 2.4.0, while maximum supported version is 2.3.0`。从以下两种修复中选择一种：

- **路径 A**：把 Hilt 版本（`com.google.dagger`）升级到 2.60.1 或更高。修改 `gradle/libs.versions.toml` 之前先询问用户。
- **路径 B**：保留当前 Hilt 版本，在 `app/build.gradle.kts` 的注解处理器路径中加入更高版本的元数据读取器：

<br />

    dependencies {
        ksp("org.jetbrains.kotlin:kotlin-metadata-jvm:2.4.21")
    }

使用 GPU 后端时，在 `AndroidManifest.xml` 的 `<application>` 内加入这两行。当应用要下载模型时，在
`<application>` 之外添加 `INTERNET` 权限：

<br />

    <uses-permission android:name="android.permission.INTERNET"/>

    <application>
        <uses-native-library
            android:name="libvndksupport.so"
            android:required="false"/>
        <uses-native-library
            android:name="libOpenCL.so"
            android:required="false"/>
    </application>

### 步骤 2：从 litert-community 中选择模型

在 Hugging Face 上从 [litert-community](https://huggingface.co/litert-community) 选择一个 `.litertlm` 文件。可以先从
`litert-community/gemma-4-E2B-it-litert-lm` 开始（文件为 `gemma-4-E2B-it.litertlm`，
2.6 GB）。如果需要 0.6 GB 的模型，可以从 `litert-community/Qwen3-0.6B` 开始（文件为
`Qwen3-0.6B.litertlm`）。这两个文件都能在 CPU 和 GPU 上运行。像
`_Google_Tensor_G5` 或 `.mediatek.mt6993` 这样的 SoC 后缀表示 NPU 构建，本
skill 不涵盖。模型卡片会说明测试过的后端和大小。

在选择这两个之外的其他模型文件之前、在编写应用内下载代码之前，以及某个模型没有对应的 `.litertlm` 文件时，你必须先阅读 [获取模型](references/get-a-model.md)。

### 步骤 3：把模型文件放到设备上

选择一条路径：

- **路径 A（用 `adb` 做本地测试）**：只有以下三个条件都成立时才运行下面的命令：`adb devices` 列出了设备、该设备上已安装应用的 debug 构建、用户提供了本地 `.litertlm` 路径。任一条件不成立就不要运行这些命令，而是把它们作为实现后由用户执行的步骤报告给用户。把 `<path>` 替换为用户本地路径，把 `<package>` 替换为应用的 application ID：

  1. `adb push <path> /data/local/tmp/model.litertlm`
  2. `adb shell run-as <package> cp /data/local/tmp/model.litertlm files/`
- **路径 B（应用内下载）**：在应用中编写下载代码。使用应用的 HTTP 客户端写入 `filesDir`，或用 `DownloadManager` 写入
  `getExternalFilesDir(null)`。`DownloadManager` 无法写入内部
  存储。加载之前显示下载进度，并对照模型卡片检查文件大小。绝不要在 agent 自己的会话中下载模型文件。

- **路径 C（[Play for On-Device AI](references/android/google/play/on-device-ai.md)）**：使用 AI Delivery 库
  （`com.google.android.play:ai-delivery`）编写解析 fast-follow 或按需 AI 包
  路径的代码：
  `AiPackManagerFactory.getInstance(context).getPackLocation(name)?.assetsPath()`。
  在包下载完成之前该调用返回 `null`，这种情况下要显示下载状态。创建 AI pack 模块并把应用
  上传到 Play Console 是由用户执行的实现后步骤。

无论用哪条路径，都要把文件的绝对路径传给 engine。

### 步骤 4：在主线程之外初始化 engine

用 `EngineConfig(modelPath = ..., backend = ...,
cacheDir = ...)` 创建 engine，并在后台线程调用 `initialize`：

- `Backend.CPU()` 是 `EngineConfig` 的默认值，不需要设备提供任何东西。
- `Backend.GPU()` 需要步骤 1 中的两行清单配置。缺少它们时，engine 仍会初始化，但第一条回复会以错误 `Can not find
  OpenCL library on this device` 结束。
- `cacheDir` 可以加快第二次加载。

### 步骤 5：实现对话 ViewModel

在 `AndroidViewModel` 中通过单线程 executor 驱动 engine 和 conversation，以流式输出回复，并向 UI 暴露不可变状态：

<br />

    import android.app.Application
    import androidx.lifecycle.AndroidViewModel
    import com.google.ai.edge.litertlm.Backend
    import com.google.ai.edge.litertlm.Contents
    import com.google.ai.edge.litertlm.Conversation
    import com.google.ai.edge.litertlm.ConversationConfig
    import com.google.ai.edge.litertlm.Engine
    import com.google.ai.edge.litertlm.EngineConfig
    import java.util.concurrent.Executors
    import kotlin.coroutines.cancellation.CancellationException
    import kotlinx.coroutines.CoroutineScope
    import kotlinx.coroutines.SupervisorJob
    import kotlinx.coroutines.asCoroutineDispatcher
    import kotlinx.coroutines.cancel
    import kotlinx.coroutines.delay
    import kotlinx.coroutines.flow.MutableStateFlow
    import kotlinx.coroutines.flow.StateFlow
    import kotlinx.coroutines.flow.asStateFlow
    import kotlinx.coroutines.flow.update
    import kotlinx.coroutines.launch
    import kotlinx.coroutines.sync.Mutex
    import kotlinx.coroutines.sync.withLock

    data class ChatState(
        val ready: Boolean = false,
        val busy: Boolean = false,
        val reply: String = "",
        val error: String? = null
    )

    class ChatViewModel(app: Application) : AndroidViewModel(app) {
        private val executor = Executors.newSingleThreadExecutor()
        private val scope = CoroutineScope(
            SupervisorJob() + executor.asCoroutineDispatcher()
        )
        private val mutex = Mutex()
        private var engine: Engine? = null
        private var conversation: Conversation? = null
        private val _state = MutableStateFlow(ChatState())
        val state: StateFlow<ChatState> = _state.asStateFlow()

        fun load(modelPath: String, backend: Backend = Backend.CPU()) {
            scope.launch {
                mutex.withLock {
                    if (engine?.engineConfig?.modelPath == modelPath) return@launch
                    release()
                    try {
                        val config = EngineConfig(
                            modelPath = modelPath,
                            backend = backend,
                            cacheDir = getApplication<Application>().cacheDir.path
                        )
                        engine = Engine(config).also { it.initialize() }
                        conversation = checkNotNull(engine).createConversation(
                            ConversationConfig(
                                systemInstruction =
                                    Contents.of("You are a helpful assistant.")
                            )
                        )
                        _state.value = ChatState(ready = true)
                    } catch (e: Exception) {
                        release()
                        _state.value = ChatState(error = e.message)
                    }
                }
            }
        }

        fun send(text: String) {
            scope.launch {
                if (!_state.value.ready || _state.value.busy) return@launch
                _state.update { it.copy(busy = true, reply = "", error = null) }
                try {
                    val replies = checkNotNull(conversation).sendMessageAsync(text)
                    replies.collect { message ->
                        _state.update { it.copy(reply = it.reply + message) }
                    }
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    _state.update { it.copy(error = e.message) }
                } finally {
                    _state.update { it.copy(busy = false) }
                }
            }
        }

        private suspend fun release() {
            _state.update { it.copy(ready = false) }
            while (_state.value.busy) {
                conversation?.cancelProcess()
                delay(100)
            }
            conversation?.close()
            conversation = null
            engine?.close()
            engine = null
            _state.value = ChatState()
        }

        override fun onCleared() {
            scope.launch {
                mutex.withLock { release() }
                executor.shutdown()
            }.invokeOnCompletion { scope.cancel() }
        }
    }

`sendMessageAsync(text)` 返回由分块组成的 `Flow<Message>`，每个分块的文本由 `toString`
给出。`sendMessage(text)` 会阻塞并返回完整回复。
conversation 会保留历史记录，所以下一次 `send` 会继续这次聊天。
`busy` 会让按钮在 flow 完成之前保持禁用。

要设置采样，在 `ConversationConfig` 中传入 `SamplerConfig(topK = 10, topP = 0.95,
temperature = 0.8)`。三个参数都是必需的，
其中 `topP` 和 `temperature` 是 `Double`。

用已经加载的模型路径调用 `load` 不会做任何事，无论它要求哪个
后端。旋转屏幕后的第二次调用会保留已加载的模型，
即使应用已经回退到另一个后端也是如此。`send` 只在
状态为 `ready` 且不是 `busy` 时运行，与按钮的判断相同。在
`release` 停止回复期间落下的点击不会做任何事。排在某个
`load` 之后的点击，会在没有回复正在流式输出时到达该 `load` 所加载的模型。

### 步骤 6：接好 Compose 屏幕

`viewModel` 和 `collectAsStateWithLifecycle` 来自
`androidx.lifecycle:lifecycle-viewmodel-compose` 和
`androidx.lifecycle:lifecycle-runtime-compose`（2.10.0）：

<br />

    import androidx.compose.foundation.layout.Column
    import androidx.compose.foundation.rememberScrollState
    import androidx.compose.foundation.verticalScroll
    import androidx.compose.material3.Button
    import androidx.compose.material3.Text
    import androidx.compose.material3.TextField
    import androidx.compose.runtime.Composable
    import androidx.compose.runtime.LaunchedEffect
    import androidx.compose.runtime.getValue
    import androidx.compose.runtime.mutableStateOf
    import androidx.compose.runtime.remember
    import androidx.compose.runtime.setValue
    import androidx.compose.ui.Modifier
    import androidx.lifecycle.compose.collectAsStateWithLifecycle
    import androidx.lifecycle.viewmodel.compose.viewModel
    import com.google.ai.edge.litertlm.Backend

    @Composable
    fun ChatScreen(modelPath: String, viewModel: ChatViewModel = viewModel()) {
        val state by viewModel.state.collectAsStateWithLifecycle()
        var input by remember { mutableStateOf("") }
        LaunchedEffect(modelPath) { viewModel.load(modelPath, Backend.GPU()) }
        Column {
            Text(
                state.reply,
                Modifier.weight(1f).verticalScroll(rememberScrollState())
            )
            state.error?.let { Text(it) }
            TextField(value = input, onValueChange = { input = it })
            Button(
                onClick = { viewModel.send(input); input = "" },
                enabled = state.ready && !state.busy
            ) {
                Text("Send")
            }
        }
    }

### 步骤 7：管理 engine 生命周期

- 只要屏幕还在，就把 engine 保存在 `ViewModel` 中。多个屏幕共享同一个 engine 时，把它放在应用作用域的持有者中。
- `ViewModel` 使用自己的线程和作用域。`viewModelScope` 在 `onCleared` 运行之前就被取消，所以在那里启动的关闭操作不会执行。`onCleared` 会在关闭完成后取消 `scope`。
- `release` 会把 `ready` 置为关闭，并持续调用 `cancelProcess` 直到流式回复的 flow 结束。该 flow 最迟在回复自然结束时结束。之后 `release` 关闭 conversation 和 engine，各一次。
- `onCleared` 和替换模型的 `load` 都会在 `Mutex` 下调用 `release`，一次一个，因为 `release` 在回复停止期间会挂起。
- 要开始新的聊天，关闭 conversation 并用 `createConversation` 创建一个新的。保持 engine 处于已加载状态。

## 实现后由用户执行的步骤

代码编译通过后，向用户报告适用的步骤：

- 如果步骤 3 中的路径 A 没有运行，用路径 A 里的两条 `adb` 命令把模型复制到设备。
- 如果应用使用步骤 3 中的路径 C，创建存放 `.litertlm` 文件的 AI pack 模块，并把应用上传到 Play Console。
- 如果该模型没有对应的 `.litertlm` 文件，在工作站上转换模型。这个 skill 不负责转换模型。
- 当用户需要完整的参考应用时，指向 [Google AI Edge Gallery](https://github.com/google-ai-edge/gallery/blob/main/README.md)。

## 故障排查

| 现象 | 原因 | 修复 |
|---|---|---|
| 第一条回复很慢。 | `initialize` 在首次使用时才运行。 | 在应用启动时加载并设置 `cacheDir`。 |
| 第一条 GPU 回复以 `Can not find OpenCL library on this device` 结束。 | 清单中缺少 `uses-native-library` 条目。 | 把步骤 1 中的两个条目加到 `<application>` 内。 |
| `close` 抛出 `IllegalStateException`。 | engine 或 conversation 被关闭了两次，或者 `initialize` 抛出过异常。 | 只在 `initialize` 返回之后保存 engine，并在 `close` 之后把每个字段置为 `null`。 |
| 构建失败并报 `[Hilt] Provided Metadata instance has version 2.4.0`。 | Hilt 2.59.2 无法读取 `litertlm-android` 0.18.0 中的 Kotlin 2.4 元数据。 | 按步骤 1 中的路径 A 或路径 B 处理。 |

## 检查清单

- \[ \] `minSdk` 是否设为 `24` 或更高，并且 `com.google.ai.edge.litertlm:litertlm-android:0.18.0` 是否已加到 `app/build.gradle.kts` 中？
- \[ \] 使用 GPU 后端时，`AndroidManifest.xml` 是否在 `<application>` 内声明了 `libvndksupport.so` 和 `libOpenCL.so`，并带有 `android:required="false"`？
- \[ \] `.litertlm` 文件是否从设备文件系统的绝对路径加载，而不是从 `assets/` 加载？
- \[ \] `initialize`、`sendMessageAsync`、`cancelProcess` 和 `close` 是否都运行在同一个单线程后台 executor 上？
- \[ \] conversation 是否在 engine 之前关闭，且各自只关闭一次？
- \[ \] 项目能否用 `./gradlew assembleDebug` 编译通过？

## 反模式

- **绝不**在 Android 主线程调用 `Engine.initialize`。
- **绝不**把 `.litertlm` 文件放在 `assets/` 中或打包进 APK。
- **绝不**对 `initialize` 抛出过异常的 engine 调用 `close`。
- **绝不**在回复正在流式输出时关闭 engine；先调用 `cancelProcess` 直到 flow 结束。
- **绝不**在 `onCleared` 中从 `viewModelScope` 关闭 `Engine` 或 `Conversation`；该作用域已被取消。
