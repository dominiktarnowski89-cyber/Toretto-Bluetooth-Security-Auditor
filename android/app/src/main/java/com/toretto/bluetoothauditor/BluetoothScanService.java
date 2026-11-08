package com.toretto.bluetoothauditor;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanRecord;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.IBinder;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;

public class BluetoothScanService extends Service {
    public static final String ACTION_UPDATE = "com.toretto.bluetoothauditor.UPDATE";
    public static final String ACTION_START = "START";
    public static final String ACTION_STOP = "STOP";
    private static final String CHANNEL_ID = "toretto_ble_scan";
    private static final int NOTIFICATION_ID = 7101;
    private static final Object LOCK = new Object();
    private static final LinkedHashMap<String, Track> TRACKS = new LinkedHashMap<>();
    private static long observations = 0;
    private static boolean scanning = false;
    private static String state = "Skanowanie zatrzymane";

    private BluetoothLeScanner scanner;
    private ScanCallback callback;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private long lastNotificationUpdate = 0;

    private static final class Track {
        final String fingerprint;
        final String firstSeen;
        final String raw;
        final Set<String> addresses = new LinkedHashSet<>();
        String lastSeen;
        String lastAddress;
        String name;
        int rssi;
        int sightings = 1;
        int handoffs = 0;

        Track(String fp, String timestamp, String address, int signal, String deviceName, String rawHex) {
            fingerprint = fp;
            firstSeen = timestamp;
            lastSeen = timestamp;
            lastAddress = address;
            rssi = signal;
            name = deviceName;
            raw = rawHex;
            addresses.add(address);
        }

        void add(String timestamp, String address, int signal, String deviceName) {
            if (!lastAddress.equals(address)) handoffs++;
            lastAddress = address;
            lastSeen = timestamp;
            rssi = signal;
            if (deviceName != null && !deviceName.isEmpty()) name = deviceName;
            addresses.add(address);
            sightings++;
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? ACTION_START : intent.getAction();
        if (ACTION_STOP.equals(action)) {
            stopScanning();
            return START_NOT_STICKY;
        }

        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(
                NOTIFICATION_ID,
                buildNotification("Przygotowywanie skanowania BLE"),
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE
            );
        } else {
            startForeground(NOTIFICATION_ID, buildNotification("Przygotowywanie skanowania BLE"));
        }
        startScanning();
        return START_STICKY;
    }

    private boolean hasScanPermission() {
        if (Build.VERSION.SDK_INT >= 31) {
            return checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED;
        }
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void startScanning() {
        if (!hasScanPermission()) {
            setState("Brak uprawnień Bluetooth — otwórz aplikację i przyznaj uprawnienia");
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return;
        }
        BluetoothManager manager = (BluetoothManager) getSystemService(BLUETOOTH_SERVICE);
        BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
        if (adapter == null || !adapter.isEnabled()) {
            setState("Bluetooth jest wyłączony lub niedostępny");
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return;
        }
        scanner = adapter.getBluetoothLeScanner();
        if (scanner == null) {
            setState("Skaner BLE jest niedostępny");
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return;
        }

        callback = new ScanCallback() {
            @Override public void onScanResult(int callbackType, ScanResult result) {
                accept(result);
            }
            @Override public void onBatchScanResults(java.util.List<ScanResult> results) {
                for (ScanResult result : results) accept(result);
            }
            @Override public void onScanFailed(int errorCode) {
                setState("Błąd skanowania BLE: " + errorCode);
                stopScanning();
            }
        };
        try {
            scanner.startScan(
                null,
                new ScanSettings.Builder()
                    .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
                    .setReportDelay(0)
                    .build(),
                callback
            );
            synchronized (LOCK) {
                scanning = true;
                state = "Skanowanie BLE działa w tle";
            }
            updateNotification("Skanowanie BLE działa");
            broadcastUpdate();
        } catch (SecurityException error) {
            setState("Brak uprawnień do skanowania: " + error.getMessage());
            stopScanning();
        } catch (Exception error) {
            setState("Nie można uruchomić skanowania: " + error.getMessage());
            stopScanning();
        }
    }

    private void accept(ScanResult result) {
        ScanRecord record = result.getScanRecord();
        if (record == null || record.getBytes() == null || record.getBytes().length == 0) return;
        byte[] rawBytes = record.getBytes();
        String fingerprint = sha256(rawBytes);
        String address;
        try {
            address = result.getDevice().getAddress();
        } catch (SecurityException error) {
            address = "address-unavailable";
        }
        String name = record.getDeviceName() == null ? "" : record.getDeviceName();
        String timestamp = now();
        synchronized (LOCK) {
            Track track = TRACKS.get(fingerprint);
            if (track == null) {
                TRACKS.put(fingerprint, new Track(
                    fingerprint, timestamp, address, result.getRssi(), name, toHex(rawBytes)
                ));
            } else {
                track.add(timestamp, address, result.getRssi(), name);
            }
            observations++;
        }
        broadcastUpdate();
        long current = System.currentTimeMillis();
        if (current - lastNotificationUpdate > 5000) {
            lastNotificationUpdate = current;
            updateNotification("Obserwacje: " + getObservationCount() + " | wzorce: " + getFingerprintCount());
        }
    }

    private void stopScanning() {
        if (scanner != null && callback != null) {
            try { scanner.stopScan(callback); } catch (Exception ignored) { }
        }
        synchronized (LOCK) {
            scanning = false;
            state = "Skanowanie zatrzymane. Obserwacje: " + observations;
        }
        broadcastUpdate();
        stopForeground(STOP_FOREGROUND_REMOVE);
        stopSelf();
    }

    private void setState(String value) {
        synchronized (LOCK) {
            scanning = false;
            state = value;
        }
        broadcastUpdate();
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        // Deliberately keep the foreground scan alive when the app is swiped from Recents.
        super.onTaskRemoved(rootIntent);
    }

    @Override
    public void onDestroy() {
        if (scanner != null && callback != null) {
            try { scanner.stopScan(callback); } catch (Exception ignored) { }
        }
        synchronized (LOCK) {
            scanning = false;
        }
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "TORETTO — skanowanie Bluetooth", NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Informuje o działającym skanowaniu BLE w tle");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(channel);
        }
    }

