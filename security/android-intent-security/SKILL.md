---
name: android-intent-security
description: Android Intent 安全最佳实践。审计 AndroidManifest.xml 中的组件配置（activity、service、receiver），或审计处理传入 Intent 的源代码（getIntent、getParcelableExtra）以防范 Intent 重定向与未授权访问时，使用这个 skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - recipe
  - Android
  - Security
  - Intent
  - Redirection
  - PendingIntent
  - ContentProvider
  - Service
  - Signature
  - Verification
  - sanitizer
  - Vulnerability
  - Best Practices
---

这个 skill 提供保护 Android 组件（Activity、Service、BroadcastReceiver、ContentProvider）
以及安全处理 Intent 的指南与模式，防止权限提升与未授权访问。

## 术语表

- **Intent：** 一种异步消息对象，用于请求另一个应用组件执行某个操作。
- **导出的组件：** 可以被设备上其他应用启动的组件（`android:exported="true"`）。
- **粘性 Intent：** 一种广播 Intent，发送后会保留在系统缓存中，任何应用都可以读取其内容。
- **签名级权限：** 保护级别设为 `signature` 的权限，只授予使用同一开发者密钥签名的应用。
- **onNewIntent：** 当 Activity 以 `FLAG_ACTIVITY_SINGLE_TOP` 启动且已位于历史栈顶部运行时触发的 Activity 生命周期回调。
- **PendingIntent：** 授予其他应用（例如系统服务）的一种令牌，使其能以创建者的权限执行预先定义的 Intent。
- **可变的 PendingIntent：** 底层 Intent 参数可被接收方应用修改的 PendingIntent。
- **ContentProvider：** 封装数据并通过标准 query/insert 接口提供给其他应用的组件。
- **IntentSanitizer：** AndroidX Core 中的工具类，通过过滤未授权的组件、action 或 extra，构造传入 Intent 的安全净化副本。
- **Intent 重定向（转发）：** 应用从不可信来源接收 Intent，并用它启动私有、非导出组件所导致的漏洞。

## 前置条件

- agent **必须**能够说明 `onCreate`、`onNewIntent` 与 `singleTop` 启动模式的作用及其安全影响。
- agent **必须**能够在 `AndroidManifest.xml` 中声明 `<activity>`、`<service>`、`<receiver>`、`<provider>` 标签，并定义它们的 `android:exported` 与 `android:permission` 属性。
- agent **必须**能够使用 `PackageManager` 实现签名校验。

## 限制

- 这个 skill 聚焦于 Android 平台上本地组件间与应用间通信的安全。
- 这个 skill **不**覆盖网络安全、Web 集成或主机到服务器的安全。

## 配置与依赖

- **Android SDK：** 标准硬件支持的 keystore 操作与组件校验要求最低 API Level 23（Android 6.0）。
- **AndroidX Core 库：** 要使用 `IntentSanitizer`，`androidx.core:core:1.9.0` 或更高版本是**必需的**。
- **标准 API 访问：** 运行时组件校验需要标准的 Android `PackageManager` API。

*** ** * ** ***

## Intent 安全逻辑与决策

### 1. Intent 路由对比

评估不同 Intent 传递方式的安全特性：

| Intent 传递方式 | 作用范围 | 推荐使用场景 |
|---|---|---|
| 显式 Intent（内部） | 应用私有 | 启动应用内部的 Activity/Service |
| 隐式 Intent | 全系统 | 启动系统相机、拨号器或分享 |
| 本地广播（LocalBroadcastManager）（已废弃） | 应用私有 | 内部异步事件分发。**已废弃**：请改用 Kotlin Flow/SharedFlow、LiveData 等应用内观察者或响应式模式。 |
| 系统广播 | 全系统 | 接收系统事件（NFC、蓝牙） |

### 2. PendingIntent 可变性标志选项

评估 PendingIntent 可变性标志的安全影响：

