Gradle 运行期间给出简短的进度更新是可以的；最终消息只有报告。所有命令都在项目根目录下运行；`<skill_dir>` 是这个 skill 的目录。

## 1. 配置

对于低于 9.3.0 的 AGP 版本（AGP \< 9.3.0），把本地 R8 副本更新到最新版本，以启用 Configuration Analyzer 报告生成。如果上次运行残留了 `tmp/r8analysis/settings.gradle.kts.orig`（或 `settings.gradle.orig`），先还原它（步骤 8）。如果 `settings.gradle` 或 `settings.gradle.kts` 已经把 `com.android.tools:r8` 9.4.34 或更高版本加入 classpath，就跳过这一步的其余内容。

这一处临时改动是这个 skill 唯一的文件编辑。交互运行时，在修改 `settings.gradle` 或 `settings.gradle.kts` 之前先征得用户确认（非交互运行时跳过确认）。如果用户拒绝，或要求你不要修改构建文件或源文件，就不要编辑该文件，并跳过步骤 2 到 8：不带评分地报告规则层面和构建文件层面的发现，并用一句话说明衡量这些指标需要这处临时 R8 改动。绝不要把 `N/A%` 当作评分输出。

编辑之前先备份文件（Groovy 用 `settings.gradle`）：

    mkdir -p tmp/r8analysis
    cp settings.gradle.kts tmp/r8analysis/settings.gradle.kts.orig

在项目的 `settings.gradle` 或 `settings.gradle.kts` 文件中，把 R8 工具加入 classpath 依赖。

    pluginManagement {
        buildscript {
            repositories {
                google()
                mavenCentral()
            }
            dependencies {
                // Update to a more recent R8 version.
                classpath("com.android.tools:r8:9.4.34")
            }
        }
    }

## 2. 生成 proto

报告和文件必须生成在 `{project_root}/tmp/r8analysis`。如果该目录不存在，就创建它。例如：

    mkdir -p "$PWD/tmp/r8analysis"

## 3. 删除已有文件

为了确保这次调用不会使用之前运行的数据，删除 `{project_root}/tmp/r8analysis` 中的中间文件 `keepruleradius.json` 和 `analysis_result.txt`，以及其中的 proto 文件。运行以下 Bash 命令：

    rm -f tmp/r8analysis/keepruleradius.json tmp/r8analysis/analysis_result.txt
    find tmp/r8analysis -name '*.pb' -delete

## 4. 生成 Configuration Analyzer 报告

用系统属性 `-Dcom.android.tools.r8.dumpkeepradiustodirectory=$PWD/tmp/r8analysis` 对 skill 步骤 2 中找到的模块和变体运行 R8，以生成 Configuration Analyzer 报告。该属性不是 Gradle 任务的输入，所以需要 `--rerun` 和 `--no-build-cache`，才能让 R8 在 release 构建已是最新或已缓存时仍然运行（例如模块 `app`、变体 `release` 对应的 `:app:minifyReleaseWithR8`）：

    ./gradlew :<module>:minify<Variant>WithR8 --rerun --no-build-cache \
      -Dcom.android.tools.r8.dumpkeepradiustodirectory=$PWD/tmp/r8analysis

## 5. 转换为 JSON

要把 `{project_root}/tmp/r8analysis` 中生成的 protobuf 文件转换为 JSON，运行以下脚本。JSON 必须生成在 `{project_root}/tmp/r8analysis`。该脚本会导入 `keep_radius_pb2.py`，它与脚本一起放在 `<skill_dir>/scripts/` 中。

    python3 <skill_dir>/scripts/convert_pb_to_json.py \
      tmp/r8analysis \
      tmp/r8analysis/keepruleradius.json

## 6. 分析

对生成的 JSON 运行以下分析脚本，得到 keep 规则的影响并对其排序。

    python3 <skill_dir>/scripts/analyze.py tmp/r8analysis/keepruleradius.json

输出 `analysis_result.txt`，其中包含评分和规则影响。

## 7. 报告高影响规则

步骤 6 中的 `analyze.py` 脚本已经算出了影响最大的规则、被包含的规则和完全相同的规则，记录了每条规则的来源，并把它们写入 `tmp/r8analysis/analysis_result.txt`。你必须直接使用这些数据。

## 8. 还原 settings 改动

如果你在步骤 1 中修改了 `settings.gradle` 或 `settings.gradle.kts`，就在步骤 6 之后还原它；任何一步失败时也要立即还原（Groovy 用 `settings.gradle`）：

    mv tmp/r8analysis/settings.gradle.kts.orig settings.gradle.kts
