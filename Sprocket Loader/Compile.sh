#!/bin/bash

set -e

MAIN_SCRIPT="Modloader.py"
ICON_PNG="sprocket.png"
ICON_ICO="sprocket.ico"

mkdir -p dist/linux dist/windows

echo "=========================================="
echo "Starting Single-Binary Compilation with Icons..."
echo "=========================================="

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "Error: Main script '$MAIN_SCRIPT' not found!"
    exit 1
fi

# Verification checks for icon files
if [ ! -f "$ICON_PNG" ] || [ ! -f "$ICON_ICO" ]; then
    echo "Warning: Ensure '$ICON_PNG' and '$ICON_ICO' exist in this folder for icons to apply correctly."
fi

# 1. Compile for Linux
# --add-data bundles the PNG inside the binary so the script can load it for the title bar
echo "[Linux] Building native binary with icon..."
pyinstaller --onefile \
            --name="Modloader_Linux" \
            --add-data "${ICON_PNG}:." \
            --distpath ./dist/linux \
            "$MAIN_SCRIPT"

# 2. Compile for Windows via Wine
# --icon changes the actual .exe file icon in File Explorer
echo "[Windows] Building .exe via Wine with icon..."
if command -v wine &> /dev/null; then
    wine python -m pip install pyinstaller --quiet 2>/dev/null || true

    wine python -m PyInstaller --onefile \
                               --name="Modloader_Windows" \
                               --icon="$ICON_ICO" \
                               --add-data "${ICON_PNG};." \
                               --distpath ./dist/windows \
                               "$MAIN_SCRIPT"
else
    echo "[Windows] Skipping: Wine is not installed."
fi

echo "=========================================="
echo "Compilation complete!"
echo "=========================================="

echo "Cleaning up temporary build files..."
rm -rf build/ *.spec
echo "Finished"
