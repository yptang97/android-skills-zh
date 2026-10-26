关于耗电、电源轨、网络流量和唤醒锁的专家提示。
keywords:
- power
- battery
- wakelock
- suspend
- network
- modem
- bluetooth

## - 耗电

- 排查整体耗电时，先查询 `power_rails` 轨道，并对每条电源轨累加能耗（`power_ma * duration`）。
- 要确认设备在熄屏期间是否正常休眠，查询 `suspend_state` 轨道；如果「suspended」状态的时间不足，说明存在保持唤醒的问题。
- 要找出设备无法进入休眠的根本原因，查询 `kernel_wakelock` 轨道，并按每个唤醒锁汇总总时长。
- 如果排名靠前的内核唤醒锁名称中包含 `bt_` 或 `bcm`（例如 `bt_host_wake`），就把它的时间与 `bluetooth_scan_results` 轨道中的事件做交叉比对。
- 如果 `power_rails` 中的 modem 电源轨显示高能耗，查询 `network_packets` 表，按 UID 汇总流量，从而定位到具体应用。
- 分析来自共享 UID 的网络流量时，利用与网络数据包关联的 `socket_tag` 做更细粒度的归因。
- 把影响折算成统一的能量单位（例如毫瓦时，mWh），以便比较不同问题的严重程度。
