---
name: media3-cast-integration
description: 使用 Jetpack Media3 在 Android 应用中实现 Google Cast 支持。涵盖添加构建依赖、更新清单（manifest）、配置 OptionsProvider，以及在基于 Compose 和基于 View 的 UI 中管理用于播放的 CastPlayer 或 RemoteCastPlayer。在添加 Cast 功能或从旧式 Cast SDK 迁移到 Media3 Cast 时使用。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - Android
  - Media3
  - Cast
  - Integration
  - Migration
  - ExoPlayer
  - MediaSession
  - Jetpack Media3
---

## 前置条件

- Jetpack Media3 版本必须为 `>= 1.9.0`。更低版本不支持 Cast。

## 术语表

- **`CastPlayer`** ：Media3 `Player`，同时控制本地和远端 Cast 设备上的播放。
- **`RemoteCastPlayer`** ：与 Cast 接收端通信的 Media3 `Player`，仅用于远端播放。
- **Google Cast SDK**：处于维护模式的旧式投屏 SDK，已被 Jetpack Media3 取代。
- **`OptionsProvider`** ：为初始化 GMS `CastContext` 提供配置选项的接口。

## 通用指南

- 旧式 [Google Cast SDK](https://developers.google.com/cast) 处于维护模式。
- 对于新的 Cast 配置：
  - 你必须使用 [Jetpack Media3 Cast](references/android/media/media3/cast/index.md)。
  - 除非明确要求，否则不得使用旧式 Cast SDK。

## 步骤 1：配置依赖

要完成这一步，你**必须**确保以下内容：

- 在应用级构建文件中声明 `media3-cast` 依赖，版本为 1.9.0 或更高。

      implementation("androidx.media3:media3-cast:1.11.1")

- 确保所需的 Media3 依赖存在：

  - `androidx.media3:media3-exoplayer`
  - `androidx.media3:media3-session`
  - `androidx.media3:media3-ui-compose`
- 如果应用使用旧式 View，添加 `media3-ui`。

- 在所有 Media3 依赖中强制使用相同版本。

- 以 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)中「Add build dependencies」一节的配置为准。

- **对于尚无 Cast 集成的应用：**

  - 确认旧式 Cast SDK（`libs.play.services.cast.framework`）不存在。
- **如果是从旧式 Cast SDK 迁移：**

  - 先添加 Media3 Cast 依赖。
  - 此阶段保持现有旧式依赖不动，以避免编译错误。

## 步骤 2：更新清单

要完成这一步，你**必须**确保以下内容：

- 在清单的 `<application>` 标签内声明 Cast options provider。
- 默认使用 `DefaultCastOptionsProvider`。参见 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)中的「OptionsProvider」一节。
- 仅在明确要求时声明自定义 `OptionsProvider`。参见[自定义 CastOptions](references/android/media/media3/cast/customize-castoptions.md)。
- 确保存在 `INTERNET` 权限。不要添加任何不必要的权限。
- **如果是从旧式 Cast SDK 迁移：**
  - 不要删除现有的自定义 options provider 文件或清单条目。

## 步骤 3：实现播放器与 service

### 架构基线

在集成 Media3 Cast 之前，现有应用通常采用以下两种配置之一：

- **仅本地播放：** 只使用 Media3 `ExoPlayer` 支持本地播放。
- **旧式 Cast 配置：** 本地播放使用 `ExoPlayer`，远端播放则在旧式 `RemoteMediaClient` 之上套一层 `Player` 包装。UI 与 `MediaSession` 交互，`MediaSession` 与 `ForwardingPlayer` 交互，后者最终把控制路由到本地或远端播放。

要完成这一步，你**必须**确保以下内容：

- 在应用的 `MediaSessionService`（或 `MediaLibraryService`）的 `onCreate()` 方法中初始化 `ExoPlayer` 和 `CastPlayer`。
- 默认使用 `CastPlayer`，除非明确要求 `RemoteCastPlayer`。参见 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)中的「Build a CastPlayer」一节。
- 对于 `CastPlayer`，把实例直接传给 `MediaSession.Builder`。
- 替换所有旧式的转发播放器包装。
- 暂时不要删除旧式类文件，以免迁移期间出现编译错误。

### 进阶：`RemoteCastPlayer`

- 仅在用户明确要求时使用 `RemoteCastPlayer`。
- 用 `localPlayer` 初始化 `MediaSession`，并在 `RemoteCastPlayer` 上设置 `SessionAvailabilityListener`，以便在 Cast 会话可用性变化时转移播放状态：

    class PlaybackService : MediaSessionService() {
      private var mediaSession: MediaSession? = null
      private lateinit var localPlayer: ExoPlayer
      private lateinit var remotePlayer: RemoteCastPlayer

      override fun onCreate() {
        super.onCreate()

        localPlayer = ExoPlayer.Builder(this).build()
        remotePlayer = RemoteCastPlayer.Builder(this).build()
        mediaSession = MediaSession.Builder(this, localPlayer).build()

        remotePlayer.setSessionAvailabilityListener(
          object : SessionAvailabilityListener {
            override fun onCastSessionAvailable() {
              transferPlaybackState(localPlayer, remotePlayer)
            }

            override fun onCastSessionUnavailable() {
              transferPlaybackState(remotePlayer, localPlayer)
            }
          }
        )
      }

      private fun transferPlaybackState(previousPlayer: Player, newPlayer: Player) {
        if (previousPlayer.mediaItemCount > 0) {
          val transferStateBuilder = PlayerTransferState.builderFromPlayer(previousPlayer)
          if (previousPlayer.playbackState == Player.STATE_ENDED ||
              previousPlayer.currentPosition == C.TIME_END_OF_SOURCE) {
            transferStateBuilder.setCurrentMediaItemIndex(0)
            transferStateBuilder.setCurrentPosition(0)
          }
          transferStateBuilder.build().setToPlayer(newPlayer)
        }

        previousPlayer.stop()
        previousPlayer.clearMediaItems()
        newPlayer.prepare()
        mediaSession?.setPlayer(newPlayer)
      }
    }

