# 真机刷入流程（Mi 11 Ultra / star）· 临时引导 TWRP

> 前置：BL 已解锁；手机电量 >50%；电脑装好 platform-tools（fastboot/adb）。
> 此流程**不写 recovery/boot 分区**：TWRP 与被测内核都是 `fastboot boot` 临时引导，断电/重启即回原系统。
> 只有一个例外：在 TWRP 里刷 AnyKernel3 zip 时，它会按包内 anykernel.sh 写入 `boot_a/boot_b`（含 vbmeta 补丁），这是有意的一步。

## 1. 下载与校验

| 文件 | 用途 | 校验 |
| --- | --- | --- |
| [twrp-3.7.1_12-v9.0_A17-star-skkk.img](https://sourceforge.net/projects/recovery-for-xiaomi-devices/files/star/twrp-3.7.1_12-v9.0_A17-star-skkk.img/download) | 临时 TWRP（Android 17 基线, 2026-09-19, header v3） | sha256 `33d5217cb2f7ef27869294c303cb13bb…`（本地已核对首 32 位） |
| [star-resukisu-susfs-stockalign.zip](https://github.com/cc884-cue/android_kernel_xiaomi_sm8350_star_5.4.274/releases/tag/build-cert-2026-10) | 构建认证内核卡刷包 | sha256 `673328a40f567e9f64d9c4595c1a970e275e5b85d13832668398e91cfd5d51fd` |
| [star-resukisu-susfs-ci.zip](https://github.com/cc884-cue/android_kernel_xiaomi_sm8350_star_5.4.274/releases/tag/ci-v1) | CI 独立复现构建卡刷包 | release.txt 内含 |

两个内核包刷一个就够；CI 包更小且由公开 CI 重现，推荐 **star-resukisu-susfs-ci.zip**。

## 2. 材料准备

- **备份原 boot**（必须）：TWRP dd 或 fastboot 均可：
  ```bash
  # 已 root/有临时 TWRP 时可用 dd；未刷过任何东西时先跳到第 3 步临时进 TWRP 再备份
  adb shell su -c 'dd if=/dev/block/by-name/boot_$(getprop ro.boot.slot) of=/sdcard/boot-backup.img'
  adb pull /sdcard/boot-backup.img
  ```
- 手机进入 fastboot：关机 → 按住 音量下 + 电源 插线（或 `adb reboot bootloader`）
- U 盾电脑检查：`fastboot devices` 有输出

## 3. 临时引导 TWRP（不写分区）

```bash
fastboot boot twrp-3.7.1_12-v9.0_A17-star-skkk.img
```

- 等待 30–60 秒进入 TWRP 界面
- 必要时允许"修改系统分区"提示
- （可选但强烈推荐）在 TWRP 里先做完整备份：Backup → 勾 Boot + Vendor_boot + Vbmeta + Super → 刷入内核前留一份本地

## 4. 传入并刷入内核 zip

```bash
adb push star-resukisu-susfs-ci.zip /sdcard/
```

TWRP: Install → 选择 zip → 滑动确认。脚本会：设备检查（仅 star/mars）→ 写入 boot_a/boot_b → 自动 PATCH_VBMETA 处理。

## 5. 首次启动判定

```bash
adb wait-for-device && adb shell uname -r      # 应输出 5.4.274-qgki-g4dfe63e0666f
adb shell su -c 'dmesg | grep -iE "susfs|kernelsu|resukisu"'
adb logcat | grep -i 'module.* disagree\|Invalid module format'   # 外设模块 CRC 失败会在这里出现
```

| 现象 | 判定 |
| --- | --- |
| 正常进系统、显示正常 | display 内建成功 → 下一步 WLAN/audio/camera 内建 |
| 卡黑屏/Logo、不可与 adb | 显示路径未走通：回滚原 boot（`fastboot flash boot boot-backup.img`），取 console-ramoops（ramoops 已移植，断电重启后在 pstore 看到 panic 日志） |
| 系统起来但 WiFi/触控/BT 缺 | 非黑屏问题，是模块 CRC 面 → 预期内，进入内建清单迭代 |

## 6. 失败回滚（必须能一击回退）

```bash
fastboot flash boot boot-backup.img        # 或先临时 fastboot boot boot-backup.img 验证真伪
```

## 备选：不用 TWRP（fastboot 临时引导内核）

```bash
# magiskboot 重打包：拆原 boot.img → 换 kernel → repack
magiskboot unpack boot-backup.img
cp /path/to/Image.gz kernel && magiskboot repack boot-backup.img new-boot.img
fastboot boot new-boot.img
```

## 相关文档

- [`docs/build-cert-2026-10.md`](build-cert-2026-10.md)：构建认证记录
- [`docs/vendor-module-crc-analysis.md`](vendor-module-crc-analysis.md)：为何按需内建
