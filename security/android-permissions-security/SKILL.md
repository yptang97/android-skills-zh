---
name: android-permissions-security
description: 审计、发现缺口并修复 Android 权限与 IPC 组件相关的安全漏洞。适用于审查 AndroidManifest.xml、定义自定义权限、加固 Service、Receiver 和 Provider、使用 Binder 校验调用方签名与 UID，或实现运行时权限流程的场景。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - recipe
  - Android
  - Security
  - Permissions
  - IPC
  - Binder
  - UID
  - Caller Verification
  - knownSigner
  - signature
  - ContentProvider
  - Service
  - Receiver
  - Broadcast
  - UriPermission
  - runtime permissions
  - SecurityException
  - Photo Picker
  - Vulnerability
  - Remediation
---

审计权限漏洞、实施最小权限原则、
加固 IPC 边界，以及在 Android 生态中处理运行时权限的指南。

## 术语表

- **运行时权限（Runtime Permission）：** 危险权限（例如相机、位置），在 Android 6.0+（API 23+）上必须由用户在运行时授予。
- **自定义权限（Custom Permission）：** 由应用定义的权限（`<permission>`），用于限制对其导出组件的访问。
- **保护级别（Protection Level）：** 定义操作系统如何授予该权限的属性（`normal`、`dangerous`、`signature`、`knownSigner`）。
- **knownSigner：** 保护标志（API 31+），向签名证书摘要匹配可信摘要的合作方应用授予签名级访问。
- **SigningInfo：** 对象（API 28+），提供某个应用的签名历史和多个签名证书。
- **Binder 调用方身份：** 通过 `Binder.getCallingUid()` 获得的、代表调用进程的可信 UID。
- **URI 权限：** 通过 `grantUriPermissions` 和 intent 标志授予的、针对内容 URI 的临时细粒度访问权限。

## 前置条件

- 在应用级 `build.gradle` 文件中添加 `androidx.core:core-ktx` 和 `androidx.activity:activity-ktx`（或 `androidx.fragment:fragment-ktx`）依赖，以使用 `ContextCompat` 和 `ActivityResultContracts`。
- 使用 `knownSigner` 合作方权限（`android:knownCerts`）时，确保项目的 `compileSdk` 和 `targetSdk` 至少为 31（Android 12）。
- 使用广播身份共享（`BroadcastOptions.setShareIdentityEnabled`）时，确保 `compileSdk` 和 `targetSdk` 至少为 34（Android 14）。

*** ** * ** ***

## 1. 安全审计与权限缺口排查手册

审计 Android 项目的权限与 IPC 安全漏洞时，按以下各个方面系统检查：

