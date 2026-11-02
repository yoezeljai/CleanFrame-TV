#!/bin/bash
# Builds dist/CleanFrame-firetv.apk: the Tizen 3.0 page (old-WebView safe) in an Android launcher.
# Uses the SDK in ../android-sdk (build-tools 34, platform 34) and Java 17; no Gradle.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${ANDROID_SDK:-$ROOT/../android-sdk}"
BT="$SDK/build-tools/34.0.0"
JAR="$SDK/platforms/android-34/android.jar"
export JAVA_HOME="${JAVA_HOME:-/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home}"
OUT="$ROOT/dist/android"
KEY="$ROOT/.local/android/cleanframe.keystore"

python3 "$ROOT/scripts/build-tizen3.py"
rm -rf "$OUT" && mkdir -p "$OUT/assets" "$OUT/res" "$OUT/gen" "$OUT/classes"
cp -R "$ROOT/dist/tizen3" "$OUT/assets/www"
rm -f "$OUT/assets/www/config.xml"
cp "$ROOT/android/device-android.js" "$OUT/assets/www/device.js"
sed -i '' 's|<meta name="viewport" content="width=device-width, initial-scale=1">|<meta name="viewport" content="width=1920, initial-scale=0.5, user-scalable=no">|' "$OUT/assets/www/index.html"
grep -q 'width=1920' "$OUT/assets/www/index.html"

# The 2016 Fire TV Stick has ~1 GB RAM and slow storage: ship 4 wallpapers, not 15, at 1280 px wide.
python3 "$ROOT/scripts/trim_wallpapers.py" "$OUT/assets/www/assets" --max-width 1280 forest misty cove alpine

cp -R "$ROOT/android/res/." "$OUT/res/"
python3 - "$ROOT/app/icon.png" "$OUT/res/drawable" <<'EOF'
import sys
from PIL import Image
icon = Image.open(sys.argv[1]).convert('RGBA')
icon.save(sys.argv[2] + '/icon.png')
banner = Image.new('RGBA', (320, 180), (29, 42, 48, 255))
small = icon.resize((140, 140), Image.LANCZOS)
banner.paste(small, (90, 20), small)
banner.save(sys.argv[2] + '/banner.png')
EOF

"$BT/aapt2" compile --dir "$OUT/res" -o "$OUT/res.zip"
"$BT/aapt2" link -o "$OUT/base.apk" -I "$JAR" --manifest "$ROOT/android/AndroidManifest.xml" \
  -A "$OUT/assets" --java "$OUT/gen" "$OUT/res.zip"
"$JAVA_HOME/bin/javac" -nowarn --release 8 -Xlint:-options -classpath "$JAR" -d "$OUT/classes" \
  $(find "$ROOT/android/src" "$OUT/gen" -name '*.java')
"$BT/d8" --min-api 22 --lib "$JAR" --output "$OUT" $(find "$OUT/classes" -name '*.class')
(cd "$OUT" && zip -q -j base.apk classes.dex)
"$BT/zipalign" -f -p 4 "$OUT/base.apk" "$OUT/aligned.apk"

# The key and its password stay in .local/ (git-ignored); a first build creates both.
PASS="$ROOT/.local/android/keystore.pass"
if [ ! -f "$KEY" ]; then
  mkdir -p "$(dirname "$KEY")"
  (umask 077; openssl rand -base64 24 > "$PASS")
  "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$KEY" -storepass:file "$PASS" -keypass:file "$PASS" \
    -alias cleanframe -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=CleanFrame" >/dev/null
fi
"$BT/apksigner" sign --ks "$KEY" --ks-pass "file:$PASS" --key-pass "file:$PASS" \
  --out "$ROOT/dist/CleanFrame-firetv.apk" "$OUT/aligned.apk"
echo "Built $ROOT/dist/CleanFrame-firetv.apk"
