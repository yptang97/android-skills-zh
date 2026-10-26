---
name: android-for-cars-parked-apps
description: 把现有的 Android 视频流媒体应用、游戏和网页浏览器改造为可在 Android Auto
  与 Android Automotive OS 上作为驻车应用（parked app）运行。涵盖清单配置、Google Play
  硬件功能声明、兼容模式、返回导航入口、方向与显示连续性、可控系统栏 insets、不规则
  显示挖孔、驾驶分心生命周期处理、配合 CarUxRestrictionsManager 的 MediaSession 播放
  限制、行驶中的后台音频，以及浏览器敏感数据保护。在迁移、构建或审查面向汽车的驻车
  应用以满足 Car App Quality 指南时使用这个 skill。不要用于为行驶中使用而设计的媒体
  音频应用、模板化 Car App Library 导航、兴趣点、物联网、天气或通信类应用。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-09'
  keywords:
  - Android Auto
  - Android Automotive OS
  - parked apps
  - video
  - games
  - browsers
  - adaptive
---

把现有的 Android 视频应用、游戏和网页浏览器改造为可在 Android Auto 与 Android
Automotive OS 上作为驻车应用运行。按以下步骤操作，以满足 Google Play 分发的
Car App Quality 指南。

## 前置条件

- 从一个已存在的自适应 Android 应用开始，且属于受支持的驻车应用类别之一：视频流媒体应用、游戏或网页浏览器。

## 术语表

- **驻车应用（parked apps）**：驻车应用仅在车辆驻车时于 Android Auto 和 Android Automotive OS 上运行。驻车类别有三类：视频、游戏和浏览器；其他类别不能作为驻车应用发布。
- **Android Auto**：Android Auto 是手机驱动的投屏系统。应用在用户手机上执行，并通过有线或无线连接投射到车内显示屏。Android Auto 是与 Android Automotive OS 相互独立的平台。
- **Android Automotive OS**：Android Automotive OS（简称 AAOS）是直接运行在车辆上的 Android 变体。Android Automotive OS 是与 Android Auto 相互独立的平台。
- **视频类别**：视频应用在驻车时播放流媒体视频。在 Android Automotive OS 上普遍可用；Android Auto 不支持。
- **游戏类别**：游戏应用在驻车时提供游戏玩法。在 Android Automotive OS 和 Android Auto 上普遍可用。
- **浏览器类别**：网页浏览器让用户在驻车时浏览网页。在 Android Automotive OS 上为 beta；Android Auto 不支持。
- **媒体类别**：不属于驻车类别。媒体应用在行驶或驻车时播放音频内容（音乐、电台、有声书，不含视频）。
- **Android for Cars 平台**：Android for Cars 是包含 Android Auto 与 Android Automotive OS 的统称。
- **普遍可用类别**：在受支持的平台上，可用于 Google Play 的内部测试、封闭测试、开放测试和生产轨道。
- **Beta 类别**：可用于内部或封闭测试轨道；开放测试和生产轨道需要先加入早期访问计划。
- **行驶中的音频**：Android Automotive OS 上的 beta 功能，允许视频应用在车辆行驶时播放音频。
- **Car App Quality 指南**：审查应用是否符合 Tier 3（*Car ready*）、Tier 2（*Car optimized*）或 Tier 1（*Car differentiated*）标准时，**必须**查看 [car app quality guidelines](references/android/docs/quality-guidelines/car-app-quality/index.md)。
- **Android Automotive OS 兼容模式**：兼容模式（`android.software.car.display_compatibility`）是部分车型上的系统特性，提供系统级返回入口、安全区域渲染、密度缩放，以及不透明的驾驶模式阻断（把活动置为 *Stopped*）。兼容模式只与支持 Android Automotive OS 的应用相关，对仅支持 Android Auto 的应用不适用。

## 代码库探查

在代码库中搜索 `AndroidManifest.xml`（Unity 项目里则是创建
`Assets/Plugins/Android/AndroidManifest.xml`）、
`res/xml/automotive_app_desc.xml`、`build.gradle`、`build.gradle.kts`
或 `gradle/libs.versions.toml` 文件。定位已有的视频播放器、
`MediaSession` 类、`requestedOrientation` 调用和 `WindowInsets`
处理逻辑。除非用户另有指示，添加依赖前先征求许可。

## 步骤 1：配置应用清单

在 `AndroidManifest.xml` 中声明应用类别、目标平台、硬件功能要求和
Activity 配置。

### 1.1：确定应用类别

