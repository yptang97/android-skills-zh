## 1. 由宿主求值的本地状态（`rememberMutableRemoteInt` 与 `valueChange`）

Wear OS 小组件渲染在系统宿主进程内。标准的 Jetpack
Compose 内存状态（`mutableStateOf`、`mutableIntStateOf`）在手表界面上被点击时无法触发重组。

用 `rememberMutableRemoteInt(initialValue)` 分配一个远程状态寄存器，
然后在宿主播放器内用
`valueChange(remoteInt, remoteInt + delta)` 直接修改它，无需 IPC 往返：

- 把 `remoteInt.toRemoteString` 当作 `RemoteInt` 上的**成员函数**调用（例如 `"Label: ".rs + remoteInt.toRemoteString`）。**严禁**把 `toRemoteString` 作为顶层扩展导入。

```kotlin
import androidx.compose.remote.creation.compose.action.valueChange
import androidx.compose.remote.creation.compose.layout.RemoteAlignment
import androidx.compose.remote.creation.compose.layout.RemoteArrangement
import androidx.compose.remote.creation.compose.layout.RemoteColumn
import androidx.compose.remote.creation.compose.layout.RemoteComposable
import androidx.compose.remote.creation.compose.layout.RemoteRow
import androidx.compose.remote.creation.compose.modifier.RemoteModifier
import androidx.compose.remote.creation.compose.modifier.fillMaxSize
import androidx.compose.remote.creation.compose.state.rdp
import androidx.compose.remote.creation.compose.state.rememberMutableRemoteInt
import androidx.compose.remote.creation.compose.state.rs
import androidx.compose.runtime.Composable
import androidx.wear.compose.remote.material3.RemoteButton
import androidx.wear.compose.remote.material3.RemoteText

@RemoteComposable
@Composable
fun StatefulAdjusterSection() {
    val value = rememberMutableRemoteInt(0)

    RemoteColumn(
        modifier = RemoteModifier.fillMaxSize(),
        verticalArrangement = RemoteArrangement.Center,
        horizontalAlignment = RemoteAlignment.CenterHorizontally,
    ) {
        // Call value.toRemoteString() as a member method (no extension import)
        RemoteText(text = "Value: ".rs + value.toRemoteString())
        RemoteRow(horizontalArrangement = RemoteArrangement.spacedBy(8.rdp)) {
            RemoteButton(onClick = valueChange(value, value - 1)) {
                RemoteText("-".rs)
            }
            RemoteButton(onClick = valueChange(value, value + 1)) {
                RemoteText("+".rs)
            }
        }
    }
}
```

## 2. 启动 Activity 与后台刷新回调（`pendingIntentAction`）

用 `pendingIntentAction` 在点击时启动 `Activity`（例如 `MainActivity`），
或派发后台 `BroadcastReceiver` 刷新：

- 始终传入 `(Context) -> PendingIntent` lambda：`pendingIntentAction { ctx -> PendingIntent.getActivity(...) }` 或 `pendingIntentAction { ctx -> PendingIntent.getBroadcast(...) }`。
- 把返回的 `Action` 附加到 `RemoteButton(onClick = action)`，或通过 `RemoteModifier.clickable(action)` 附加到任意容器。
- 在 `BroadcastReceiver` 中调用 `goAsync`，并调用 `widget.triggerUpdateAll(context)` 刷新所有活动的小组件实例。使用清单广播时，还需在 `AndroidManifest.xml` 中注册 `<receiver>`。

```kotlin
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.compose.remote.creation.compose.action.pendingIntentAction
import androidx.compose.remote.creation.compose.layout.RemoteColumn
import androidx.compose.remote.creation.compose.layout.RemoteComposable
import androidx.compose.remote.creation.compose.modifier.RemoteModifier
import androidx.compose.remote.creation.compose.modifier.clickable
import androidx.compose.remote.creation.compose.modifier.fillMaxSize
import androidx.compose.remote.creation.compose.state.rs
import androidx.compose.runtime.Composable
import androidx.wear.compose.remote.material3.RemoteButton
import androidx.wear.compose.remote.material3.RemoteText
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@RemoteComposable
@Composable
fun InteractiveHeaderAndRefreshSection(
    activityClass: Class<*>,
    receiverClass: Class<out BroadcastReceiver>,
) {
    val launchActivityAction = pendingIntentAction { ctx ->
        val intent = Intent(ctx, activityClass).apply {
            flags =
                Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        PendingIntent.getActivity(
            ctx,
            100,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    val backgroundRefreshAction = pendingIntentAction { ctx ->
        val intent = Intent(ctx, receiverClass).apply {
            action = ACTION_REFRESH_WIDGET
        }
        PendingIntent.getBroadcast(
            ctx,
            101,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    RemoteColumn(modifier = RemoteModifier.fillMaxSize()) {
        RemoteText(
            text = "Open App".rs,
            modifier = RemoteModifier.clickable(launchActivityAction),
        )
        RemoteButton(onClick = backgroundRefreshAction) {
            RemoteText(text = "Refresh".rs)
        }
    }
}

const val ACTION_REFRESH_WIDGET = "com.example.wear.ACTION_REFRESH_WIDGET"

class WidgetUpdateReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                MyWidget().triggerUpdateAll(context)
            } finally {
                pendingResult.finish()
            }
        }
    }
}
```