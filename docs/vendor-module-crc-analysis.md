# 官方 vendor 模块 CRC 兼容性分析与黑屏根因(实测定论)

设备:Mi 11 Ultra (star),官方系统 HyperOS 2.0.7.0(官方内核 `5.4.274-qgki-g4dfe63e0666f`)。
分析对象:从官方线刷包 `star_images_OS2.0.7.0.UKACNXM`(super.img → vendor_a erofs)提取的全部 226 个 vendor 内核模块(`/lib/modules/5.4-gki/`)。

## 结论

1. **黑屏根因**:官方 vendor 的 `msm_drm.ko` 依赖 710 个符号,与本仓库内核(CRC 侧)仅约 1/3 匹配,包括 `module_layout` 本体不匹配,且缺失小米私有导出符号(如 `mi_display_pm_suspend_callback_set`)。模块加载即失败 → 无显示 → 黑屏;授权弹窗无法渲染 → adb 永远 `unauthorized`。
2. **vermagic 并非屏障**:`kernel/module.c` 的 `same_magic()` 在 MODVERSIONS 启用时只比较版本号之后的后缀(空格分隔),版本字符串本身不参与判定;兼容性完由符号 CRC 决定。
3. **CRC 面无法通过任何公开源码拼凑复现**:官方 274 私有内核在核心头文件/导出符号上叠有未公开改动,本文三个"最接近官方"的可构建基底,兼容率全部 ≤45%。

## 实测数据(对 14126 个符号引用的总量)

| 内核基底 | 配置 | MATCH | DIFF | MISSING | 兼容率 |
|---|---|---|---|---|---|
| 本仓库(274 基座 + KSU/SUSFS) | 社区 config | 6376 | 6895 | 855 | 45.1% |
| MiCode `star-r-oss`(5.4.61 全量官方源码) | 官方 274 `.config`(IKCONFIG 提取) | 6384 | 7347 | 395 | 45.2% |
| 纯上游 LTS `linux-5.4.274` | 官方 274 `.config` | 4926 | 6912 | 2288 | 34.9% |
| ACK `android-5.4`(公共分支) | — | 冻结于 5.4.63,无 274 提交,不可用 | | | |

配置本身不是瓶颈:5640 项官方 config 在 MiCode 61 树上保留 5372 项,值差异仅 3 项(编译器版本噪音);丢弃项绝大多数为仅存在于私有堆栈的平台符号(如 `CONFIG_SCHED_WALT`、`CONFIG_MIGT`、`CONFIG_SF_BINDER`、`CONFIG_DEBUG_POWER_MI` 相关实现)。

`init_rwsem` 一类 CRC 表面上"看起来不同"的项实为十六进制前导零格式差异(数值相等)。

## 工程对策

不依赖任何 vendor 模块,把关键驱动**内建进内核**(`CONFIG_DISPLAY_BUILD=y` 内建显示栈等),CRC 与本内核自洽。WLAN/音频/相机等模块后续同样内建化或随包注入本仓库自产 `.ko`。

## 复现工具

`module-crc-check.py`(本目录):解析 `.ko` 的 `__versions` 表(`struct modversion_info`:aarch64 上 crc 为 `u64` + 56 字节符号名),与 `Module.symvers` 数值化比对,输出 MATCH/DIFF/MISSING 分类。

## 2026-10 复核（官方 OTA 实机包）

改用卡刷 OTA 包（`star-ota_full-OS2.0.7.0.UKACNXM`，payload → EROFS vendor.img）复核官方模块清单：

- `/vendor/lib/modules/`：**112 个** `.ko`，vermagic `5.4.274-qgki-g4dfe63e0666f`，`modules.load` 112 条 —— 这是 ROM 实机**真正加载**的集合（此前分析的 226 个属 `5.4-gki/` 旧集，vermagic 无 `-qgki`，ROM 不加载）。
- 结论不变：vermagic 版本部分与官方 release 一致，但 CRC 仍锚定私有树（官方构建提交 `4dfe63e0666f`、toolchain `clang 11.0.2`），公开源码树无法对齐。运行时以 `dmesg` 的 insmod 结果为最终判据。
- vendor 模块完整清单与 vermagic 表见 [`firmware-notes.md`](firmware-notes.md)；内核配置侧的官方对齐分析见 [`stock-config-delta.md`](stock-config-delta.md)。