| 漏洞领域 | 搜索位置 / 匹配模式 | 风险 | 修复动作 |
|---|---|---|---|
| **自定义权限保护过弱** | `AndroidManifest.xml` 中出现 `android:protectionLevel="normal"`、`"dangerous"` 或 `"signatureOrSystem"` | 未授权的应用可以申请或声称该权限而不受限制 | 升级为 `signature` 或 `signature|knownSigner`，并配置 `android:knownCerts`。 |
| **URI 权限授予范围过宽** | `<provider>` 中出现 `<grant-uri-permission android:pathPrefix="/" />` 或 `pathPrefix=""` | 把 provider 的全部数据泄漏给第三方 | 改为明确的受限子路径（例如 `android:pathPrefix="/shared/"`）。保留 `android:grantUriPermissions="true"`。移除任何通配的 `pathPrefix="/"`。 |
| **ContentProvider 读写权限未拆分** | `<provider>` 只有通用的 `android:permission`，或缺少 `android:readPermission` 与 `android:writePermission` | 只读调用方能执行写操作，或只写调用方能执行读操作 | 配置细粒度的 `android:readPermission="...READ_DATA"` 和 `android:writePermission="...WRITE_DATA"`，并**同时**在 `<manifest>` 根级别以 `android:protectionLevel="signature"`（或 `signature|knownSigner`）声明对应的自定义 `<permission>` 标签。 |
| **调用方身份校验可被伪造** | Service 中出现 `intent.getStringExtra("calling_package")`、`intent.getStringExtra("sender")`、`callingPackage == "..."` | 恶意调用方可以伪造 intent extra 或字符串 | 移除字符串校验；使用 `Binder.getCallingUid()` 和 `pm.hasSigningCertificate()` 以密码学方式校验调用方 UID。 |
| **绑定 Service 权限被绕过** | Binder AIDL stub 中出现 `checkCallingOrSelfPermission()` 或 `enforceCallingOrSelfPermission()` | 在 IPC 之外或身份被清除时回退到宿主应用 UID，导致混淆代理（Confused Deputy）绕过 | 改为 `enforceCallingPermission("...WRITE_DATA", ...)` 或 `checkCallingPermission("...WRITE_DATA")`。 |
| **绑定 Service 缺少方法级校验** | 绑定 Service 的 AIDL 方法在未强制写权限的情况下修改状态 | 只有只读绑定权限的调用方能调用会修改状态的写操作 | 在会修改状态的 AIDL 方法内添加 `enforceCallingPermission("...WRITE_DATA", "Caller lacks WRITE_DATA permission")`。 |
| **运行时权限流程有缺陷** | 缺少 `shouldShowRequestPermissionRationale()`、缺少永久拒绝的处理，或在循环中反复请求 | 用户体验差、出现死循环，或无法恢复权限 | 实现三态流程：检查是否已授予 -\> 检查是否需要说明弹窗 -\> 启动请求契约。遇到永久拒绝时，引导用户到 `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`。 |
| **同时请求位置权限** | 在一次请求中使用 `arrayOf(ACCESS_FINE_LOCATION, ACCESS_BACKGROUND_LOCATION)` | 在 Android 11+（API 30+）上会被拒绝 | 先请求前台位置（`ACCESS_FINE_LOCATION`、`ACCESS_COARSE_LOCATION`）。只有在前台权限已授予后，再单独用一步请求 `ACCESS_BACKGROUND_LOCATION`。 |
| **为媒体访问申请宽泛存储权限** | 为让用户选择图片而申请 `READ_EXTERNAL_STORAGE` 或 `READ_MEDIA_IMAGES` | 权限过度、侵犯用户隐私 | 迁移到零权限的 Photo Picker（`ActivityResultContracts.PickVisualMedia`）。 |
| **缓存权限状态** | 把权限状态存在 `var cachedLocationPermissionGranted = ...` 中 | 权限被撤销或过期后会失效 | 在调用时动态查询 `ContextCompat.checkSelfPermission()`，并用 try-catch 包住受保护调用以捕获 `SecurityException`。 |
| **不安全的广播** | `sendBroadcast(intent)` 未指定目标包或接收方权限；接收方未校验发送方 | 数据被截获或指令被伪造 | 设置明确的包（`intent.setPackage(...)`）、传入接收方权限，并启用 `BroadcastOptions.setShareIdentityEnabled(true)`（API 34+）以校验 `sentFromPackage`。 |

*** ** * ** ***

## 2. 自定义权限与保护级别

在清单中声明自定义权限或合作方证书时，你必须遵循 [`<permission>` 元素指南](references/android/guide/topics/manifest/permission-element.md)中的说明。

- **`signature`**：仅限使用同一开发者密钥签名的应用访问。
- **`signature|knownSigner`**（API 31+）：仅限签名证书摘要与 `android:knownCerts` 中声明的哈希匹配的合作方应用访问。
- **`normal` 或 `dangerous`**：**不要**用于应用之间的私有 IPC。
- **`signatureOrSystem`**：**已废弃**（API 23）。把已废弃的 `signatureOrSystem` 权限升级为 `signature`。非系统应用应避免使用。

### 清单片段

#### 签名级自定义权限

当你希望通过在清单中声明 `<permission>` 并对目标组件应用 `android:permission`，把组件访问严格限制为使用同一开发者证书签名的应用时，使用 `signature` 权限。