- **视频应用**：视频应用**必须**在 `<application>` 上设置 `android:appCategory="video"`，并且**不得**包含带 `uses name="video"` 的 `app/src/main/res/xml/automotive_app_desc.xml`。
- **游戏**：游戏**必须**在 `<application>` 上设置 `android:appCategory="game"`。如果应用支持手柄输入，用 `android:required="false"` 声明 `android.hardware.gamepad`。
- **浏览器**：浏览器**必须**在导出的 `<activity>`（`android:exported="true"`）的 `MAIN` `<intent-filter>` 中包含 `<category android:name="android.intent.category.APP_BROWSER"/>`。

### 1.2：确定目标平台与硬件功能

- **Android Auto**：面向 Android Auto（Android 15+）的应用**必须**在 `AndroidManifest.xml` 文件的某个 `<intent-filter>` 中加入 `<category android:name="android.intent.category.CAR_LAUNCHER"/>`。除非用户指定了其他 intent filter，否则加到 `MAIN` `<intent-filter>` 中。如果应用只面向 Android Automotive OS，**绝不要**加这个类别。
- **Android Automotive OS**：面向 Android Automotive OS 的应用**必须**在 `AndroidManifest.xml` 文件中声明 `<uses-feature android:name="android.hardware.type.automotive" android:required="false"/>`（移动或多形态因子轨道用 `"false"`；只有在专用 Automotive OS 轨道发布时才用 `"true"`）。如果应用只面向 Android Auto，**绝不要**加这个 feature 标签。
- **非必需硬件功能（`DO-1`）**：为满足 Google Play 的 feature 要求与 `DO-1`，把不受支持的功能（`android.hardware.wifi`、`android.hardware.screen.portrait`、`android.hardware.screen.landscape`、`android.hardware.camera`）用 `android:required="false"` 声明，并去掉汽车上不存在的功能上的 `android:required="true"`。
- **显示连续性（`LS-C1`）**：在 `<activity>` 上为 `screenSize`、`smallestScreenSize`、`orientation`、`screenLayout` 和 `density` 配置 `android:configChanges`，这样切换到远端显示屏或从其上切回时，Activity 不会被重建，播放也不会卡顿。
- **兼容模式与驾驶分心**：声明兼容模式是可选的，只与支持 Android Automotive OS 的应用相关。**绝不要**为仅支持 Android Auto 的应用添加兼容模式。添加 `android.hardware.type.automotive` 会禁用兼容模式，除非在 `<application>` 中加入 `<meta-data android:name="android.software.car.display_compatibility" android:value="true"/>`。当应用在 `AndroidManifest.xml` 中声明 `android.software.car.display_compatibility` 时，应用**必须**在运行时检查 `PackageManager.hasSystemFeature("android.software.car.display_compatibility")`，并在其返回 `true` 时隐藏应用内重复的返回或关闭入口。驻车应用**不得**在任何 `<activity>` 上包含 `<meta-data android:name="distractionOptimized" android:value="true"/>`（`DD-2`、`DD-3`）。

## 步骤 2：提供返回导航与方向支持

### 2.1：添加应用内返回与关闭入口

Android Automotive OS 车辆不要求配备硬件或软件返回按钮，也不要求手势导航（`AN-1`）。
在每个非根屏幕上提供显式的 UI 返回与关闭控件，包括详情屏幕和全屏播放器：

- **如果 `AndroidManifest.xml` 未声明 `android.software.car.display_compatibility`**：无条件显示应用内的返回与关闭控件。
- **如果 `AndroidManifest.xml` 声明了带 `android:value="true"` 的 `android.software.car.display_compatibility`**：仅在 `PackageManager.hasSystemFeature("android.software.car.display_compatibility")` 返回 `false` 时显示应用内返回与关闭控件。

### 2.2：为运行时方向请求加防护

车载显示屏的方向是固定的。在固定竖屏的车载显示屏上请求横屏会导致黑边或
闪烁循环（`DO-1`）。移除硬编码的 `android:screenOrientation` 清单属性，并在设置
`requestedOrientation` 之前检查 `PackageManager.FEATURE_SCREEN_LANDSCAPE` 和
`PackageManager.FEATURE_SCREEN_PORTRAIT`。

## 步骤 3：适配系统栏与不规则显示挖孔

### 3.1：跟踪可控系统栏 insets

在 Android Automotive OS 上，OEM 可以把系统栏锁定为常显，以保证空调和车辆控制仍然可达（`AR-1`）。用 `OnControllableInsetsChangedListener` 跟踪可控 insets，只隐藏可控的系统栏，并对不可控的 `statusBars`、`navigationBars` 和 `displayCutout` insets 应用 `windowInsetsPadding`。

### 3.2：安全地渲染到不规则显示挖孔区域

