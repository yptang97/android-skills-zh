{{#IF_ANY data_sources, disclosure}}
{{ACTIVATE_GOAL}}
{{/IF_ANY}}
## 数据安全与隐私审计

### 需要核查的政策

- **政策精神**：用户有权完整知晓哪些个人或敏感信息离开了他们的设备。按 Play 商店
  规则，任何离开设备的用户数据传输都必须在
  Play 商店数据安全表单中明确声明，而敏感或不明显的数据收集
  需要事先的应用内显著披露和用户明确同意。

- **通用评估矩阵**：
  | 场景 | 技术观察 | `user_initiated` | `is_third_party` | 披露状态 | 严重程度 | 问题摘要 |
  | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
  | **1** | **未传输**（仅本地） | N/A | N/A | `EXEMPT` | `SUGGESTION` | 「符合数据安全要求（仅本地）」 |
  | **2A** | **已传输** + **后台** + **未披露** | `false` | （任意） | `MISSING` | `CRITICAL` | 「**静默后台上传**」：违反政策。数据在未事先披露的情况下被发送。 |
  | **2B** | **已传输** + **后台** + **已发现披露** | `false` | （任意） | `DISCLOSED` | `IMPORTANT` | 「**后台上传（声称已披露）**」：已发现证据；需要 Critic 复核。 |
  | **3** | **已传输** + **用户主动发起** + **第一方** | `true` | `false` | `EXEMPT` | `IMPORTANT` | 「**用户主动发起的收集**」：免于披露，但**必须**在 Play 商店表单中声明。 |
  | **4** | **已传输** + **用户主动发起** + **第三方** | `true` | `true` | `EXEMPT` | `SUGGESTION` | 「**手动分享**」：**政策豁免**。由用户触发向第三方的传输；无需披露或声明。 |

- **豁免情形参考**：
  - **匿名数据**：完全匿名且无法关联到用户的数据属于豁免范围。
  - **端到端加密（E2EE）**：开发者无法读取的 E2EE 数据
    属于豁免范围。
  - **开放网络的 WebView**：在浏览开放网络的 WebView 中输入的数据
    属于豁免范围。
  - *如果上述任一情形适用，请把严重程度降为 `SUGGESTION` 并标记
    `EXEMPT`。*

---

### 审计流程

#### 步骤 0：事实梳理

- **识别第三方 SDK**：如果你观察到网络、崩溃上报或
  跟踪遥测，请按需使用文件读取工具检查项目的构建文件（例如 build.gradle、
  build.gradle.kts、libs.versions.toml），
  以确认集成了哪些 SDK（Analytics、Ads 等）。
- **理解离开设备的出口**：运用你对标准 Android
  框架组件的原生知识来识别传输目的地。重点关注活跃的
  出站通道，例如标准 HTTP/REST 库（如 OkHttp、Retrofit、
  Ktor、HttpURLConnection）、把数据传出设备的 WebView、后台同步
  任务，或分析/遥测框架（如 Firebase、Mixpanel、Adjust、
  AppsFlyer）。
- **识别披露**：查看下面的 `disclosure`。把它们作为步骤 2 的
  起点。

#### 步骤 1：核查实际发生的传输（前向追踪）

对下面 `data_sources` 中列出的每个数据来源，从给出的确切位置出发，
把技术信号追踪到它的传输终点。
- **强制起点**：定位到 `data_sources` 列表中指定的
  文件和行号。
- **循环纪律**：你必须分析所列**每一条**证据的传输路径，
  确认它是否到达离开设备的出口。
- **证据**：给出数据被传入出口的文件/行号，以及
  该出口已知传输行为的简要论证（例如网络
  上传、遥测负载）。
- **语义对齐**：用提供的 `*Description*` 确认
  代码证据确实与该数据类型的语义范围相符。如果
  变量或逻辑指向的是无关数据（例如一个并不
  标识用户 `NAME` 的 `fileName`），请把它视为误报，并按
  **证据标准**降级或剔除该发现。
- **出口分类**：判断目的地：
  1. **第一方 / 服务提供商（`is_third_party: false`）**：
     开发者控制的服务器、Firebase、自建 API 等。
  2. **第三方（`is_third_party: true`）**：社交 SDK、广告网络，或
     用户通过 Android 分享面板（`Intent.ACTION_SEND`）选择的应用。
- **歧义处理要求**：如果目的地不明确（例如通用 URL 或
  混淆过的 SDK），你必须默认为 `is_third_party: false`（宁可判为
  收集）。
- **设备内传输**：把通过 Intent/ContentProvider 向另一个应用静默共享数据
  也视为传输（`is_transferred: true`），即使它
  没有使用网络。

#### 步骤 2：语义搜索保护措施（UI 披露）

**条件执行**：**仅当** `is_transferred` 为
`true` 且 `user_initiated` 为 `false` 时才执行这一步。
- **理由**：用户主动发起的操作（场景 3 和 4）免于显著
  披露要求。如果 `user_initiated` 为 true，不要搜索披露。
- **语义搜索**：查看下面的 `disclosure` 列表。
- **闸门检查**：检查展示该同意界面的 Activity/Fragment
  是否充当闸门（即，是否把数据收集逻辑的初始化挡在其后）。不要尝试
  从底层的 repository 反向追踪到 UI。
- **内容检查**：UI 必须说明收集了*什么*以及*如何*使用。
- **证据**：给出版局文件名并附上找到的具体文本。

#### 步骤 3：汇总

- **`findings`（关键）**：对于下面 `data_sources` 列表中发现的**每一种**
  数据类型，你都必须构造并在 `"findings"` 数组内**恰好**输出**一个**
  对象，无论它是合规还是违规。
- **求值键**：对 `"findings"` 中每个数据类型对象，评估并
  填充：
  1.  **psl_constant**：把它严格设为该数据类型的大写 **PSL Constant**
     （即下面**待追踪数据来源**一节中的**Data Type**
     标题，例如 `"PRECISE_LOCATION"`、`"CONTACTS"`）。这对
     下游匹配至关重要。
  2.  **policy_id**：根据正在执行的检查，把它严格设为 `"prominent_disclosure_policy"`
     或 `"data_safety_section"`。
  3.  **is_transferred**：如果数据被传输
     到设备之外或传输给设备上的第三方，则为 `true`（JSON Boolean）；如果仅在
     本地，则为 `false`（JSON Boolean）。
  4.  **user_initiated**：如果用户显式触发
     该传输，则为 `true`（JSON Boolean）。
  5.  **is_third_party**：如果目的地是第三方
     （例如分享面板、社交 SDK），则为 `true`（JSON Boolean）；如果是
     第一方/服务提供商（例如你自己的后端），则为 `false`（JSON Boolean）。
  6.  **prominent_disclosure_status**：严格设为以下三个
     大写枚举之一：`"DISCLOSED"`（找到可见披露与用户同意）、
     `"MISSING"`（未找到披露，或该界面不是有效的闸门）、
     `"EXEMPT"`（按政策免于显著披露）。
  7.  **purpose**：归类收集该数据的目的（例如「应用
     功能」「分析」「仅本地功能」）。
  8.  **linked_to_user**：如果数据关联到某个
     身份、邮箱或设备 ID，则为 `true`（JSON Boolean），否则为 `false`（JSON Boolean）。

- **把 findings 严格映射到 5 个场景：**使用「需要核查的政策」中的场景矩阵，
  根据 `is_transferred`、`user_initiated`、`is_third_party` 和
  `prominent_disclosure_status` 的组合，设置合适的 `severity` 与 `issue_summary`。

---

### 领域特定启发式

在严格遵守你的执行准则中定义的「启发式与外推边界」的前提下，
应用以下启发式：
1. **隐式数据泄漏（日志循环）**：检查是否有任何自定义日志
   框架（例如 Crashlytics、自定义错误日志器或遥测 SDK）
   把敏感变量作为诊断负载的一部分接收。如果用户
   标识（例如邮箱、账号 ID）或精确位置被传入
   会把负载上传到设备之外的日志器，这就算作**已传输**
   （`is_transferred`：true）。
2. **第三方 SDK 抽取**：按需查看项目的构建文件
   （例如 build.gradle 或 libs.versions.toml）。如果 Google Ads 或
   Firebase 之类的 SDK 已被初始化并且能访问 context，评估它们
   是否在自动抽取广告 ID 或设备标识。如果
   这些库已加载且清单申请了宽泛的网络
   权限，请把这些设备标识视为出于分析/营销目的而**已传输**
   （`is_transferred`：true）。
3. **间接同意**：如果你找到 `AlertDialog` 或披露说明，请核实
   它是否是真正的闸门。如果应用在用户点击「Accept」*之前*
   就开始跟踪用户数据，或者用户关闭对话框后仍能
   继续使用应用而数据跟踪依然活跃，请把这标记为
   `prominent_disclosure_policy` 下的 `CRITICAL` 违规。

---

### 代码库上下文与证据

{{#IF semantic_files.LEGAL}}
**语义初筛起点（关注的文件）**：
以下文件很可能包含隐私或同意逻辑：
- 与 **LEGAL** 相关：
  {{#EACH semantic_files.LEGAL}}
  - `{{ITEM}}`
  {{/EACH}}
{{/IF}}

{{#IF data_sources}}
**待追踪数据来源**：
{{#EACH data_sources}}
- **Data Type**：{{KEY}}
  *Description: {{VALUE.description}}*
  {{#EACH VALUE.findings}}
  - `{{ITEM}}`
  {{/EACH}}
{{/EACH}}
{{/IF}}

{{#IF disclosure}}
**UI 披露起点**：
{{#EACH disclosure}}
- `{{ITEM}}`
{{/EACH}}
{{/IF}}

## 输出 schema

把最终 JSON 输出保存到 `{{TEMP_DIR}}/worker_{{GOAL_NAME}}.json`。

```json
{
  "domain": "Data Safety and Privacy",
  "findings": [
    {
      "psl_constant": "STRING_VALUE (The exact PSL Constant, e.g., USER_ACCOUNT)",
      "policy_id": "prominent_disclosure_policy | data_safety_section",
      "issue_summary": "STRING_VALUE",
      "severity": "CRITICAL | IMPORTANT | SUGGESTION",
      "files_involved": ["STRING_VALUE"],
      "evidence": "STRING_VALUE",
      "recommendation": "STRING_VALUE",

      # UNIFIED DATA SAFETY METADATA LOOKUP KEYS:
      "is_transferred": true | false,
      "user_initiated": true | false,
      "is_third_party": true | false,
      "prominent_disclosure_status": "DISCLOSED | MISSING | EXEMPT",
      "purpose": "STRING_VALUE",
      "linked_to_user": true | false
    }
  ]
}
```