```xml
<permission
    android:name="com.example.snippets.permission.ACCESS_SECURE_API"
    android:protectionLevel="signature" />
```

<br />

#### KnownSigner 合作方权限（API 31+）

当你希望只向特定的外部合作方应用授予访问权限时，使用 `signature|knownSigner` 权限：在清单中声明 `<permission>`，并让 `android:knownCerts` 指向一个包含可信 SHA-256 证书摘要的资源数组。


```xml
<resources xmlns:tools="http://schemas.android.com/tools">
    <!-- SHA-256 fingerprints of trusted partner certificates (lowercase, no colons) -->
    <string-array name="trusted_partner_certs" tools:ignore="Typos">
        <item>103938ee4537e59e8ee792f654504fb8346fc6b346d0bbc4415fc339fcfc8ec1</item>
    </string-array>
</resources>
```

<br />


```xml
<permission
    android:name="com.example.snippets.permission.PARTNER_API"
    android:protectionLevel="signature|knownSigner"
    android:knownCerts="@array/trusted_partner_certs" />
```

<br />

*** ** * ** ***

## 3. 导出组件的保护与 URI 权限

- **私有组件**：始终设置 `android:exported="false"`。
- **导出组件**：必须要求权限（`android:permission`、`android:readPermission`、`android:writePermission`）。
- **细粒度 URI 授予**：为安全共享保留 `android:grantUriPermissions="true"`，但要把授予范围限制到具体子路径。**绝不**使用通配的 `pathPrefix="/"`。
- **自定义权限声明**：在 provider 上拆分读写权限时，你**必须**在 `<manifest>` 根级别以 `android:protectionLevel="signature"`（或 `signature|knownSigner`）声明这些 `<permission>` 标签。
- **修复已有的通配授予**：你**必须**找出并移除任何已有的 `<grant-uri-permission android:pathPrefix="/" />` 或 `pathPrefix=""`，替换为明确的受限子路径（例如 `android:pathPrefix="/shared/"`）。
- **细粒度 `UriPermission` 管理**：与其在清单中做宽泛授予，不如使用运行时的 `android.content.UriPermission` 令牌，实现按 URI 的最小权限共享：
  - *授予临时访问*：`context.grantUriPermission(targetPackage,
    uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)`，或给外发 intent 附加 `Intent.FLAG_GRANT_READ_URI_PERMISSION`。
  - *持久化访问*：接收方应用调用 `contentResolver.takePersistableUriPermission(uri, modeFlags)`，以获得重启后依然有效的访问权限。
  - *审计生效的授予*：检查 `contentResolver.persistedUriPermissions`（`List<UriPermission>`），核实已授予的 URI（`uriPermission.uri`、`uriPermission.isReadPermission()`、`uriPermission.isWritePermission()`）。
  - *撤销访问*：操作一结束就调用 `context.revokeUriPermission(uri, modeFlags)` 或 `contentResolver.releasePersistableUriPermission(uri, modeFlags)`。

### 清单片段：完整的安全 ContentProvider 声明

在 `<manifest>` 根级别声明拆分后的读写权限：


```xml
<permission
    android:name="com.example.snippets.permission.READ_DATA"
    android:protectionLevel="signature" />
<permission
    android:name="com.example.snippets.permission.WRITE_DATA"
    android:protectionLevel="signature" />
```

<br />

然后用这些权限和受限的 URI 授予来配置 provider：


```xml
<provider
    android:name=".permissions.SecureDataProvider"
    android:authorities="com.example.snippets.partnerprovider"
    android:exported="true"
    android:readPermission="com.example.snippets.permission.READ_DATA"
    android:writePermission="com.example.snippets.permission.WRITE_DATA"
    android:grantUriPermissions="true">
    <grant-uri-permission android:pathPrefix="/shared/" />
</provider>
```

<br />

### 运行时细粒度 UriPermission 管理片段


