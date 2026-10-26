许多 Android API 在设计时就考虑了不可变性，以避免异步环境中的竞争条件。不过，这常常让习惯可变 builder 模式的开发者出错。

## 常见不可变类

以下类的流式 API 会**返回新实例**。你必须重新赋值给变量。

| 类 | 返回新实例的方法 | 未重新赋值的结果 |
|---|---|---|
| `PendingRecording` | `withAudioEnabled`, `asPersistentRecording` | 音频不会被录制。 |
| `ImageCapture.Builder` | `setTargetRotation`, `setTargetResolution` | 输出方向错误。 |
| `Recorder.Builder` | `setQualitySelector`, `setExecutor` | 录制使用默认画质。 |
| `Viewport.Builder` | `setScaleType`, `setLayoutDirection` | 取景器被拉伸。 |

## 使用标准模式

### CameraX 视频录制

要配置视频录制，使用以下代码：


```kotlin
// WRONG
run {
  val pending = recorder.prepareRecording(context, opts)
  pending.withAudioEnabled() // This returns a new instance which is ignored
  val active = pending.start(exec, listener)
}

// CORRECT
run {
  val pending = recorder.prepareRecording(context, opts)
      .withAudioEnabled() // Chaining works
  val active = pending.start(exec, listener)
}

// ALSO CORRECT
run {
  var pending = recorder.prepareRecording(context, opts)
  pending = pending.withAudioEnabled() // Reassignment
  val active = pending.start(exec, listener)
}
```

<br />

### Viewport 构造

要配置 viewport，使用以下代码：


```kotlin
val viewport = ViewPort.Builder(Rational(width, height), displayRotation)
    .setScaleType(ViewPort.FILL_CENTER)
    .build()
```

<br />
