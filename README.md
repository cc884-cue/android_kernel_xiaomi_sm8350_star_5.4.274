[简体中文](README.zh-CN.md)

# Xiaomi Mi 11 Ultra (star) Kernel · Linux 5.4.274

ARM64 / Qualcomm QGKI kernel source for the **Xiaomi Mi 11 Ultra (codename `star`)**, with ReSukiSU Root built in. The target system is **HyperOS 2.0.7.0 / Android 14**; "target" does not imply that on-device compatibility has been verified.

> **Status: development and verification candidate, NOT a confirmed daily-driver build.** A kernel image built from the documented baseline compiles, but boot, flashing, and Root functionality have not yet been verified on the target phone. Recovery ZIPs, if any, are candidate packages only; they are not guaranteed to boot or to be safe to flash.

The code baseline verified by this document is [`b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff).

## Device & configuration

| Item | Source / config facts |
| --- | --- |
| Device | Xiaomi Mi 11 Ultra, `star`, SM8350 / Lahaina platform |
| Arch & baseline | ARM64, Qualcomm QGKI; top-level [Makefile](Makefile) reports Linux `5.4.274` |
| Base defconfig | [`vendor/lahaina-qgki_defconfig`](arch/arm64/configs/vendor/lahaina-qgki_defconfig) |
| Device fragment | [`vendor/star_QGKI.config`](arch/arm64/configs/vendor/star_QGKI.config) |
| Root fragment | [`vendor/star_root.config`](arch/arm64/configs/vendor/star_root.config) |
| Merge order | `lahaina-qgki_defconfig` → `star_QGKI.config` → `star_root.config` → `olddefconfig` |
| Version suffix | Inherited from the base defconfig (`-qgki`); configured `kernelrelease` is `5.4.274-qgki` |

Keeping the version suffix does not make this kernel ABI-compatible a priori with any ROM kernel, external modules, or vendor firmware.

## Kernel features: enabled config ≠ verified on hardware

The entries below can be checked in the device fragments and in the `.config` produced by the merge order above. `y` means built-in and `m` means a loadable module; `m` modules still need to be built, packaged, and wired into the device's module-loading flow. **Driver presence or a successful build is not a claim that the hardware works.**

| Feature | Key configs | Status & notes |
| --- | --- | --- |
| WLAN | `CONFIG_CNSS_QCA6490=y`, `CONFIG_QCA_CLD_WLAN=m` | QCA6490 platform support built in; CLD WLAN host driver is a module |
| Under-display fingerprint | `CONFIG_INPUT_FINGERPRINT=y`, `CONFIG_FINGERPRINT_GOODIX_FOD=m` | Goodix FOD is a module |
| Touch | `CONFIG_TOUCHSCREEN_CYPRESS_CYTTSP5=m` (+ I2C / DEVICE_ACCESS / LOADER), `CONFIG_TOUCHSCREEN_ST_FTS_V521_SPI=m`, `CONFIG_TOUCHSCREEN_XIAOMI_TOUCHFEATURE=m` | Several touch drivers plus the Xiaomi touch interface; not all are used on one device |
| ToF | `CONFIG_STMVL53L5=m` | Module config |
| Proximity | `CONFIG_MIUS_PROXIMITY=y` | Built in |
| Haptics | `CONFIG_INPUT_AW8697_HAPTIC=y` | AW8697 built in |
| IR over SPI | `CONFIG_LIRC=y`, `CONFIG_RC_CORE=y`, `CONFIG_IR_SPI=m` | IR framework built in; SPI driver is a module |
| Charging & battery | `CONFIG_QTI_BATTERY_CHARGER=y`, `CONFIG_BQ2597X=y`, `CONFIG_BQ_FUEL_GAUGE=y`, `CONFIG_BQ_FG_1S=y` | Built in; no claim on charging power, thermals, or battery life |
| Wireless charging | `CONFIG_MI_WIRELESS=y` | Built in; no on-device verification yet |
| exFAT | `CONFIG_EXFAT_FS=y` | Built-in filesystem support |
| Scheduler | `CONFIG_SCHED_WALT=y` | WALT enabled; no performance or battery claims |
| DT overlay | `CONFIG_BUILD_ARM64_DT_OVERLAY=y` | Enabled; does not mean the DT matches the target ROM |

### memfd executable-sealing backport

The current baseline includes:

- [`66b567591`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/66b5675917a059569f40b381ff00261d861b44f4): backport of memfd executable sealing, adding `F_SEAL_EXEC`, `MFD_NOEXEC_SEAL`, `MFD_EXEC` and related handling.
- [`e829f5a5f`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/e829f5a5f5754c9334001da45f00c2e91d67791c): `F_SEAL_EXEC` handling in the hugetlbfs attribute-modification path.
- [`b60a8bd59`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff): ordering of exec-seal vs write-seal checks so implied write seals are covered by write-mapping checks, plus self-test additions.

Implementation lives in [`mm/memfd.c`](mm/memfd.c), [`mm/shmem.c`](mm/shmem.c), [`fs/hugetlbfs/inode.c`](fs/hugetlbfs/inode.c); test code in [`tools/testing/selftests/memfd/memfd_test.c`](tools/testing/selftests/memfd/memfd_test.c). Existing test source does not mean those tests ran on the target phone.

## Root: how it is done

### ReSukiSU, built into the kernel

[`KernelSU/`](KernelSU/) in this tree is a vendored ReSukiSU source snapshot. Its [`kernel/Kbuild`](KernelSU/kernel/Kbuild) pins the vendored branch as **ReSukiSU `v4.2.0-rc2`, upstream snapshot short SHA `3576e6a5`**; that identifies the source snapshot, not what a manager app will show on a phone, and is not a promise to track upstream latest.

[`drivers/kernelsu`](drivers/kernelsu) links to `KernelSU/kernel`, [`drivers/Kconfig`](drivers/Kconfig) pulls in its options, and [`drivers/Makefile`](drivers/Makefile) builds it under `CONFIG_KSU`. With `CONFIG_KSU=y` in `star_root.config`, this is **built-in kernel root**, not a manager-APK-only setup and not a runtime-loadable kernel module.

### Linux 5.4 manual hooks

The fragment enables:

```text
CONFIG_KSU=y
CONFIG_KSU_MANUAL_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_SETUID_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_INITRC_HOOK=y
CONFIG_KSU_MANUAL_HOOK_AUTO_INPUT_HOOK=y
```

Under `CONFIG_KSU_MANUAL_HOOK` the kernel already has explicit call sites:

| Path | Hooked content |
| --- | --- |
| [`fs/exec.c`](fs/exec.c) | ReSukiSU handlers before/after exec |
| [`fs/open.c`](fs/open.c) | Called before the access check in `faccessat` |
| [`fs/stat.c`](fs/stat.c) | Path handling in `newfstatat` / `fstatat64`, and result handling in `newfstat` / `fstat64` |
| [`kernel/reboot.c`](kernel/reboot.c) | ReSukiSU reboot extension entry |

Per [`KernelSU/kernel/Kconfig`](KernelSU/kernel/Kconfig), the three `AUTO_*` options hook setuid, init-rc handling, and input events (via `input_handler`) using LSM. Manual hooks plus these automatic options together form the integration. Do not oversimplify it to "all hooks are one hand-edited syscall", and do not assume anything is verified.

Actual use still requires the matching ReSukiSU user-space components / manager, and validation of authorization, boot flow, policies, and modules. Building the kernel image does not build or install those components.

### SUSFS v2.1.0 is NOT integrated

**This tree does not include the SUSFS v2.1.0 kernel patches, and the Root config does not enable SUSFS.** The generated config has `# CONFIG_KSU_SUSFS is not set`; there is no `fs/susfs.c` or `include/linux/susfs.h`.

The vendored ReSukiSU source does contain SUSFS-conditional interfaces, compat scripts, and manager code, but their presence does not mean the SUSFS kernel patch is integrated. This version does not claim hiding or integrity-check bypass capability.

## Building

### Prerequisites

Linux build host with Git, Make, Bash, host C/C++ toolchain, Flex, Bison, OpenSSL dev headers, ELF dev headers (`libelf`), `bc`, Python 3, and a full Clang/LLVM toolchain (LLD, `llvm-ar`, `llvm-nm`, `llvm-objcopy`, ...). Depending on targets, `dtc` and `pahole` may also be needed.

The recorded image build used **Ubuntu Clang 18.1.3**. This config enables Clang LTO, CFI, Shadow Call Stack, and module versioning; do not assume arbitrary compilers/configs still reuse vendor modules. Examples assume tools named `clang`, `ld.lld`, etc. are on PATH; adjust PATH for a specific LLVM version first.

### Generate config and build the image

In a Bash shell, with the output directory outside the source tree:

```bash
git clone https://github.com/<your-user>/android_kernel_xiaomi_sm8350_star_5.4.274.git
cd android_kernel_xiaomi_sm8350_star_5.4.274

# To reproduce the verified baseline:
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

# Clang 18 compat warning flags; unrelated to config generation.
KCFLAGS_COMPAT="-Wno-pointer-to-enum-cast -Wno-unaligned-access \
-Wno-cast-function-type-strict -Wno-enum-compare-conditional \
-Wno-enum-enum-conversion"
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" Image.gz
```

Config generation has been verified in a separate output directory: it matches the `.config` used for the previously successful image build, SHA-256:

```text
7cca4ca70700f3e91090676017f5c74b85f25bc08d2af39e2c9e3f1c4c42992b
```

Main artifacts: `$OUT/arch/arm64/boot/Image`, `$OUT/arch/arm64/boot/Image.gz`, plus `vmlinux` and `System.map`. These are direct Make-build examples, not a full ROM or Recovery ZIP build script.

### Modules and device trees are extra steps

```bash
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" modules dtbs
make "${KMAKE[@]}" INSTALL_MOD_PATH="$OUT/modules-staging" modules_install
```

These are additional build-target examples. **A successful `Image.gz` build record is not proof that all modules and DTB/DTBO artifacts build**. `modules_install` only stages modules; it does not handle Android partition packaging or on-device loading.

`m` items (WLAN, fingerprint, touch, ToF, IR, ...) need matching `.ko` files, dependencies, and device-loading config. Check target-ROM firmware, device trees, module ABI, and signing requirements. A kernel image file is not a flashable full boot image by itself.

## What has been verified, and what is missing

**Verified:** baseline `b60a8bd59f8c`, the config above, kernel image build with Clang 18.1.3 producing `Image` / `Image.gz`. The build log contains a static-symbol-export warning for `embms_tm_multicast_recv`, so it is not called "warning-free". Config generation and its hash were re-verified when these docs were updated.

**Not verified / not implied:**

- Booting, flashing, and full HyperOS 2.0.7.0 / Android 14 adaptation on the Mi 11 Ultra.
- Peripherals, WLAN, charging, suspend/resume, stability, performance, or battery tests.
- Runtime compatibility of all modules and DTB/DTBO with the target ROM.
- ReSukiSU manager connection, Root authorization, policies, boot scripts, or user modules.
- memfd self-tests run on the target device.
- Candidate Recovery ZIP install/boot/rollback on a real device.

Treat all artifacts as unverified candidates. Check the model and partition layout before flashing, keep the original boot image, a restorable backup, and a clear rescue path; do not use candidate packages as certified releases, and do not use them on other models.

## Repository layout (project additions)

| Path | Content |
| --- | --- |
| [`docs/firmware-notes.md`](docs/firmware-notes.md) | Notes on the reference firmware package (HyperOS 2.0.7.0) and its unpacked boot artifacts |
| [`scripts/unpack_firmware.sh`](scripts/unpack_firmware.sh) | Helper to unpack an OTA payload (boot/vendor_boot) for reference and patching |
| [`docs/upstream-patch-policy.md`](docs/upstream-patch-policy.md) | Upstream ACK patch policy retained for contributions |

## Source & licensing

Upstream and component licenses/copyrights are preserved: kernel [`COPYING`](COPYING), [`LICENSES/`](LICENSES/), [`KernelSU/LICENSE`](KernelSU/LICENSE). The original [`README`](README) is kept unchanged upstream-facing; this file adds the project's purpose and current integration status.