```kotlin
object UriPermissionManager {

    /** Grants temporary read access to a specific URI for a partner package. */
    fun grantScopedUriAccess(context: Context, targetPackage: String, uri: Uri) {
        context.grantUriPermission(
            targetPackage,
            uri,
            Intent.FLAG_GRANT_READ_URI_PERMISSION
        )
    }

    /** Audits active persisted URI permissions held by the application. */
    fun getActivePersistedPermissions(context: Context): List<UriPermission> {
        return context.contentResolver.persistedUriPermissions
    }

    /** Revokes temporary URI access when data transfer completes. */
    fun revokeScopedUriAccess(context: Context, uri: Uri) {
        context.revokeUriPermission(
            uri,
            Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
        )
    }
}
```

<br />

*** ** * ** ***

## 4. 以密码学方式校验调用方身份

绝不要信任 Intent 或字符串参数中提供的调用方包名（`getCallingPackage()`、`intent.getStringExtra("calling_package")`、
`intent.getStringExtra("sender")`、`intent.getStringExtra("package")`）。Intent
extra 和字符串形式的包名都可能被恶意应用伪造。

### 严重漏洞：使用 intent extra 伪造包名


```kotlin
// VULNERABLE PATTERN: DO NOT DO THIS
val callingPackage = intent?.getStringExtra("calling_package")
if (callingPackage != null && SignatureUtils.verifyPartnerPackage(this, callingPackage)) {
    // A malicious app passes "com.example.partner" in the extra.
    // The signature check verifies the installed partner on disk, but the CALLER was malicious!
}
```

<br />

### 安全做法：以密码学方式校验调用方 UID

1. **彻底移除**所有 `intent.getStringExtra("calling_package")`、`intent.getStringExtra("sender")` 和 `callingPackage == "..."` 校验。
2. 在活跃的 Binder IPC 事务中（例如 AIDL `Stub` 方法或 `ContentProvider` 方法）使用 `Binder.getCallingUid()` 获取调用方身份。
3. 使用 `PackageManager.hasSigningCertificate()`（API 28+）或 `PackageManager.getPackagesForUid()` 校验调用方证书。

### 完整的 CallerVerifier 实现

把它应用到目前执行可伪造校验的那个 service 上。

- **放置位置**：把 `CallerVerifier` 声明在**同一个文件**里，与你正在修复的 service 放在一起（例如放在 `SecureDataService.kt` 内）。不要把校验逻辑挪到新文件里，却把原来的 service 留在那不动。
- **活跃的 Binder IPC 上下文**：`Binder.getCallingUid()` 只在活跃的 Binder 事务期间返回远端调用方的 UID（在 `Service.onStartCommand()` 或 `Service.onBind()` 内绝不成立，那里返回的是 `Process.myUid()`）。要拒绝 `callingUid == Process.myUid()`，这样在活跃 IPC 事务之外或调用 `Binder.clearCallingIdentity()` 之后的调用会失败关闭，而不是绕过校验。
- **可空性**：`packageInfo.signatures` 的类型是 `Array<Signature>?`。严格按下面所写复制 `?: return false` 这个保护。直接迭代 `packageInfo.signatures` 会编译失败，报错「Non-nullable value required to call an 'iterator()' method in a for-loop.」


