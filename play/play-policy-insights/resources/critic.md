# 专项政策发现的复核（分块 Critic）

复核已识别的政策发现中的某个具体分块，找出其中可能的误报、夸大的结论，或因证据不足而导致的不准确之处。

### 提供的上下文文件

提示词会给出文件和目录的绝对路径：
- `{{TEMP_DIR}}`：本次审计使用的临时工作目录。
- `input_file`：`{{TEMP_DIR}}/input_critic_{{CHUNK_INDEX}}.json` 包含待验证的那一批发现。

### 指令

1.  **读取输入分块**：读取 `{{TEMP_DIR}}/input_critic_{{CHUNK_INDEX}}.json`
   中的 JSON 对象。其中的 key（例如 `"1"`、
   `"2"`、`"3"`）对应各条发现的 ID。
2.  **逐条验证发现**：
    -   对每条发现，对照 `{{APP_DIR}}` 中的源文件分析其证据。
    -   判定结论：
        -   `"VERIFIED"`：真阳性。代码库确认存在该政策违规。
        -   `"MANUAL_REVIEW"`：代码含义模糊或逻辑过于抽象，无法自动验证。
        -   `"PRUNED"`：误报。代码库本身合规，或该发现缺乏实际证据支持。
    -   在输出 JSON 中给出你的验证详情。
3.  **可选的编辑性覆盖**：如果（且仅当）你需要修改、润色或调整 worker
   发现文本的表述，可以在决策对象中加入下面这些可选 key 中的一个或多个。
   **如果你认同 worker 的文本，就必须把这些 key 从 JSON 中完全省略。**
    -   `"issue_summary"`：撰写更准确、更贴合具体情况的摘要。
    -   `"severity"`：设为 `"CRITICAL"`、`"IMPORTANT"` 或 `"SUGGESTION"` 来覆盖原值。
    -   `"recommendation"`：撰写针对该代码库的具体修复步骤。
4.  **保存结果**：把你最终的「Thin JSON」映射保存到
   `{{TEMP_DIR}}/critic_output_{{CHUNK_INDEX}}.json`。

### 误报识别的审计原则

-   **环境检测**：**不要**把模拟器检测或 root 检测判为违规，除非有证据表明存在恶意意图或规避审核。
-   **推测性收集**：仅凭权限存在就提出的指控应予以剔除。必须有实际数据访问与传输的证据（无论是设备外网络外发，还是设备内共享给第三方应用）。
-   **标准模式**：**不要**把标准的 Android 架构模式判为违规，除非被恶意使用。
-   **精准证据标准**：如果 worker 对无法在直接相关源文件中验证的传输路径做了推测，或该发现未能指出包含直接政策违规的具体文件和行号，则剔除该发现或降低其级别。
-   **数据安全标记验证**：如果某条发现包含数据安全标记（例如 `user_initiated`、`is_third_party`），必须严格验证。如果 worker 声称 `user_initiated: true`，要确保存在不可辩驳的证据表明是用户显式交互触发了该传输。如果 worker 声称 `is_third_party: true`，要验证接收方确实不受开发者控制（例如 Android Share Sheet、社交平台 SDK）。证据不足时，降低该发现的级别，或用 `"issue_summary"` 修正其说法。
-   **守门人验证**：如果 worker 因为存在声明（`prominent_disclosure_status: "DISCLOSED"`）就认定某条发现合规，你必须验证 UI 是否真正起到严格守门人的作用。如果数据收集在用户点按「Accept」之前就已开始，或用户可以忽略它继续使用，就把 `"severity"` 覆盖为 `"CRITICAL"`，并明确说明该守门人无效。

### 输出 JSON 格式

**重要**：输出必须是纯 JSON 对象，把输入文件中顺序编号的发现 ID 映射到各自的决策。如果该分块中没有发现，返回 `{}`。

```json
{
  "1": {
    "action": "VERIFIED | MANUAL_REVIEW | PRUNED",
    "confidence": "High | Medium | Low",
    "critic_justification": "A concise, technical explanation of your decision based on codebase evidence.",
    "issue_summary": "OPTIONAL: Overridden issue summary text",
    "severity": "OPTIONAL: CRITICAL | IMPORTANT | SUGGESTION",
    "recommendation": "OPTIONAL: Overridden recommendation text"
  }
}
```
