# Experimental QNX 8 x86-64 boot image

`mkifs` successfully generates a 2.3 MB image from `toretto.build` using QNX SDP 8.0. The first QEMU TCG attempt (`-kernel image.ifs`, 2 vCPU, 2 GiB RAM, 24-second timeout) printed SeaBIOS `Booting from ROM..` but **did not confirm QNX startup**. This is an experimental buildfile, not a validated VM configuration.

The buildfile references Netcup-specific absolute paths to a cross-compiled executable and a sample report; replace these paths for another build host. Do not treat compilation or image generation as a successful runtime test. Next investigate the QNX boot method and serial console before validating the analyzer.

## Second boot attempt (serial diagnostics)

On Netcup, QEMU 10.0.13 was run with TCG, 2 vCPU, 2048 MiB, `-display none -serial stdio -monitor none -nic none -kernel <IFS>`. The alternate IFS used `startup-x86 -v -D 8250.3f8.4.115200`. `mkifs` succeeded, but the 16-second test timed out (exit 124) without guest serial output. This does **not** establish a successful QNX boot. Investigate QNX-supported boot packaging and serial startup before claiming runtime validation.

The VPS exposes neither `/dev/kvm` nor `svm`/`vmx` CPU flags, so QEMU is limited to software emulation unless the hosting provider enables nested virtualization.