```kotlin
object CallerVerifier {
    private const val TRUSTED_PARTNER_SHA256 =
        "A1B2C3D4E5F60708090A0B0C0D0E0F1011121314151617181920212223242526"

    fun isCallerAuthorized(context: Context): Boolean {
        val callingUid = Binder.getCallingUid()
        if (callingUid == android.os.Process.myUid()) return false

        val pm = context.packageManager
        // Modern API 28+ check by UID:
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            val certBytes = hexStringToByteArray(TRUSTED_PARTNER_SHA256)
            return pm.hasSigningCertificate(callingUid, certBytes, PackageManager.CERT_INPUT_SHA256)
        }

        // Fallback for legacy APIs:
        val callingPackages = pm.getPackagesForUid(callingUid) ?: return false
        for (pkg in callingPackages) {
            if (verifyPackageSignature(pm, pkg)) {
                return true
            }
        }
        return false
    }

    @Suppress("DEPRECATION")
    private fun verifyPackageSignature(pm: PackageManager, packageName: String): Boolean {
        return try {
            val packageInfo = pm.getPackageInfo(packageName, PackageManager.GET_SIGNATURES)
            val signatures = packageInfo.signatures ?: return false
            for (sig in signatures) {
                val digest = java.security.MessageDigest.getInstance("SHA-256").digest(sig.toByteArray())
                val hex = digest.joinToString("") { "%02X".format(it) }
                if (hex.equals(TRUSTED_PARTNER_SHA256, ignoreCase = true)) return true
            }
            false
        } catch (e: PackageManager.NameNotFoundException) {
            false
        }
    }

    private fun hexStringToByteArray(s: String): ByteArray {
        val len = s.length
        val data = ByteArray(len / 2)
        for (i in 0 until len step 2) {
            data[i / 2] = ((Character.digit(s[i], 16) shl 4) + Character.digit(s[i + 1], 16)).toByte()
        }
        return data
    }
}
```

<br />

*** ** * ** ***

## 5. 绑定 Service 中的方法级 Binder 强制校验（SecureBoundService.kt）

在暴露 AIDL Binder stub 的绑定 Service 中，使用 `enforceCallingPermission()` 保护会修改状态的方法。

### 关键安全规则：在 service 中绝不使用 CallingOrSelfPermission

- **绝不**使用 `checkCallingOrSelfPermission()` 或 `enforceCallingOrSelfPermission()`。
- **原因：** 在活跃的 Binder 事务期间，这个方法检查调用方的权限。但如果该方法在本地被调用（活跃 IPC 之外），或者 IPC 调用方身份被丢弃，它就会回退去检查宿主应用的权限。由于宿主应用持有该权限，这个回退会授予访问权并绕过安全边界，造成混淆代理（Confused Deputy）漏洞。
- **必须使用：** `enforceCallingPermission("com.example.snippets.permission.WRITE_DATA",
  "Caller lacks WRITE_DATA permission")` 或 `checkCallingPermission("com.example.snippets.permission.WRITE_DATA")`。

### 完整的 SecureBoundService 实现


```kotlin
class SecureBoundService : Service() {

    private val binder = object : IMyService.Stub() {
        override fun getData(): String {
            // Read-only operation guarded by manifest-level permission
            return "Confidential Data"
        }

        override fun modifyData(newData: String) {
            // MUST use enforceCallingPermission or checkCallingPermission.
            // NEVER use checkCallingOrSelfPermission or enforceCallingOrSelfPermission.
            this@SecureBoundService.enforceCallingPermission(
                "com.example.snippets.permission.WRITE_DATA",
                "Caller lacks WRITE_DATA permission"
            )
            updateInternalState(newData)
            Log.d("SecureBoundService", "Data modified to: $newData with proper WRITE_DATA permission check")
        }
    }

    override fun onBind(intent: Intent?): IBinder = binder

    private fun updateInternalState(data: String) {
        // Internal state update logic
    }
}
```

<br />

*** ** * ** ***

## 6. 安全的运行时权限工作流（RuntimePermissionsActivity.kt）

在实现运行时权限请求或处理权限被拒绝的各种状态时，你必须遵循 [请求运行时权限指南](references/android/training/permissions/requesting.md)和 [权限概览](references/android/guide/topics/permissions/overview.md)中的说明。实现三态流程，不要缓存状态，也不要制造无限重试循环：

1. **检查是否已授予**：`ContextCompat.checkSelfPermission(this,
   permission) == PackageManager.PERMISSION_GRANTED`。
2. **检查是否需要说明**：用 `shouldShowRequestPermissionRationale(permission)` 在请求前给出解释性上下文。
3. **启动请求契约**：`ActivityResultContracts.RequestPermission()`。
4. **处理永久拒绝**：在回调中，如果权限被拒绝且 `!shouldShowRequestPermissionRationale(permission)`，就引导用户到 `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`。

### 完整的 RuntimePermissionsActivity.kt 实现


