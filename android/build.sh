#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}"
PLATFORM="$SDK/platforms/android-36"
BT="$SDK/build-tools/36.0.0"
APP="$ROOT/android/app"
OUT="$ROOT/dist/android"
WORK="$ROOT/build/android"
mkdir -p "$OUT" "$WORK/classes" "$WORK/dex" "$WORK/gen" "$HOME/.config/toretto-bt-auditor"
rm -rf "$WORK/classes" "$WORK/dex" "$WORK/gen"
mkdir -p "$WORK/classes" "$WORK/dex" "$WORK/gen"
"$BT/aapt" package -f -m -J "$WORK/gen" -M "$APP/src/main/AndroidManifest.xml" -S "$APP/src/main/res" -I "$PLATFORM/android.jar" --min-sdk-version 26 --target-sdk-version 36 --version-code 2 --version-name 1.1.0 -F "$WORK/unsigned.apk"
mapfile -t JAVA_FILES < <(find "$APP/src/main/java" "$WORK/gen" -name "*.java" -print)
javac -encoding UTF-8 -source 8 -target 8 -classpath "$PLATFORM/android.jar" -d "$WORK/classes" "${JAVA_FILES[@]}"
mapfile -t CLASS_FILES < <(find "$WORK/classes" -name "*.class" -print)
"$BT/d8" --min-api 26 --lib "$PLATFORM/android.jar" --output "$WORK/dex" "${CLASS_FILES[@]}"
(cd "$WORK/dex" && zip -q "$WORK/unsigned.apk" classes.dex)
"$BT/zipalign" -f -p 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"
KEYDIR="$HOME/.config/toretto-bt-auditor"
KEYSTORE="$KEYDIR/debug.keystore"
if [[ ! -f "$KEYSTORE" ]]; then
  keytool -genkeypair -keystore "$KEYSTORE" -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=TORETTO Local Debug"
  chmod 600 "$KEYSTORE"
fi
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out "$OUT/toretto-bluetooth-auditor-android-1.1.0.apk" "$WORK/aligned.apk"
"$BT/apksigner" verify --verbose --print-certs "$OUT/toretto-bluetooth-auditor-android-1.1.0.apk"
"$BT/aapt" dump badging "$OUT/toretto-bluetooth-auditor-android-1.1.0.apk" | head -12
sha256sum "$OUT/toretto-bluetooth-auditor-android-1.1.0.apk"
echo "APK=$OUT/toretto-bluetooth-auditor-android-1.1.0.apk"
echo "Signing: local debug key; not a Play Store release key."
