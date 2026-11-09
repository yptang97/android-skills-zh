---
name: verified-email
description: 提供在 Android Credential Manager API 上实现已验证邮箱（verified email）取回的完整工作流。
  用这个 skill 把安全、免 OTP 的邮箱验证流程集成到 Android 应用中。这个 skill 通过使用来自
  Google 等可信提供方的加密验证凭据，解决注册流程摩擦大的问题。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-11-07'
  keywords:
  - implementation
  - Android
  - Credential Manager
  - Digital Credentials
  - Verified Email
  - OpenID4VP
  - SD-JWT
  - OTP-less
  - authentication
  - passkeys
  - CredMan
  - identity.
---

## 基础

- *[Digital Credentials 概述](references/android/identity/digital-credentials/email-verification.md)*：了解可加密验证的文档以及 Credential Manager 的作用。
- *[术语表](references/android/identity/digital-credentials/email-verification-implementation.md)*：`dcql_query`、`UserInfoCredential` 和 `GetDigitalCredentialOption` 的定义。

### 标准 \& 示例

- *[OpenID4VP 标准](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html#name-introduction)*：用于构造数字凭据请求的规范。
- *[Digital Credentials 演示](https://digital-credentials.dev/)*：示例请求与跨平台测试工具。
- *[W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/)*：加密安全声明的数据模型。
- *[SD-JWT](https://datatracker.ietf.org/doc/draft-ietf-oauth-selective-disclosure-jwt/)*：响应中使用的选择性披露 JSON Web Token 格式。
- *[mdoc](https://www.iso.org/standard/69084.html)*：移动文档的 ISO/IEC 18013-5 标准。

### 要求

- **SDK 版本**：最低要求 SDK 28（Android 9）。
- **GMS 版本**：Google Play services 版本 25.49.x 或更高。

### 使用场景

邮箱验证适用于以下场景：

- **账号创建/注册**：跳过手动邮箱验证以减少摩擦。
- **账号恢复**：在恢复流程中安全地验证邮箱归属。
- **重新认证**：为高风险操作提供通用的验证手段，与最初的登录方式无关。

### 限制与细节

- **Workspace 账号**：Google 不为 Google Workspace 账号签发可验证凭据。
- **新鲜度**：对于非 @gmail.com 地址，Google 在账号创建时验证过该邮箱，但没有新鲜度声明；需额外实现 OTP 之类的挑战。

### 范围与前置条件

**关键**：本 skill 只关注 **Android 客户端集成**。它**不**实现应用服务端的加密校验逻辑。为安全起见，必须由你的后端实现对返回凭据的服务端校验。

## 为使用场景探索代码库

在项目源码中用以下查询入手，找到对应不同使用场景、可实施已验证邮箱的相关界面：

- `SignUpScreen`
- `"Email address"`
- `"Recover Account"`
- `"Account Recovery"`
- `"Forgot password?"`
- `"Delete Account"`

## 确定集成点

要有效实现该功能，你必须先在代码库中定位相关流程。开始时，用以下策略针对不同使用场景使用已验证邮箱：

### 1. 搜索导航路由

如果你的应用使用 Navigation，搜索与认证相关的路由或目的地：

查找：

- **关键字**：`signup`、`registration`、`create_account`、`forgot_password`、`recovery`、`verify_email`。
- **代码模式**：用这些字符串搜索 `NavHost` 或 `composable` 目的地。

### 2. 定位认证 ViewModel

找到处理用户属性与账号创建、账号恢复的业务逻辑：

- **关键字**：`SignUpViewModel`、`AuthViewModel`、`RegistrationRepository`。
- **代码模式**：查找 `onCreateAccount`、`onRecoverAccount` 或 `validateEmail` 之类的方法。

### 3. 找到敏感操作的重新认证实例

对于重新认证场景，找到用户执行敏感操作的位置：

- **关键字**：`ChangePassword`、`UpdatePayment`、`DeleteAccount`、`UpdateDetails`、`EditUserDetails`

## 实现要点提示

- 构造 Digital Credential 请求并呈现给用户。
- 确保遵循[文档](references/android/identity/digital-credentials/email-verification-implementation.md)中所述的请求 JSON 结构。
- 在向用户呈现请求时，检查结果凭据是否为 DigitalCredential，以及 credential.credentialJson 是否作为 responseJsonString。
- 解析来自客户端的响应。
- 如果尚不存在 passkey，提供一个创建 passkey 的选项。
- 假定有一个本地 `SdJwtParser` 用于解析原始 SD-JWT 并返回 `JSONObject`。
- 用 `VerifiedUserInfo` 数据类存储解析出的姓名和邮箱。
- 给开发者留一个 TODO，用于处理应用的服务端校验与解析。
- API 调用成功后把用户引导到主界面，并弹出带用户详情的 snackbar，仅作参考。

## 概述

本指南描述如何通过 [OpenID for Verifiable Presentations（OpenID4VP）](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html)请求，使用 [Digital Credentials Verifier API](references/android/identity/digital-credentials/credential-verifier/request-credential.md)实现已验证邮箱的取回。

## 添加依赖

在应用的 `build.gradle` 文件中，添加以下 Credential Manager 依赖：

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

## 初始化 Credential Manager

用应用或 activity 的 context 创建一个 `CredentialManager` 对象。

    // Use your app or activity context to instantiate a client instance of
    // CredentialManager.
    private val credentialManager = CredentialManager.create(context)

## 构造 Digital Credential 请求

要请求已验证邮箱，构造一个包含 [`GetDigitalCredentialOption`](https://developer.android.com/reference/androidx/credentials/GetDigitalCredentialOption) 的 [`GetCredentialRequest`](https://developer.android.com/reference/android/credentials/GetCredentialRequest)。该选项需要一个格式为 OpenID for Verifiable Presentations（OpenID4VP）请求的 `requestJson` 字符串。

OpenID4VP 请求 JSON 必须遵循特定结构。当前提供方支持带外层 `"digital": {"requests": [...]}` 包装的 JSON 结构。

        val nonce = generateSecureRandomNonce()

        // This request follows the OpenID4VP spec
        val openId4vpRequest = """
    {
      "requests": [
        {
          "protocol": "openid4vp-v1-unsigned",
          "data": {
            "response_type": "vp_token",
            "response_mode": "dc_api",
            "nonce": "$nonce",
            "dcql_query": {
              "credentials": [
                {
                  "id": "user_info_query",
                  "format": "dc+sd-jwt",
                   "meta": { 
                      "vct_values": ["UserInfoCredential"] 
                   },
                  "claims": [ 
                    {"path": ["email"]}, 
                    {"path": ["name"]},  
                    {"path": ["given_name"]},
                    {"path": ["family_name"]},
                    {"path": ["picture"]},
                    {"path": ["hd"]},
                    {"path": ["email_verified"]}
                  ]
                }
              ]
            }
          }
        }
      ]
    }
    """

        val getDigitalCredentialOption = GetDigitalCredentialOption(requestJson = openId4vpRequest)
        val request = GetCredentialRequest(listOf(getDigitalCredentialOption))

请求包含以下关键信息：

- **DCQL 查询**：`dcql_query` 指定凭据类型和被请求的声明（`email_verified`）。你可以请求其他声明来判断验证级别。一些可能用到的声明如下：

  - `email_verified`：在响应中为布尔值，表示邮箱是否已验证。
  - `hd`（托管域名）：在响应中为空。

  > [!NOTE]
  > **注意：** 如果响应中 `email_verified` 为 `true` 且 `hd` 为空，说明该账号是授权的 Google 账号。Google 不为 Google Workspace 账号签发[可验证凭据](references/android/identity/digital-credentials/index.md)。不过，为非 Workspace 账号签发的可验证凭据中会带 `hd` 字段。建议你实现该字段的处理，让应用具备前瞻性。如果邮箱不是 @gmail.com，Google 在该 Google 账号创建时验证过此邮箱，但没有新鲜度声明。因此对于非 Google 邮箱，你应考虑额外的挑战（例如 OTP）来验证用户。要了解凭据的 schema 以及校验 `email_verified` 等字段的具体规则，参见 [Google Identity 指南](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)。

- **nonce**：每次请求都会生成一个唯一、加密安全的随机值。这对安全至关重要，可防止重放攻击。

- `UserInfoCredential`：该值表示一种包含用户属性的特定数字凭据类型。在请求中包含它，是区分邮箱验证场景的关键。

接下来，把 `openId4vpRequest` JSON 包装进 `GetDigitalCredentialOption`，创建 `GetCredentialRequest`，并调用 `getCredential()`。

> [!NOTE]
> **注意：** `hd` 和 `email_verified` 字段在 Credential Manager 的内置 UI 中对用户隐藏。你不能只用这些隐藏字段发起请求——遇到这类请求，返回的是 [`GetCredentialCancellationException`](https://developer.android.com/reference/kotlin/androidx/credentials/exceptions/GetCredentialCancellationException)。

## 向用户展示请求

用 Credential Manager 的内置 UI 向用户展示请求。

    coroutineScope {
        try {
            // Requesting Digital Credential from user...
            val result = credentialManager.getCredential(activity, request)

            when (val credential = result.credential) {
                is DigitalCredential -> {
                    val responseJsonString = credential.credentialJson

                    // Successfully received digital credential response.

                    // Next, parse this response and send it to your server.
                    // ...
                }

                else -> {
                    // handle Unexpected State() - Up to the developer
                }
            }
        } catch (e: Exception) {
            // handle exceptions - Up to the developer
        }
    }

> [!NOTE]
> **注意：** Digital Credentials 没有 Sign in with Google 的 `preferImmediatelyAvailableCredentials` 的等价物。如果找不到可验证凭据（例如设备上没有符合条件的账号），用户会看到「No options available」或类似的系统界面。

## 在客户端解析响应 <a id="parse-response"></a>

> [!WARNING]
> **警告：** 从 2026 年 8 月起，[响应 JSON](https://developer.android.com/reference/androidx/credentials/DigitalCredential#getCredentialJson())格式已更新为严格符合 W3C 标准。它包含 `data` 和 `protocol` 键，OpenID4VP 的 `vp_token` 嵌套在 `data` 内，而旧格式直接持有 `vp_token`。请确保客户端解析与服务端校验在过渡期内同时处理两种格式，同时旧的实现会被逐步淘汰。2026 年 8 月之后才开始集成邮箱验证流程的应用只需使用新格式。

收到响应后，你可以在客户端做一次初步解析。这有助于立即更新 UI，例如展示用户的姓名。

> [!IMPORTANT]
> **重要：** 这一步不是为了校验。完整的加密验证必须在你的服务器上完成。

以下代码提取原始 [Selective Disclosure JWT（SD-JWT）](https://datatracker.ietf.org/doc/rfc9901/) 并使用辅助方法解码其中的声明。

    // 1. Parse the outer JSON wrapper to get the `vp_token`
    val responseData = JSONObject(responseJsonString)
    val dataObject = responseData.getJSONObject("data")
    val vpToken = dataObject.getJSONObject("vp_token")

    // 2. Extract the raw SD-JWT string
    val credentialId = vpToken.keys().next()
    val rawSdJwt = vpToken.getJSONArray(credentialId).getString(0)

    // 3. Use your parser to get the verified claims
    // Server-side validation/parsing is highly recommended.

    // Assumes a local parser like the one in our SdJwtParser.kt sample
    val claims = SdJwtParser.parse(rawSdJwt)
    Log.d("TAG", "Parsed Claims: ${claims.toString(2)}")

    // 4. Create your VerifiedUserInfo object with REAL data
    val userInfo = VerifiedUserInfo(
        email = claims.getString("email"),
        displayName = claims.optString("name", claims.getString("email"))
    )

## 处理响应

Credential Manager API 会返回 [`DigitalCredential`](https://developer.android.com/reference/androidx/credentials/DigitalCredential) 响应。

以下是原始 `responseJsonString` 的示例，以及解析内部 SD-JWT 后声明的样子；除已验证邮箱外，你还会拿到附加的元数据：

    /*
    // Example of the raw JSON response from credential.credentialJson:
    {
      "protocol": "openid4vp-v1-unsigned",
      "data": {
        "vp_token": {
          // This key matches the 'id' you set in your dcql_query
          "user_info_query": [
            // The SD-JWT string (Issuer JWT ~ Disclosures ~ Key Binding JWT)
            "eyJhbGciOiJ...~WyI...IiwgImVtYWlsIiwgInVzZXJAZXhhbXBsZS5jb20iXQ~...~eyJhbGciOiJ..."
          ]
        }
      }
    }

    // Example of the parsed and verified claims from the SD-JWT on your server:
    {
      "cnf": {
        "jwk": {..}
      },
      "exp": 1775688222,
      "iat": 1775083422,
      "iss": "https://verifiablecredentials-pa.googleapis.com",
      "vct": "UserInfoCredential",
      "email": "jane.doe.246745@gmail.com",
      "email_verified": true,
      "given_name": "Jane",
      "family_name": "Doe",
      "name": "Jane Doe",
      "picture": "http://example.com/janedoe/me.jpg",
      "hd": ""
    }
     */

> [!IMPORTANT]
> **重要：** 我们强烈建议在收到已验证邮箱后触发 Credential Manager 的 [passkey 创建](references/android/identity/passkeys/create-passkeys.md)。

## 账号创建的服务端验证

由于取回的邮箱经过加密验证，你可以省略邮箱 OTP 验证步骤，显著降低注册摩擦，并可能提升转化率。这一过程最好在服务器上处理。客户端把原始响应（包含 `vp_token`）和原始 nonce 发送到新的服务端端点。

为进行校验，你的应用必须在创建账号或让用户登录之前，把完整的 `responseJsonString` 发送到服务器做加密校验。

数字凭据为你的服务器提供两个关键的验证层级：

- **数据真实性**：校验签发方（`iss`）URL 和 `SD-JWT` 签名，可证明这些数据由可信机构签发。
- **持有者身份**：校验 `cnf` 字段和 Key Binding（`kb`）签名，可确认凭据是由最初签发时的同一台设备在共享，防止其被截获或在其他设备上使用。

服务器上的校验必须做到以下几点：

- **校验签发方**：确保 `iss`（签发方）字段与 `https://verifiablecredentials-pa.googleapis.com` 一致。
- **校验签名**：用 https://verifiablecredentials-pa.googleapis.com/.well-known/vc-public-jwks 上可用的公钥（JWK）检查 SD-JWT 的签名。

> [!NOTE]
> **注意：** 使用标准库（例如 Node.js 的 [@sd-jwt/sd-jwt-vc](https://datatracker.ietf.org/doc/rfc9901/)）按 [OpenID for Verifiable Presentations 规范](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html)执行上述校验步骤。

为了完整的安全性，还要确保校验 `nonce`，以防重放攻击。

把上述步骤组合起来，服务器就能同时校验数据真实性和持有者身份，确保在创建新账号之前凭据未被截获或伪造。

> [!WARNING]
> **警告：** 如[在客户端解析响应](#parse-response)中所述，从 2026 年 8 月起，[响应 JSON](https://developer.android.com/reference/androidx/credentials/DigitalCredential#getCredentialJson())格式已更新为符合 W3C 标准。请确保客户端解析与服务端校验在过渡期内同时处理两种格式，同时旧的实现会被逐步淘汰。2026 年 8 月之后才开始集成邮箱验证流程的应用只需使用新格式。

    try {
        // Send the raw credential response and the original nonce to your server.
        // Your server must validate the response. createAccountWithVerifiedCredentials
        // is a custom implementation per each RP for server side verification and account creation.
        val serverResponse = createAccountWithVerifiedCredentials(responseJsonString, nonce)

        // Server returns the new account info (e.g., email, name)
        val claims = JSONObject(serverResponse.json)

        val userInfo = VerifiedUserInfo(
            email = claims.getString("email"),
            displayName = claims.optString("name", claims.getString("email"))
        )

        // handle response - Up to the developer
    } catch (e: Exception) {
        // handle exceptions - Up to the developer
    }

## 创建 passkey

创建账号后一个可选但强烈推荐的下一步是立即为该账号[创建 passkey](references/android/identity/passkeys/create-passkeys.md)。这为用户提供了安全、免密码的登录方式。该流程与标准 passkey 注册完全相同。

## WebView 支持

要让该流程在 [`WebView`](https://developer.android.com/reference/android/webkit/WebView) 中工作，开发者应实现 [JavaScript 桥接](references/android/identity/sign-in/credential-manager-webview.md)（JS Bridge）来完成交接。该桥接让 `WebView` 对象能通知原生应用，由原生应用执行对 Credential Manager API 的实际调用。

## 另请参阅

- [已验证邮箱取回概述](references/android/identity/digital-credentials/email-verification.md)
- [Credential Manager](references/android/identity/credential-manager/index.md)

## 关键安全指南

为维护邮箱验证流程的完整性，以下安全要求是强制性的：

- **服务端校验**：对于账号创建这类安全敏感操作，绝不要信任客户端解析出的声明。把完整的原始 `responseJsonString` 和原始 `nonce` 发送到应用服务器做完整校验。
- **Nonce 完整性**：为每次请求生成唯一、加密安全的 nonce，并且**绝不**在多个请求间复用 nonce，以防重放攻击。
- **加密校验**：应用服务器必须校验签发方（`iss`）字段、SD-JWT 签名，并用 `cnf` 字段校验持有者身份。