```kotlin
class RuntimePermissionsActivity : ComponentActivity() {

    private val cameraLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
            if (isGranted) {
                startCameraPreview()
            } else {
                if (!shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
                    // User selected 'Don't ask again' or permanently denied.
                    // Direct user to Application Details Settings.
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                        data = Uri.fromParts("package", packageName, null)
                    }
                    startActivity(intent)
                } else {
                    showSnackbar("Camera permission is required to preview camera feed.")
                }
            }
        }

    fun requestCameraPermissionSafely() {
        val permission = Manifest.permission.CAMERA
        when {
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED -> {
                startCameraPreview()
            }
            shouldShowRequestPermissionRationale(permission) -> {
                showSnackbar("Camera permission is needed to preview camera feed.")
                cameraLauncher.launch(permission)
            }
            else -> {
                cameraLauncher.launch(permission)
            }
        }
    }

    private fun startCameraPreview() {
        Log.d("RuntimePermissionsActivity", "Camera preview started")
    }

    private fun showSnackbar(msg: String) {
        Log.i("RuntimePermissionsActivity", msg)
    }
}
```

<br />

*** ** * ** ***

## 7. 零权限替代方案与顺序流程

在实现照片或媒体选择时，你必须遵循 [Photo Picker API 指南](https://developer.android.com/training/data-storage/shared/photopicker)中的说明，以避免申请宽泛的存储权限。

- **Photo Picker**：优先使用 `ActivityResultContracts.PickVisualMedia()`，而不是申请宽泛的存储权限（`READ_MEDIA_IMAGES`、`READ_EXTERNAL_STORAGE`）。
- **顺序位置流程**：先请求 `ACCESS_FINE_LOCATION` 和 `ACCESS_COARSE_LOCATION`。绝不要同时请求 `ACCESS_BACKGROUND_LOCATION`。只有在前台位置已授予之后，才在单独的一步里请求后台位置。

### Photo picker 实现


```kotlin
private val photoPickerLauncher =
    registerForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) {
            handleImageUri(uri)
        }
    }

fun selectPhoto() {
    photoPickerLauncher.launch(
        PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
    )
}
```

<br />

### 顺序位置请求实现


```kotlin
private val foregroundLocationLauncher =
    registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->
        val fineGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
        val coarseGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] ?: false
        if (fineGranted || coarseGranted) {
            startForegroundLocationUpdates()
        }
    }

fun requestForegroundLocation() {
    foregroundLocationLauncher.launch(
        arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
    )
}

// Background location requested only AFTER foreground is granted and user explicitly opts in:
private val backgroundLocationLauncher =
    registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
        if (isGranted) {
            startBackgroundTracking()
        }
    }
```

<br />

*** ** * ** ***

## 8. 无状态检查与错误边界

- **绝不在内存变量里缓存权限状态**（例如 `cachedLocationPermissionGranted`）。每次操作前动态检查 `ContextCompat.checkSelfPermission()`。
- **用 try-catch 包住 API 调用**：在受权限保护的框架调用（例如位置查询）周围捕获 `SecurityException`，以优雅处理一次性权限被撤销的情况。


```kotlin
fun performLocationAccess() {
    val fine = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
    val coarse = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION)
    if (fine != PackageManager.PERMISSION_GRANTED && coarse != PackageManager.PERMISSION_GRANTED) {
        requestForegroundLocation()
        return
    }

    val provider = if (fine == PackageManager.PERMISSION_GRANTED) {
        LocationManager.GPS_PROVIDER
    } else {
        LocationManager.NETWORK_PROVIDER
    }

    try {
        val location = locationManager.getLastKnownLocation(provider)
        processLocation(location)
    } catch (e: SecurityException) {
        Log.e("LocationAccess", "Permission revoked at runtime", e)
    }
}
```

<br />

*** ** * ** ***

## 9. 安全广播（API 34+ 身份共享）

使用显式 intent、必需的接收方权限，或 Android 14+ 的广播选项：


```kotlin
// Sender: Enforce permission and share identity
val intent = Intent("com.example.snippets.permission.ACTION_SECRET_UPDATE").apply {
    setPackage("com.example.partner") // Explicit target
}
val isUdc = Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE
val options = if (isUdc) {
    BroadcastOptions.makeBasic().apply {
        setShareIdentityEnabled(true)
    }.toBundle()
} else null

sendBroadcast(intent, "com.example.snippets.permission.RECEIVE_SECRET_UPDATE", options)
```

<br />


```kotlin
// Receiver: Validate sender on Android 14+
class ProtectedReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == "com.example.snippets.permission.ACTION_SECRET_UPDATE") {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                val sender = sentFromPackage
                if (sender != "com.example.trusted_sender") {
                    return // Reject unauthorized sender
                }
            }
            processUpdate(intent)
        }
    }

    private fun processUpdate(intent: Intent) {}
}
```

<br />

*旧版本兼容（API 34 之前）*：在 API 33 及更低版本上，**绝不**使用 `PendingIntent.getCreatorPackage()` 或
`PendingIntent.getCreatorUid()` 校验广播发送方，因为任何获得可信应用
`PendingIntent` 的应用都能附加并发送它（见 [Pending Intent 的发送方](references/android/privacy-and-security/risks/sender-of-pending-intents.md)）。
而应在清单中用 `signature` 或 `signature|knownSigner`
（API 31+）权限限制该 `<receiver>`；如果 `minSdkVersion` 低于 31，则使用
绑定的 `Service` 或 `ContentProvider`，并校验 `Binder.getCallingUid()`。

*** ** * ** ***

## 质量检查清单

### 应当

- **必须**在 `<manifest>` 根级别为自定义权限和 ContentProvider 拆分权限声明 `<permission android:name="..."
  android:protectionLevel="signature" />`（或 `signature|knownSigner`）。
- **必须**为所有私有组件显式设置 `android:exported="false"`，从而无需再做自定义权限管理。
- **必须**使用 `Binder.getCallingUid()` 和证书哈希（`PackageManager.hasSigningCertificate` 或 `getPackagesForUid`）以密码学方式校验调用方，而不是检查可伪造的 intent extra。
- **必须**在运行时请求之前以及处理拒绝时检查 `shouldShowRequestPermissionRationale()`。
- **必须**在权限被永久拒绝时引导用户到 `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`。
- **必须**对会修改状态的 AIDL 方法用 `enforceCallingPermission()` 或 `checkCallingPermission()` 做方法级强制校验。
- **必须**把 ContentProvider 的 URI 权限限定到明确的子路径（例如 `android:pathPrefix="/shared/"`），同时保留 `android:grantUriPermissions="true"`。
- **必须**在受保护的 API 调用周围捕获 `SecurityException`。
- **必须**顺序请求前台和后台位置权限，绝不同时请求。

### 绝不

- **绝不**从 Intent extra 中提取或校验包名（`intent.getStringExtra("calling_package")`、`intent.getStringExtra("sender")`、`intent.getStringExtra("package")`）。始终使用 `Binder.getCallingUid()` 和证书做校验。
- **绝不**使用 `PendingIntent.getCreatorPackage()` 或 `PendingIntent.getCreatorUid()` 校验广播或 IPC 发送方。
- **绝不**只为调用方伪造问题添加清单权限，却保留可伪造的 intent extra 校验。
- **绝不**用 `checkCallingOrSelfPermission()` 或 `enforceCallingOrSelfPermission()` 保护对外部调用方开放的方法。始终使用 `enforceCallingPermission()` 或 `checkCallingPermission()`。
- **绝不**使用已废弃的 `signatureOrSystem`。
- **绝不**声明或保留 `<grant-uri-permission android:pathPrefix="/"
  />` 或 `pathPrefix=""`。始终替换为受限子路径。
- **绝不**在拒绝后制造无限权限请求循环。
- **绝不**在同一次请求里同时申请前台和后台位置权限。
- **绝不**把权限授予状态缓存在内存字段里。
