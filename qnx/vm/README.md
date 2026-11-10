# Experimental QNX 8 x86-64 boot image

`mkifs` successfully generates a 2.3 MB image from `toretto.build` using QNX SDP 8.0. The first QEMU TCG attempt (`-kernel image.ifs`, 2 vCPU, 2 GiB RAM, 24-second timeout) printed SeaBIOS `Booting from ROM..` but **did not confirm QNX startup**. This is an experimental buildfile, not a validated VM configuration.

The buildfile references Netcup-specific absolute paths to a cross-compiled executable and a sample report; replace these paths for another build host. Do not treat compilation or image generation as a successful runtime test. Next investigate the QNX boot method and serial console before validating the analyzer.