| 标志名称 | 可变性 | 推荐使用场景 |
|---|---|---|
| `PendingIntent.FLAG_IMMUTABLE` | 不可变 | 几乎所有 PendingIntent 的默认选择，例如闹钟与通知 |
| `PendingIntent.FLAG_MUTABLE` | 可变 | 通知内联回复、slice action（需要显式目标 Intent） |

### 3. Intent 处理与重定向逻辑

IF（组件把嵌套 Intent 作为 extra 接收）{
IF（可用的 AndroidX Core 为 1.9.0 或更高版本）{
必须构造 `IntentSanitizer`，显式允许列出组件、action、data 与 extra。
必须在启动前调用 `sanitizeByThrowing()` 或 `sanitizeByFiltering()`。
} ELSE {
必须拒绝或剥离 URI 权限授予标志（`FLAG_GRANT_READ_URI_PERMISSION`、`FLAG_GRANT_WRITE_URI_PERMISSION`、`FLAG_GRANT_PERSISTABLE_URI_PERMISSION`、`FLAG_GRANT_PREFIX_URI_PERMISSION`）。
必须使用 `resolveActivity()` 解析目标组件，并校验其 `packageName` 与 `className` 都与显式允许清单中的组件匹配。
}
严禁在未做校验的情况下直接启动嵌套 Intent。
} ELSE IF（组件处理广播）{
必须依赖系统的受保护广播（Protected Broadcast）机制处理系统事件（该机制保证发送方是系统框架）。
必须用签名级权限保护自定义接收器，或对动态接收器使用 `RECEIVER_NOT_EXPORTED` 限制发送方。
IF（使用 `ContextCompat.registerReceiver` 并带有 `RECEIVER_NOT_EXPORTED` 且 `minSdk < 33`）{
必须确认 `AndroidManifest.xml` 中已声明 `<permission android:name="${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" android:protectionLevel="signature" />` 与 `<uses-permission android:name="${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" />`。
}
}

### 4. PendingIntent 安全逻辑

IF（为传递给其他应用而创建 PendingIntent）{
必须默认使用 `PendingIntent.FLAG_IMMUTABLE`。
IF（该 PendingIntent 必须是可变的）{
必须在基础 `Intent` 上设置显式的目标组件或包名。
严禁创建隐式、可变的 `PendingIntent`。
}
}

### 5. ContentProvider 安全逻辑

IF（ContentProvider 仅供应用内部使用）{
必须设置 `android:exported="false"`。
} ELSE {
必须用 `android:readPermission` 与 `android:writePermission` 保护它。
必须设置 `android:grantUriPermissions="false"`，除非确实需要临时 URL 访问。
}

### 6. Service 调用方校验逻辑

IF（导出的 Service 与可信的同族/合作方应用通信）{
必须暴露跨进程接口（例如 AIDL `Stub` 或 `Messenger`），而不是仅在同一进程内可用的本地 `Binder` 子类。
必须在每次 IPC 请求时校验调用方——在 AIDL `Stub` 方法（或 `onTransact()`）内使用 `Binder.getCallingUid()`，或在 `Messenger` 的 `Handler` 中使用 `Message.sendingUid`——并校验调用包的签名证书指纹与你信任的证书哈希匹配。
}

*** ** * ** ***

## 代码与配置模式

### 1. 安全的 Intent 重定向（手动校验）

在无法使用现代净化库时，启动嵌套 Intent 前先校验其目标。

- **预期输入：**
  - 传入的 `Intent`，其中包含名为 `EXTRA_NESTED_INTENT` 的嵌套 `Intent` extra。
- **预期输出：**
  - 安全则启动目标组件；校验失败则抛出 `SecurityException`。