## 步骤 4：配置 UI

### 基于 Compose 的 UI

要完成这一步，你**必须**确保以下内容：

- 参见 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)中的「Add a MediaRouteButton Composable to the Player」一节，了解 Compose 集成指南。
- 使用 `androidx.media3.cast` 包中的 [`MediaRouteButton` composable](https://developer.android.com/reference/kotlin/androidx/media3/cast/MediaRouteButton.composable)。
- 不要在 Compose UI 层级中使用 `AndroidView`。
- 把 `MediaRouteButton` 放在播放控件旁边的区域。不要把它藏在系统 UI 之后。
- 不要为自定义播放器 UI 使用 `PlayerSurface`。使用 Material3 的 [`Player`
  composable](https://developer.android.com/reference/kotlin/androidx/media3/ui/compose/material3/Player.composable)。
- 在播放位置切换时强制重组，以确保 UI 同步。对 `DeviceInfo` 变化使用 key
  约束：

      @OptIn(UnstableApi::class)
      @Composable
      fun MainScreen() {
         val player = rememberMediaController()
         val deviceInfo = rememberDeviceInfo(player)
         player?.let { activePlayer -> key(deviceInfo) { PlayerScreen(player = activePlayer) } }
      }

      @Composable
      private fun rememberMediaController(): Player? {
         // Logic to connect MediaController to MediaSession and release it
      }

      @Composable
      private fun rememberDeviceInfo(player: Player?): DeviceInfo? {
         var deviceInfo by remember(player) { mutableStateOf(player?.deviceInfo) }
         DisposableEffect(player) {
             val activePlayer = player ?: return@DisposableEffect onDispose {}
             deviceInfo = activePlayer.deviceInfo
             val listener = object : Player.Listener {
                 override fun onDeviceInfoChanged(info: DeviceInfo) {
                     deviceInfo = info
                 }
             }
            activePlayer.addListener(listener)
            onDispose { activePlayer.removeListener(listener) }
         }
         return deviceInfo
      }

### 基于 View 的 UI

要完成这一步，你**必须**确保以下内容：

- 对于基于 View 的 UI 配置，参见 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)中的「Add UI elements」一节。
- 投屏 Activity 必须继承 `AppCompatActivity` 或 `FragmentActivity`，并使用 `Theme.AppCompat` 的派生主题。
- 如果要把 `MediaRouteButton` 加到 options 菜单，确保 `AppCompat` 主题有可见的 `ActionBar`。
- 把 `CastButtonFactory` 的所有实例和 import 替换为 `MediaRouteButtonFactory`。
- 在 `onDeviceInfoChanged` 事件发生时重新绑定 `PlayerView.player` 引用，以防黑屏或 UI 冻结：

      private val playerListener: Player.Listener =
        object : Player.Listener {
          override fun onDeviceInfoChanged(deviceInfo: DeviceInfo) {
            // Resetting to null bypasses PlayerView.setPlayer()'s instance equality check
            // (this.player == player), forcing it to re-bind the video surface to the controller.
            playerView.player = null
            playerView.player = controller
          }
        }

- **迁移到 Compose：**

  - 不要用 `AndroidView` 包装旧式 `PlayerView`。
  - 按 [CastPlayer 快速入门](references/android/media/media3/cast/create-castplayer.md)实现 Material3 的 [`Player` composable](https://developer.android.com/reference/kotlin/androidx/media3/ui/compose/material3/Player.composable)和 [`MediaRouteButton` composable](https://developer.android.com/reference/kotlin/androidx/media3/cast/MediaRouteButton.composable)。
  - 移除旧式 XML 布局声明、菜单文件和 View 组件引用。

## 步骤 5：清理旧式 Cast SDK 代码

> [!WARNING]
> **Warning:** 不要直接执行清理。只有在用户明确要求时才移除旧式文件和依赖。

要完成这一步，你**必须**确保以下内容：

- 移除旧式 GMS Cast SDK（`libs.play.services.cast.framework`）和 MediaRouter（`libs.androidx.mediarouter`）依赖。
- 如果采用 `DefaultCastOptionsProvider`，删除自定义 `OptionsProvider` 类和清单条目。
- 如果存在旧式 `MediaTransferReceiver` 的清单声明，移除它。
- 移除对旧式 Cast SDK 组件的所有引用，例如旧式辅助包装、转发播放器和 `RemoteMediaClient` 接口。
- 如果迁移到 Compose 已完成，删除旧式 View XML 布局、菜单文件和 `PlayerView` 的引用。
