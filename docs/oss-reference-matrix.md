# MiCode star-r-oss 参考对照（stock 私有配置的公开源码可得性）

参考仓库:MiCode/Xiaomi_Kernel_OpenSource `star-r-oss` 分支(Linux 5.4.61,Mi 11 Ultra 官方 Android 11 时代开源内核,本地克隆校验于 2026-10)。

本树(5.4.274 基座 + ReSukiSU/SUSFS)与官方 2.0.7.0 内核(`5.4.274-g4dfe63e0666f`)的配置差分见 [`stock-config-delta.md`](stock-config-delta.md)。本文回答:差分里 `stock_only` 的小米私有 Kconfig,在 star-r-oss 里有没有可移植的源码?

## 可得性矩阵(实测 grep)

| 私有配置 | star-r-oss | 结论 |
| --- | --- | --- |
| `MILLET` / `MIHW`(`drivers/mihw` 组) | ✅ `drivers/mihw/`(millet_binder/core/hs/pkg/sig、oem_cgroup、uapi) | 可移植,但耦合 binder 钩子,MILLET 属 MiUI 功耗统计;官方 2.0.7.0 实机 `modules.load` 112 模块集中无此模块需求,当前阶段不移植 |
| `OEM_KERNEL`(`init/Kconfig` + `drivers/mihw/oem_kernel.c`) | ✅ | 同上(mihw 组),暂不移植 |
| `DEBUG_POWER_MI`(pinctrl 调试) / `DEBUG_POLICY_STATUS` / `FASTBOOT_CMD_CTRL_UART` / `GPIO_TESTING_MODE` | ✅ | 调试类,与开机问题无关联,暂不移植 |
| `EROFS_FS_CLUSTER_PAGE_LIMIT` | ✅ 参数存在于 `fs/erofs/Kconfig` | 星桥参数,非功能缺失;后续需要时单独回移 |
| `XLOGCHAR`、`MI_CNSS_STATISTIC`、`MI_RECLAIM`、`BOOTUP_RECLAIM`、`CAM_RECLAIM`、`MIGT`、`SF_BINDER`、`MI_UFS_FFU`、`UFS_WB`、`MIUI_ZRAM_MEMORY_TRACKING`、`MI_MEMORY_SYSFS`、`PASSTHROUGH_SYSTEM`、`PACKAGE_RUNTIME_INFO`、`PERF_CRITICAL_RT_TASK`、`F2FS_CP_OPT`、`QCOM_MINIDUMP_ENCRYPT`、`TOUCHSCREEN_ST_FTS_V521_SPI_K2` | ❌ 均不在 oss 中（5.4.61 时代尚未发布或属更私密分支） | 无公开源码可依；同 [`vendor-module-crc-analysis.md`](vendor-module-crc-analysis.md) 结论 —— CRC 面无法拼凑，**放弃模块化复用，按需内建/等效替代** |

另确认:官核 2.0.7.0 交付的 `CONFIG_CLD=y`(stock WLAN 内建)与 oss 的 `CONFIG_QCA_CLD_WLAN=m` 结构差异说明官方私有 WLAN 源码也一样不可得 —— 与"内建 WLAN/audio/camera"路线(next steps)自洽。

## 移植策略定论

1. **以"按效果内建"替换"按源码复现 private"**:哪些外设在真机测试中异常,就把对应驱动编进内核(技术包 audio/camera + qca_cld3_wlan 源码均在本树)。
2. **mihw 组(millet/oem_kernel)仅在出现功耗/卡顿类回归时再移植**,首次移植先以 `m` 模块化兜底,便于回退。
3. oss 的 **Kconfig/defconfig 差异**只作参考,不直接采用(基线代差 213 个 patchlevel,其 `arch/arm64/configs/vendor/star_defconfig` 与官方 274 内核实测配置差距大于本仓库现行组合,详见 stock-config-delta)。
