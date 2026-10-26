> **前置条件：** 确保 `$SKILL_ROOT` 已按
> `$SKILL_ROOT/references/env_setup.md` 完成初始化。

## 把随附的 `trace_processor` 加入 `PATH`

这个 skill 在
`$SKILL_ROOT/references/perfetto/bin/trace_processor` 提供了一个 `trace_processor` 包装脚本。让它在本会话中可被调用：

    # some installs lose the exec bit
    chmod +x "$SKILL_ROOT/references/perfetto/bin/trace_processor"
    export PATH="$SKILL_ROOT/references/perfetto/bin:$PATH"
    trace_processor --version                   # smoke test

完成之后，本 skill 中所有裸写的 `trace_processor ...` 命令都能按原样工作。如果每条命令都在新的 shell 里执行，就在该命令里重复 `export` 那一行。在 Windows 上，跳过 `PATH` 设置，改为用
`python "$SKILL_ROOT/references/perfetto/bin/trace_processor" ...` 调用。

说明：

- 第一次调用会把预编译的原生二进制文件（按宿主平台挑选合适的那个）下载到 `~/.local/share/perfetto/prebuilts/` 并缓存；只有首次调用要承担下载开销。
- **不要**下载、符号链接或用 `find` 查找另一个 `trace_processor` 或 `trace_processor_shell`——包装脚本固定到本 skill 的发布版本。
- 如果用户环境有自己强制的 `trace_processor`（Google 内部环境、OEM 构建环境、CI 镜像），优先使用该团队特有的配置。
