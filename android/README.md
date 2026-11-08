# Android companion
Package: com.toretto.bluetoothauditor. Version 1.1.0, target SDK 36, minimum SDK 26.

BLE observations use Android BluetoothLeScanner. Raw advertising records are fingerprinted with SHA-256; a fingerprint seen on multiple addresses is flagged for investigation. The app does not pair, connect, open GATT, inject packets, or access the network.

Android does not expose raw controller HCI traces to ordinary apps. Full BTSnoop/HCI capture remains a Linux desktop feature. Android can filter or throttle scans. A shared fingerprint is not proof of cloning; BLE privacy address rotation can produce the same pattern.

## Background BLE scanning (1.1.0)

BLE scanning is owned by a started foreground service (BluetoothScanService) using Android's connectedDevice foreground-service type. The service posts an ongoing notification while scanning. The activity lifecycle no longer stops scanning when the screen is locked, the app is backgrounded, or its task is swiped from Recents. Use the in-app **Zatrzymaj** control to stop it. Observations are retained in process memory while the service runs; JSON export remains available from the activity.

Android 14+ requires the connected-device foreground-service permission and an eligible runtime Bluetooth permission. Android 13+ also asks for notification permission; if denied, Android may show foreground-service status in its task manager but suppress the notification from the notification drawer. Battery optimization and OEM background restrictions can still terminate long-running work; for best continuity, set the app battery use to **Unrestricted** in Android app settings if the device offers that option. No application can continue after force-stop, Bluetooth being disabled, or OS process termination.

The launcher uses a custom TORETTO Bluetooth adaptive vector icon; the ongoing notification has its own monochrome status icon.
