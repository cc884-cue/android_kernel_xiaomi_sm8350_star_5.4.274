# 官方内核配置与本仓库配置的差异分析（stock config delta）

数据来源：官方 OTA 包 `star-ota_full-OS2.0.7.0.UKACNXM-user-14.0-ac1c7f7203.zip`（payload.bin → boot.img），用 [`scripts/extract-ikconfig`](../scripts/extract-ikconfig) 从官方 `Image` 内嵌的 IKCONFIG 提取，共 7040 行，存档于 [`docs/stock-kernel-config-OS2.0.7.0.txt`](stock-kernel-config-OS2.0.7.0.txt)。对比基准为本仓库合并顺序：
`lahaina-qgki_defconfig → star_QGKI.config → star_root.config → star_stock_align.config → olddefconfig`。

## 关键事实

| 项 | 官方 | 本仓库 |
| --- | --- | --- |
| 内核 release | `5.4.274-qgki-g4dfe63e0666f` | 相同（`star_root.config` 固定 LOCALVERSION；`.scmversion` 防止追加） |
| 编译器 | Android `(6877366 based on r383902b1) clang 11.0.2` | 本地验证用 GCC 13.3（生产构建用 Clang 18；CRC 复现建议尝试 clang 11） |
| 源码侧提交 | `4dfe63e0666f` 不在任何公开仓库中 | 公开树可追到 `b60a8bd59f8c`（memfd 系列后移植集成） |

官方提交 `4dfe63e0666f` 为小米私有树（与 [`docs/vendor-module-crc-analysis.md`](vendor-module-crc-analysis.md) 的 CRC 结论互证）。

## 配置对齐结果（加 `star_stock_align.config` 后）

符号总量对比（本树 Kconfig 上下文内）：完全一致的 stock 符号 5518 个；剩余差异分布：

| 类别 | 数量 | 说明 |
| --- | --- | --- |
| stock_only | 113 | 绝大多数为小米私有特性（本树无对应 Kconfig，无法启用，见下） |
| ours_only | 134 | 我们的 ReSukiSU/SUSFS、debug 能力与编译器自检项（本树新增/合法差异） |
| different | 5 | 编译器自检（CC/GCC_VERSION、CLANG_VERSION、CC_VERSION_TEXT）、LOCALVERSION（本仓库有意固定完整 vermagic，语义等价）、STATIC_USERMODEHELPER_PATH 已对齐 |

对齐策略分三类：

1. **可对齐（已加进 [`star_stock_align.config`](../arch/arm64/configs/vendor/star_stock_align.config)）**：`CMDLINE=ramoops_memreserve=4M`、`LOG_BUF_SHIFT=21`、`IPC_LOG_MINIDUMP_BUFFERS=0`、MTD 链（BLOCK2MTD/OOPS/OF_PARTS 等）、`I3C`/`I3C_MASTER_MSM_GENI`、`BLK_WBT`/`BLK_WBT_MQ`、`ZRAM_WRITEBACK`、`SERIAL_MSM_GENI_CONSOLE`/`EARLY_CONSOLE`、`JOYSTICK_XPAD_FF/LEDS`、`NETFILTER_XT_MATCH_CONNBYTES`、`CFG80211_CRDA_SUPPORT`、`STATIC_USERMODEHELPER_PATH=/system/bin/micd`，以及模块化对齐（`CNSS2`、`CNSS_QMI_SVC`、`ICNSS2`、`LEDS_QTI_FLASH` 系、`QTI_BATTERY_CHARGER`、`MI_HARDWARE_ID`、`NFC_QTI_I2C` — 官方都是 `m`）。
2. **树内硬编码不可对**：`QCOM_WATCHDOG_BARK_TIME/PET_TIME` 在本树被 `range 11000 11000 / 9360 9360` 锁死（官方 20000/15000）；`KASAN_STACK` 使用 gcc 时强制回 1（clang 构建自然为 0，与官方一致）。改这两个默认值需要动 Kconfig，未纳入。
3. **私有特性无法对齐**：下表。

## 本树缺失的小米私有配置（stock_only 高价值清单）

`XLOGCHAR`、`MI_CNSS_STATISTIC`、`MI_RECLAIM`、`BOOTUP_RECLAIM`、`CAM_RECLAIM`、`MILLET`、`MIGT`、`MIHW`、`SF_BINDER`、`MI_UFS_FFU`、`UFS_WB`、`MIUI_ZRAM_MEMORY_TRACKING`、`MI_MEMORY_SYSFS`、`OEM_KERNEL`、`QGKI_SYSTEM`、`PASSTHROUGH_SYSTEM`、`PACKAGE_RUNTIME_INFO`、`PERF_CRITICAL_RT_TASK`、`DEBUG_POWER_MI`、`DEBUG_POLICY_STATUS`、`FASTBOOT_CMD_CTRL_UART`、`TOUCHSCREEN_ST_FTS_V521_SPI_K2`、`CLD`(stock WLAN 内建)、`F2FS_CP_OPT`、`EROFS_FS_CLUSTER_PAGE_LIMIT`、`QCOM_MINIDUMP_ENCRYPT`、`GPIO_TESTING_MODE`、`SHADOW_CALL_STACK`/`CFI_CLANG`/`THINLTO` 等 clang 工具链项（clang 构建时可选）。

这些缺失同时解释了 CRC 面无法复现的另一半原因：官方 `.config` 引用了公开树不存在的 Kconfig，官方源码相对公开树有系统性私有扩展。

## 复现方法

```bash
bash scripts/extract-ikconfig <官方 boot.img 解出的 Image> > stock.config   # 需 bash 解释（不要 dash）
```

与 `O=自定义目录` 逐格 diff：`scripts/config` 或 `%d.config` 文本对比即可。
