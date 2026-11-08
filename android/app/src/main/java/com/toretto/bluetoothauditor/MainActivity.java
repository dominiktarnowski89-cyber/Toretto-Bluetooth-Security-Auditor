package com.toretto.bluetoothauditor;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int PERMISSIONS_REQUEST = 11;
    private static final int EXPORT_REQUEST = 12;
    private TextView status;
    private TextView output;
    private boolean receiverRegistered = false;

    private final BroadcastReceiver scanReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (!BluetoothScanService.ACTION_UPDATE.equals(intent.getAction())) return;
            String summary = intent.getStringExtra("summary");
            String state = intent.getStringExtra("state");
            boolean running = intent.getBooleanExtra("running", false);
            if (summary != null) output.setText(summary);
            if (state != null) status.setText(state);
            updateButtons(running);
        }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        if (!hasPermissions()) requestPermissionsIfNeeded();
        refreshFromService();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(14), dp(14), dp(14), dp(10));

        TextView title = new TextView(this);
        title.setText("TORETTO Bluetooth Security Auditor");
        title.setTextSize(20);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Android BLE | Identity & Spoofing Detection");
        subtitle.setTextSize(13);
        root.addView(subtitle);

        status = new TextView(this);
        status.setPadding(0, dp(10), 0, dp(8));
        root.addView(status);

        LinearLayout row = new LinearLayout(this);
        Button start = new Button(this);
        Button stop = new Button(this);
        start.setText("Skanuj BLE");
        stop.setText("Zatrzymaj");
        start.setOnClickListener(view -> startBackgroundScan());
        stop.setOnClickListener(view -> stopBackgroundScan());
        row.addView(start, new LinearLayout.LayoutParams(0, dp(50), 1));
        row.addView(stop, new LinearLayout.LayoutParams(0, dp(50), 1));
        root.addView(row);

        LinearLayout row2 = new LinearLayout(this);
        Button export = new Button(this);
        Button clear = new Button(this);
        Button diagnostics = new Button(this);
        export.setText("Eksport JSON");
        clear.setText("Wyczyść historię");
        diagnostics.setText("Diagnostyka telefonu");
        export.setOnClickListener(view -> exportJson());
        clear.setOnClickListener(view -> {
            BluetoothScanService.clearHistory();
            refreshFromService();
        });
        diagnostics.setOnClickListener(view -> showDiagnostics());
        row2.addView(export, new LinearLayout.LayoutParams(0, dp(48), 1));
        row2.addView(clear, new LinearLayout.LayoutParams(0, dp(48), 1));
        row2.addView(diagnostics, new LinearLayout.LayoutParams(0, dp(48), 1));
        root.addView(row2);

        ScrollView scroll = new ScrollView(this);
        output = new TextView(this);
        output.setTextSize(12);
        output.setTypeface(android.graphics.Typeface.MONOSPACE);
        output.setPadding(dp(8), dp(10), dp(8), dp(10));
        scroll.addView(output);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        TextView note = new TextView(this);
        note.setText("Skanowanie działa w usłudze pierwszoplanowej z trwałym powiadomieniem. "
            + "Blokada ekranu nie zatrzymuje pomiaru. Bez parowania, połączeń i GATT. "
            + "Wspólny fingerprint nie dowodzi, że to ten sam fizyczny nadajnik.");
        note.setTextSize(11);
        note.setPadding(0, dp(8), 0, 0);
        root.addView(note);
        setContentView(root);
        refreshFromService();
    }

    private boolean hasPermissions() {
        if (Build.VERSION.SDK_INT >= 31) {
            return checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED;
        }
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestPermissionsIfNeeded() {
        if (Build.VERSION.SDK_INT >= 31) {
            if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[] {
                    Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.POST_NOTIFICATIONS
                }, PERMISSIONS_REQUEST);
            } else {
                requestPermissions(new String[] {
                    Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.BLUETOOTH_CONNECT
                }, PERMISSIONS_REQUEST);
            }
        } else {
            requestPermissions(new String[] { Manifest.permission.ACCESS_FINE_LOCATION }, PERMISSIONS_REQUEST);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode != PERMISSIONS_REQUEST) return;
        boolean bluetoothGranted = hasPermissions();
        status.setText(bluetoothGranted
            ? "Uprawnienia Bluetooth przyznane."
            : "Brak uprawnień Bluetooth — skanowanie niedostępne.");
    }

    private void startBackgroundScan() {
        if (!hasPermissions()) {
            requestPermissionsIfNeeded();
            return;
        }
        Intent service = new Intent(this, BluetoothScanService.class);
        service.setAction(BluetoothScanService.ACTION_START);
        try {
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service);
            else startService(service);
            status.setText("Uruchamianie skanowania w tle…");
        } catch (Exception error) {
            status.setText("Nie można uruchomić usługi: " + error.getMessage());
        }
    }

    private void stopBackgroundScan() {
        Intent service = new Intent(this, BluetoothScanService.class);
        service.setAction(BluetoothScanService.ACTION_STOP);
        startService(service);
        status.setText("Zatrzymywanie skanowania…");
    }

    private void updateButtons(boolean running) {
        // Button state is also communicated in the status line; no activity lifecycle action stops the service.
    }

    private void refreshFromService() {
        if (output != null) output.setText(BluetoothScanService.getSummary());
        if (status != null) status.setText(BluetoothScanService.getState());
    }

    @Override
    protected void onStart() {
        super.onStart();
        IntentFilter filter = new IntentFilter(BluetoothScanService.ACTION_UPDATE);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(scanReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(scanReceiver, filter);
        }
        receiverRegistered = true;
        refreshFromService();
    }

    @Override
    protected void onStop() {
        if (receiverRegistered) {
            unregisterReceiver(scanReceiver);
            receiverRegistered = false;
        }
        super.onStop();
    }

    private void showDiagnostics() {
        StringBuilder details = new StringBuilder("DIAGNOSTYKA TELEFONU\n");
        details.append("Producent: ").append(Build.MANUFACTURER)
            .append("\nModel: ").append(Build.MODEL)
            .append("\nAndroid: ").append(Build.VERSION.RELEASE)
            .append(" (API ").append(Build.VERSION.SDK_INT).append(")\n");
        details.append("Uprawnienia skanowania: ").append(hasPermissions() ? "przyznane" : "brak").append("\n");

        BluetoothManager manager = (BluetoothManager) getSystemService(BLUETOOTH_SERVICE);
        BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
        details.append("Adapter Bluetooth: ")
            .append(adapter == null ? "niedostępny" : (adapter.isEnabled() ? "włączony" : "wyłączony"))
            .append("\n");

        if (adapter != null && hasPermissions()) {
            try {
                Set<BluetoothDevice> paired = adapter.getBondedDevices();
                details.append("Sparowane urządzenia Classic: ").append(paired.size()).append("\n");
                for (BluetoothDevice device : paired) {
                    details.append(" - ")
                        .append(device.getName() == null ? "(brak nazwy)" : device.getName())
                        .append(" | ").append(device.getAddress()).append("\n");
                }
            } catch (SecurityException error) {
                details.append("Lista sparowanych: brak uprawnień CONNECT\n");
            }
        }
        details.append("\nLista sparowanych urządzeń nie jest skanem urządzeń w pobliżu.");
        output.setText(details.toString());
        status.setText("Diagnostyka lokalna Android.");
    }

    private void exportJson() {
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_TITLE, "toretto-android-ble-" + System.currentTimeMillis() + ".json");
        startActivityForResult(intent, EXPORT_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != EXPORT_REQUEST || resultCode != RESULT_OK || data == null) return;
        Uri uri = data.getData();
        if (uri == null) return;
        try (OutputStream stream = getContentResolver().openOutputStream(uri)) {
            if (stream == null) throw new IllegalStateException("Nie można otworzyć pliku docelowego");
            stream.write(BluetoothScanService.getExportJson().getBytes(StandardCharsets.UTF_8));
            Toast.makeText(this, "Raport JSON zapisany", Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            Toast.makeText(this, "Błąd eksportu: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
}
