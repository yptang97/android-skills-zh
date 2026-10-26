# 翻译术语表

本文件是 `android-skills-zh` 中译法的**唯一权威**。翻译或复核任何文件时，先查本表；已登记的术语必须严格沿用，不得同义替换。

## 使用说明

- 术语按语境判断：表格给出的是**默认译法**，若语境明显不同（例如 `Reference` 指某个具体 API 的参考文档，而非章节标题），可按语境处理，但仍需与本表不冲突。
- 「保留英文」区的词一律不译，包括大小写形态。
- 新增或修改术语：先在「待定区」提交，确认后移入「已决定」区并填写决定日期。

## 已决定的翻译

### 结构性与通用标题

| 英文 | 中文 | 备注 |
| --- | --- | --- |
| Prerequisites | 前置条件 | 固定 schema 标题 |
| Steps | 步骤 | 固定 schema 标题 |
| Step 1 / Step 2 | 步骤 1 / 步骤 2 | |
| Reference / References | 参考 / 参考资料 | 章节标题；`references/` 目录名不译 |
| Workflow / Workflows | 工作流 | |
| Overview | 概述 | |
| What it does | 功能说明 | 固定 schema 标题 |
| When to reach for it | 何时使用 | 固定 schema 标题 |
| It's working if | 生效表现 | 固定 schema 标题 |
| Where it fits | 适用范围 | 固定 schema 标题 |
| Common questions | 常见问题 | 固定 schema 标题 |
| Checklist | 检查清单 | |
| Troubleshooting | 故障排查 | |
| Pitfalls / Common pitfalls | 常见陷阱 | |
| Caveats | 注意事项 | |
| Summary / Wrap-up | 小结 | |
| Verification / Verify | 验证 | 动词与名词同译 |
| Best practices | 最佳实践 | |
| Anti-pattern / Anti-patterns | 反模式 | |
| Use case / Use cases | 使用场景 | |
| Guideline / Guidelines | 指南 | |
| Migration / Migrate | 迁移 | |
| Deprecated | 已废弃 | |
| Breaking change | 破坏性变更 | |
| Release notes | 版本说明 | |

### Android / Kotlin 技术术语

| 英文 | 中文 | 备注 |
| --- | --- | --- |
| application / app | 应用 | |
| module | 模块 | |
| dependency / dependencies | 依赖 | |
| build | 构建 | 动词与名词 |
| configuration / configure | 配置 | |
| implementation | 实现 | |
| setup | 配置 | 「环境搭建」语境可用「搭建」 |
| lifecycle | 生命周期 | |
| callback | 回调 | |
| coroutine | 协程 | |
| thread | 线程 | |
| state | 状态 | `State` 作为 API 类型时保留 |
| layout | 布局 | |
| theme | 主题 | |
| style | 样式 | |
| screen | 屏幕 | |
| window | 窗口 | |
| device | 设备 | |
| emulator | 模拟器 | |
| runtime | 运行时 | 指运行期环境时 |
| startup | 启动 | |
| jank | 卡顿 | |
| frame | 帧 | |
| performance | 性能 | |
| accessibility | 无障碍 | |
| annotation | 注解 | |
| parameter | 参数 | |
| exception | 异常 | |
| crash | 崩溃 | |
| log / logging | 日志 / 记录日志 | |
| trace | 跟踪 | Perfetto 语境可保留 trace |
| profiler | 性能分析器 | 产品名 Android Profiler 保留 |
| benchmark | 基准测试 | |
| warning | 警告 | |
| error | 错误 | |
| on-device | 端侧 | |
| backward compatibility | 向后兼容 | |
| opt-in / opt-out | 选用 / 退出 | |
| feature flag | 功能开关 | |
| rollout | 灰度发布 | |
| prompt | 提示词 | |
| tool | 工具 | |
| instruction | 指令 | |
| context window | 上下文窗口 | |
| subagent | 子代理 | |
| placeholder | 占位符 | |
| boilerplate | 样板代码 | |
| snippet | 代码片段 | |
| repository | 仓库 | |
| branch | 分支 | |
| commit | 提交 | |
| release | 发布 | 指版本时用「版本」 |
| upgrade / downgrade | 升级 / 降级 | |
| install | 安装 | |
| signature | 签名 | |
| permission | 权限 | |
| credential | 凭据 | |
| token | 令牌 | 认证语境；LLM 语境保留 Token |
| manifest | 清单 | `AndroidManifest.xml` 保留原名 |
| artifact | 构件 | |
| dependency injection | 依赖注入 | |
| preview | 预览 | |

## 保留英文（不译）

### 产品与品牌

`Android`、`Google`、`Google Play`、`Play`、`Jetpack`、`Jetpack Compose`、`Compose`、`Material 3`、`Wear OS`、`Android XR`、`Android TV`、`Android for Cars`、`Android Studio`、`Gemini`、`Antigravity`、`Claude Code`、`Codex`、`Firebase`、`CameraX`、`Media3`、`Glance`、`Hilt`、`KSP`、`KAPT`、`R8`、`ProGuard`、`AGP`、`Gradle`、`Kotlin`、`Perfetto`、`Baseline Profile`、`Macrobenchmark`、`LiteRT`、`ML Kit`、`AppFunctions`、`Navigation 3`、`edge-to-edge`、`insets`、`Insets`、`Composable`、`Flow`、`StateFlow`、`ViewModel`、`Intent`、`Service`、`BroadcastReceiver`、`ContentProvider`、`Activity`、`Fragment`、`APK`、`AAB`、`SDK`、`API`、`NDK`、`JNI`、`ADB`、`CI`、`PR`、`JSON`、`YAML`、`HTML`、`CSS`、`URI`、`URL`、`MCP`、`LLM`、`AI`、`agent`、`skill`、`skills`、`skill file`

### 结构性标识

目录名、文件名、`SKILL.md`、`references/`、`scripts/`、frontmatter keys（`name`、`description`、`license`、`metadata`、`author`、`last-updated`、`keywords`、`allowed-tools` 等）、JSON/YAML/TOML keys、包名、类名、函数名、命令与参数、环境变量名、Markdown 链接 URL。

## 待定区

| 英文 | 候选译法 | 状态 | 决定于 |
| --- | --- | --- | --- |