```kotlin
fun safeIntentRedirectionManual() {
    val nestedIntent = IntentCompat.getParcelableExtra(intent, "EXTRA_NESTED_INTENT", Intent::class.java)
    if (nestedIntent != null) {
        // 1. Check for URI permission grants to prevent URI permission bypass
        val hasUriPermissionGrants = (
            nestedIntent.flags and (
                Intent.FLAG_GRANT_READ_URI_PERMISSION or
                    Intent.FLAG_GRANT_WRITE_URI_PERMISSION or
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or
                    Intent.FLAG_GRANT_PREFIX_URI_PERMISSION
                )
            ) != 0
        if (hasUriPermissionGrants) {
            throw SecurityException("Nested intent contains forbidden URI permission grant flags!")
        }

        // 2. Clear any selector intent that could override resolution
        nestedIntent.selector = null

        // 3. Resolve the target activity and verify both packageName and className
        //    match the expected allowlisted destination
        val target = nestedIntent.resolveActivity(packageManager)
        if (target != null &&
            target.packageName == packageName &&
            target.className == TargetActivity::class.java.name
        ) {
            // 4. Explicitly pin the resolved component to prevent intent interception
            nestedIntent.component = target
            startActivity(nestedIntent)
        } else {
            throw SecurityException("Invalid or disallowed redirect target: $target")
        }
    }
}
```

<br />

### 2. 用 IntentSanitizer 实现安全的 Intent 重定向

使用 AndroidX `IntentSanitizer`（AndroidX Core 1.9.0+）过滤或拒绝动态 Intent。

- **预期输入：**
  - 不可信的传入 `Intent`。
- **预期输出：**
  - `Intent`：只包含已允许的组件、类别与 action 的净化副本。若使用 `sanitizeByThrowing()`，违规时抛出 `SecurityException`。

```kotlin
fun safeIntentRedirectionSanitizer() {
    // Allowlist: anything NOT listed is rejected (only component is required; other fields are optional).
    // No allowFlags(): every flag, including FLAG_GRANT_*_URI_PERMISSION, is rejected.
    val sanitizer = IntentSanitizer.Builder()
        .allowComponent(ComponentName(this, TargetActivity::class.java))
        .allowAction(Intent.ACTION_VIEW)
        .allowData { it.scheme == ContentResolver.SCHEME_CONTENT && it.authority == "$packageName.provider" }
        .allowType("text/plain")
        .allowExtra("user_display_name", String::class.java) { it.length <= 100 } // type and content
        .build()

    val safeIntent = try {
        val untrusted = IntentCompat.getParcelableExtra(intent, "EXTRA_NESTED_INTENT", Intent::class.java)
            ?: return
        sanitizer.sanitizeByThrowing(untrusted)
    } catch (_: SecurityException) {
        Log.w("SECURITY_ALERT", "Blocked non-allowlisted nested intent")
        return
    } catch (_: BadParcelableException) { // e.g. an extra naming an unknown Parcelable/Serializable
        Log.w("SECURITY_ALERT", "Malformed nested intent")
        return
    }

    // The sanitizer doesn't enforce presence; check what the target actually requires.
    if (safeIntent.getStringExtra("user_display_name") == null) {
        Log.w("SECURITY_ALERT", "Nested intent missing user_display_name")
        return
    }
    startActivity(safeIntent)
}
```

<br />

### 3. 自定义签名权限保护

在清单中声明自定义签名级权限，保护同族应用之间的通信。

- **预期输入：** 清单配置。
- **预期输出：** 只能被使用同一开发者证书签名的应用启动的 Activity。

```xml
<permission
    android:name="com.example.snippets.permission.INTERNAL_COMMUNICATION"
    android:protectionLevel="signature" />
```

<br />

```xml
<activity
    android:name=".intents.InternalSharingActivity"
    android:exported="true"
    android:permission="com.example.snippets.permission.INTERNAL_COMMUNICATION">
    <intent-filter>
        <action android:name="com.example.snippets.ACTION_SHARE" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
</activity>
```

<br />

### 4. 安全的 onNewIntent 生命周期校验（热启动保护）

