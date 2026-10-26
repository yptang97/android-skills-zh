本 skill 说明如何为 ML Kit Prompt API 优化提示词。

## 指南与规则

Prompt API 的提示词设计最佳实践见
[提示词设计](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prompt-design)。请应用这些核心规则：

- 包含用于 in-context learning 的示例，并给出输出的示例。下面这个提示词示例之所以算 in-context learning，是因为它给出了期望模型输出的示例：Analyze the message and return whether the customer sentiment is positive, negative, or neutral. Example 1: Input - "This product doesn't work"; Output - "Negative" Example 2: Input - "I liked this product"; Output - "Positive"
- 让提示词保持简洁。删除重复或反复出现的指令。不要包含 hello、please、do this、help me with 这类对话式填充语。例如，冗长的提示词如："Hello! I want you to act as an expert translator for me today. I am going to give you a short paragraph of text in English, and I would really like it if you could translate it into formal, high-level Business French. Please make sure that you do not include any intro like 'Here is your translation' or any closing remarks at all. Just output the translation itself." 可以用下面这个简洁的提示词来改进："Translate to formal Business French. Return ONLY the translation"
- 使用成对的 XML/HTML 定界符来标记动态输入（例如 `<email>[content]</email>`），把用户数据与提示词指令清晰地隔离开。说明这些定界符代表占位符文本，实际实现中应由代码替换。
- 如果输出需要把响应解析成特定格式，使用 [Structured Output API](https://developer.android.com/agents/skills/device-ai/prompt-api/references/structured-output)。不要把 Structured Output API 的实现写进提示词本身，而是在向用户展示优化后的提示词之后再提及它，让用户知道如何解析模型输出。使用 Structured Output API 的提示词必须从函数签名返回 `@Generable` 类型的对象，而不是字符串或 JSON 字符串。
- 通过添加输出约束让输出保持简短，例如词数、字符数、条目数或句子数。例如添加这样的约束："The summarization must be 10 words or fewer."
- 对规定模型应如何行为的简短指令使用 [system instructions](https://developer.android.com/agents/skills/device-ai/prompt-api/references/system-instructions)，对超过 200 词的提示词使用 [prefix caching](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prefix-caching)。

## 示例

以下是用户可能请你优化的提示词示例，以及改进后的优化版本。

### 示例 1

未优化的提示词：

    Process this customer email and return the order ID, what was bought, the phone
    number, and what they want. Format it as JSON so my app can read it.

优化后的提示词：

    ## Task

    Extract key details from the customer email below.

    ## Customer Email

    <email>
    [email_content]
    </email>

说明：因为用户想用这个提示词提取的信息非常适合用 Structured Output API 处理，优化后的提示词隐式使用了
Structured Output API，不需要显式定义提取数据的 schema。在向用户解释为提示词所做优化的回复里，要提到
优化后的提示词是为配合 Structured Output API 使用而设计的。同时说明 "" 定界符表示占位符文本，在实际实现中
应替换为代码。

### 示例 2

未优化的提示词：

    Given this itinerary for a trip: [Flight to Paris (CDG), Check-in: Hotel Le
    Meurice, Visit to the Louvre, Dinner at Le Jules Verne, Eiffel Tower Visit,
    Versailles Palace Tour, Montmartre Walk, Seine River Cruise, Pastry and Macaron
    Tasting, Flight Out], generate the following: overall vibe, tips on how to
    prepare for this trip, and common short phrases to learn for the trip.

优化后的提示词：

    ## Task

    Analyze the trip itinerary below and extract details to build a concise travel
    guide.

    ## Rules
    - Overall vibe: Limit to 1 short sentence (under 15 words).
    - Preparation tips: Provide exactly 3 short tips (maximum 10 words per tip).
    - Useful phrases: Provide exactly 3 phrases (under 15 words each).

    ## Itinerary

    <itinerary>
    [itinerary_content]
    </itinerary>
