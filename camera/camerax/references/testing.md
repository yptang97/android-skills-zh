相机功能的自动化测试出了名地困难，因为你
无法轻松伪造物理硬件、光照或运动。本指南提供
可靠、隔离的相机测试模式。

## 建立测试思路

| 挑战 | 常规做法 | 相机技术做法 |
|---|---|---|
| **框架** | `Mockito` 或 `MockK` | **用 Fake 代替 mock** |
| **断言** | `assertEquals`、`assertTrue` | **Google Truth、`assertThat`** |
| **环境** | 隐式环境 | **显式 `@RunWith` 注解** |
| **异步操作** | `Thread.sleep` | **显式 `timeoutMillis` 或 `IdlingResource`** |

*** ** * ** ***

## 遵循实现指南

### 用 Fake 代替 mock

**不要使用 Mockito。** 对 `ImageProxy` 或 `CameraInfo` 这类复杂、快速变化的接口
依赖 mock 会让测试变得脆弱。应当构建「Fake」
实现，用它们验证状态而不是行为。


```kotlin
// Create a Fake ImageProxy for ML Testing (Fakes over Mocks)
val fakeImage = FakeImageProxy(w = 640, h = 480)

// Feed the fake buffer into your analyzer
```

<br />

### 伪造相机能力

使用 `androidx.camera:camera-testing` 中的 `FakeAppConfig` 在测试中模拟
特定的硬件限制，例如一台没有闪光灯的设备。


```kotlin
// Use awaitInstance() extension function for coroutine-based provider retrieval
val cameraProvider = ProcessCameraProvider.awaitInstance(context)
```

<br />

### 使用 Truth 断言

使用 Google Truth 的 `assertThat`，而不是标准的 JUnit 断言。它
提供更易读的断言链和更有用的失败信息。

### 测试异步生命周期

相机初始化是异步的。使用 `IdlingResource` 确保
你的测试在断言之前等到 `UseCase` 已经绑定。

要测试异步生命周期，请使用以下模式：

1. 用 `CountDownLatch` 或 `IdlingResource` 包住 `ProcessCameraProvider` 的初始化。
2. 只有在 `cameraControl` 实例非 null 之后才做断言。

*** ** * ** ***

## 测试常见陷阱

- **资源泄漏** ：为避免「Camera in Use」错误，请在 `@After` 块中调用 `cameraProvider.unbindAll`。
- **「初始化不稳定」** ：相机测试在 CI 上经常失败，因为「Virtual Camera」预热太慢。请为首次初始化设置足够长的显式超时。
- **权限阻塞** ：要绕过系统权限对话框，请在 Espresso 测试中使用 `GrantPermissionRule`。
- **分辨率不匹配** ：在模拟器上测试时往往默认 640x480。请确保你的 `ResolutionSelector` 能正确处理这种低分辨率回退。