确保复用动态 Intent 的 Activity（例如后台启动路径）在 `onNewIntent` 内应用同样严格的安全过滤。

- **预期输入：**
  - `newIntent`（`Intent`）：新传入的 Intent。
- **预期输出：**
  - 仅当新 Intent 通过安全校验时才执行处理逻辑。

```kotlin
override fun onNewIntent(newIntent: Intent) {
    super.onNewIntent(newIntent)

    // Set the intent to ensure intent returns the new one
    intent = newIntent

    // Validate the intent payload
    if (validateIntent(newIntent)) {
        processIntentPayload(newIntent)
    } else {
        Log.w("SECURITY_ALERT", "Received invalid or insecure intent during warm boot")
    }
}

private fun validateIntent(intent: Intent): Boolean {
    return intent.hasExtra("VALID_PAYLOAD_MARKER")
}
```

<br />

### 5. 安全地创建 PendingIntent

除非明确要求可变性，否则强制使用不可变。

- **预期输入（不可变）：** 一个 Intent 目标。
- **预期输出（不可变）：** 无法被接收方修改的 `PendingIntent`。
- **预期输入（可变）：** 已设置显式组件的 Intent。
- **预期输出（可变）：** 锁定到特定接收器组件的可变 `PendingIntent`，防止被劫持。

```kotlin
fun createPendingIntents(context: Context) {
    // 1. Secure Immutable PendingIntent (Default)
    val intent = Intent(context, TargetActivity::class.java)
    val pendingIntent = PendingIntent.getActivity(
        context,
        0,
        intent,
        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
    )

    // 2. Secure Mutable PendingIntent (e.g., Notification Direct Reply)
    val mutableIntent = Intent().apply {
        // MUST set explicit target component to prevent redirection hijacking
        component = ComponentName(context, ReplyReceiver::class.java)
    }
    val mutablePendingIntent = PendingIntent.getBroadcast(
        context,
        0,
        mutableIntent,
        PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
    )
}
```

<br />

### 6. 安全的 ContentProvider 配置与查询

安全地暴露 ContentProvider，并将查询参数化以防止 SQL 注入。

- **预期输入：**
  - `uri`（`Uri`）：查询 URI。
  - `projection`（`String[]`）：要检索的列。
  - `selection`（`String`）：查询条件。
  - `selectionArgs`（`String[]`）：映射到 selection 占位符（`?`）的值。
- **预期输出：**
  - `Cursor`：过滤后的查询结果，严格受 projection 映射约束。

```xml
<provider
    android:name=".intents.SecureDataProvider"
    android:authorities="com.example.snippets.provider"
    android:exported="true"
    android:readPermission="com.example.snippets.permission.READ_DATA"
    android:writePermission="com.example.snippets.permission.WRITE_DATA"
    android:grantUriPermissions="false" />
```

<br />

```kotlin
override fun query(
    uri: Uri,
    projection: Array<String>?,
    selection: String?,
    selectionArgs: Array<String>?,
    sortOrder: String?
): Cursor? {
    val queryBuilder = SQLiteQueryBuilder()
    queryBuilder.tables = tableName
    // Strict projection map to prevent querying unauthorized columns
    queryBuilder.projectionMap = mapOf(
        "_id" to "_id",
        "display_name" to "display_name"
    )
    // Enable strict validation (always available since minSdk is 36)
    queryBuilder.setStrict(true)
    queryBuilder.setStrictColumns(true)
    queryBuilder.setStrictGrammar(true)

    // MUST parameterize selection criteria; NEVER append selection strings directly
    val db = dbHelper.readableDatabase
    return queryBuilder.query(db, projection, selection, selectionArgs, null, null, sortOrder)
}
```

<br />

### 7. Service 调用方签名校验

在导出的绑定服务中，对传入的跨进程 IPC 调用校验调用应用的签名证书。

- **预期输入：**
  - 传入的跨进程 Binder 事务（例如 AIDL `Stub` 方法调用或 `onTransact()`）。
