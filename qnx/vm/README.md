# Experimental QNX 8 x86-64 boot image

`mkifs` successfully generates a 2.3 MB image from `toretto.build` using QNX SDP 8.0. The first QEMU TCG attempt (`-kernel image.ifs`, 2 vCPU, 2 GiB RAM, 24-second timeout) printed SeaBIOS `Booting from ROM..` but **did not confirm QNX startup**. This is an experimental buildfile, not a validated VM configuration.

The buildfile references Netcup-specific absolute paths to a cross-compiled executable and a sample report; replace these paths for another build host. Do not treat compilation or image generation as a successful runtime test. Next investigate the QNX boot method and serial console before validating the analyzer.

## Second boot attempt (serial diagnostics)

On Netcup, QEMU 10.0.13 was run with TCG, 2 vCPU, 2048 MiB, `-display none -serial stdio -monitor none -nic none -kernel <IFS>`. The alternate IFS used `startup-x86 -v -D 8250.3f8.4.115200`. `mkifs` succeeded, but the 16-second test timed out (exit 124) without guest serial output. This does **not** establish a successful QNX boot. Investigate QNX-supported boot packaging and serial startup before claiming runtime validation.

The VPS exposes neither `/dev/kvm` nor `svm`/`vmx` CPU flags, so QEMU is limited to software emulation unless the hosting provider enables nested virtualization.

## Confirmed QNX runtime test

The official QNX SDP 8.0 `mkqnximage --type=qemu --arch=x86_64 --cpu=2 --ram=2G --graphics=no --noprompt --force` successfully built an approximately 11 MiB IFS and QEMU disk image. Running with QEMU 10.0.13 in TCG mode reached QNX services and mounted the system filesystems. The native analyzer was embedded in a rebuilt IFS and executed on the sample report. The test returned `TORETTO_TEST_EXIT=0`, `Observations: 11; fingerprint groups: 11`, and produced a valid JSON report with 11 groups. This validates basic QNX x86-64 runtime operation, **not** Bluetooth live collection, ARM64 runtime, or multi-address alert parity.

The initial runtime attempt returned `Missing identity_observations array` because the QNX JSON decoder requires entering the root object before pushing the array; the native source has been corrected.
