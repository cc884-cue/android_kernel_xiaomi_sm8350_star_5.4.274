[简体中文](README.zh-CN.md)

# Xiaomi Mi 11 Ultra (star) Kernel · Linux 5.4.274

ARM64 / Qualcomm QGKI kernel source for the **Xiaomi Mi 11 Ultra (codename `star`)**, with ReSukiSU Root built in. The target system is **HyperOS 2.0.7.0 / Android 14**; "target" does not imply that on-device compatibility has been verified.

> **Status: development and verification candidate, NOT a confirmed daily-driver build.** A kernel image built from the documented baseline compiles, but boot, flashing, and Root functionality have not yet been verified on the target phone. Recovery ZIPs are candidate packages only; they are not guaranteed to boot or to be safe to flash.

The code baseline verified by this document is [`b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff`](https://github.com/dundwv/android_kernel_xiaomi_sm8350_star_5.4.274/commit/b60a8bd59f8c3dbd56e57b1ed05e7bc26586c9ff).

## Project status (susfs-integration line)

Goal: SUSFS root-hiding kernel for the Mi 11 Ultra (star) on stock HyperOS 2.0.7.0 (Android 14, stock kernel release `5.4.274-qgki-g4dfe63e0666f`), with KernelSU (ReSukiSU rc2) support.

**Done:**

- SUSFS v2.1.0 core integrated with ReSukiSU rc2 inline hooks; the configured build is clean.
- AnyKernel3 flashable zips via [`anykernel3/build.sh`](anykernel3/build.sh).
- Stock Xiaomi ramoops/pstore reservation ported ([`fs/pstore/ram.c`](fs/pstore/ram.c)) so `ramoops_memreserve=4M` on the cmdline actually reserves console-ramoops storage.
- Root cause of the black screen identified ([`docs/vendor-module-crc-analysis.md`](docs/vendor-module-crc-analysis.md)): stock vendor modules (`/vendor/lib/modules/5.4-gki/*.ko`) can never load into any rebuildable kernel because their symbol CRCs are anchored in Xiaomi's private (unpublished) kernel sources - measured match rate ≤45% for every publicly obtainable base, including the full official 5.4.61 OSS with the exact stock `.config`. Display (`msm_drm.ko`) is therefore now built **into the kernel** (`CONFIG_DISPLAY_BUILD=y` in `techpack/display/config/lahainadisp.conf`).

**Next steps:**

- Device test of the display-builtin build.
- If boot OK: bake WLAN/audio/camera into the kernel the same way (sources are in-tree; techpack audio/camera + qca_cld3_wlan already build as self-consistent modules).
- The pstore capture path stays available for forensics on any remaining boot failure.

## Device & configuration

| Item | Source / config facts |
| --- | --- |
| Device | Xiaomi Mi 11 Ultra, `star`, SM8350 / Lahaina platform |
| Arch & baseline | ARM64, Qualcomm QGKI; top-level [Makefile](Makefile) reports Linux `5.4.274` |
| Base defconfig | [`vendor/lahaina-qgki_defconfig`](arch/arm64/configs/vendor/lahaina-qgki_defconfig) |
| Device fragment | [`vendor/star_QGKI.config`](arch/arm64/configs/vendor/star_QGKI.config) |
| Root fragment | [`vendor/star_root.config`](arch/arm64/configs/vendor/star_root.config) (no-root variant: [`vendor/star_root_noksu.config`](arch/arm64/configs/vendor/star_root_noksu.config)) |
| Stock-alignment fragment | [`vendor/star_stock_align.config`](arch/arm64/configs/vendor/star_stock_align.config), from the stock-config delta in [`docs/stock-config-delta.md`](docs/stock-config-delta.md) |
| Merge order | `lahaina-qgki_defconfig` → `star_QGKI.config` → `star_root.config` → `star_stock_align.config` → `olddefconfig` |
| Version suffix | `star_root.config` pins `CONFIG_LOCALVERSION` to the stock HyperOS 2.0.7.0 suffix and disables `CONFIG_LOCALVERSION_AUTO`; with the empty `.scmversion` marker, `uname -r` becomes `5.4.274-qgki-g4dfe63e0666f`, matching the stock ROM's vendor_dlkm module vermagic |

Keeping the version suffix does not make this kernel ABI-compatible a priori with any ROM kernel, external modules, or vendor firmware.

## Kernel features: enabled config ≠ verified on hardware

The entries below can be checked in the device fragments and in the `.config` produced by the merge order above. `y` means built-in and `m` means a loadable module; `m` modules still need to be built, packaged, and wired into the device's module-loading flow. **Driver presence or a successful build is not a claim that the hardware works.**

| Feature | Key configs | Status & notes |
| --- | --- | --- |
| Display | `techpack/display` built into the kernel (`CONFIG_DISPLAY_BUILD=y`) | Vendor `msm_drm.ko` cannot load (CRC analysis); display is baked in |
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

### Linux 5.4 hooks: SUSFS inline-hook mode

The root fragment enables:

```text
CONFIG_KSU=y
CONFIG_KSU_SUSFS=y
CONFIG_KSU_SUSFS_SUS_PATH=y
CONFIG_KSU_SUSFS_SUS_MOUNT=y
CONFIG_KSU_SUSFS_SUS_KSTAT=y
CONFIG_KSU_SUSFS_SPOOF_UNAME=y
CONFIG_KSU_SUSFS_ENABLE_LOG=y
CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS=y
CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG=y
CONFIG_KSU_SUSFS_OPEN_REDIRECT=y
CONFIG_KSU_SUSFS_SUS_MAP=y
```

The ReSukiSU hook mode is a Kconfig `choice`; this config selects **`KSU_SUSFS` (SUSFS inline hooks)** instead of the earlier `CONFIG_KSU_MANUAL_HOOK` combination. The kernel side integrates SUSFS **`v2.1.0`** (authoritative `SUSFS_VERSION` in [`include/linux/susfs.h`](include/linux/susfs.h)), ported file-by-file over this 5.4.274 QGKI tree using the reference v2.1.0 implementation. New kernel files:

| File | Content |
| --- | --- |
| [`fs/susfs.c`](fs/susfs.c) · [`include/linux/susfs.h`](include/linux/susfs.h) · [`include/linux/susfs_def.h`](include/linux/susfs_def.h) | SUSFS v2.1.0 core (sus mount/kstat/path/map/open-redirect, uname/cmdline spoofing, avc-log spoofing, ksu-domain mount isolation, ...) |

Main v1.5.5 → v2.1.0 structural changes (upstream design):

- `sus_su` removed (`fs/sus_su.c`, ...); devpts su special file is no longer hooked.
- Process state now uses thread flags (`TIF_PROC_NO_SU` / `TIF_PROC_UMOUNTED` in [`include/linux/susfs_def.h`](include/linux/susfs_def.h)) instead of added `task_struct` KABI fields.
- Sus-mount spoofing is handled by fake `mnt_id`s from `DEFAULT_KSU_MNT_ID=500000` via `susfs_alloc_unshare_ksu_vfsmnt` / `susfs_alloc_non_unshare_ksu_vfsmnt`; no KABI field backup.
- New command sets required by ReSukiSU rc2 `dispatch.c`: `SUSFS_SUS_MAP`, `SUSFS_OPEN_REDIRECT`, `HIDE_SUS_MNTS_FOR_NON_SU_PROCS`, `AVC_LOG_SPOOFING`, `ADD_SUS_PATH_LOOP`, ...

Explicit ReSukiSU call sites in the kernel (v2.1.0 style, guarded by `CONFIG_KSU` / `CONFIG_KSU_SUSFS`):

| Path | Hooked content |
| --- | --- |
| [`fs/exec.c`](fs/exec.c) | execve dispatches `ksu_handle_execveat` / `ksu_handle_execveat_sucompat` via the `ksu_su_compat_enabled` static key |
| [`fs/open.c`](fs/open.c) | `do_faccessat` path handling (static-key dispatch when allowing uid) |
| [`fs/stat.c`](fs/stat.c) | `vfs_statx` path handling + `ksu_handle_vfs_fstat` in `vfs_statx_fd` (kstat size spoofing) |
| [`kernel/reboot.c`](kernel/reboot.c) | ReSukiSU reboot extension entry (magic return) |
| [`kernel/sys.c`](kernel/sys.c) | `setresuid` handling replacing the manual-mode LSM auto hooks |
| [`fs/read_write.c`](fs/read_write.c) | `read` init-rc handling (`ksu_is_init_rc_hook_enabled` static key) |
| [`drivers/input/input.c`](drivers/input/input.c) | Input-event handling (`ksu_is_input_hook_enabled` static key) |

In SUSFS mode the LSM `AUTO_*` automatic hooks are unavailable (their Kconfig depends on `CONFIG_KSU_MANUAL_HOOK`); the explicit call sites above carry the full integration, and ReSukiSU's build-time `inline_hook_check` / `susfs_compat` checks require their presence. The v1.5.5-era exec/devpts `sus_su` hooks are gone with v2.1.0.

Mount-related integration lives in [`fs/namespace.c`](fs/namespace.c) (`mnt_alloc_group_id`, `mnt_free_id`, `vfs_create_mount`, `clone_mnt`, `copy_mnt_ns`, `susfs_get_non_sus_mnt_id_from_mnt`, ...), [`fs/statfs.c`](fs/statfs.c), [`fs/proc/fd.c`](fs/proc/fd.c), [`fs/proc_namespace.c`](fs/proc_namespace.c), [`fs/notify/fdinfo.c`](fs/notify/fdinfo.c); path and maps hiding in [`fs/namei.c`](fs/namei.c), [`fs/readdir.c`](fs/readdir.c), [`fs/proc/task_mmu.c`](fs/proc/task_mmu.c); symbol and log spoofing in [`kernel/kallsyms.c`](kernel/kallsyms.c), [`fs/proc/cmdline.c`](fs/proc/cmdline.c), [`security/selinux/avc.c`](security/selinux/avc.c), [`kernel/sys.c`](kernel/sys.c). All changes are guarded by the corresponding `CONFIG_KSU_SUSFS*` options; disabling them keeps the original KABI layout and behavior.

Actual use still requires the matching ReSukiSU user-space components / manager, and validation of authorization, boot flow, policies, and modules. Building the kernel image does not build or install those components.

### SUSFS version correspondence

The kernel side is `SUSFS_VERSION "v2.1.0"`; command-number ABI aligns with ReSukiSU rc2 `dispatch.c`. v2.1.0 officially supports 4.14+; this integration is a file-by-file port of a community-adapted 5.4 QGKI v2.1.0 tree, **not a claim of compatibility with every QGKI 5.4 patch set, target-ROM vendor modules, or HyperOS system components**.

## Building

### Prerequisites

Linux build host with Git, Make, Bash, host C/C++ toolchain, Flex, Bison, OpenSSL dev headers, ELF dev headers (`libelf`), `bc`, Python 3, and a full Clang/LLVM toolchain (LLD, `llvm-ar`, `llvm-nm`, `llvm-objcopy`, ...). Depending on targets, `dtc` and `pahole` may also be needed.

The recorded image build used **Ubuntu Clang 18.1.3**. This config enables Clang LTO, CFI, Shadow Call Stack, and module versioning; do not assume arbitrary compilers/configs still reuse vendor modules. Examples assume tools named `clang`, `ld.lld`, etc. are on PATH; adjust PATH for a specific LLVM version first.

### Generate config and build the image

In a Bash shell, with the output directory outside the source tree:

```bash
git clone https://github.com/cc884-cue/android_kernel_xiaomi_sm8350_star_5.4.274.git
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
  arch/arm64/configs/vendor/star_root.config \
  arch/arm64/configs/vendor/star_stock_align.config
make "${KMAKE[@]}" olddefconfig
make -s "${KMAKE[@]}" kernelrelease
# must print 5.4.274-qgki-g4dfe63e0666f

# Clang 18 compat warning flags; unrelated to config generation.
KCFLAGS_COMPAT="-Wno-pointer-to-enum-cast -Wno-unaligned-access \
-Wno-cast-function-type-strict -Wno-enum-compare-conditional \
-Wno-enum-enum-conversion"
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" Image.gz
```

Main artifacts: `$OUT/arch/arm64/boot/Image`, `$OUT/arch/arm64/boot/Image.gz`, plus `vmlinux` and `System.map`.

**Release / vermagic alignment**: `star_root.config` pins `CONFIG_LOCALVERSION` to the stock HyperOS 2.0.7.0 suffix and turns off `CONFIG_LOCALVERSION_AUTO`; the empty `.scmversion` file at the repo root stops `scripts/setlocalversion` from appending `+`. The final `uname -r` is `5.4.274-qgki-g4dfe63e0666f`, matching stock ROM; the vermagic version part of vendor_dlkm modules then aligns (the `CONFIG_MODVERSIONS` symbol CRCs can still differ depending on compiler/config - check the first-boot dmesg for insmod results).

### Modules and device trees are extra steps

```bash
make "${KMAKE[@]}" KCFLAGS="$KCFLAGS_COMPAT" \
  -j"$(nproc)" modules dtbs
make "${KMAKE[@]}" INSTALL_MOD_PATH="$OUT/modules-staging" modules_install
```

These are additional build-target examples. **A successful `Image.gz` build record is not proof that all modules and DTB/DTBO artifacts build**. `modules_install` only stages modules; it does not handle Android partition packaging or on-device loading.

Vendor-module compatibility: stock `vendor/lib/modules/*.ko` and `5.4-gki/*.ko` cannot load into any rebuildable kernel (see [`docs/vendor-module-crc-analysis.md`](docs/vendor-module-crc-analysis.md) and [`docs/module-crc-check.py`](docs/module-crc-check.py)); key drivers must be built in or self-built. `m` items (WLAN, fingerprint, touch, ToF, IR, ...) need matching self-built `.ko` files. A kernel image file is not a flashable full boot image by itself.

## Flashing on the Mi 11 Ultra (star / HyperOS 2.0.7.0)

AnyKernel3 template (see [`anykernel3/`](anykernel3/)) produces the recovery flashable zip:

```bash
O="$OUT" PACKAGE_NAME="$RELEASE-resukisu-susfs" ./anykernel3/build.sh
# -> $OUT/5.4.274-qgki-g4dfe63e0666f-resukisu-susfs.zip
```

The zip is a **pure kernel swap** (`split_boot` / `flash_boot`): original ramdisk/dtb/dtbo preserved, A/B boot slots, `PATCH_VBMETA_FLAG=auto`, device check accepting only `star` / `mars`.

Test steps (unlocked bootloader required):

1. Back up the original boot image (`dd` or a TWRP backup).
2. Prefer Recovery (TWRP) to flash the zip; alternatively `fastboot boot` a temporarily repacked image (repack original boot ramdisk + dtb with magiskboot/mkbootimg yourself).
3. After boot, install the ReSukiSU **v4.2.0-rc2 manager APK** matching the kernel ABI (source in `KernelSU/manager`), and confirm SUSFS feature switches in the manager.
4. If peripheral modules fail CRC (`disagrees about version of symbol` / `Invalid module format` in dmesg), roll back to the original boot image, then decide whether to replace `vendor_dlkm` modules in the package or bake key drivers in.

Known scope: this tree has no 5.10 BPF backport (the reference tree's venus-5.10bpf line has one); stock Android 14 HyperOS does not depend on it. Do not flash packages built from this tree onto Android 15+ / HyperOS 4.

## What has been verified, and what is missing

**Verified:** baseline `b60a8bd59f8c`, the config above, kernel image build with Clang 18.1.3 producing `Image` / `Image.gz`. The build log contains a static-symbol-export warning for `embms_tm_multicast_recv`, so it is not called "warning-free". Config generation and its hash were re-verified when these docs were updated. SUSFS v2.1.0 + ReSukiSU rc2 inline-hook builds clean; display-builtin variant packaged.

**Not verified / not implied:**

- Booting, flashing, and full HyperOS 2.0.7.0 / Android 14 adaptation on the Mi 11 Ultra.
- Peripherals, WLAN, charging, suspend/resume, stability, performance, or battery tests.
- Runtime compatibility of modules and DTB/DTBO with the target ROM.
- ReSukiSU manager connection, Root authorization, policies, boot scripts, or user modules.
- memfd self-tests run on the target device.
- Candidate Recovery ZIP install/boot/rollback on a real device.

Treat all artifacts as unverified candidates. Check the model and partition layout before flashing, keep the original boot image, a restorable backup, and a clear rescue path; do not use candidate packages as certified releases, and do not use them on other models.

## Repository layout (project additions)

| Path | Content |
| --- | --- |
| [`docs/stock-config-delta.md`](docs/stock-config-delta.md) | Stock kernel config delta analysis (IKCONFIG extraction + `star_stock_align.config` alignment) |
| [`docs/stock-kernel-config-OS2.0.7.0.txt`](docs/stock-kernel-config-OS2.0.7.0.txt) | Archived stock kernel `.config` (reference only, not a buildable defconfig) |
| [`docs/vendor-module-crc-analysis.md`](docs/vendor-module-crc-analysis.md) | Vendor module symbol-CRC analysis (root cause of the black screen) |
| [`docs/module-crc-check.py`](docs/module-crc-check.py) | Tool to re-run the CRC compatibility measurement |
| [`docs/firmware-notes.md`](docs/firmware-notes.md) | Reference firmware (HyperOS 2.0.7.0) notes and unpacked boot/vendor artifacts |
| [`scripts/unpack_firmware.sh`](scripts/unpack_firmware.sh) | OTA payload unpack helper |
| [`anykernel3/`](anykernel3/) | AnyKernel3 flashable-zip template + build script |
| [`docs/upstream-patch-policy.md`](docs/upstream-patch-policy.md) | Upstream ACK patch policy retained for contributions |

## Source & licensing

Upstream and component licenses/copyrights are preserved: kernel [`COPYING`](COPYING), [`LICENSES/`](LICENSES/), [`KernelSU/LICENSE`](KernelSU/LICENSE). The original upstream patch policy is preserved at [`docs/upstream-patch-policy.md`](docs/upstream-patch-policy.md); this file and the Chinese [`README.zh-CN.md`](README.zh-CN.md) document the project's purpose and current integration status.