- **预期输出：**
  - 如果调用方 UID 的签名证书与可信合作方哈希匹配，则执行所请求的服务操作；否则抛出 `SecurityException`。

```kotlin
class SecureBoundService : Service() {
    companion object {
        // Expected SHA-256 hash of the trusted app's signing certificate (Base64 encoded)
        private const val TRUSTED_PARTNER_SHA256 = "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V="
    }

    override fun onBind(intent: Intent): IBinder {
        // Return the binder. Do NOT perform signature verification in onBind() because
        // the binder connection is cached by Android, which can bypass checks on subsequent binds.
        return LocalBinder()
    }

    private fun enforceTrustedCaller() {
        val callingUid = Binder.getCallingUid()
        // Allow calls from the same application
        if (callingUid == Process.myUid()) {
            return
        }
        val pm = packageManager
        val packages = pm.getPackagesForUid(callingUid)

        if (packages.isNullOrEmpty() || !verifySignature(pm, packages[0])) {
            throw SecurityException("Access Denied: Caller signature is untrusted.")
        }
    }

    private fun verifySignature(pm: PackageManager, packageName: String): Boolean {
        try {
            val trustedSha256Raw = Base64.decode(TRUSTED_PARTNER_SHA256, Base64.DEFAULT)
            // API 28+ handles rotated certificates and avoids manual hashing.
            // Since minSdk is 36, this is always available.
            return pm.hasSigningCertificate(packageName, trustedSha256Raw, PackageManager.CERT_INPUT_SHA256)
        } catch (e: Exception) {
            Log.e("SECURITY_ERROR", "Verification failed for package: $packageName", e)
        }
        return false
    }

    inner class LocalBinder : Binder() {
        fun doSecureWork() {
            // Verify caller identity on every transaction method call
            enforceTrustedCaller()
            // Safe to proceed with sensitive operations
        }
    }
}
```

<br />

*** ** * ** ***

## 错误处理

安全地处理组件绑定、数据库查询与 Intent 重定向失败，避免泄露内部结构。

```kotlin
fun safeErrorHandling(callingPackage: String?) {
    try {
        val payload = intent.getStringExtra("DATA_EXTRA") ?: throw IllegalArgumentException("Payload parameter missing.")
        // Create a specific target intent using the validated payload
        val targetIntent = Intent(this, TargetActivity::class.java).apply {
            putExtra("SECURE_PAYLOAD", payload)
        }
        startActivity(targetIntent)
    } catch (e: SecurityException) {
        // MUST log security violations for audit, but NEVER expose exception details to the user.
        Log.e("SECURITY_ERROR", "Unauthorized component transition blocked. Calling Package: ${callingPackage ?: "Unknown"}", e)
        // MUST provide generic user feedback.
        showFeedbackToUser("Process request failed: Access Denied.")
    } catch (e: IllegalArgumentException) {
        Log.w("INTEGRITY_WARNING", "Missing intent parameter", e)
    }
}
```

<br />

    // Secure handling of ContentProvider queries on the client side:
    try {
        val cursor = contentResolver.query(providerUri, projection, selection, selectionArgs, null)
    } catch (e: SQLiteException) {
        Log.e("PROVIDER_ERROR", "ContentProvider database query failed", e)
        // Secure handling: prevent raw query syntax details from leaking to UI
    }

*** ** * ** ***

## 报告指南

当执行这个 skill 对代码库应用安全加固更新时，agent **必须**为开发者生成结构化的「最佳实践与安全对齐更新」报告。报告**必须**写入会话的构件目录（或在最终回复中打印），并包含：