    private Notification buildNotification(String text) {
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
            ? new Notification.Builder(this, CHANNEL_ID)
            : new Notification.Builder(this);
        Intent open = getPackageManager().getLaunchIntentForPackage(getPackageName());
        android.app.PendingIntent pending = open == null ? null : android.app.PendingIntent.getActivity(
            this, 0, open, android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_IMMUTABLE
        );
        builder.setSmallIcon(R.drawable.ic_stat_toretto)
            .setContentTitle("TORETTO Bluetooth Auditor")
            .setContentText(text)
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .setOnlyAlertOnce(true);
        if (pending != null) builder.setContentIntent(pending);
        return builder.build();
    }

    private void updateNotification(String text) {
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.notify(NOTIFICATION_ID, buildNotification(text));
    }

    private void broadcastUpdate() {
        Intent update = new Intent(ACTION_UPDATE);
        update.setPackage(getPackageName());
        update.putExtra("summary", getSummary());
        update.putExtra("running", isScanning());
        update.putExtra("state", getState());
        sendBroadcast(update);
    }

    public static boolean isScanning() {
        synchronized (LOCK) { return scanning; }
    }

    public static long getObservationCount() {
        synchronized (LOCK) { return observations; }
    }

    public static int getFingerprintCount() {
        synchronized (LOCK) { return TRACKS.size(); }
    }

    public static String getState() {
        synchronized (LOCK) { return state; }
    }

    public static String getSummary() {
        synchronized (LOCK) {
            StringBuilder text = new StringBuilder("WZORCE REKLAMOWE: ")
                .append(TRACKS.size()).append("\nOBSERVACJE: ").append(observations).append("\n\n");
            int index = 1;
            for (Track track : TRACKS.values()) {
                text.append(index++).append(". ")
                    .append(track.addresses.size() > 1
                        ? "UWAGA: TEN SAM ODCISK / WIELE ADRESÓW"
                        : "Jeden adres")
                    .append("\nNazwa: ").append(track.name.isEmpty() ? "(brak)" : track.name)
                    .append("\nAdresy: ");
                int count = 0;
                for (String address : track.addresses) {
                    if (count++ > 0) text.append(", ");
                    text.append(address);
                }
                text.append("\nSHA-256: ").append(track.fingerprint.substring(0, 16))
                    .append("\nObserwacje: ").append(track.sightings)
                    .append(" | zmiany adresu: ").append(track.handoffs)
                    .append(" | RSSI: ").append(track.rssi).append(" dBm")
                    .append("\nPierwsza: ").append(track.firstSeen)
                    .append("\nOstatnia: ").append(track.lastSeen).append("\n\n");
            }
            if (TRACKS.isEmpty()) text.append("Brak danych. Uruchom skanowanie i poczekaj na reklamy BLE.");
            return text.toString();
        }
    }

    public static String getExportJson() {
        synchronized (LOCK) {
            try {
                JSONObject root = new JSONObject();
                root.put("schema_version", 1);
                root.put("application", "TORETTO Bluetooth Security Auditor Android");
                root.put("exported_at", now());
                root.put("observations", observations);
                root.put("scanning", scanning);
                root.put("state", state);
                JSONArray fingerprints = new JSONArray();
                for (Track track : TRACKS.values()) {
                    JSONObject item = new JSONObject();
                    item.put("fingerprint_sha256", track.fingerprint);
                    item.put("addresses", new JSONArray(track.addresses));
                    item.put("name", track.name);
                    item.put("sightings", track.sightings);
                    item.put("address_handoffs", track.handoffs);
                    item.put("rssi_last_dbm", track.rssi);
                    item.put("first_seen", track.firstSeen);
                    item.put("last_seen", track.lastSeen);
                    item.put("raw_advertising_data_hex", track.raw);
                    item.put("interpretation", track.addresses.size() > 1
                        ? "Same advertising fingerprint on multiple addresses: BLE privacy rotation or multiple transmitters are both possible."
                        : "One address observed.");
                    fingerprints.put(item);
                }
                root.put("fingerprints", fingerprints);
                return root.toString(2);
            } catch (Exception error) {
                return "{}";
            }
        }
    }

    public static void clearHistory() {
        synchronized (LOCK) {
            TRACKS.clear();
            observations = 0;
        }
    }

    private static String sha256(byte[] bytes) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            return toHex(digest);
        } catch (Exception error) {
            return "hash-error";
        }
    }

    private static String toHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte value : bytes) result.append(String.format(Locale.US, "%02x", value & 255));
        return result.toString();
    }

    private static String now() {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US);
        format.setTimeZone(TimeZone.getTimeZone("UTC"));
        return format.format(new Date());
    }
}
