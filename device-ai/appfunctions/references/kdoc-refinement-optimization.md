为 AI agent 和 Model Context Protocol 优化 AppFunction KDoc。

## 指令

### 工作流：面向 agent 的文档

1. **明确核心结果**：用有力的祈使动词开头，例如「Search」「Create」或「Update」。聚焦*用户收益*，而不是代码实现。
2. **工作流依赖**：如果必须先调用另一个函数，用标准句式明确说明：**Required workflow: Call "Function A" first to "Objective"**。
3. **参数文档**：
   - 对于**函数**：使用具体的 `@param` 标签。把校验规则和默认值写在这里。
   - 对于**可序列化类**：直接在每个属性声明处写内联 KDoc。KSP **不会**从类级标签中提取文档。
4. **错误面映射**：重写 `@throws` 说明，为 AI agent 提供有用的恢复步骤，例如「如果出现 "Error"，建议用户检查网络连接。」

### 工作流：面向 server 指令的全局应用描述

在为 `app_metadata.xml` 编写 `appfn:description` 时，遵循以下指令：

1. **记录跨函数关系**：说明工具之间的依赖或调用顺序，例如「拉取数据前始终先调用 'authenticate'。」
2. **记录操作模式**：指导 LLM 采用节省令牌的用法，例如「用 'batch_update' 代替多次 'update' 调用。」
3. **说明约束**：定义清晰的边界，例如「文件操作限定在工作区内」或「速率限制：每分钟 10 个请求。」
4. **反模式**：
   - 不要重复单个函数的说明。
   - 不要加入营销话术或主观夸赞。
   - 不要试图提示模型的性格或对话风格。

## 关键约束

### 描述性，而非祈使

描述函数*做*什么，而不是 LLM *必须*做什么。避免「你必须调用...」这类说法，改用「此函数提供...」。

### 不要「废话」

删除「此方法用于...」或「有助于...」这类对话式填充。保持简洁、技术化。

### 可序列化类使用内联 KDoc

**强制要求**：对于 `@AppFunctionSerializable` 类，每个属性的文档必须内联。对这类类，KSP 会忽略类级的 `@param` 或 `@property` 标签。

## 示例

### 示例：MCP 重构

**原始**：

`/** This function helps you find people. */`

**改进后**：

     /**
       * Search for message recipients by name or email.
       * Required workflow: Call this before "sendMessage" to obtain valid recipient IDs.
       * @param query Search string for name/email. If null, returns 3 most recent contacts.
       * @return List of "Recipient" objects matching the query.
       */

### 示例：全局应用描述

**改进后**：

    This app provides functions for task management and team collaboration.

    Operational Patterns:
    - Always use 'searchUsers' to resolve user handles to internal IDs before calling 'assignTask'.
    - Prefer 'batchUpdateStatus' when modifying more than three tasks simultaneously to reduce latency.

    Constraints:
    - Task titles are limited to 100 characters.
    - Attachment uploads are limited to 5 MB.
