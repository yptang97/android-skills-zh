如果你需要把 Prompt API 的响应解析成特定格式（例如 JSON）以便进一步处理，请使用 Structured Output API。

借助 Structured Output API，你可以用 Kotlin 类和注解定义目标输出结构。随后 Prompt API 会以你的 Kotlin 对象的形式返回响应。

生成结构化输出在以下任务中特别有用：

- **实体抽取**：从非结构化文本中抽取结构化字段（例如事件名称、日期、地点）。
- **分类**：把输入文本归入预定义的类别。
- **数据序列化**：把非结构化的用户输入转换成适合存入数据库或用于 API 调用的格式。

## 前置条件

要确认设备上是否提供 Structured Output API，请使用 `isStructuredOutputFeatureAvailable()` API。如果设备上提供 Structured Output API，该 API 返回 `true`，否则返回 `false`。

    suspend fun isStructuredOutputFeatureAvailable(): Boolean

Structured Output API 还有以下要求：

- Android API 级别 26 或更高（`minSdk` 26）
- KSP 插件版本 2.3.6 或更高

## 限制

Structured Output API 有以下限制：

- 仅支持 Kotlin。
- ProGuard 可能干扰带注解类的解析。如果解析时出现错误，请把你的带注解类加入 [keep 规则](https://developer.android.com/topic/performance/app-optimization/keep-rules-overview)，将其从 ProGuard 处理中排除，例如：

    # Keep classes used by structured output for deserialization for release builds.
    -keep class com.google.mlkit.genai.demo.kotlin.Plant { *; }

## 配置项目

要开始使用 Structured Output API，请按以下步骤操作：

1. 如果尚未添加，请在你应用级的 `build.gradle.kts`（或 `build.gradle`）文件中[把 ML Kit Prompt API 添加为依赖项](https://developer.android.com/agents/skills/device-ai/prompt-api/references/get-started#configure-project)。

2. 把 KSP 插件添加到项目级的 `build.gradle.kts` 文件中。请使用与你的 Kotlin 版本兼容的 KSP 插件版本；我们建议使用 KSP 2.3.6 或更高版本。

       dependencies {
           ...
           classpath "com.google.devtools.ksp:com.google.devtools.ksp.gradle.plugin:2.3.6"
       }

3. 把结构化编译器依赖项添加到应用级的 `build.gradle.kts` 文件中：

       dependencies {
           ...
           ksp("com.google.mlkit:genai-schema-compiler:1.0.0-alpha1")
       }

## 定义输出结构

使用 Kotlin 数据类定义你希望模型返回的数据结构。定义输出结构主要用到两个注解：

- 用 `@Generable` 注解把该类定义为结构化输出的目标。
- 在类的属性上使用 `@Guide` 注解，提供描述与约束，引导模型的输出。

以下示例定义了用于抽取植物信息的结构：

    import com.google.mlkit.genai.schema.annotations.Generable
    import com.google.mlkit.genai.schema.annotations.Guide

    @Generable
    data class PlantList(
        @Guide(description = "The list of plants found", minItems = 1, maxItems = 5)
        val plants: List<Plant>
    )

    @Generable("Information about a plant species")
    data class Plant(
        @Guide(description = "The common name of the plant")
        val commonName: String,
        
        @Guide(description = "The full latin scientific name of the plant")
        val scientificName: String,
        
        @Guide(
            description = "The maximum height of the plant in centimeters.",
            minimum = 1.0,
            maximum = 10000.0
        )
        val maxHeightCm: Int,
        
        @Guide(description = "Whether the plant is poisonous or not")
        val isPoisonous: Boolean?,
        
        @Guide(
            description = "The primary continent where this plant is native to",
            enumValues = ["Africa", "Antarctica", "Asia", "Australia", "Europe", "North America", "South America"]
        )
        val nativeContinent: String
    )

### 支持的类型与约束

以下类型可在带 `@Generable` 注解的类中使用，并列出各自支持的 `@Guide` 约束：

| 类型 | 说明 | 支持的 `@Guide` 约束 |
|---|---|---|
| `String` | 用于文本。 | `description`、`enumValues` |
| `Double` / `Float` | 用于浮点数。 | `description`、`minimum`、`maximum` |
| `Int` / `Long` | 用于整数。 | `description`、`minimum`、`maximum` |
| `Boolean` | 用于 true/false 值。 | `description` |
| `List<T>` | 用于受支持类型的列表或嵌套的 `@Generable` 类。 | `description`、`minItems`、`maxItems` |
| `List<String>` | 用于 `String` 值的列表。 | `description`、`enumValues`、`minItems`、`maxItems` > [!NOTE] > **注意：** 设置 `enumValues` 参数会定义列表各个条目允许的取值。 |
| `@Generable` 类 | 用于嵌套的结构化对象。 | `description` |

> [!NOTE]
> **注意：** 不支持嵌套 `@Generable` 类之间的循环依赖（例如某个类引用自身，或类 A 引用类 B、而类 B 又引用类 A）。

## 生成结构化内容

要请求结构化输出，请使用 `generateTypedContentRequest` 辅助函数包装你的标准提示词，并指定目标输出类。

    // 1. Initialize your GenerativeModel as usual
    val generativeModel = Generation.getClient()

    // 2. Prepare the prompt text
    val promptText = "List some common plants found in California."
    val baseRequest = GenerateContentRequest.Builder(TextPart(promptText)).build()

    // 3. Create the typed request, specifying the target class (e.g., PlantList)
    val typedRequest = generateTypedContentRequest(
        generateContentRequest = baseRequest,
        outputClass = PlantList::class
    )

    // 4. Run the inference
    try {
        val typedResponse = generativeModel.generateContent(typedRequest)
        
        // 5. Access the parsed object
        // The response candidates contain the parsed object of type T (PlantList in this case)
        val plantList: PlantList? = typedResponse.candidates.firstOrNull()?.response
        
        if (plantList != null) {
            // Process the structured data
            for (plant in plantList.plants) {
                Log.d("StructuredOutput", "Found plant: ${plant.commonName} (${plant.scientificName})")
            }
        } else {
            Log.e("StructuredOutput", "Failed to parse response into the desired structure.")
            
            // Inspect finish reason for details
            val finishReason = typedResponse.candidates.firstOrNull()?.finishReason
            Log.d("StructuredOutput", "Finish reason: $finishReason")
        }
    } catch (e: GenAiException) {
        // Handle API errors
        when (e.errorCode) {
            GenAiException.STRUCTURED_OUTPUT_INVALID_CLASS -> {
                Log.e("StructuredOutput", "The class structure is not supported.")
            }
            GenAiException.STRUCTURED_OUTPUT_INVALID_VALUE -> {
                Log.e("StructuredOutput", "The model generated values that violate the schema constraints.")
            }
            else -> {
                Log.e("StructuredOutput", "API error: ${e.message}")
            }
        }
    }

## 处理 finishReason 与错误

使用 Structured Output API 时，你应处理该 API 可能抛出的异常；如果解析后的响应为 null，还应检查响应各候选中的 `finishReason` 属性。

### finishReason 取值

`finishReason` 属性可以取以下值之一：

- `TypedFinishReason.STOP`：模型成功完成生成，输出符合 schema。
- `TypedFinishReason.MAX_TOKENS`：模型因达到 Token 上限而停止。输出可能不完整。
- `TypedFinishReason.PARSE_CLASS_ERROR`：模型完成了生成，但生成的 JSON 无法解析为目标 Kotlin 类。
- `TypedFinishReason.STRUCTURE_NOT_ANNOTATED`：目标类或其嵌套类缺少必需的 `@Generable` 注解。
- `TypedFinishReason.STRUCTURE_VALUES_INVALID`：生成的值违反了 `@Guide` 注解中定义的约束（例如取值超出范围、列表长度越界）。
- `TypedFinishReason.OTHER`：生成因其他原因停止。

### 异常

Structured Output API 可能抛出带以下错误码的 `GenAiException`：

- `GenAiException.STRUCTURED_OUTPUT_INVALID_CLASS`（-104）：带注解类的结构无效，或包含不受支持的类型。这通常是开发期的配置错误。请检查你的 `@Generable` 数据类定义，确认所有属性类型都受支持，且不存在循环依赖。
- `GenAiException.STRUCTURED_OUTPUT_INVALID_VALUE`（-105）：模型生成的值无效，或未通过约束校验。这是运行时错误。如果你频繁遇到该错误，可以考虑以下解决办法：
  - 细化提示词指令，更严格地引导模型。
  - 如果 `@Guide` 注解中的约束（例如 minimum、maximum 或列表长度限制）对模型能力来说过于严格，可以适当放宽。
  - 在应用中实现兜底策略，例如重试请求或显示默认状态。

## 统计 Token 数量

要检查结构化提示词是否在输入 Token 上限之内，请用 [`countTokens()`](https://developer.android.com/android/reference/com/google/mlkit/genai/prompt/GenerativeModel#countTokens(com.google.mlkit.genai.prompt.GenerateContentRequest)) 方法计算 Token 数量。

由于结构化输出请求需要把 schema 结构告知模型，仅对原始提示词文本（使用 `GenerateContentRequest` 实例）计算 Token 数并不准确。要得到准确的 Token 数，必须把完整的 `GenerateTypedContentRequest` 实例（包含目标类与 schema 配置）传给 `countTokens()` 方法：

    suspend fun <T : Any> countTokens(request: GenerateTypedContentRequest<T>): CountTokensResponse
