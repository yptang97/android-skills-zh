{{#IF_ALL requested_permissions.exact_alarm, exact_alarm}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.foreground_service, foreground_service}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.accessibility, accessibility}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.APPS_ON_DEVICE, data_sources.APPS_ON_DEVICE}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.SMS_CALL_LOG, data_sources.SMS_CALL_LOG}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.MEDIA, data_sources.MEDIA}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.AUDIO, data_sources.AUDIO}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.ALL_FILES, data_sources.FILES_AND_DOCS}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.LOCATION, data_sources.PRECISE_LOCATION}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.LOCATION, data_sources.APPROX_LOCATION}}{{ACTIVATE_GOAL}}{{/IF_ALL}}
{{#IF_ALL requested_permissions.CONTACTS, data_sources.CONTACTS}}{{ACTIVATE_GOAL}}{{/IF_ALL}}

## 权限与 API 审查

### 提示：推断核心功能

由于你必须判断某些权限能否由应用的「核心用途」证明合理，可以使用以下快速
启发式方法：
1. **「坏掉」测试**：该功能对应用的主要用途是否不可或缺？如果去掉该功能后
   应用仍然可用、仍然有价值，那它就不属于核心功能。
2. **清单意图**：检查 `AndroidManifest.xml`。`LAUNCHER` Activity 的名称以及
   专门的 `<intent-filter>` 声明（例如默认短信处理程序）能强烈说明应用的主要
   用途。
3. **命名**：包名（`{{PACKAGE_NAME}}`）和应用标签（`{{APP_NAME}}`）往往直接
   描述了应用的用途。
4. **执行上下文**：在 `BackupManager` 这类类中使用，说明是核心功能；而在
   `AdHelper`、`CrashReporter` 或 `AnalyticsManager` 中使用，则说明是次要功能。
5. **强制规则**：**广告、分析或社交分享**这类次要功能**永远不能**成为后台
   位置、所有文件访问或宽泛媒体访问等受限权限的理由。

---

### 待核查的政策

{{#IF_ALL requested_permissions.MEDIA, data_sources.MEDIA}}
#### 照片与视频访问政策（Policy ID: photo_video_access_policy）

- **目标**：评估应用的核心功能是否能证明对照片的宽泛访问合理，还是应当迁移到
  Android Photo Picker。
- **政策精神**：用户隐私至上。只有专门的媒体管理类应用（如相册或备份应用）才
  应申请宽泛的媒体存储权限。对于头像上传、自定义分享或添加附件这类标准任务，
  开发者必须使用范围受限的 API，以避免安全风险。
- **证据**：
  {{#EACH data_sources.MEDIA}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.MEDIA}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | Target SDK | 是否申请了宽泛的媒体权限？ | 已检查的条件 / 上下文 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **33 或更高** | 是 | 应用申请宽泛的媒体访问权限（例如 `READ_MEDIA_IMAGES`），但功能只需要用户选定的媒体。 | `IMPORTANT` | 迁移到 **Android Photo Picker**（`MediaStore.ACTION_PICK_IMAGES`），它不需要任何权限弹窗。 |
  | **任意** | 是 | 应用申请宽泛的存储/媒体权限，但它并不是专门的媒体管理类应用（例如社交或工具类应用）。 | `IMPORTANT` | 迁移到 **Android Photo Picker**，用于单项或多项媒体选择。 |

- **领域特定启发式（严格限定范围）**：
  不要只看标准的原生文件选择器。用下面的启发式方法做外推：
  1. **用户选定媒体启发式**：分析代码在何处处理用户选定的文件。如果图片或视频
     严格通过用户点击按钮来加载（例如「上传头像」「分享照片」「添加附件」），并且
     一次只处理一个，那么宽泛的文件系统媒体权限在结构上就是多余的。标记
     `IMPORTANT` 违规，并建议迁移到 Photo Picker。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.ALL_FILES, data_sources.FILES_AND_DOCS}}
#### 所有文件访问政策（Policy ID: all_files_access_policy）

- **目标**：评估应用的核心用途是否能证明高风险 `MANAGE_EXTERNAL_STORAGE` 权限
  合理。
- **政策精神**：完整的文件系统访问是一种受限特权。Play Store 严格把
  `MANAGE_EXTERNAL_STORAGE` 限定在那些全盘读写对核心用途至关重要的应用（例如
  文件管理器、病毒扫描器、备份工具）。不合规的应用必须改用 Scoped Storage 或
  Storage Access Framework（SAF）。
- **证据**：
  {{#EACH data_sources.FILES_AND_DOCS}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.ALL_FILES}}
  - `{{ITEM}}`
  {{/EACH}}
- **通用评估矩阵**：
  | 应用核心用途 | 权限是否合理？ | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **文件管理器、杀毒、备份/恢复或文档管理器** | 是（合规） | 无 | 无需处理；核心用途证明该受限权限合理。 |
  | **标准工具类、社交媒体、游戏或生产力应用** | 否（违规） | `CRITICAL` | 从清单中移除 `MANAGE_EXTERNAL_STORAGE`。对于文档选择或本地文件保存，迁移到 **Storage Access Framework（SAF）**。 |

- **领域特定启发式（严格限定范围）**：
  精细审查文件系统是如何被查询的：
  1. **Scoped Storage 是否足够**：用存储 API 检查相关文件。如果应用使用文件系统
     路径仅仅是为了记录诊断日志、存放自定义缓存或保存简单的下载产物，那么宽泛
     访问就不合理。建议改用应用专属目录（`Context.getExternalFilesDir()`），它
     不需要任何权限。
{{/IF_ALL}}

{{#IF requested_permissions.LOCATION}}
{{#IF_ANY data_sources.PRECISE_LOCATION, data_sources.APPROX_LOCATION}}
#### 位置访问政策（Policy ID: location_access_policy）

- **目标**：核实位置访问是必需的、使用最小范围，并且已妥善披露。
- **政策精神**：用户跟踪极为敏感。应用必须收集所需的最小位置范围（大致位置还是
  精确位置），提供清晰醒目的披露，并且绝不能使用后台跟踪，除非它对安全、导航或
  体能健身功能是必需的。
- **证据**：
  {{#IF data_sources.PRECISE_LOCATION}}
  - **精确位置使用情况**：
    {{#EACH data_sources.PRECISE_LOCATION}}
    - `{{ITEM}}`
    {{/EACH}}
  {{/IF}}
  {{#IF data_sources.APPROX_LOCATION}}
  - **大致位置使用情况**：
    {{#EACH data_sources.APPROX_LOCATION}}
    - `{{ITEM}}`
    {{/EACH}}
  {{/IF}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.LOCATION}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | 范围 | Target SDK | 发现的问题 / 已检查的条件 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **前台** | 任意 | 申请了 `ACCESS_FINE_LOCATION`，但功能只需要城市级或大致天气/搜索功能。 | `IMPORTANT` | 把清单降级为 `ACCESS_COARSE_LOCATION`，以遵守最小范围的强制要求。 |
  | **前台** | 任意 | 应用用途（`{{APP_NAME}}`）并不涉及位置，却使用了前台跟踪，且缺少醒目披露提示代码。 | `IMPORTANT` | 在申请前台权限*之前*，实现一个**应用内醒目披露**对话框，说明会收集哪些位置数据。 |
  | **后台** | 任意 | 仅出于广告、营销或一般分析而申请 `ACCESS_BACKGROUND_LOCATION`。 | `CRITICAL` | **高风险违规**：从代码库中彻底移除后台位置收集。 |
  | **后台** | 任意 | 申请了后台位置，但功能在前台位置访问下也能运行。 | `IMPORTANT` | 把该功能降级为仅前台位置跟踪，并移除后台权限。 |
  | **后台** | 任意 | 后台位置是正当需要的，但醒目披露没有提到「位置」以及「当应用关闭或不在使用时」。 | `IMPORTANT` | 更新醒目披露文本，明确写出「位置」和「当关闭或不在使用时」。 |
  | **前台** | **37 或更高** | 在 Android 17+ 上申请精确位置。 | `SUGGESTION` | 迁移到 **Location Button** API，作为精确前台位置的最小范围机制。 |

- **领域特定启发式（严格限定范围）**：
  主动追查自定义后台任务与披露：
  1. **前台是否足够的测试**：分析触发位置更新的后台线程、`WorkManager` 任务或
     后台服务。如果后台流程执行的同步或位置计算可以推迟到用户正在查看应用时
     再做，标记 `IMPORTANT` 违规。
  2. **合理预期测试**：如果应用标签（`{{APP_NAME}}`）或包名暗示这是一个按常理
     不该跟踪位置的工具类应用，就评估任何间接的地理跟踪（例如对网络 IP 地址做
     地理查询，或把本地 Wi-Fi SSID 日志发到设备外）。若发现此类行为，标记
     `IMPORTANT` 级「缺少醒目披露」。
{{/IF_ANY}}
{{/IF}}

{{#IF_ALL requested_permissions.CONTACTS, data_sources.CONTACTS}}
#### 联系人访问政策（Policy ID: contacts_access_policy）

- **目标**：评估宽泛的联系人访问（`READ_CONTACTS`）是否合理，还是应当使用
  Android Contact Picker。
- **政策精神**：通讯录包含敏感的个人信息。Play Store 要求应用使用范围受限的
  联系人访问，除非宽泛、持续的联系人同步至关重要（例如社交网络的找朋友或完整的
  联系人管理器）。
- **证据**：
  {{#EACH data_sources.CONTACTS}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.CONTACTS}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | Target SDK | 访问模式 | 已检查的条件 / 发现 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **任意** | 宽泛（`READ_CONTACTS`） | 为一次性交易、文件分享、推荐或简单表单而申请宽泛访问。 | `IMPORTANT` | 迁移到 **Android Contact Picker**（`Intent.ACTION_PICK_CONTACTS`），以安全地查询联系人。 |
  | **37 或更高** | 宽泛（`READ_CONTACTS`） | Target SDK 为 37+（2026 年 10 月生效），且宽泛访问被用于次要或标准任务。 | `IMPORTANT` | 迁移到 **Android Contact Picker**，因为宽泛的联系人访问已受限。 |

- **领域特定启发式（严格限定范围）**：
  评估联系人查询的深度：
  1. **单项验证**：搜索读取联系人表（`ContactsContract.CommonDataKinds`）的数据库
     cursor。如果这些 cursor 只是让用户选择单个好友、手机号或邮箱地址，那么宽泛
     的联系人访问就是违规。建议改用 Contact Picker。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.exact_alarm, exact_alarm}}
#### 精确闹钟政策（Policy ID: exact_alarm_policy）

- **目标**：评估应用的核心功能是否能证明 `USE_EXACT_ALARM` 权限合理。
- **政策精神**：精确闹钟会损害系统性能和电池续航。Play Store 严格把高风险的
  `USE_EXACT_ALARM` 权限限定在闹钟、计时器和日历应用，这些场景中精确到秒的时序
  至关重要。
- **证据**：
  {{#EACH exact_alarm}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.exact_alarm}}
  - `{{ITEM}}`
  {{/EACH}}
- **通用评估矩阵**：
  | 应用核心用途 | 申请的权限 | 是否合理？ | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **闹钟、计时器或日历应用** | `USE_EXACT_ALARM` | 是（合规） | 无 | 无需处理。 |
  | **标准工具类、游戏、同步或生产力应用** | `USE_EXACT_ALARM` | 否（违规） | `IMPORTANT` | 改用 `SCHEDULE_EXACT_ALARM`（它遵守系统电池约束），或使用标准的 `AlarmManager` 非精确调度。 |

- **领域特定启发式（严格限定范围）**：
  检查闹钟的触发目标：
  1. **对时间不敏感的同步**：核实调度闹钟的那部分文件。如果闹钟被用来拉取网络
     更新、清理缓存文件、触发分析上传或推送本地每日通知，那么精确时序并不合理。
     建议用 `WorkManager` 而不是 `AlarmManager` 处理后台任务。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.foreground_service, foreground_service}}
#### 前台服务（Policy ID: foreground_services_policy）

- **目标**：核实前台服务的声明与理由说明。
- **政策精神**：前台服务让进程在后台保持存活，必须对用户高度可见。每个声明的
  服务都必须在清单中定义合适的 `foregroundServiceType`，而 `specialUse` 这类特殊
  类型需要具体的 tag property 理由说明。
- **证据**：
  {{#EACH foreground_service}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.foreground_service}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | 服务配置 | 理由说明检查 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **缺少 type 标签** | 声明了前台服务，但缺少 `foregroundServiceType` 属性。 | `CRITICAL` | 在清单的服务声明中添加合适的 `android:foregroundServiceType` 属性。 |
  | **缺少 specialUse 属性** | 服务类型为 `specialUse`，但清单缺少必需的 `<property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" ...>` 标签。 | `CRITICAL` | 在 service 块内添加 `<property>` 标签，并给出合法的子类型字符串。 |
  | **类型不对齐** | 声明的 FGS 类型与应用的核心用途在逻辑上不一致。 | `IMPORTANT` | 重新对齐 FGS 类型以匹配应用功能；如果用户可见的前台存在并不合理，就把后台操作迁移到 **WorkManager**。 |
  | **声明提醒** | 已声明前台服务（即使类型正确）。 | `SUGGESTION` | **需要 Play Console 声明**：对于 target Android 14+ 的应用，你必须为所使用的每种类型在 Play Console（App content 部分）中完成前台服务声明，提供功能描述、用户影响视频和具体用例选择。 |

- **领域特定启发式（严格限定范围）**：
  审视 specialUse 的理由说明与服务行为：
  1. **理由字符串审查**：读取 `specialUse` 的 `<property>` 标签文本。如果文本包含
     弱化、样板化或占位式的理由（例如「需要后台进程才能让应用运行」），标记
     `IMPORTANT` 违规，并提醒开发者 Google Play 审核人员会拒绝该服务。
  2. **通知完整性**：核实 FGS 实现是否创建了有效的用户可见通知。如果服务启动时
     没有关联 `startForeground()` 或通知构建逻辑，标记 `IMPORTANT` 违规。
  3. **Play Console 声明确认**：如果使用了任何前台服务，标记 `SUGGESTION`，提醒
     开发者必须在 Play Console 中提交专门的声明表单，且需要提供该功能的视频演示。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.accessibility, accessibility}}
#### 无障碍 API 政策（Policy ID: accessibility_api_policy）

- **目标**：核实无障碍服务的配置与理由说明。
- **政策精神**：无障碍 API 提供深度的系统访问能力，用于帮助残障用户。把这些 API
  用于非无障碍任务（例如 UI 自动化、屏幕抓取、后台监控或广告拦截）被 Google Play
  严格禁止，会导致应用立即被拒。
- **证据**：
  {{#EACH accessibility}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.accessibility}}
  - `{{ITEM}}`
  {{/EACH}}
- **通用评估矩阵**：
  | 服务配置 | 真实代码用法 | 是否合理？ | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **`isAccessibilityTool="true"`** | 代码为普通用户执行屏幕抓取、广告拦截或自动点击流程。 | 否（违规） | `CRITICAL` | **被 Play Store 拒绝的高风险**：移除无障碍辅助配置。把 UI 自动化迁移到标准的 Android 测试库。 |
  | **`isAccessibilityTool` 为 false 或缺失** | 代码实现了无障碍监听器，但应用并不是专门的无障碍辅助应用。 | 缺少醒目披露 | `CRITICAL` | **被 Play Store 拒绝的高风险**：由于你为普通工具类应用申请了无障碍权限，你必须在请求用户启用该服务之前，实现应用内的**醒目披露与明确同意页面**，否则应用会被拒。 |

- **领域特定启发式（严格限定范围）**：
  追查无障碍事件的摄取路径：
  1. **遥测外流**：扫描无障碍服务的方法（`onAccessibilityEvent`）。如果服务捕获
     屏幕文本、通知或按键并转发到本地缓存、SharedPreferences 或设备外的网络日志
     端点，就按无障碍 API 政策标记 `CRITICAL` 违规。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.APPS_ON_DEVICE, data_sources.APPS_ON_DEVICE}}
#### 应用可见性（Policy ID: package_visibility_policy）

- **目标**：评估应用的核心功能是否能证明对已安装应用的宽泛可见性
  （`QUERY_ALL_PACKAGES` 或相关包 API）合理。
- **政策精神**：已安装应用列表会暴露敏感的用户习惯。Play Store 严格把
  `QUERY_ALL_PACKAGES` 权限限定在直接负责设备安全管理的应用（杀毒、文件管理器、
  设备搜索）。
- **证据**：
  {{#EACH data_sources.APPS_ON_DEVICE}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.APPS_ON_DEVICE}}
  - `{{ITEM}}`
  {{/EACH}}
- **通用评估矩阵**：
  | 应用核心用途 | 申请的权限 | 是否合理？ | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **杀毒、文件管理器或设备搜索** | `QUERY_ALL_PACKAGES` | 是（合规） | 无 | 无需处理。 |
  | **任意应用** | `QUERY_ALL_PACKAGES` | 否，被用于广告、分析或次要营销。 | `IMPORTANT` | **高风险违规**：从清单中移除该权限。如果分享/集成确实需要包检查，改用具体的 `<queries>` intent 声明。 |

- **领域特定启发式（严格限定范围）**：
  检查间接查询：
  1. **间接的包搜索**：检查代码是否用 `PackageManager.getInstalledPackages()` 动态
     查询包详情，或在循环中检查 intent。如果这些 intent 列表被用来推断是否存在
     竞品应用或广告画像，就标记 `IMPORTANT` 级违反应用可见性指南。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.SMS_CALL_LOG, data_sources.SMS_CALL_LOG}}
#### 短信与通话记录权限（Policy ID: sms_call_log_policy）

- **目标**：评估应用的核心功能是否能证明访问敏感短信或通话记录数据合理。
- **政策精神**：短信与通话详情属于高风险数据。Google Play 把访问权限限定给默认
  电话处理程序和默认短信处理程序。标准工具类或购物类应用必须使用非特权 API 来
  完成基于短信的验证。
- **证据**：
  {{#EACH data_sources.SMS_CALL_LOG}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.SMS_CALL_LOG}}
  - `{{ITEM}}`
  {{/EACH}}
- **通用评估矩阵**：
  | 代码上下文 | 发现的问题 / 已检查的触发条件 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **OTP/账号验证** | 应用申请短信权限以自动读取登录验证码（OTP）。 | `IMPORTANT` | 迁移到 **SMS Retriever API** 或 **SMS User Consent API**，它们不需要任何权限。 |
  | **工具类或次要功能** | 应用为非核心的仪表板或通知功能申请短信/通话记录访问。 | `CRITICAL` | **高风险违规**：从清单中彻底移除短信与通话记录权限。 |
  | **默认短信处理程序** | 应用看起来是合法的处理程序（例如实现了必需的 intent filter）。 | `SUGGESTION` | **Play Console 声明**：你必须在 Play Console 中提交**权限声明表单**，并可能被要求提供该核心功能的视频演示。 |

- **领域特定启发式（严格限定范围）**：
  审查后台接收器：
  1. **后台短信监听**：检查是否有 `BroadcastReceiver` 监听
     `android.provider.Telephony.SMS_RECEIVED`。如果该接收器在后台解析文本，却不是
     指定的默认短信处理程序，标记 `CRITICAL` 违规。
  2. **默认处理程序确认**：如果应用申请了短信/通话记录权限，并正确实现了系统要求
     的默认处理程序 intent filter，标记 `SUGGESTION`，提醒开发者必须提交 Play
     Console 声明表单。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.AUDIO, data_sources.AUDIO}}
#### 录音政策（Policy ID: audio_recording_policy）

- **目标**：评估应用的核心功能是否能证明对录音的宽泛访问合理。
- **政策精神**：未经提示的录音是严重的隐私侵害。应用应严格只在用户可见、有明确
  时长边界的操作中申请麦克风访问。Target SDK 34+ 鼓励对临时需求使用系统托管的
  Microphone Button。
- **证据**：
  {{#EACH data_sources.AUDIO}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.AUDIO}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | Target SDK | 录音触发上下文 | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- |
  | **34 或更高** | 应用为偶发的、由用户发起的语音输入或短时录音申请宽泛的 `RECORD_AUDIO` 权限。 | `IMPORTANT` | 迁移到 **Android Microphone Button** API，以安全地处理临时音频。 |
  | **任意** | 应用在没有用户明确控制的情况下为次要功能（分析、user-agent 细节等）捕获音频。 | `IMPORTANT` | 移除麦克风权限。对于一般搜索，集成标准的 Android Speech Recognizer intent。 |

- **领域特定启发式（严格限定范围）**：
  核实录音指示器与线程：
  1. **持续捕获**：扫描活跃的录音线程（`AudioRecord` 或 `MediaRecorder`）。如果应用
     最小化时录音循环仍可能处于活跃状态，或没有可见的用户指示器，就标记为
     `CRITICAL` 违规。
{{/IF_ALL}}

{{#IF_ALL requested_permissions.FILES_AND_DOCS, data_sources.FILES_AND_DOCS}}
#### 文件与文档访问政策（Policy ID: files_and_docs_policy）

- **目标**：评估宽泛的文件访问（非媒体）是否合理，还是应当使用
  Storage Access Framework。
- **政策精神**：在现代 Android 版本上，存储隔离（Scoped Storage）是强制要求。
  对共享文件的宽泛访问受到严格限制。标准文件、文档和下载文件夹应当通过范围受限
  的 contract 来访问，以防全局文件系统窥探。
- **证据**：
  {{#EACH data_sources.FILES_AND_DOCS}}
  - `{{ITEM}}`
  {{/EACH}}
  **已申请的相关权限**：
  {{#EACH requested_permissions.FILES_AND_DOCS}}
  - `{{ITEM}}`
  {{/EACH}}
  {{#IF TARGET_SDK}}
  **Target SDK**：`{{TARGET_SDK}}`
  {{/IF}}
- **通用评估矩阵**：
  | Target SDK | 存储配置 | 是否合理？ | 严重程度 | 直接可执行的建议 |
  | :--- | :--- | :--- | :--- | :--- |
  | **30 或更高** | 应用为简单的文档选择而申请宽泛的 `READ_EXTERNAL_STORAGE` 或 `WRITE_EXTERNAL_STORAGE`。 | 否（违规） | `IMPORTANT` | **Scoped Storage 强制要求**：把你的文档/文件选择迁移到 **Storage Access Framework（SAF）**（`Intent.ACTION_OPEN_DOCUMENT`）。 |

- **领域特定启发式（严格限定范围）**：
  审视外部目录的创建：
  1. **手动文件同步启发式**：检查代码是否在外部存储上创建自定义的根级文件夹
     （例如 `Environment.getExternalStorageDirectory() + "/my_folder"`）。如果这些
     目录是为标准文档输出或日志而创建，标记 `IMPORTANT` 违规。引导开发者使用
     scoped storage 路径。
{{/IF_ALL}}

## 输出 schema

把最终 JSON 输出保存到 `{{TEMP_DIR}}/worker_{{GOAL_NAME}}.json`。

```json
{
  "domain": "Permissions and APIs",
  "findings": [
    {
      "policy_id": "STRING_VALUE (The exact Policy ID, e.g., photo_video_access_policy)",
      "issue_summary": "STRING_VALUE",
      "severity": "CRITICAL | IMPORTANT | SUGGESTION",
      "files_involved": ["STRING_VALUE"],
      "evidence": "STRING_VALUE",
      "recommendation": "STRING_VALUE"
    }
  ]
}
```