1. **安全对齐领域：** 所应用的改进类别（例如安全的 Intent 重定向、安全的 PendingIntent 配置、ContentProvider 数据防护）。
2. **影响与优先级：** 本次更新所处理的潜在安全风险（例如组件劫持防护、私有数据隔离）。
3. **变更范围：** 所有被修改的类、XML 文件与依赖的列表。
4. **实现摘要：** 方案的具体细节（例如「把嵌套 Intent 解析改为使用 `IntentSanitizer` API，并采用严格的组件允许清单」）。
5. **代码差异：** 展示确切修改内容的标准 unified diff。

### 最佳实践与安全对齐更新模板

向开发者报告变更时，使用以下 markdown 模板：

    ### 最佳实践与安全对齐更新：[Security Alignment Area]

    *   **改进说明：** [加固更新的简要说明以及推荐原因]
    *   **优先级：** [High / Medium / Low]
    *   **对齐操作：** [更新摘要，例如转换为 FLAG_IMMUTABLE]

    #### 修改的文件
    *   `[Relative path to File 1]`
    *   `[Relative path to File 2]`

    #### 实现差异
    ```diff
    // Insert Unified Diff here

#### 测试与验证

1. \[验证组件行为正确的步骤 1，例如运行组件单元测试\]
2. \[验证回归安全性的步骤 2\] \`\`\`

*** ** * ** ***

## 反模式

- **严禁**在未校验解析出的组件（`packageName` 与 `className`）是否匹配显式允许清单、且未拒绝或剥离 URI 权限授予标志的情况下，启动来自不可信来源的嵌套 `Intent`。
- **严禁**使用粘性广播（`sendStickyBroadcast`）。
- **严禁**因为某个导出组件运行在后台线程或做了内部检查，就认为它是安全的。
- **严禁**在没有签名级权限限制的情况下，向组件暴露敏感功能（例如 SSO 认证或支付处理）。
- **严禁**在 `onNewIntent` 中处理传入 Intent 时，未应用与 `onCreate` 相同的安全控制。
- **严禁**在基础 `Intent` 未设置显式目标组件的情况下，创建可变的 `PendingIntent`。
- **严禁**在 `ContentProvider` 查询中使用动态字符串拼接构造 selection 子句。
- **严禁**在 `BroadcastReceiver.onReceive` 中使用 `Binder.getCallingUid` 识别广播发送方，因为它返回接收器自身的 UID，而不是发送方的 UID。

## 最佳实践

- **必须**为所有不需要外部通信的组件显式设置 `android:exported="false"`。
- **必须**在同族应用之间通信时，用带 `android:protectionLevel="signature"` 的自定义权限保护所有导出组件。
- **必须**校验所有传入的 Intent extra，并妥善处理缺失参数以防止崩溃。
- **必须**依赖系统的**受保护广播**机制处理系统事件（例如开机完成、包变更），因为系统会阻止不可信应用伪造这些 action。
- **必须**用签名级权限保护自定义广播，或对动态接收器使用 `RECEIVER_NOT_EXPORTED` 限制发送方身份（并且当 `minSdk < 33`、使用 `ContextCompat.registerReceiver` 时，**必须**确认 `AndroidManifest.xml` 中存在 `<permission android:name="${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" android:protectionLevel="signature" />` 与 `<uses-permission android:name="${applicationId}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION" />`）。
- **必须**在处理载荷前于 `onNewIntent()` 内调用 `setIntent(newIntent)`，以保持活动引用最新。
- **必须**在构造 `PendingIntent` 实例时默认使用 `PendingIntent.FLAG_IMMUTABLE`。
- **必须**用 `readPermission` 与 `writePermission` 保护导出的 `ContentProviders`。
- **必须**在 `ContentProvider` 的 query/update 方法中强制使用参数化的 selection 结构。
- **必须**在导出的绑定服务中，通过跨进程接口（例如 AIDL `Stub` 或 `Messenger`）在运行时对传入的 IPC 事务校验调用应用的签名证书。
- 如果项目引入了 AndroidX Core 1.9.0+，**必须**在重定向前用 `androidx.core.content.IntentSanitizer` 净化传入的动态 Intent。
