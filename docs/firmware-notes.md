# 参考固件：HyperOS 2.0.7.0（Mi 11 Ultra / star）

本仓库内核源码的适配目标固件为 **HyperOS OS2.0.7.0.UKACNXM**（Android 14）。

## 固件包

区域包名：`star-ota_full-OS2.0.7.0.UKACNXM-user-14.0-ac1c7f7203.zip`（Fastboot 卡刷 OTA，payload 格式）。该包约 5.9 GB，**不要**提交到本仓库；建议放在源码树之外的工作目录。

## 已解包内容（本地工作目录 `star-os2.0.7.0-firmware/`）

- `extracted/` — `boot.img`(201,326,592 B)、`vendor_boot.img`(100,663,296 B)、`dtbo.img`(16 MiB)、`vbmeta.img`(8 KiB)、`vbmeta_system.img`(4 KiB)
- `components/boot/` — boot 里拆出的 `kernel`(51,161,600 B, ARM64 Image) 与 `ramdisk`
- `components/vendor_boot/` — `dtb`(4,223,378 B) 与 `vendor_ramdisk`
- `bin/payload-dumper-go` — 解包工具

`boot.img` 为 Android bootimg（header v3 页大小 4096），与 `build.config.msm.lahaina` 的 `BOOT_IMAGE_HEADER_VERSION=3` 一致。

## 打包对应关系

| 产物 | 来源 | 去向 |
| --- | --- | --- |
| `Image.gz` | 内核构建 | 重新打包 `boot.img`（替换 kernel） |
| dtb | `dtbs` 构建 | 打包进 `vendor_boot`（原 dtb 校验用解包产物） |
| modules | `modules_install` | 打入 vendor_ramdisk/供应商模块路径（按目标 ROM 逻辑） |

重新打包 boot 需要 mkbootimg（header v3：`--header-version 3 --os-version` 参数需与原包一致），刷写前用 `vbmeta.img` 观察是否有 AVB 校验需求。

## 风险提示

所有候选产物（含 Recovery ZIP）未在真机验证启动；刷写前自行备份 boot/vendor_boot 并准备救援路径。