要在曲面或非矩形车载显示屏上满足 Tier 1 标准 `AR-2`，
**绝不要**使用 `LAYOUT_IN_DISPLAY_CUTOUT_MODE_DEFAULT`（`0`）或
`LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES`（`1`）。用
`res/values-car-v30/integers.xml` 中的 `car` 资源限定符配置
`LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS`（`3`）或
`LAYOUT_IN_DISPLAY_CUTOUT_MODE_NEVER`（`2`）：

```xml
<integer name="windowLayoutInDisplayCutoutMode">3</integer>
```

<br />

用 `WindowInsets.safeDrawing` 保护交互式 UI、应用栏和可滚动列表。

## 步骤 4：满足驾驶分心与媒体播放要求

### 4.1：在生命周期切换时暂停播放，并阻止行驶中恢复播放

车辆开始移动时，系统会用阻断式遮罩覆盖驻车 Activity，并触发 `onPause`（在兼容模式车辆上还触发 `onStop`）。为满足 `DD-2`、`DD-3` 和 `MC-1`：

1. 使用 `androidx.lifecycle:lifecycle-runtime-compose` 中的 `LifecycleEventEffect`，在 `ON_PAUSE` 或 `ON_STOP` 时暂停播放。
2. 暴露一个 `MediaSession`（`androidx.media3:media3-session`），提供播放、暂停或停止命令以及条目元数据（`MC-1`），并在 `onCleared` 中释放它。
3. 在 `build.gradle.kts` 中加入 `useLibrary("android.car")`，把 `ExoPlayer` 包装在 `ForwardingSimpleBasePlayer` 中，监听 `CarUxRestrictionsManager`，在 `isRequiresDistractionOptimization` 变为 `true` 时暂停播放，并在 `getState` 中移除 `COMMAND_PLAY_PAUSE`，使外部 `MediaSession` 控件在行驶中无法恢复播放：

```kotlin
@UnstableApi
class CarAwarePlayer(context: Context) :
    ForwardingSimpleBasePlayer(ExoPlayer.Builder(context).build()) {
    private var shouldPreventPlay = false
    private var pausedByUxRestrictions = false
    private lateinit var carUxRestrictionsManager: CarUxRestrictionsManager

    init {
        if (context.packageManager.hasSystemFeature(PackageManager.FEATURE_AUTOMOTIVE)) {
            val car = Car.createCar(context)
            carUxRestrictionsManager =
                car.getCarManager(Car.CAR_UX_RESTRICTION_SERVICE) as CarUxRestrictionsManager
            shouldPreventPlay =
                carUxRestrictionsManager.currentCarUxRestrictions.isRequiresDistractionOptimization
            invalidateState()

            carUxRestrictionsManager.registerListener { restrictions: CarUxRestrictions ->
                shouldPreventPlay = restrictions.isRequiresDistractionOptimization
                if (!shouldPreventPlay && pausedByUxRestrictions) {
                    handleSetPlayWhenReady(true)
                    invalidateState()
                } else if (shouldPreventPlay && isPlaying) {
                    pausedByUxRestrictions = true
                    handleSetPlayWhenReady(false)
                    invalidateState()
                }
            }
        }
    }

    override fun getState(): State {
        val state = super.getState()
        return state.buildUpon()
            .setAvailableCommands(
                state.availableCommands.buildUpon()
                    .removeIf(COMMAND_PLAY_PAUSE, shouldPreventPlay)
                    .build()
            )
            .build()
    }

    override fun handleRelease(): ListenableFuture<*> {
        if (::carUxRestrictionsManager.isInitialized) {
            carUxRestrictionsManager.unregisterListener()
        }
        return super.handleRelease()
    }
}
```

<br />

### 4.2：支持行驶中的后台音频（可选 beta 功能）

由于这是可选的 beta 功能，除非用户要求，**绝不要**实现它。要实现该功能：

1. 在 `AndroidManifest.xml` 中声明 `<uses-feature android:name="com.android.car.background_audio_while_driving" android:required="false" />`，并一并声明 `FOREGROUND_SERVICE` 和 `FOREGROUND_SERVICE_MEDIA_PLAYBACK` 权限。
2. 用 `androidx.car.app:app` 中的 `CarFeatures.isFeatureEnabled(context, CarFeatures.FEATURE_BACKGROUND_AUDIO_WHILE_DRIVING)` 检查运行时的车辆支持情况。只在 `!isBackgroundAudioWhileDrivingSupported && restrictions.isRequiresDistractionOptimization` 时设置 `shouldPreventPlay`。
3. 把 `MediaSession` 和播放器放在导出的 `MediaSessionService` 中，并设置 `android:foregroundServiceType="mediaPlayback"`，然后在 UI 中用 `MediaController.Builder` 和 `buildAsync` 建立连接。

