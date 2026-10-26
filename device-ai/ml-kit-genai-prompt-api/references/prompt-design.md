使用 Prompt API 时，有一些特定策略可用于定制你的提示词并取得最佳结果。本页介绍为
Gemini Nano 格式化提示词的最佳实践。

关于更通用的提示词工程指引，请参阅 [Prompt Engineering
whitepaper](https://www.kaggle.com/whitepaper-prompt-engineering)、[Prompt Engineering for Generative
AI](https://developer.android.com/machine-learning/resources/prompt-eng) 和 [Prompt design strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)。

或者，如果想自动精简并改进提示词，可以使用
[zero-shot optimizer](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/zero-shot-optimizer#optimizing_for_smaller_models)，它可以面向
`gemma-3n-e4b-it` 这类端侧模型。

## 提示词设计最佳实践

为 Prompt API 设计提示词时，使用以下技巧：

- **提供示例以进行上下文学习**。在提示词中加入分布良好的示例，
  向 Gemini Nano 展示你期望的结果类型。

  使用上下文学习时，可以考虑启用 [prefix caching](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prefix-caching) 功能，
  因为提供示例会让提示词变长，并增加推理时间。
- **保持简洁**。冗长的开场白和重复的指令可能产生次优结果。让提示词保持聚焦、切中要点。
  如果你需要重复某条指导模型行为的简短指令，可以考虑使用
  [system instructions](https://developer.android.com/agents/skills/device-ai/prompt-api/references/system-instructions)。

- **结构化提示词**，以生成更有效的回复，例如这个
  [sample prompt template](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/prompt-design-strategies#sample-prompt-template)，它清晰地定义了指令、约束和示例。

- **保持输出简短**。LLM 的推理速度在很大程度上取决于输出长度。仔细考虑如何为你的用例生成
  尽可能短的输出，并通过手动后处理把输出整理成选定的格式。为了确保回复输出符合你期望的
  格式，请使用 [Structured Output API](https://developer.android.com/agents/skills/device-ai/prompt-api/references/structured-output)。

- **添加分隔符**。使用 `<background_information>`、`<instruction>` 和 `##` 这类分隔符，
  在提示词的不同部分之间建立分隔。对 Gemini Nano 来说，在组件之间使用 `##` 尤为关键，
  因为它能显著降低模型无法正确解释每个组件的可能性。

- **优先使用简单逻辑和更聚焦的任务**。如果你发现需要多步推理的提示词难以取得好结果
  （例如 *先执行 X，如果 X 的结果是 A，就执行 M；否则执行 N；然后执行 Y……*），
  可以考虑把任务拆开，让每次 Gemini Nano 调用处理一个更聚焦的任务，同时用代码把多次调用
  串联起来。如果你确实需要一次性处理复杂的、推理密集的任务，可以考虑使用
  [thinking mode](https://developer.android.com/ml-kit/genai/prompt/android/thinking-mode)。

- **对确定性任务使用较低的 temperature 值**。对于实体抽取或翻译这类不依赖创造性的任务，
  可以考虑从 `temperature` 值 `0.2` 开始，并根据测试结果调整该值。
