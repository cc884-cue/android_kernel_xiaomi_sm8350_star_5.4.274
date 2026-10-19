# 构建认证记录 - 2026-10-19

## 环境

| 项 | 值 |
| --- | --- |
| 主机 | Linux (Ubuntu 24.04, x86_64, 8 vCPU / 23 GB) |
| 工具链 | Ubuntu clang 18.1.3 (LLVM=1 LLVM_IAS=1, ld.lld 18) |
| 源码基线 | `cc884-cue/android_kernel_xiaomi_sm8350_star_5.4.274` main(含 susfs-integration 合线 + star_stock_align 配置) |
| 构建脚本 | 根外 O=/workspace/build/star-clang18,配置序 = `lahaina-qgki_defconfig → star_QGKI → star_root → star_stock_align → olddefconfig` |

## 结果

| 项 | 结果 |
| --- | --- |
| `make -s kernelrelease` | `5.4.274-qgki-g4dfe63e0666f`(与官方 HyperOS 2.0.7.0 `uname -r` 精确一致) |
| `Image.gz` | 通过,19,716,280 B(techpack display 内建 `CONFIG_DRM_MSM=y` + SUSFS v2.1.0 + ReSukiSU rc2) |
| `modules` / `dtbs` | 通过,102 个模块 MODPOST;本树模块 98 个 `modules_install`;17 个 DTB |
| 链接期修复 | `star_stock_align.config` 两处保守修正:`QTI_BATTERY_CHARGER`、`MI_HARDWARE_ID`、`CNSS2`/`CNSS_QMI_SVC`/`ICNSS2` 保持 y(内建消费者 `qcom-spmi-wled.c`/`qti_battery_charger.c` 依赖其导出符号;`icnss2` 需要内核内 `pil_restart_level` tracepoint,已注释并留 WLAN 内建路线说明) |
| AnyKernel3 卡刷包 | `star-resukisu-susfs-stockalign.zip`,22,785,343 B,SHA-256 `673328a40f567e9f64d9c4595c1a970e275e5b85d13832668398e91cfd5d51fd` |

## 官方模块 CRC 复测(构建附带验证)

对本轮 `Module.symvers` 重测官方实机包代表性模块:全体兼容率 28%-56%,`module_layout` 等 CRC 不一致 —— 官方 vendor 模块仍不可复用,详见 [`vendor-module-crc-analysis.md`](vendor-module-crc-analysis.md) 2026-10 节。

## 认证结论

**构建认证通过**:1) 配置可复现官方 release;2) display 内建 + SUSFS/ReSukiSU 内建能出完整镜像与自洽模块;3) 官方模块不可复用结论被独立工具链交叉验证。**真机启动/功能验证仍缺**(卡刷包为候选产物,烧录前备份 boot/vendor_boot)。

复现:`./anykernel3/build.sh`(见根 README)与 CI 脚本脚本化步骤均按本文环境开展的,任何变更后应重新跑一遍并更新本文件。
