---
name: restore-credentials
description: 提供使用 androidx.credentials 库实现 Android Restore Credentials 功能所需的
  知识与工作流。用这个 skill 创建、登录和删除恢复密钥，让用户在新设备上恢复应用后能静默登录。
  内容涵盖版本兼容性、依赖、服务端前置条件，以及创建、取回和清除恢复密钥的完整客户端实现。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-11-08'
  keywords:
  - Credential Manager
  - Restore Credentials
  - backup & restore
  - backup
  - restore
  - implementation
---

## 基础

目标是通过 Android Credential Manager API（`androidx.credentials`）实现 **Restore Credentials** 功能。这让使用或正在集成 Credential Manager 的应用能在用户于新设备上恢复应用时静默地把用户重新登录。Restore Credentials 独立于应用的主认证方式（密码、passkey、联合登录）运行，且无需改动现有登录流程的 UI。

### 范围

**关键：** 本 skill 只关注 Android 客户端集成，**不**实现服务端的加密校验逻辑。必须提醒开发者这一点，并在实现完成后向其说明[需要告知开发者的要点](#backend-guidelines)。

## 实现指南

在为开发者的应用实现 Restore Credentials 时，记住以下几点：

1. 实现之前，你**必须**阅读并理解[双层恢复架构](#two-tier-restoration-architecture)，并查看[该做与不该做](#dos-and-donts)。
2. 实现之后，你**必须**向开发者呈现[后端指南](#backend-guidelines)，提醒其完成后端配置。务必提醒开发者：后端仍需由他们自己实现。

## 双层恢复架构 <a id="two-tier-restoration-architecture"></a>

为了获得有韧性的登录体验，通过**双层架构**取回凭据：

1. **第 1 层（主路径——后台）：** 在设备设置过程中通过应用的 `BackupAgent.onRestoreFinished()` 回调自动执行。这在用户首次打开应用之前就完成一次无感的恢复，使后台同步和通知送达得以进行。
2. **第 2 层（次路径——前台）：** 在 Launcher 的 `Activity.onCreate()` 中运行，用于兜住后台恢复未完成的情况（例如网络中断、恢复延迟），或 `allowBackup` 被禁用的情况。

如果清单中的 `allowBackup` 设为 true，两层都要实现。否则只实现第 2 层（前台恢复）。**不要**改动清单中 `allowBackup` 的值。

如果你给应用添加了 `BackupAgent`，还**必须**在清单中设置 `android:fullBackupOnly="true"`。如果在你实现之前应用里已经存在 `BackupAgent`，**不要**这样做。

## 该做与不该做 <a id="dos-and-donts"></a>

**该做：**

- 检查 `AndroidManifest.xml` 中 allowBackup 的值，据此判断需要实现哪些内容。
- 为 createCredential 实现回退：始终先以 `isCloudBackupEnabled` 设为 true 调用它。如果抛出 `E2eeUnavailableException`，捕获该异常，并把 `isCloudBackupEnabled` 设为 `false` 重试调用。
- 如果清单中 `allowBackup` 为 true，实现一个 `BackupAgent`（`android.app.backup.BackupAgent` 的子类）。
- 如果你给应用添加了 `BackupAgent`，在清单中设置 `android:fullBackupOnly="true"`。
- 在用户退出登录时调用 `clearCredentialState()`。这是彻底登出用户所必需的安全措施。
- 在新设备上首次启动应用时尝试获取恢复密钥；如果你的应用使用了 `BackupAgent.onRestoreFinished()` 回调，也要在该回调中尝试。
- 即使用户已登录，也要确保创建恢复凭据。
- 确保 `onRestoreFinished()` 中的凭据取回与登录同步执行（例如使用 `runBlocking`）。
- 如果你的应用使用通知，也在 `BackupAgent` 中恢复通知。（例如捕获 FCM token 并发送给后端）
- 如果你实现了模拟网络请求或桩代码，确保把所有占位符替换为有效且格式正确的 JSON 载荷，用于凭据请求。
- 把凭据创建和取回分别封装进各自专用的函数。因为凭据创建必须在多处调用（注册、登录），取回要跨多个层级（`BackupAgent` 和 Launcher `Activity`），这样做可以避免代码重复。
- 实现完成后，提醒开发者[实现后端](#implementation-guide)的关键指南。
- 如果组织有多个包名不同的应用，为每个应用分别生成恢复密钥，因为恢复密钥与唯一的应用包名绑定。

**不该做：**

- 不要改动 `AndroidManifest.xml` 中 `allowBackup` 的值。Restore Credentials 功能不受 allowBackup 设置影响，也就是说只要存在 Restore Credential，即使用户的 `allowBackup` 为 false，用户仍会被自动登录。
- 如果 `AndroidManifest.xml` 中 `allowBackup` 为 `false`，不要实现 `BackupAgent`。
- 不要假定 `GetCredentialResponse` 中存储的凭据是 `PublicKeyCredential` 类型。它的类型是 `RestoreCredential`。
- 不要在构造 `GetCredentialRequest` 时把 `GetRestoreCredentialOption` 与任何其他 `CredentialOption` 组合在一起。
- 不要假定 `CredentialManager` 或 Android 系统会在用户退出应用时自动删除恢复密钥。你必须用 `TYPE_CLEAR_RESTORE_CREDENTIAL` 类型的 `ClearCredentialStateRequest` 显式调用 `clearCredentialState`。
- 不要移除任何已有的 `clearCredentialState()` 调用。未指定类型的 `ClearCredentialStateRequest` 只会清除所有非恢复类凭据。

## 实现步骤 <a id="implementation-guide"></a>

使用以下指南实现 Android 客户端代码。**逐步**遵循，不要实现任何后端功能，完成后只需提醒开发者查看[后端指南](#backend-guidelines)。

## 版本兼容性

Credential Manager 的 Restore Credentials 可在运行 Android 9（API 级别 28）及更高版本的设备上工作，要求 Google Play services（GMS）核心版本为 `242200000`（v24.22）或更高，并且 `androidx.credentials` 库版本为 `1.5.0` 或更高。在没有 Google Play services 或 GMS 版本较低的设备上，捕获 `CreateCredentialProviderConfigurationException` 和 `GetCredentialProviderConfigurationException`，让你的应用优雅回退到标准登录。

## 前置条件

配置一个 WebAuthn [依赖方服务器](#backend-guidelines)，与用于 [passkey](#dos-and-donts) 的服务器类似。如果你已经配置好[服务器](#two-tier-restoration-architecture)来处理 passkey 认证，可以沿用同一套 WebAuthn 注册与断言端点来处理恢复密钥。

> [!NOTE]
> **注意：** 虽然 passkey 和恢复密钥的服务端加密校验相同，你的客户端应用可以在不支持面向用户的 passkey 的情况下支持恢复密钥。在后端数据库中把恢复密钥用独立的凭据标志存储，使它们不出现在面向用户的 passkey 管理界面中。

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

Restore Credentials 从 `androidx.credentials` 库的 `1.5.0` 及更高版本起可用。不过建议尽量使用依赖的最新稳定版本。

### `android:allowBackup` 如何影响 Restore Credentials

[`android:allowBackup`](references/android/guide/topics/manifest/application-element.md) 清单属性控制应用数据备份，它与 Restore Credentials 的交互体现在三个不同方面：

- **恢复密钥传输（与 `allowBackup` 无关）**：无论 `android:allowBackup` 是 `true` 还是 `false`，Google Play services 都会通过端到端加密的云备份或本地设备到设备（D2D）传输来传送 `RestoreCredential` 密钥对。对于 D2D 传输，恢复密钥总会传输；唯一不传输的情况是云备份过程中用户在 Android 设置里选择了退出云备份。
- **在 `BackupAgent` 中后台恢复（要求 `android:allowBackup="true"`）**：用户在新设备上打开应用之前的静默后台登录（`BackupAgent.onRestoreFinished()`）只在清单中配置了 `android:allowBackup="true"` 和 `android:backupAgent` 时才运行。如果 `android:allowBackup="false"`，在用户首次启动主 `Activity` 时恢复会话。你也可以两种方式都实现，让恢复更健壮。
- **Android Studio 云备份测试（要求 `android:allowBackup="true"`）**：在 Android Studio 的 Backup and Restore 工具中测试 **Cloud** 备份类型需要 `android:allowBackup="true"`，而 **Device to Device** 测试则与 `allowBackup` 无关。

## 概述

Restore Credentials 在用户的旧设备和新设备上遵循三阶段生命周期：

1. [**在旧设备上创建恢复密钥**](#create-restore-key)：用户登录后（或者应用启动时用户已登录且本地存储中没有记录恢复密钥），从依赖方服务器获取创建选项并调用 `credentialManager.createCredential()`。
2. [**在新设备上用恢复密钥登录**](#sign-restore)：用双层策略取回已传输的 `RestoreCredential`：先在 `BackupAgent.onRestoreFinished()` 中静默取回（当 `android:allowBackup="true"` 时），使后台同步和推送通知立即恢复；再在应用首次启动时于 Launcher `Activity.onCreate()` 中作为回退取回。
3. [**退出登录时删除恢复密钥**](#delete-restore)：当用户退出登录或其会话被服务器判为失效时，调用 `credentialManager.clearCredentialState()`，传入 `ClearCredentialStateRequest(ClearCredentialStateRequest.TYPE_CLEAR_RESTORE_CREDENTIAL)`，并清除本地同步标志。

## 创建恢复密钥 <a id="create-restore-key"></a>

你的应用应覆盖用户登录的所有情形，确保活跃用户都已创建恢复密钥。在以下场景中创建恢复密钥：

- 用户已登录且尚未创建恢复密钥（例如在主 `Activity` 的 `onCreate()` 方法中）。
- 用户正在登录或完成新账号注册流程时。

为避免在每次应用启动时都调用 `createCredential()`，在本地存储中保存一个本地同步标志，例如 `has_synced_restore_credential`。不要把这个标志存放在默认会被备份的 `SharedPreferences` 或 `DataStore` 中，除非该文件在 `data_extraction_rules.xml` 中被排除；否则 Auto Backup 会把 `has_synced_restore_credential = true` 复制到新设备上，阻止新设备生成或轮换自己的恢复密钥。

> [!NOTE]
> **注意：** 恢复密钥与应用唯一的包名绑定。如果组织的主应用和子应用包名不同，为每个应用分别创建恢复密钥。

### 实例化 Credential Manager

用应用的 activity context 实例化一个 `CredentialManager` 对象。

    // Use your app or activity context to instantiate a client instance of
    // CredentialManager.
    private val credentialManager = CredentialManager.create(context)

### 从应用服务器获取凭据创建选项

在应用服务器中使用兼容 FIDO 的库，把创建恢复凭据所需的 `PublicKeyCredentialCreationOptions` JSON 发送给客户端应用。有关服务端实现的更多信息，见[服务端指南](https://developers.google.com/identity/passkeys/developer-guides/server-registration)。

创建选项 JSON 与 passkey 注册的结构相同：

    {
      "challenge": "<base64url-encoded challenge>",
      "rp": {
        "name": "<relying party name>",
        "id": "<relying party host name>"
      },
      "user": {
        "id": "<base64url-encoded user ID>",
        "name": "<user name>",
        "displayName": "<user display name>"
      },
      "pubKeyCredParams": [
        {
          "type": "public-key",
          "alg": -7
        }
      ],
      "attestation": "none",
      "excludeCredentials": [
        {
            "id": "<base64url-encoded credential ID to exclude>", 
            "type": "public-key"
        }
      ],
      "authenticatorSelection": {
        "requireResidentKey": true,
        "residentKey": "required",
        "userVerification": "required"
      }
    }

确保你的创建选项 JSON 满足以下要求：

- `challenge` 与 `user.id`：把两个值都编码为不带填充的 Base64URL 字符串（把 `+` 替换为 `-`，把 `/` 替换为 `_`，并去掉末尾的 `=`）。使用标准 Base64 字符或原始整数 ID 会导致 `CreateRestoreCredentialDomException` 或 `IllegalArgumentException`。
- `rp.id`：设为你的依赖方域名（例如 `example.com`）。
- `pubKeyCredParams`：包含 `{"type": "public-key", "alg": -7}`（ES256）和 `{"type": "public-key", "alg": -257}`（RS256）。

### 创建恢复密钥

从服务器收到公钥创建选项 JSON 后，把该 JSON 包装进 [`CreateRestoreCredentialRequest`](https://developer.android.com/reference/androidx/credentials/CreateRestoreCredentialRequest) 对象，并在 `CredentialManager` 对象上调用 [`createCredential()`](https://developer.android.com/reference/androidx/credentials/CredentialManager#createCredential(android.content.Context,androidx.credentials.CreateCredentialRequest))。

    // requestJson contains the credential creation options sent by the server
    val createRestoreRequest = CreateRestoreCredentialRequest(requestJson)
    val response = try {
        credentialManager.createCredential(context, createRestoreRequest)
    } catch (e: E2eeUnavailableException) {
        // Fall back to local device-to-device (D2D) restore if cloud E2EE is unavailable
        credentialManager.createCredential(
            context,
            CreateRestoreCredentialRequest(requestJson, isCloudBackupEnabled = false),
        )
    }

#### 代码要点

- `CreateRestoreCredentialRequest` 对象包含以下字段：

  - `requestJson`：应用服务器以 [Web Authentication API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API) 格式发送的凭据创建选项，对应 [`PublicKeyCredentialCreationOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)。
  - `isCloudBackupEnabled`：`Boolean` 字段，决定恢复密钥是否应备份到云端。默认情况下该标志为 `true`。该字段有以下取值：

    - `true`：（**推荐**）如果用户启用了 Google 备份和端到端加密（例如屏幕锁定），该值允许把恢复密钥备份到云端。
    - `false`：该值把密钥保存在本地而不放在云端。如果用户选择从云端恢复，该密钥在新设备上不可用，但它在通过数据线或 Wi-Fi 进行的本地设备到设备（D2D）设置过程中仍会传输。

  > [!CAUTION]
  > **小心：** 首次调用时把 `isCloudBackupEnabled` 设为 `true`，只在抛出 `E2eeUnavailableException` 时才回退到 `isCloudBackupEnabled = false`。如果用户禁用了云备份（或 `isCloudBackupEnabled` 为 `false`），之后又从云备份恢复，取回恢复密钥的调用会失败。用云备份恢复你应用的用户拿不到恢复密钥，也不会被自动登录。

### 处理凭据创建响应

Credential Manager API 返回 [`CreateRestoreCredentialResponse`](https://developer.android.com/reference/androidx/credentials/CreateRestoreCredentialResponse) 类型的响应。该响应以 [JSON 格式](https://w3c.github.io/webauthn/#authenticatorattestationresponse)持有公钥凭据注册响应。

把应用中的 `response.registrationResponseJson` 发送给依赖方服务器，以校验公钥并与用户的账号一并存储，然后在本机存储中记录本地同步标记。有关服务端校验的更多信息，见 [passkey 的指南](references/android/identity/passkeys/create-passkeys.md)。

在恢复密钥创建过程中，处理以下异常：

- [`CreateRestoreCredentialDomException`](https://developer.android.com/reference/androidx/credentials/exceptions/restorecredential/CreateRestoreCredentialDomException)：当 `requestJson` 无效或不符合 WebAuthn 的 [`PublicKeyCredentialCreationOptionsJSON`](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson) 格式时抛出该异常。
- [`E2eeUnavailableException`](https://developer.android.com/reference/androidx/credentials/exceptions/restorecredential/E2eeUnavailableException)：当 `isCloudBackupEnabled` 为 `true`，但用户设备没有数据备份或端到端加密（例如屏幕锁定）时抛出该异常。
  为了在云端 E2EE 不可用时仍能为本地设备到设备（D2D）传输创建 Restore Credentials，捕获 `E2eeUnavailableException` 后立即用 `CreateRestoreCredentialRequest(requestJson, isCloudBackupEnabled = false)` 重试 `createCredential()`。
- `IllegalArgumentException`：当 `requestJson` 为空、不是有效 JSON，或缺少符合 WebAuthn [规范](https://w3c.github.io/webauthn/#dictdef-publickeycredentialcreationoptionsjson)的有效 Base64URL 编码 `user.id` 时抛出该异常。

## 用恢复密钥登录 <a id="sign-restore"></a>

用 Restore Credentials 在设备设置过程中静默登录用户。

### 从应用服务器获取凭据取回选项

在新设备上调用 `getCredential()` 之前，先向应用服务器请求一个 WebAuthn `PublicKeyCredentialRequestOptions` JSON challenge。因为新设备上的应用此时还不知道是哪个用户在登录，这个端点必须是**未认证**的（无用户发现）。相关服务端指南见[用 passkey 登录](references/android/identity/passkeys/sign-in-with-passkeys.md)和[服务端认证指南](https://developers.google.com/identity/passkeys/developer-guides/server-authentication#create_credential_request_options)。

取回选项 JSON 的结构如下：

    {
      "challenge": "<your app challenge>",
      "allowCredentials": [],
      "rpId": "<your app server domain>"
    }

服务端按以下方式配置取回选项 JSON：

- `allowCredentials`：省略该字段或传入空数组（`[]`），因为在恢复之前不知道用户的账号。`getCredential()` 返回后，你的服务器从 `response.userHandle` 字段识别用户（该值与创建时注册的 `user.id` 一致），并按 `id`（`credentialId`）查找公钥。
- `userVerification`：设为 `"discouraged"`（或 `"preferred"`）。因为 Restore Credentials 静默运行，没有生物识别或屏幕锁定界面，Android 会把 `"required"` 覆盖为 `"discouraged"`，返回给服务器的认证器数据中 User Verified（`uv`）标志为 `false`。把你的 WebAuthn 服务端校验器配置为对恢复密钥断言接受 `uv = false`。

### 获取恢复密钥

要在新设备上获取恢复密钥，把服务器的 `requestJson` 包装进 `GetCredentialRequest` 中的 `GetRestoreCredentialOption`，并在 `CredentialManager` 对象上调用 `getCredential()`。

> [!CAUTION]
> **小心：** 不要在同一个 `GetCredentialRequest` 中把 `GetRestoreCredentialOption` 与任何其他 `CredentialOption`（例如 `GetPublicKeyCredentialOption` 或 `GetPasswordOption`）组合。把多个选项与 `GetRestoreCredentialOption` 一起传入会抛出 `IllegalArgumentException`。

实现**双层恢复策略**，使用户无论后台应用数据恢复是否运行都能登录：

- **第 1 层（在 `BackupAgent.onRestoreFinished()` 中后台恢复）**：如果启用了应用数据备份（`android:allowBackup="true"`），继承 [`BackupAgent`](https://developer.android.com/reference/android/app/backup/BackupAgent) 并重写 [`onRestoreFinished()`](https://developer.android.com/reference/android/app/backup/BackupAgent#onRestoreFinished())（不要使用 `onRestore()`，它只对旧式键值备份调用）。因为 `onRestoreFinished()` 是同步的，而 `getCredential()` 是 Kotlin 的 `suspend` 函数，用 `runBlocking(Dispatchers.IO)` 桥接该调用。没有恢复密钥时静默捕获 `NoCredentialException`。
- **第 2 层（在 Launcher `Activity.onCreate()` 中前台回退）**：在应用首次启动且不存在本地会话时，在显示登录界面之前从 `lifecycleScope` 调用 `getCredential()`。这覆盖了 `android:allowBackup="false"` 的应用，也能在 `onRestoreFinished()` 运行时设备离线的情况下恢复。

如果你给一个已使用 Auto Backup 且 `android:allowBackup="true"` 的应用新增 `BackupAgent`，还要在 `AndroidManifest.xml` 的 `<application>` 元素上设置 `android:fullBackupOnly="true"`，让 Android 继续使用 Auto Backup 而不是切换到旧式键值备份。

> [!IMPORTANT]
> **重要：** 取回凭据时推送通知不会自动恢复。在 `BackupAgent.onRestoreFinished()` 中（或第 2 层登录后立即），用 `FirebaseMessaging.getInstance().token.await()` 获取一个最新的 Firebase Cloud Messaging（FCM）注册令牌并注册到后端，让后台通知在用户打开应用之前就能恢复。

        suspend fun getRestoreKey(
            fetchAuthenticationJson: () -> String,
        ) {
            // Fetch the options required to get the restore key
            val authenticationJson = fetchAuthenticationJson()

            // Create the GetRestoreCredentialOption object
            val options = GetRestoreCredentialOption(authenticationJson)
            val getRequest = GetCredentialRequest(listOf(options))

            try {
                val response = credentialManager.getCredential(context, getRequest)

                // Type-check and extract the restore credential
                val credential = response.credential
                if (credential is RestoreCredential) {
                    val responseJson = credential.authenticationResponseJson
                }
            } catch (e: NoCredentialException) {
                // No restore key is present on this device
            }
        }

    class MyBackupAgent : BackupAgent() {

        override fun onRestoreFinished() {
            super.onRestoreFinished()
            val credentialManager = CredentialManager.create(this)
            val restoreFunctions = RestoreCredentialsFunctions(this, credentialManager)

            runBlocking(Dispatchers.IO) {
                restoreFunctions.getRestoreKey(
                    fetchAuthenticationJson = {
                        /* Fetch challenge JSON from server */ ""
                    }
                )
            }
        }
    }

Credential Manager API 返回 [`GetCredentialResponse`](https://developer.android.com/reference/androidx/credentials/GetCredentialResponse)，其 `credential` 属性是 [`RestoreCredential`](https://developer.android.com/reference/androidx/credentials/RestoreCredential)（而不是 `PublicKeyCredential`），其中包含 `authenticationResponseJson`。

### 处理登录响应

把应用中的 `restoreCredential.authenticationResponseJson` 发送给依赖方服务器，以校验加密断言并为用户签发新的会话令牌。有关服务端校验的细节，见[用 passkey 登录](references/android/identity/passkeys/sign-in-with-passkeys.md)。

在为恢复密钥设计后端存储和生命周期策略时，遵循以下指南：

- **把恢复密钥与用户 passkey 区分开**：在后端数据库中给恢复密钥打上标记，使它们不出现在面向用户的 passkey 管理界面中，也不参与用户验证（`uv = true`）检查。
- **支持每个用户有多台活跃设备**：一个用户可以拥有多台设备（例如手机和平板）。允许同一用户账号下存在多个活跃恢复密钥（例如按设备或安装 ID 建立索引），而不是覆盖单行记录。
- **设置合适的 TTL 并清理孤立密钥**：卸载应用或清除应用数据会删除本地恢复密钥而不通知服务器。保留恢复密钥的时间要足以渡过设备升级窗口（即使用户在旧设备上传输后退出登录），并按不活跃 TTL 或每用户密钥数量上限清理陈旧密钥。

## 删除恢复密钥 <a id="delete-restore"></a>

Credential Manager 是无状态的，也不感知用户活动，所以它不会在使用后自动删除恢复密钥。要删除恢复密钥，调用 [`clearCredentialState()`](https://developer.android.com/reference/androidx/credentials/CredentialManager#clearCredentialState(androidx.credentials.ClearCredentialStateRequest)) 方法。出于安全考虑，用户每次退出登录时都删除该密钥，这样他们下次启动应用时不会被静默地重新登录。

> [!NOTE]
> **注意：** 用户退出登录也可能远程发生，例如用户在网上修改密码，或被服务器远程登出（例如你的服务器返回 HTTP `401 Unauthorized` 错误）。如果你的应用检测到**服务端会话失效**，也要在设备上删除恢复密钥。

恢复密钥只在以下情形被移除：

- **系统级操作**：用户卸载应用或清除应用数据。
- **应用级调用**：在应用代码中处理用户退出登录时，通过调用 [`clearCredentialState()`](https://developer.android.com/reference/androidx/credentials/CredentialManager#clearCredentialState(androidx.credentials.ClearCredentialStateRequest)) 以编程方式删除密钥。

因为默认的 `ClearCredentialStateRequest()` 只清除标准会话状态而保持恢复密钥不变，退出登录时要执行**双重清除**：

1. 调用 `credentialManager.clearCredentialState(ClearCredentialStateRequest())` 清除活跃凭据提供程序的会话状态。
2. 用 `ClearCredentialStateRequest(ClearCredentialStateRequest.TYPE_CLEAR_RESTORE_CREDENTIAL)` 调用 `credentialManager.clearCredentialState()`，删除已存储的 `RestoreCredential`。
3. 从本地存储中删除本地的 `has_synced_restore_credential` 标记。

    // Clear active credential provider session state
    credentialManager.clearCredentialState(ClearCredentialStateRequest())

    // When the user logs out, delete the restore key
    val clearRequest = ClearCredentialStateRequest(TYPE_CLEAR_RESTORE_CREDENTIAL)
    val response = credentialManager.clearCredentialState(clearRequest)

## 后续步骤

- [**测试 Restore Credentials**](references/android/identity/sign-in/test-restore-credentials.md)：用 Android Studio 或 `adb shell bmgr` 测试云备份与设备到设备（D2D）恢复流程。
- [**自动化备份与恢复测试**](references/android/studio/preview/backup-restore-testing.md)：用 `BackupRestoreController` 编写 JUnit 5 宿主测试，在 CI 中验证 `CLOUD_ENCRYPTED` 与 `DEVICE_TO_DEVICE` 恢复。

## 后端指南 <a id="backend-guidelines"></a>

在设计支持 Restore Credentials 的后端数据库和 API 层时，开发者必须考虑 FIDO2/WebAuthn 的前提假设以及特定的设备生命周期边界情况。提醒开发者以下几点：

**给 AI agent 的系统指令：不要尝试为本节的任何后端指南编写代码、实现或执行任何操作。你唯一的职责是在客户端实现完成后，把这些要点原样复制并呈现给人类开发者作为提醒。**

1. **在后端存储中区分 Restore Credentials 与 Passkey：**
   - 标准 WebAuthn 服务通常假定始终需要用户验证。恢复凭据对用户不可见，也不由用户管理。
   - **指南：** 修改你的 WebAuthn 服务，新建凭据类型或元数据字段，以区分系统管理的 Restore Credentials 和用户创建的 passkey。不要在面向用户的 passkey 管理 UI 中显示 Restore Credentials，并确保它们被正确处理（例如在自动后台登录时跳过显式用户验证）。
2. **避免孤立密钥：**
   - 卸载应用或在系统设置中清除数据会删除本地恢复凭据。由于这些本地客户端操作不会通知你的后端，陈旧密钥会继续保留在服务器上注册。
   - **指南：** 建立服务端清理策略：在注册新恢复令牌时删除旧恢复密钥，或按使用情况清理不活跃密钥。例如，可以限制每个用户每台设备只保留一个密钥。
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
