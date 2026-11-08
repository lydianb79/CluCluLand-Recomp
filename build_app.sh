#!/bin/bash
# Builds "Clu Clu Land Remastered.app" into ./build
# Requirements: macOS 13+, Xcode or the Xcode Command Line Tools (Swift 5.9+).
set -euo pipefail
cd "$(dirname "$0")"

CONFIG="${CONFIG:-release}"
echo "▸ Building ($CONFIG)…"
if [[ "${UNIVERSAL:-0}" == "1" ]]; then
    swift build -c "$CONFIG" --arch arm64 --arch x86_64
    BIN_DIR="$(swift build -c "$CONFIG" --arch arm64 --arch x86_64 --show-bin-path)"
else
    swift build -c "$CONFIG"
    BIN_DIR="$(swift build -c "$CONFIG" --show-bin-path)"
fi

APP="build/Clu Clu Land Remastered.app"
echo "▸ Assembling $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN_DIR/CluCluLandRemastered" "$APP/Contents/MacOS/CluCluLandRemastered"
cp Resources/Info.plist "$APP/Contents/Info.plist"

# App icon
if [[ -f Resources/AppIcon.png ]] && command -v iconutil >/dev/null; then
    ICONSET="build/AppIcon.iconset"
    rm -rf "$ICONSET"; mkdir -p "$ICONSET"
    for s in 16 32 128 256 512; do
        sips -z $s $s Resources/AppIcon.png --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
        sips -z $((s*2)) $((s*2)) Resources/AppIcon.png --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
    done
    iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
    rm -rf "$ICONSET"
fi

# Bundle your own ROM dump if it sits next to the project (it is never redistributed by this repo).
for rom in "../Clu Clu Land.nes" "Clu Clu Land.nes"; do
    if [[ -f "$rom" ]]; then cp "$rom" "$APP/Contents/Resources/Clu Clu Land.nes"; echo "▸ Bundled ROM from $rom"; break; fi
done

codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || echo "  (ad-hoc codesign skipped)"
echo "✓ Done: $APP"
echo "  Run with: open \"$APP\""
