# 参考固件：HyperOS 2.0.7.0（Mi 11 Ultra / star）

本仓库内核源码的适配目标固件为 **HyperOS OS2.0.7.0.UKACNXM**（Android 14）。

## 固件包

区域包名：`star-ota_full-OS2.0.7.0.UKACNXM-user-14.0-ac1c7f7203.zip`（Fastboot 卡刷 OTA，payload 格式）。该包约 5.9 GB，**不要**提交到本仓库；建议放在源码树之外的工作目录。

## 已解包内容（本地工作目录 `star-os2.0.7.0-firmware/`）

- `extracted/` — `boot.img`(201,326,592 B)、`vendor_boot.img`(100,663,296 B)、`dtbo.img`(16 MiB)、`vbmeta.img`(8 KiB)、`vbmeta_system.img`(4 KiB)
- `components/boot/` — boot 里拆出的 `kernel`(51,161,600 B, ARM64 Image) 与 `ramdisk`
- `components/vendor_boot/` — `dtb`(4,223,378 B) 与 `vendor_ramdisk`
- `full/` — OTA payload 补充解出的 `vendor.img`(1.67 GB, EROFS)、`dtbo.img`、`modem.img`(284 MB)、`vbmeta*`
- `vendor-root/modules/` — 从 `vendor.img` 经 `erofsfuse` 提出的完整原厂模块树（见下）
- `bin/payload-dumper-go` — 解包工具

`boot.img` 为 Android bootimg（header v3 页大小 4096），与 `build.config.msm.lahaina` 的 `BOOT_IMAGE_HEADER_VERSION=3` 一致。vendor 分区为 EROFS（`LZ4_0PADDING`），用 `erofsfuse vendor.img /mnt/erofs` 挂载提取。

## 官方 vendor 内核模块（2.0.7.0 实机包实测）

| 目录 | `.ko` 数量 | vermagic | 备注 |
| --- | --- | --- | --- |
| `/vendor/lib/modules/*.ko` | 112 | `5.4.274-qgki-g4dfe63e0666f` | **运行时实际加载集**（`modules.load` 112 条，与内核 release 完全一致） |
| `/vendor/lib/modules/5.4-gki/*.ko` | 226 | `5.4.274-g4dfe63e0666f`（无 `-qgki`） | 旧版遗留集，含 `modules.dep/alias/softdep`，ROM 不从其 load |

要点：

- 实际加载的 112 模块集与官方内核 release **逐字节一致**的 vermagic（版本部分）；CRC 面不匹配时 vermagic 对齐也无济于事（见 [`vendor-module-crc-analysis.md`](vendor-module-crc-analysis.md)）。
- `modules.load` 首个为 `leds-qti-flash.ko`，随后 camera/audio/touch/battery 等按序加载。
- 官方内核用 `Android (6877366, r383902b1) clang 11.0.2` 构建，提交 `4dfe63e0666f` 属私有树。

## 打包对应关系

| 产物 | 来源 | 去向 |
| --- | --- | --- |
| `Image.gz` | 内核构建 | 重新打包 `boot.img`（替换 kernel） |
| dtb | `dtbs` 构建 | 打包进 `vendor_boot`（原 dtb 校验用解包产物） |
| modules | `modules_install` | 打入 vendor_ramdisk/供应商模块路径（按目标 ROM 逻辑） |

重新打包 boot 需要 mkbootimg（header v3：`--header-version 3 --os-version` 参数需与原包一致），刷写前用 `vbmeta.img` 观察是否有 AVB 校验需求。

## 风险提示

所有候选产物（含 Recovery ZIP）未在真机验证启动；刷写前自行备份 boot/vendor_boot 并准备救援路径。
