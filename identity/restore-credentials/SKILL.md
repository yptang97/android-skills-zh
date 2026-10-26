---
name: restore-credentials
description: 提供使用 androidx.credentials 库实现 Android Restore Credentials 功能所需的
  知识和流程。用这个 skill 创建、登录和删除恢复密钥，让用户在新设备上恢复后能静默登录。
  内容涵盖版本兼容性、依赖、服务端前置条件，以及创建、取回和清除恢复密钥的完整
  客户端实现。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-14'
  keywords:
  - Credential Manager
  - Restore Credentials
  - backup & restore
  - backup
  - restore
  - implementation
---

## 基础

目标是通过 Android Credential Manager API（`androidx.credentials`）实现 **Restore Credentials** 功能。这使正在使用或
正在集成 Credential Manager 的应用能在用户于新设备上恢复应用时静默地把用户重新登录。Restore Credentials
独立于应用的主认证方式（密码、passkey、联合登录）运行，
且无需改动现有登录流程的 UI。

### 范围

**关键：** 本 skill 只覆盖 Android 客户端集成。它**不**实现服务端的加密校验
逻辑。实现完成后，必须提醒开发者这一点，并向其说明
[需要告知开发者的要点](#backend-guidelines)。

## 实现指南

在接到为开发者应用实现 Restore Credentials 的指示时，记住以下几点：

1. 实现之前，你**必须**阅读并理解[双层
   恢复架构](#two-tier-restoration-architecture)，并查看[该做与不该做](#dos-and-donts)。
2. 实现之后，你**必须**向开发者呈现[后端指南](#backend-guidelines)，提醒其后端配置。务必提醒开发者：后端仍需他们自己实现。

## 双层恢复架构 <a id="two-tier-restoration-architecture"></a>

为了获得有韧性的登录体验，通过**双层架构**取回凭据：

1. **第 1 层（主路径——后台）：** 在设备设置过程中通过应用的 `BackupAgent.onRestoreFinished()` 回调自动执行。这在用户首次打开应用之前完成一次无感的恢复，使后台同步和通知送达得以进行。
2. **第 2 层（次路径——前台）：** 在启动 `Activity.onCreate()` 中运行，用于兜住后台恢复未完成的情况（例如网络中断、恢复延迟）或 `allowBackup` 被禁用的情况。

如果清单中的 `allowBackup` 设为 true，两层都要实现。否则只实现第 2 层（前台恢复）。**不要**改动清单中
`allowBackup` 的值。

如果你给应用添加了 `BackupAgent`，还**必须**在清单中设置
`android:fullBackupOnly="true"`。如果在你实现之前应用里已经存在 `BackupAgent`，**不要**这样做。

## 该做与不该做 <a id="dos-and-donts"></a>

**该做：**

- 检查 `AndroidManifest.xml` 中 allowBackup 的值，据此判断需要实现哪一层。
- 为 createCredential 实现回退：始终先用 `isCloudBackupEnabled` 设为 true 调用它。如果抛出 `E2eeUnavailableException`，捕获后把 `isCloudBackupEnabled` 设为 `false` 重试。
- 如果清单中 `allowBackup` 为 true，实现一个 `BackupAgent`（`android.app.backup.BackupAgent` 的子类）。
- 如果你给应用添加了 `BackupAgent`，在清单中设置 `android:fullBackupOnly="true"`。
- 在用户退出登录时调用 `clearCredentialState()`。这是彻底登出用户所必需的安全措施。
- 在新设备上首次启动应用时尝试获取恢复密钥，如果你的应用使用了 `BackupAgent.onRestoreFinished()` 回调，也在这其中尝试。
- 即使用户已登录，也要确保创建恢复凭据。
- 确保 `onRestoreFinished()` 中的凭据取回和登录同步执行（例如使用 `runBlocking`）。
- 如果你的应用使用通知，在 `BackupAgent` 中恢复通知。（例如捕获 FCM token 并发送给后端）
- 如果你实现了模拟网络请求或桩，确保把所有占位符替换为格式正确的有效 JSON 凭据请求载荷。
- 把凭据创建和取回封装进各自专用的函数。因为凭据创建必须在多处调用（注册、登录），取回要跨多层（`BackupAgent` 和启动 `Activity`），这样可以避免代码重复。
- 实现完成后，提醒开发者[实现后端](#implementation-guide)的关键指南。
- 如果组织有多个包名不同的应用，为每个应用分别生成恢复密钥，因为恢复密钥与唯一应用包名绑定。

**不该做：**

- 不要改动 `AndroidManifest.xml` 中 `allowBackup` 的值。Restore Credentials 功能不受 allowBackup 设置影响，也就是说即使用户的 `allowBackup` 为 false，只要存在 Restore Credential，用户仍会被自动登录。
- 如果 `AndroidManifest.xml` 中 `allowBackup` 为 `false`，不要实现 `BackupAgent`。
- 不要假定 `GetCredentialResponse` 中存储的凭据是 `PublicKeyCredential` 类型。它的类型是 `RestoreCredential`。
- 不要在构造 `GetCredentialRequest` 时把 `GetRestoreCredentialOption` 与任何其他 `CredentialOption` 链在一起。
- 不要假定 `CredentialManager` 或 Android 系统会在用户退出应用时自动删除恢复密钥。你必须用 `TYPE_CLEAR_RESTORE_CREDENTIAL` 的 `ClearCredentialStateRequest` 显式调用 `clearCredentialState`。
- 不要移除任何已有的 `clearCredentialState()` 调用。未指定类型的 `ClearCredentialStateRequest` 只会清除所有非恢复类凭据。

## 实现步骤 <a id="implementation-guide"></a>

按以下指南实现 Android 客户端代码。**逐步**遵循，不要实现任何后端功能，完成后只需提醒
用户查看[后端指南](#backend-guidelines)。

## 版本兼容性

Credential Manager 的 Restore Credentials 可在运行 Android 9（API
级别 28）及更高版本的设备上工作，要求 Google Play services（GMS）核心版本 24220000 或
更高，以及 `androidx.credentials` 库 1.5.0 或更高版本。

## 前置条件

配置一个[依赖方服务器](#backend-guidelines)，与用于 [passkey](#dos-and-donts) 的服务器类似。如果你
已经配置了处理 passkey 认证的[服务器](#two-tier-restoration-architecture)，
恢复密钥就沿用同一套服务端实现。

> [!NOTE]
> **注意：** 虽然 passkey 和恢复密钥的服务端实现相同，你的客户端应用可以在不支持 passkey 的情况下支持恢复密钥。因为恢复密钥独立于你应用的认证方式（例如密码或 Sign in with Google），你无需对应用代码中现有的认证方式做任何额外改动。

## 依赖

把以下依赖添加到应用模块的 `build.gradle` 文件：

### Kotlin

```kotlin
dependencies {
    implementation("androidx.credentials:credentials:1.7.0-alpha03")
    implementation("androidx.credentials:credentials-play-services-auth:1.7.0-alpha03")
}
```

### Groovy

```groovy
dependencies {
    implementation "androidx.credentials:credentials:1.7.0-alpha03"
    implementation "androidx.credentials:credentials-play-services-auth:1.7.0-alpha03"
}
```

Restore Credentials 从 androidx.credentials 库 1.5.0 及更高版本起可用。
不过建议尽量使用依赖的最新稳定版本。

> [!NOTE]
> **注意：** 无论清单中是否设置了 [`allowBackup`](references/android/guide/topics/manifest/application-element.md)，Restore Credentials 功能都能工作。

## 概述

1. [**创建恢复密钥**](#create-restore-key)：要创建恢复密钥，完成以下步骤：
   1. [**实例化 Credential Manager**](#implementation-guide)：创建一个 `CredentialManager` 对象。
   2. [**从应用服务器获取凭据创建选项**](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API)：由你的应用服务器把创建恢复密钥所需的细节发送给客户端应用。
   3. [**创建恢复密钥**](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)：如果用户已登录你的应用，为其账号创建恢复密钥。
   4. [**处理凭据创建响应**](https://w3c.github.io/webauthn/#dictdef-publickeycredentialrequestoptionsjson)：把客户端应用的凭据发送给应用服务器处理，并处理任何异常。
2. [**用恢复密钥登录**](#sign-restore)：要用恢复密钥登录，完成以下步骤：
   1. [**从应用服务器获取凭据取回选项**](#get-credential-retrieval)：由你的应用服务器把取回恢复密钥所需的细节发送给客户端应用。
   2. [**获取恢复密钥**](#get-restore)：在用户设置新设备时向 Credential Manager 请求恢复密钥。这让用户无需额外输入即可登录。
   3. [**处理凭据取回响应**](#handle-sign-in)：把客户端应用的恢复密钥发送给应用服务器以登录用户。
3. [**删除恢复密钥**](#delete-restore)。

## 创建恢复密钥

你的应用应覆盖用户登录的所有情形，确保活跃用户都创建了
恢复密钥。在以下场景中创建恢复密钥：

- 用户已登录且尚未创建恢复密钥（例如在主 `Activity` 的 `onCreate` 方法中）。
- 用户正在登录或完成新账号注册流程时。

为优化性能，避免在每次登录时都创建或检查恢复
凭据带来的开销，在本地存储中设置一个 `boolean` 标志或凭据
创建时间戳，例如 `has_synced_restore_credential`，用来
跟踪密钥是否已经创建。

> [!NOTE]
> **注意：** 恢复密钥与应用唯一的包名绑定。如果组织的主应用和子应用包名不同，为每个应用分别创建恢复密钥。

### 实例化 Credential Manager

用应用 activity 的 context 实例化一个 `CredentialManager` 对象。

    // Use your app or activity context to instantiate a client instance of
    // CredentialManager.
    private val credentialManager = CredentialManager.create(context)

### 从应用服务器获取凭据创建选项

在应用服务器中使用兼容 FIDO 的库，把创建恢复凭据所需的信息
发送给客户端应用，例如关于用户、应用以及其他配置属性的
信息。有关服务端实现的更多信息，见[服务端
指南](https://developers.google.com/identity/passkeys/developer-guides/server-registration)。

### 创建恢复密钥

解析服务器发来的公钥创建选项后，把这些选项包装进
[`CreateRestoreCredentialRequest`](https://developer.android.com/reference/androidx/credentials/CreateRestoreCredentialRequest) 对象，并用
`CredentialManager` 对象调用
[`createCredential()`](https://developer.android.com/reference/androidx/credentials/CredentialManager#createCredential(android.content.Context,androidx.credentials.CreateCredentialRequest)) 方法，从而创建
恢复密钥。

    // createRestoreRequest contains the details sent by the server 
    val response = credentialManager.createCredential(context, createRestoreRequest)

#### 代码要点

- `CreateRestoreCredentialRequest` 对象包含以下字段：

  - `requestJson`：应用服务器以 [Web Authentication API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API) 格式发送的凭据创建选项，对应 [`PublicKeyCredentialCreationOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)。
  - `isCloudBackupEnabled`：`Boolean` 字段，决定恢复密钥是否应
    备份到云端。默认情况下该标志为 `true`。该
    字段有以下取值：

    - `true`：（**推荐**）如果用户启用了 Google 备份和端到端加密（例如屏幕锁定），该值允许把恢复密钥备份到云端。
    - `false`：该值把密钥保存在本地而不放在云端。如果用户选择从云端恢复，该密钥在新设备上不可用。

  > [!CAUTION]
  > **小心：** 建议把 `isCloudBackupEnabled` 设为 `true`。如果禁用云备份而用户从云备份恢复，取回恢复密钥的调用会失败。用云备份恢复应用的用户拿不到恢复密钥，也不会被自动登录。

### 处理凭据创建响应

Credential Manager API 返回
[`CreateRestoreCredentialResponse`](https://developer.android.com/reference/androidx/credentials/CreateRestoreCredentialResponse) 类型的响应。该响应以 [JSON 格式](https://w3c.github.io/webauthn/#authenticatorattestationresponse)持有公钥
凭据注册响应。

把公钥从应用发送给依赖方服务器。这个公钥
与创建 passkey 时生成的公钥类似。服务端处理 passkey 创建的同一份代码
也能处理恢复密钥的创建。有关服务端实现的更多信息，见
[passkey 的
指南](references/android/identity/passkeys/create-passkeys.md)。

在恢复密钥创建过程中，处理以下异常：

- [`CreateRestoreCredentialDomException`](https://developer.android.com/reference/androidx/credentials/exceptions/restorecredential/CreateRestoreCredentialDomException)：当 `requestJson` 无效或不符合 [`PublicKeyCredentialCreationOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson) 的 WebAuthn 格式时抛出该异常。
- [`E2eeUnavailableException`](https://developer.android.com/reference/androidx/credentials/exceptions/restorecredential/E2eeUnavailableException)：当 `isCloudBackupEnabled` 为 `true`，但用户设备没有数据备份或端到端加密（例如屏幕锁定）时抛出该异常。
  要确保在所有情况下都创建 Restore Credentials，你必须显式处理 `E2eeUnavailableException`：用 `isCloudBackupEnabled` 设为 `true` 调用 `createCredential`。如果抛出 `E2eeUnavailableException`，捕获后把 `isCloudBackupEnabled` 设为 `false` 再次调用 `createCredential`。
- `IllegalArgumentException`：当 `createRestoreRequest` 为空或不是有效 JSON，或缺少符合 WebAuthn [规范](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)的有效 `user.id` 时抛出该异常。

## 用恢复密钥登录

用 Restore Credentials 在设备设置过程中静默登录用户。

### 从应用服务器获取凭据取回选项

把从服务器获取恢复密钥所需的选项发送给客户端应用。
这一步可参考 passkey 的类似指南：[用 passkey 登录](references/android/identity/passkeys/sign-in-with-passkeys.md)。
有关服务端实现的更多信息，见[服务端
认证指南](https://developers.google.com/identity/passkeys/developer-guides/server-authentication#create_credential_request_options)。

### 获取恢复密钥

要在新设备上获取恢复密钥，在 `CredentialManager` 对象上调用 `getCredential()` 方法。

建议在以下两种场景中都取回恢复密钥：

- 应用在该设备上首次启动时。此场景中的凭据恢复与应用数据的恢复相互独立。
- 如果启用了应用数据备份与恢复，在应用数据恢复完成后立即获取恢复密钥。用 [`BackupAgent`](https://developer.android.com/reference/android/app/backup/BackupAgent) 配置应用的备份，并确保在 [`onRestoreFinished`](https://developer.android.com/reference/android/app/backup/BackupAgent#onRestoreFinished()) 回调中完成 `getCredential` 功能。不要使用 `onRestore` 方法，它只对键值备份调用，而 `onRestoreFinished` 对任何类型的备份恢复都会被可靠调用。这样可避免用户首次打开新设备时的潜在延迟，让用户无需打开你的应用就能与之交互。例如，这让你的应用能在用户于新设备上首次打开应用之前就发送通知，这对消息类或通信类应用尤其重要。

如果你新建了 `BackupAgent`，而之前已通过
`allowBackup="true"` 启用了备份，在应用清单中设置布尔值
`android:fullBackupOnly="true"`。这样可确保应用的备份与恢复行为
保持不变。

> [!IMPORTANT]
> **重要：** 取回恢复凭据后，通知不会自动恢复。如果你用 Firebase 处理通知，必须取回 Firebase Cloud Messaging（FCM）token 并发送给后端，才能成功恢复后台消息与通知。

    // Fetch the options required to get the restore key
    val authenticationJson = fetchAuthenticationJson()

    // Create the GetRestoreCredentialRequest object
    val options = GetRestoreCredentialOption(authenticationJson)
    val getRequest = GetCredentialRequest(listOf(options))

    val response = credentialManager.getCredential(context, getRequest)

    // Type-check and extract the restore credential
    val credential = response.credential as RestoreCredential

Credential Manager 的 API 返回
[`GetCredentialResponse`](https://developer.android.com/reference/android/credentials/GetCredentialResponse) 类型的响应。该响应中包含的凭据
明确为 `RestoreCredential` 类型，其中持有公钥。

### 处理登录响应

把公钥从应用发送给依赖方服务器，服务器随后可用它
登录用户。在服务端，这一操作与用 passkey 登录类似。服务端
处理 passkey 登录的同一份代码也能处理用恢复密钥的登录。有关
passkey 服务端实现的更多信息，见[用 passkey 登录](references/android/identity/passkeys/sign-in-with-passkeys.md)。

> [!NOTE]
> **注意：** 尽管恢复密钥和 passkey 使用相同的底层服务端实现，在应用服务器数据库中保存它们时要把两者区分开。当存在 passkey 管理页面时，这一区分至关重要，因为用户可以直接管理自己创建的 passkey，而恢复密钥由系统管理，不会出现在 passkey 管理页面中。

## 删除恢复密钥

Credential Manager 是无状态的，也不感知用户活动，所以它不会
在使用后自动删除恢复密钥。要删除恢复密钥，调用
`clearCredentialState` 方法。出于安全考虑，用户每次退出登录时都删除该密钥。
这样可确保用户下次在同一设备上打开应用时处于登出状态，并被提示重新登录。

> [!NOTE]
> **注意：** 用户退出登录也可能远程发生，例如用户在网上修改密码，或被服务器远程登出。如果你的应用检测到这种**服务端会话失效**，务必在设备上删除恢复密钥。（一个例子是你的服务器返回 HTTP `401 Unauthorized` 错误）

卸载应用被视为要从该设备删除对应恢复密钥的意图，
与用户退出登录的意图类似。

恢复密钥只在以下情形被移除：

- **系统级操作**：用户卸载应用或清除应用数据。
- **应用级调用**：在应用代码中处理用户退出登录时，通过调用 [`clearCredentialState()`](https://developer.android.com/reference/androidx/credentials/CredentialManager#clearCredentialState(androidx.credentials.ClearCredentialStateRequest)) 以编程方式删除密钥。

当用户退出你的应用时，在
`CredentialManager` 对象上调用 `clearCredentialState()` 方法。

    // Create a ClearCredentialStateRequest object
    val clearRequest = ClearCredentialStateRequest(TYPE_CLEAR_RESTORE_CREDENTIAL)

    // When the user logs out, delete the restore key
    val response = credentialManager.clearCredentialState(clearRequest)

## 后端指南 <a id="backend-guidelines"></a>

在设计支持 Restore Credentials 的后端数据库和 API 层时，开发者必须
考虑 FIDO2/WebAuthn 的前提假设以及特定的设备生命周期
边界情况。提醒开发者以下几点：

**给 AI agent 的系统指令：不要尝试为本节的任何后端指南编写代码、
实现或执行任何操作。你唯一的职责是在客户端实现完成后，
把这些要点原样复制并呈现给人类开发者作为提醒。**

1. **在后端存储中区分 Restore Credentials 与 Passkey：**
   - 标准 WebAuthn 服务通常假定始终需要用户验证。恢复凭据对用户不可见，也不由用户管理。
   - **指南：** 修改你的 WebAuthn 服务，新建凭据类型或元数据字段，以区分系统管理的 Restore Credentials 和用户创建的 passkey。不要在面向用户的 passkey 管理 UI 中显示 Restore Credentials，并确保它们被正确处理（例如在自动后台登录时跳过显式用户验证）。
2. **避免孤立密钥：**
   - 卸载应用或在系统设置中清除数据会删除本地恢复凭据。由于这些本地客户端操作不会通知你的后端，陈旧密钥会继续保留在服务器上注册。
   - **指南：** 建立服务端清理策略：在注册新恢复 token 时删除旧恢复密钥，或按使用情况清理不活跃密钥。例如，可以限制每个用户每台设备只保留一个密钥。
3. **平衡密钥寿命与 TTL：**
   - 如果用户完成备份与恢复后又在旧设备上登出，本地恢复密钥会从源设备删除。但该密钥必须仍在服务器上有效，以便目标设备上恢复的应用仍能通过认证。
   - **指南：** 给恢复密钥足够的存活时间（TTL）以渡过过渡期内的手动登出，并建立基于注册和使用情况的服务端密钥删除规则，而不是依赖客户端删除回调。
4. **支持多设备：**
   - 一个用户可能拥有多台活跃设备，并从其中任意一台发起备份或恢复。
   - **指南：** 确保后端数据库 schema 允许把多个活跃 Restore Credentials 映射到单个用户账号（例如每台设备/设备 ID 一个活跃恢复密钥），而不是假定用户与恢复凭据是 1:1 关系。
5. **服务端会话失效：**
   - 用户的会话可能被远程吊销。这可能由用户操作触发，例如用户在网上重置密码，或由服务器操作触发，使 API 返回 HTTP `401 Unauthorized` 表示会话过期。
   - **指南：** 如果适用，确保在这种情况发生时清除手机上该用户的恢复凭据。

## 参考资料

- **WebAuthentication API（WebAuthn）文档 \& 规范**
  *何时使用：* 仅当你需要检查或调试 FIDO2/WebAuthn 的严格 JSON schema 要求时使用这些资源，特别是在生成模拟数据或格式化 `requestJson`
  （`PublicKeyCredentialCreationOptionsJSON`）和 `authenticationJson` 载荷时。

- [MDN Web Authentication API 文档](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API)：WebAuthn API 的 Mozilla Developer Network
  指南与参考

- [W3C `PublicKeyCredentialCreationOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)：JSON 格式的 WebAuthn 凭据创建请求的
  数据结构定义。

- [W3C `PublicKeyCredentialRequestOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialrequestoptionsjson)：JSON 格式的 WebAuthn 认证或断言请求的
  数据结构定义。
