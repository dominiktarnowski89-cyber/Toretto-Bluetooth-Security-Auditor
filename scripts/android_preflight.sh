#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v adb >/dev/null 2>&1; then
  echo "ADB_NOT_INSTALLED"
  exit 2
fi
adb start-server >/dev/null
printf '%s\n' '=== CONNECTED ANDROID DEVICES ==='
adb devices -l
printf '%s\n' '=== READ-ONLY DEVICE SUMMARY ==='
while read -r serial state _; do
  [[ -z "${serial:-}" || "$serial" == "List" ]] && continue
  if [[ "$state" != "device" ]]; then
    printf '%s: %s (unlock phone and approve RSA prompt if expected)\n' "$serial" "$state"
    continue
  fi
  printf '\nDEVICE: %s\n' "$serial"
  for prop in ro.product.manufacturer ro.product.model ro.build.version.release ro.build.version.sdk ro.build.fingerprint; do
    printf '%s=' "$prop"
    adb -s "$serial" shell getprop "$prop" | tr -d '\r'
  done
  printf '%s\n' 'BLUETOOTH_MANAGER_STATE:'
  adb -s "$serial" shell dumpsys bluetooth_manager | grep -iE 'state:|mState=|Bluetooth is (ON|OFF)' || true
done < <(adb devices | tail -n +2)
printf '\n%s\n' 'No phone settings were changed. This preflight does not verify link encryption.'
