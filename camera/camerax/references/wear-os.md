为 Wear OS 开发相机功能，很少是围绕手表自己的镜头——如果它真有镜头的话。这件事几乎总是关于创建一个**远程取景器**来控制手机的相机。

## Wear OS 远程控制的思维方式

| 特性 | 手机相机应用 | Wear OS 遥控应用 |
|---|---|---|
| **屏幕** | 矩形（大） | **圆形，尺寸小于 2 英寸** |
| **连接方式** | 本地硬件 | **Bluetooth 或 Wi-Fi 数据层 API** |
| **延迟** | 直接连接，低于 20 ms | **走网络，100 ms 到 500 ms** |
| **交互** | 多点触控手势 | **旋转输入或单击** |

*** ** * ** ***

## 遵循实现指南

### 圆形 UI 的挑战

Wear OS 设备通常是圆形的。标准的矩形布局会裁掉角落的按钮。

遵循以下蓝图建议：

- 使用 `Horologist` 或 `Wear Compose` 库。
- 列表使用 `ScalingLazyColumn`，让条目始终处于圆形显示区的“安全区”内。
- **预览缩放**：裁切矩形手机取景器的中心区域，使其适配圆形手表屏幕。

### 串流取景器画面

你无法通过 Bluetooth 发送原始的 60 fps 码流。要压缩并限流。


```kotlin
// Example: Sending a viewfinder frame to the watch
val bitmap = previewView.bitmap // Capture current frame
if (bitmap != null) {
    val compressed = compressToJpeg(bitmap, quality = 50)
    val request = PutDataMapRequest.create("/camera/preview").apply {
        dataMap.putAsset("image", Asset.createFromBytes(compressed))
    }
    Wearable.getDataClient(context).putDataItem(request.asPutDataRequest())
}
```

<br />

**优化**：把手表预览限制在 **10-15 fps**，以节省电量和带宽。

### 远程触发与同步

对“拍照”或“切换相机”这类低延迟命令，使用 `MessageClient`。


```kotlin
// Watch sends a trigger to the phone
Wearable.getMessageClient(context).sendMessage(nodeId, "/camera/capture", null)
```

<br />

### 支持旋转输入

在支持该功能的设备上，使用物理表冠（旋转输入）来控制**变焦**或**曝光**。

*** ** * ** ***

## Wear OS 常见陷阱

- **角落被裁切**：把**关闭**按钮放在方形布局的右上角，会导致在圆形手表显示区上无法点按该按钮。
- **电量消耗**：持续的 Bluetooth 数据传输、取景器同步，会消耗手表电量。手机屏幕关闭时，主动关闭遥控应用。
- **节点发现**：手机可能同时连接多个“节点”（手表、耳机或平板）。确保你的 `CapabilityClient` 过滤出具体的 `camera_remote_host` 能力。
- **断连处理**：如果手表断开连接，手机相机必须停止高功耗预览以节省电量。
