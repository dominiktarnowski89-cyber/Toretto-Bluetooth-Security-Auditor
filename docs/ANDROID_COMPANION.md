# Android companion acceptance and limitations

- Package: `com.toretto.bluetoothauditor`
- Minimum SDK: 26 (Android 8.0)
- Target SDK: 36
- Source: `android/app/src/main/java/com/toretto/bluetoothauditor/MainActivity.java`
- Build: `bash android/build.sh`
- APK output: `dist/android/toretto-bluetooth-auditor-android-1.0.0.apk`

The app scans BLE using Android BluetoothLeScanner, hashes the raw advertisement record exposed by Android, groups exact fingerprints, shows addresses/RSSI/time and exports a JSON evidence file through the Android document picker. It does not pair, connect, access GATT, inject packets, or use internet permission.

The APK is locally debug-signed for installation/testing, not Play Store publication. The local debug keystore is at `~/.config/toretto-bt-auditor/debug.keystore`; preserve it if future APK updates must install over this build.

Android platform limitation: no raw HCI/BTSnoop access for ordinary third-party apps. For HCI command/event evidence, use the Lenovo Linux application. Android may filter advertisements (including with `neverForLocation`) and throttle scans. Live device validation is pending because no Android device was attached to ADB during build.