## 步骤 5：保护浏览器应用中的敏感数据

车辆是共享设备，因此浏览器**必须**阻止访问已保存的密码和支付方式，除非有配置文件锁保护（`SD-1`）。
在把密码或支付数据同步到车辆之前，浏览器**必须**提示用户进行身份验证，
并在车载屏幕上显示通知，说明其数据将被同步到车辆（`SD-2`）。

用 `KeyguardManager` 检查是否设置了 PIN、图案或密码；如果未设置，打开
`Settings.ACTION_SECURITY_SETTINGS`；然后只用 `BiometricPrompt` 配合
`BiometricManager.Authenticators.DEVICE_CREDENTIAL` 验证身份
（车辆没有生物识别硬件）：

```kotlin
val keyguardManager = context.getSystemService<KeyguardManager>()
val isDeviceSecure = keyguardManager?.isDeviceSecure == true
lateinit var biometricPrompt: BiometricPrompt

if (!isDeviceSecure) {
    context.startActivity(
        Intent(Settings.ACTION_SECURITY_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    )
} else {
    val promptInfo = BiometricPrompt.PromptInfo.Builder()
        .setTitle(context.getString(R.string.auth_title))
        .setSubtitle(context.getString(R.string.sync_data_to_car_notice))
        .setAllowedAuthenticators(BiometricManager.Authenticators.DEVICE_CREDENTIAL)
        .build()
    biometricPrompt.authenticate(promptInfo)
}
```

<br />

## 步骤 6：验证实现

用 `./gradlew assembleDebug` 构建应用。找出并修复所有构建错误。

## 实现后指引

实现完成后，向用户提供以下指引：

- 对于 Android Auto 应用，把应用安装到手机上，并使用 Desktop Head Unit（DHU）测试。
- 对于 Android Automotive OS，把应用安装到 Android Studio 中的 Android Automotive OS 模拟器上。
- 如果应用在目标平台上属于 beta 类别，提交到开放测试或生产轨道前必须先加入早期访问计划。
- 如果应用实现了 beta 的行驶中音频功能，提交到开放测试或生产轨道前必须先加入早期访问计划。
- 提交应用之前，按 car app quality guidelines 中的相关标准测试应用。

## 反模式

- **绝不要**在驻车应用的任何 `<activity>` 上包含 `<meta-data android:name="distractionOptimized" android:value="true"/>`，也不要在视频应用中包含带 `uses name="video"` 的 `res/xml/automotive_app_desc.xml`。
- **绝不要**假定 Android Automotive OS 上存在硬件或软件返回按钮。
- **绝不要**假定系统栏只在顶部和底部，或总能被隐藏。
- **绝不要**在 Android Automotive OS 上使用 `LAYOUT_IN_DISPLAY_CUTOUT_MODE_DEFAULT` 或 `LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES`。
- **绝不要**根据车速或挡位推断 UX 限制，而应从 `CarUxRestrictionsManager` 读取 `isRequiresDistractionOptimization`。
- **绝不要**在 Android Automotive OS 的浏览器应用中用 `BiometricPrompt` 搭配生物识别验证器（`BIOMETRIC_STRONG`、`BIOMETRIC_WEAK`）；只用 `DEVICE_CREDENTIAL`。
- 如果用户只要求支持 Android Automotive OS，**绝不要**添加 `CAR_LAUNCHER` intent 类别。
- 如果用户只要求支持 Android Auto，**绝不要**添加 `android.hardware.type.automotive` feature 标签。

## 最佳实践

- **必须**在不受支持的硬件功能（`wifi`、`screen.portrait`、`screen.landscape`、`camera`）上声明 `android:required="false"`，并通过检查 `FEATURE_SCREEN_LANDSCAPE` 和 `FEATURE_SCREEN_PORTRAIT` 来保护 `requestedOrientation` 调用（`DO-1`）。
- **必须**在非兼容模式时为 Android Automotive OS 提供应用内的返回与关闭入口（`AN-1`），并使用 `WindowInsets.safeDrawing` 和 `OnControllableInsetsChangedListener` 保护所有交互式 UI 与文本，避免被系统栏和显示挖孔遮挡（`AR-1`、`AR-2`）。
- **必须**在 UX 限制生效时暂停播放，并在行驶中从 `MediaSession` 中移除 `COMMAND_PLAY_PAUSE`，除非行驶中音频受支持且已启用（`DD-2`、`DD-4`、`MC-1`）。
- **必须**在保存、访问或同步浏览器密码或支付信息之前，要求配置文件锁验证，并在屏幕上显示同步声明（`SD-1`、`SD-2`）。
