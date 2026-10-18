# 小米 11 Ultra（star）内核 · Linux 5.4.274

面向 **Xiaomi Mi 11 Ultra（小米 11 Ultra，代号 `star`）** 的 ARM64 / Qualcomm QGKI 内核源码，集成 ReSukiSU Root。适配目标为 **HyperOS 2.0.7.0 / Android 14**；这里的“目标”不代表已经完成该系统上的兼容性验证。

> **当前状态：开发与验证候选，不是已确认可日用的版本。** 已有下述源码基线的内核镜像构建通过记录，但尚未在目标手机上完成启动、刷写及 Root 功能验证。Recovery ZIP 也只是候选包，不能据此保证可开机或安全刷入。

本文核对的代码基线为 [`b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff)。本次中文说明不改变内核代码或配置。

## 目标与配置组成

| 项目 | 源码 / 配置事实 |
| --- | --- |
| 设备 | Xiaomi Mi 11 Ultra，`star`，SM8350 / Lahaina 平台 |
| 架构与基线 | ARM64，Qualcomm QGKI；顶层 [Makefile](Makefile) 标记 Linux `5.4.274` |
| 基础配置 | [`vendor/lahaina-qgki_defconfig`](arch/arm64/configs/vendor/lahaina-qgki_defconfig) |
| 设备配置片段 | [`vendor/star_QGKI.config`](arch/arm64/configs/vendor/star_QGKI.config) |
| Root 配置片段 | [`vendor/star_root.config`](arch/arm64/configs/vendor/star_root.config) |
| 合并顺序 | `lahaina-qgki_defconfig` → `star_QGKI.config` → `star_root.config` → `olddefconfig` |
| 版本后缀 | 保留基础配置的 `-qgki`；当前配置生成的 `kernelrelease` 为 `5.4.274-qgki` |

保留版本后缀并不意味着与任意 ROM 的内核 ABI、外部模块或厂商固件自动兼容。

## 内核特性：配置启用不等于真机可用

以下条目可在设备配置片段和按上述顺序生成的 `.config` 中核对。`y` 表示内建，`m` 表示以可加载模块形式配置；模块仍需单独构建、正确打包，并与设备的模块加载流程配合。这里**不将驱动存在、配置启用或编译成功表述为硬件已经实测正常**。

| 功能 | 主要配置 | 配置状态与说明 |
| --- | --- | --- |
| WLAN | `CONFIG_CNSS_QCA6490=y`、`CONFIG_QCA_CLD_WLAN=m` | QCA6490 平台支持内建，CLD WLAN 主机驱动为模块 |
| 屏下指纹 | `CONFIG_INPUT_FINGERPRINT=y`、`CONFIG_FINGERPRINT_GOODIX_FOD=m` | Goodix FOD 为模块 |
| 触控 | `CONFIG_TOUCHSCREEN_CYPRESS_CYTTSP5=m` 及其 I2C / DEVICE_ACCESS / LOADER、`CONFIG_TOUCHSCREEN_ST_FTS_V521_SPI=m`、`CONFIG_TOUCHSCREEN_XIAOMI_TOUCHFEATURE=m` | 包含多种触控驱动及小米触控接口的模块配置，不代表所有驱动都会在同一设备上使用 |
| ToF | `CONFIG_STMVL53L5=m` | 模块配置 |
| 接近感应 | `CONFIG_MIUS_PROXIMITY=y` | 内建配置 |
| 触觉反馈 | `CONFIG_INPUT_AW8697_HAPTIC=y` | AW8697 内建配置 |
| 红外 SPI | `CONFIG_LIRC=y`、`CONFIG_RC_CORE=y`、`CONFIG_IR_SPI=m` | 红外框架内建，SPI 驱动为模块 |
| 充电与电池 | `CONFIG_QTI_BATTERY_CHARGER=y`、`CONFIG_BQ2597X=y`、`CONFIG_BQ_FUEL_GAUGE=y`、`CONFIG_BQ_FG_1S=y` | 内建配置，不构成充电功率、温控或续航保证 |
| 无线充电 | `CONFIG_MI_WIRELESS=y` | 内建配置，尚无目标设备运行验证 |
| exFAT | `CONFIG_EXFAT_FS=y` | 内建文件系统支持 |
| 调度 | `CONFIG_SCHED_WALT=y` | 启用 WALT，不据此宣称性能或功耗提升 |
| 设备树覆盖 | `CONFIG_BUILD_ARM64_DT_OVERLAY=y` | 配置启用，不等于设备树与目标 ROM 已验证匹配 |

### memfd 执行封印修复

当前基线包含以下变更：

- [`66b567591`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/66b5675917a059569f40b381ff00261d861b44f4)：回移 memfd executable sealing，加入 `F_SEAL_EXEC`、`MFD_NOEXEC_SEAL`、`MFD_EXEC` 等相关处理。
- [`e829f5a5f`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/e829f5a5f5754c9334001da45f00c2e91d67791c)：在 hugetlbfs 属性修改路径中处理 `F_SEAL_EXEC`。
- [`b60a8bd59`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff)：调整执行封印与写封印的检查顺序，使相关写映射检查覆盖隐含的写封印，并补充自测试代码。

相关实现位于 [`mm/memfd.c`](mm/memfd.c)、[`mm/shmem.c`](mm/shmem.c)、[`fs/hugetlbfs/inode.c`](fs/hugetlbfs/inode.c)，测试源码位于 [`tools/testing/selftests/memfd/memfd_test.c`](tools/testing/selftests/memfd/memfd_test.c)。存在测试代码不等于这些测试已在目标手机上执行通过。

## Root 如何实现

### ReSukiSU 版本与内建方式

本树的 [`KernelSU/`](KernelSU/) 是随内核提交保存的 ReSukiSU 源码快照。其 [`kernel/Kbuild`](KernelSU/kernel/Kbuild) 的 vendored 分支固定标识为 **ReSukiSU `v4.2.0-rc2`，上游快照提交短 SHA `3576e6a5`**；这里指源码快照标识，不是手机管理器上的实测显示结果，也不是承诺跟随上游最新版。

[`drivers/kernelsu`](drivers/kernelsu) 链接到 `KernelSU/kernel`。[`drivers/Kconfig`](drivers/Kconfig) 引入其配置，[`drivers/Makefile`](drivers/Makefile) 按 `CONFIG_KSU` 纳入构建。`star_root.config` 使用 `CONFIG_KSU=y`，因此本配置是**内核内建 Root**，不是仅安装管理器 APK，也不是选择运行时加载的 Root 内核模块。

### Linux 5.4 manual hooks

本配置启用：

```text
CONFIG_KSU=y
CONFIG_KSU_MANUAL_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_SETUID_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_INITRC_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_INPUT_HOOK=y
```

在 `CONFIG_KSU_MANUAL_HOOK` 条件下，内核已有显式调用点：

| 路径 | 接入内容 |
| --- | --- |
| [`fs/exec.c`](fs/exec.c) | 在 exec 执行前后调用 ReSukiSU 的处理函数 |
| [`fs/open.c`](fs/open.c) | 在 `faccessat` 的访问检查前调用处理函数 |
| [`fs/stat.c`](fs/stat.c) | 接入 `newfstatat` / `fstatat64` 的路径处理，以及 `newfstat` / `fstat64` 的返回处理 |
| [`kernel/reboot.c`](kernel/reboot.c) | 接入 ReSukiSU 约定的 reboot 扩展处理入口 |

根据 [`KernelSU/kernel/Kconfig`](KernelSU/kernel/Kconfig)，三个 `AUTO_*` 选项分别使用 LSM 方式接入 setuid、init rc 相关处理，以及通过 `input_handler` 接入输入事件处理。manual hooks 与这些自动接入选项共同组成当前配置的集成方式，不能把它简化成“所有 hook 都是手工改同一个 syscall”或“所有功能都已验证”。

实际使用仍需要匹配的 ReSukiSU 用户空间组件 / 管理器，并验证授权、启动流程、策略及所用模块。本仓库虽带有管理器与用户空间源码，构建内核镜像并不等于已经构建或安装这些组件；Root 授权、应用兼容性及模块功能均未完成目标设备实测。

### 未集成 SUSFS v2.1.0

**当前内核树未集成 SUSFS v2.1.0 的内核补丁，当前 Root 配置也未启用 SUSFS。** 生成配置中为 `# CONFIG_KSU_SUSFS is not set`；没有 `fs/susfs.c`、`include/linux/susfs.h` 等对应内核实现文件。

ReSukiSU 自带的源码中确实有 SUSFS 条件接口、兼容脚本和管理器 / 用户空间相关代码，但这些代码的存在不等于底层 SUSFS 补丁已经集成。本版本不以此宣称隐藏或完整性检查绕过能力。

## 构建方法

### 准备环境

使用 Linux 构建环境，准备 Git、Make、Bash、C/C++ 主机编译工具、Flex、Bison、OpenSSL 开发头文件、ELF 开发头文件、`bc`、Python 3，以及完整的 Clang / LLVM 工具链（含 LLD、`llvm-ar`、`llvm-nm`、`llvm-objcopy` 等）。按构建目标可能还需要 `dtc`、`pahole` 等工具。

已有镜像构建记录使用 **Ubuntu Clang 18.1.3**。本配置启用 Clang LTO、CFI、Shadow Call Stack 与模块版本控制；不要假设更换任意编译器或配置后仍可直接复用厂商模块。以下示例使用 PATH 中名为 `clang`、`ld.lld` 等工具；使用特定 LLVM 版本时，应先调整 PATH。

### 生成配置并构建镜像

在 Bash 中执行，输出目录放在源码目录之外：

```bash
git clone --branch main --single-branch \
  https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274.git
cd android_kernel_xiaomi_sm8350_star_5.4.274

# 如需复现本文代码基线，可先执行：
# git checkout b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff

export ARCH=arm64
export OUT="$(pwd)/../out-star"
mkdir -p "$OUT"

KMAKE=(O="$OUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 \
       CROSS_COMPILE=aarch64-linux-gnu-)

make "${KMAKE[@]}" vendor/lahaina-qgki_defconfig
scripts/kconfig/merge_config.sh -m -O "$OUT" \
  "$OUT/.config" \
  arch/arm64/configs/vendor/star_QGKI.config \
  arch/arm64/configs/vendor/star_root.config
make "${KMAKE[@]}" olddefconfig
make -s "${KMAKE[@]}" kernelrelease

# Clang 18 兼容告警参数；与配置生成无关。
KCFLAGS_COMPAT="-Wno-pointer-to-enum-cast -Wno-unaligned-access \
-Wno-cast-function-type-strict -Wno-enum-compare-conditional \
-Wno-enum-enum-conversion"
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" Image.gz
```

生成配置这部分已在独立输出目录核对：与此前成功镜像构建所用 `.config` 一致，其 SHA-256 为：

```text
7cca4ca70700f3e91090676017f5c74b85f25bc08d2af39e2c9e3f1c4c42992b
```

主要产物为 `$OUT/arch/arm64/boot/Image`、`$OUT/arch/arm64/boot/Image.gz`，并包含 `vmlinux`、`System.map` 等。上述为直接 Make 构建示例，不是完整 Android ROM 或 Recovery ZIP 的制作脚本；本次文档更新没有重新执行完整内核构建。

### 模块与设备树是额外步骤

如果需要构建模块、设备树及导出模块，可在完成前述配置后按实际打包流程执行：

```bash
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" modules dtbs
make "${KMAKE[@]}" INSTALL_MOD_PATH="$OUT/modules-staging" modules_install
```

这些是额外构建目标示例，**不能把已有 `Image.gz` 构建成功记录当作全部模块与 DTB / DTBO 已验证通过**。`modules_install` 只负责导出模块，不会替你完成 Android 分区打包或设备端加载配置。

WLAN、指纹、触控、ToF、红外等 `m` 项需要匹配的 `.ko`、依赖及设备加载配置；还要核对目标 ROM 的固件、设备树、模块 ABI 和签名要求。内核镜像文件本身不是可直接通用刷入的完整启动镜像。

## 已验证什么，还缺什么

**已有记录：** `b60a8bd59f8c` 源码基线、上述配置在 Clang 18.1.3 下完成内核镜像构建，生成 `Image` / `Image.gz`。构建日志存在 `embms_tm_multicast_recv` 静态符号导出告警，因此不称为“零告警构建”。本次新增说明还验证了配置生成步骤与配置哈希一致性。

**尚未完成或不能据此推定：**

- 在小米 11 Ultra 上启动、刷写及 HyperOS 2.0.7.0 / Android 14 的完整适配验证。
- 全部外设、无线网络、充电、休眠唤醒、稳定性、性能与功耗测试。
- 全部模块、DTB / DTBO 与目标 ROM 的运行时兼容验证。
- ReSukiSU 管理器连接、Root 授权、策略、启动脚本及用户所用模块的实测。
- memfd 自测试在目标设备上的执行结果。
- 候选 Recovery ZIP 的真机安装、启动与回退验证。

请将构建产物视为待验证候选。刷写前自行核对机型与分区布局，保留原始启动镜像、可恢复的备份及明确的救援路径；不要仅凭本文将候选包当作已认证可用版本，也不要用于其他机型。

## 源码与许可证

保留上游与各组件原有许可及版权声明，参见内核 [`COPYING`](COPYING)、[`LICENSES/`](LICENSES/) 与 [`KernelSU/LICENSE`](KernelSU/LICENSE)。原有 [`README`](README) 和 [`README.md`](README.md) 保持不变；本文件仅补充本仓库目标与当前集成状态的中文说明。
