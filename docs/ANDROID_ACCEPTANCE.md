# Android 1.1.0 — background BLE scan acceptance

## Installation / update

The 1.1.0 APK is signed with the same local debug certificate as 1.0.0, so Android should permit an in-place update:

    adb install -r toretto-bluetooth-auditor-android-1.1.0.apk

If installing manually, open the APK on the phone and approve the update. Do not uninstall 1.0.0 first; uninstalling would remove application data.

## Permissions

1. Open **TORETTO Bluetooth Auditor**.
2. Grant **Nearby devices / Bluetooth scan** and **Bluetooth connect** permissions.
3. On Android 13+, grant notification permission so the ongoing scan notification is visible.
4. Ensure Bluetooth is enabled.

## Background acceptance

1. Start **Skanuj BLE** while the app is visible.
2. Verify the persistent notification says that BLE scanning is active.
3. Lock the screen for at least 5 minutes.
4. Unlock the phone and verify observation count and last-seen timestamps advanced during the locked interval.
5. Repeat while switching to another app.
6. Optionally swipe TORETTO away from Recents; the foreground service is configured with stopWithTask=false and should continue.
7. Tap **Zatrzymaj** to stop scanning; verify the ongoing notification disappears.

For a longer run, open Android Settings → Apps → TORETTO Bluetooth Auditor → Battery and select **Unrestricted** (wording may vary by vendor). Android/Oukitel power management can still stop background work; force-stop, disabling Bluetooth, rebooting, or OS process termination are outside the service guarantee.

## Evidence / limitations

- The service uses the Android connectedDevice foreground-service type and BluetoothLeScanner in low-latency mode.
- The notification is an explicit indication that scanning is running; its observation count is refreshed periodically.
- A successful build and APK signature do not prove behavior on the physical Oukitel Tank 2. Physical-device acceptance remains **NOT VERIFIED** until the steps above are completed.
- Android may throttle BLE scans and OEM power management may override normal foreground-service behavior.
- No pairing, GATT connection, packet injection, or network access is performed.
