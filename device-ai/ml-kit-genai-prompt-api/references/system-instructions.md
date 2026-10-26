系统指令让你可以为模型设定人设、设定其回复的语气，或提供它必须遵循的具体规则。这些指令与用户的提示词是分开的，模型会以更高的优先级处理它们，以确保模型按预期表现。

常见使用场景包括：

- **设定人设：**例如「你是一位乐于助人的数学家教。」
- **强制输出格式：**例如「总是用项目符号回答。」
- **设定约束：**例如「不要回答关于政治的问题。」

## 前置条件

系统指令在运行 Gemini Nano V3 及更高版本的设备上可用。支持的设备列表见 [Prompt API 设备支持](https://developer.android.com/ml-kit/genai#prompt-device)。

## 限制

不建议把系统指令与
[前缀缓存](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prefix-caching) 一起使用。一般来说，用系统指令来表达
定义模型行为的简短指令；如果你需要在多次查询中重复提示词的大部分内容并
需要优化性能，则使用前缀
缓存。

## 如何使用系统指令

要提供系统指令，创建一个 `SystemInstruction` 对象，并把它传给 `GenerateContentRequest` 构建器：

    import com.google.mlkit.genai.prompt.SystemInstruction
    import com.google.mlkit.genai.prompt.TextPart
    import com.google.mlkit.genai.prompt.generateContentRequest

    // 1. Define the system instruction
    val systemInstruction =
        SystemInstruction("You are a concise assistant. Answer in 2 sentences or less.")

    // 2. Create the request
    val request = generateContentRequest(TextPart("How does photosynthesis work?")) {
        this.systemInstruction = systemInstruction
    }

    // 3. Run inference
    try {
        val response = generativeModel.generateContent(request)
        println(response.candidates.firstOrNull()?.text)
    } catch (e: GenAiException) {
        // Handle SDK-specific exceptions
    }

你还可以把系统指令直接传入 `generateContentRequest` 请求构建器，进一步简化代码：

    val request = generateContentRequest(
        SystemInstruction("You are a pirate. Speak like one."),
        TextPart("What is the weather like today?")
    ) {
        // Optional configurations like temperature
        temperature = 0.7f
    }

## 最佳实践

以下是使用系统指令的一些最佳实践：

- **清晰直接：**模型对清晰、直接的指令比对含糊的指令执行得更好。示例如下：
  - 含糊（避免）：「不要写太多。尽量有帮助、友好，并把输出格式排好看。」
  - 清晰（推荐）：「你是一位友好的客户支持助理。回复最多 3 句话。任何列表都用项目符号。」
- **简洁：**系统指令虽然强大，但过长的指令会消耗模型有限的上下文窗口。
- **把 Token 计数算进去：**确保你的 Token 计数逻辑包含系统指令，以免低估请求大小。建议把系统指令控制在 150 词（100-200 个 Token）以内。
- **测试并迭代：**模型行为会因措辞而变化。用各种用户输入测试，确保模型始终如一地保持其人设。