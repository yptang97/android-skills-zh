{{#IF_ANY data_sources.USER_ACCOUNT, data_sources.ACCOUNT_DELETION}}
{{ACTIVATE_GOAL}}
{{/IF_ANY}}
## 用户账号与身份审计

### 提示：推断账号的存在

要判断应用是否涉及用户账号（即使它使用 Google 登录或 Firebase Auth 之类的第三方服务商），可以查找：
1. **登录/认证界面**：名为 `login`、`auth`、`signin` 或 `signup` 的语义文件或布局。
2. **账号管理**：`AccountManager`、`CredentialManager` 或 `Firebase.auth` 之类的 API。
3. **用户资料**：引用了 `profile`、`my account` 或 `user settings` 的 UI 字符串或数据模型。

### 需要核查的政策

{{#IF_ANY data_sources.USER_ACCOUNT, semantic_files.USER_ACCOUNT}}
#### Play Console 要求（Policy ID: login_credentials）

- **目标**：识别应用是否实现了登录墙或认证界面。
- **政策精神**：为确保 Play 商店审核人员能顺利测试和审计应用，如果应用功能被登录界面
  限制，开发者必须在 Play Console 中提交可用且不会过期的凭据。
- **证据**：
  {{#IF semantic_files.USER_ACCOUNT}}
  - **账号文件**：
    `{{#EACH semantic_files.USER_ACCOUNT}}{{ITEM}}, {{/EACH}}`
  {{/IF}}
  {{#IF data_sources.USER_ACCOUNT}}
  - **账号信号**：
    `{{#EACH data_sources.USER_ACCOUNT}}{{ITEM}}, {{/EACH}}`
  {{/IF}}
- **通用评估矩阵**：
  | 应用状态 | 发现/条件 | 严重程度 | 可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **检测到登录界面** | 应用展示或包含登录界面、注册墙或认证界面。 | `IMPORTANT` | **管理控制台要求**：由于你的应用实现了登录流程，你必须在 Play Console 面板中完成两项手动设置才能通过审核：<br>1. **审核人员演示凭据**：提交有效且不会过期的测试凭据，使 Google Play 审核人员能访问你受限制的功能。<br>2. **账号删除链接**：提交一个公开的账号删除网页链接，以满足 Google Play 的数据删除政策。 |

- **领域特定启发式规则（严格受限）**：
  不要只看标准原生登录按钮。按以下启发式规则做推断：
  1. **隐藏的守门人**：分析某些关键功能（例如同步本地数据库、结账表单或仅限会员的面板）
     是否即使用户直接进入首页也需要认证。如果你推断出某些功能工作流需要登录，
     就按登录墙处理，并输出 `IMPORTANT` 级别的控制台凭据与删除链接提醒。
{{/IF_ANY}}

{{#IF_ANY data_sources.USER_ACCOUNT, data_sources.ACCOUNT_DELETION}}
#### 账号删除要求（Policy ID: account_deletion）

- **目标**：如果应用涉及用户账号，就必须提供易于发现的应用内账号删除机制。
- **政策精神**：用户有权要求删除数据，这是一项基本权利。如果用户能在应用内创建账号，
  就必须能在应用内删除账号。删除必须清除远程数据库记录，而不仅仅是退出登录。
- **证据**：
  {{#IF data_sources.USER_ACCOUNT}}
  - **账号信号（存在性）**：
    `{{#EACH data_sources.USER_ACCOUNT}}{{ITEM}}, {{/EACH}}`
  {{/IF}}
  {{#IF data_sources.ACCOUNT_DELETION}}
  - **删除信号（机制）**：
    `{{#EACH data_sources.ACCOUNT_DELETION}}{{ITEM}}, {{/EACH}}`
  {{/IF}}
- **通用评估矩阵**：
  | 应用账号状态 | 发现/删除证据 | 严重程度 | 可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **涉及用户账号** | 应用管理用户账号，但没有任何代码、布局或字符串表明存在应用内删除按钮或删除流程。 | `IMPORTANT` | **实现应用内删除**：创建一个极易发现的入口（例如放在用户资料/账号设置下），让用户能直接在应用内发起账号删除。 |

- **领域特定启发式规则（严格受限）**：
  不要只分析基础的「Delete」按钮。要主动分析自定义实现和灰色地带的实现：
  1. **部分删除陷阱**：阅读所有找到的删除机制的实现。如果代码只调用了 `clearPreferences()`、
     清除了本地 cookie，或触发标准的 `logout()`，却没有发送远程删除/清除的网络 API 调用来
     清理后端用户记录，就把它标记为违反删除要求的 `IMPORTANT` 问题。
  2. **间接用户账号**：如果应用使用第三方登录桥接（例如 Google 登录、Firebase），
     但没有在自己的服务器上存储显式的账号资料，只要有任何用户偏好或设备标识符
     被远程缓存，它仍然涉及用户账号信息。这种情况下同样需要删除链接/按钮。
{{/IF_ANY}}

## 输出 schema

把最终的 JSON 输出保存到 `{{TEMP_DIR}}/worker_{{GOAL_NAME}}.json`。

```json
{
  "domain": "User Account and Identity",
  "findings": [
    {
      "policy_id": "STRING_VALUE (The exact Policy ID, e.g., account_deletion)",
      "issue_summary": "STRING_VALUE",
      "severity": "CRITICAL | IMPORTANT | SUGGESTION",
      "files_involved": ["STRING_VALUE"],
      "evidence": "STRING_VALUE",
      "recommendation": "STRING_VALUE"
    }
  ]
}
```
