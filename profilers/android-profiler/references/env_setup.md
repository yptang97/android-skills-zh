## 设置 `$SKILL_ROOT`

每个会话设置一次 `$SKILL_ROOT`。

本 skill 引用的每个文件——工作流 markdown、参考文档、辅助脚本和下载的依赖——都以 `$SKILL_ROOT/...`
的形式书写，相对于 **skill 根目录**（存放本 skill 的 `SKILL.md` 的目录）。
把它设置为你加载 `SKILL.md` 的那个目录的绝对路径，只设一次：

    # Substitute with the directory the SKILL.md lives in.
    export SKILL_ROOT="/absolute/path/to/skills/profilers/android-profiler"
