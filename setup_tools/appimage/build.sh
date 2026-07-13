#!/bin/bash
set -e

VERSION="${1:-$(git describe --tags --always 2>/dev/null || echo "dev")}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
APPDIR="$ROOT/build/AppDir"
TOOLSDIR="$ROOT/build/tools"

PYTHON_BIN="$(which python3)"
PYTHON_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_LIB="$(dirname "$PYTHON_BIN")/../lib/libpython${PYTHON_VER}.so.1.0"
PYTHON_STDLIB="$(dirname "$PYTHON_BIN")/../lib/python${PYTHON_VER}"

echo "=== Build AppImage ==="
echo "Version:   $VERSION"
echo "Python:    $PYTHON_BIN ($PYTHON_VER)"
echo "Output:    ddt4all-${VERSION}-x86_64.AppImage"

rm -rf "$APPDIR" "$TOOLSDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# --- Python binaire ---
cp "$PYTHON_BIN" "$APPDIR/usr/bin/python${PYTHON_VER}"
ln -sf "python${PYTHON_VER}" "$APPDIR/usr/bin/python3"

# --- libpython ---
if [ -f "$PYTHON_LIB" ]; then
  cp "$PYTHON_LIB" "$APPDIR/usr/lib/"
  cp -a "$(dirname "$PYTHON_LIB")/libpython${PYTHON_VER}.so" "$APPDIR/usr/lib/" 2>/dev/null || true
fi

# --- stdlib + venv site-packages ---
# D'abord copier le site-packages du venv (contient PyQt5, pyserial, etc.)
cp -r "$PYTHON_STDLIB/site-packages" "$APPDIR/usr/lib/python${PYTHON_VER}/"
# Puis la stdlib système (encodings, os.py, etc.) sans écraser site-packages
SYS_STDLIB="$(python3 -c "import os; print(os.path.dirname(os.__file__))")"
if [ -d "$SYS_STDLIB" ] && [ "$(readlink -f "$SYS_STDLIB")" != "$(readlink -f "$PYTHON_STDLIB")" ]; then
  for item in "$SYS_STDLIB"/*; do
    bn="$(basename "$item")"
    if [ "$bn" != "site-packages" ]; then
      cp -r "$item" "$APPDIR/usr/lib/python${PYTHON_VER}/" 2>/dev/null || true
    fi
  done
fi

# --- Installer ddt4all (écrase l'édition éditable du venv) ---
pip install --upgrade --no-deps --force-reinstall --target "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages" .

# --- Icône ---
cp resources/icons/obd.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/ddt4all.png"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/ddt4all.png" "$APPDIR/ddt4all.png"

# --- Desktop file ---
cat > "$APPDIR/usr/share/applications/ddt4all.desktop" << EOF
[Desktop Entry]
Name=DDT4All
Comment=CAN bus ECU diagnostic tool
Categories=Development;Electronics;
Exec=ddt4all
Icon=ddt4all
Type=Application
Terminal=false
EOF
cp "$APPDIR/usr/share/applications/ddt4all.desktop" "$APPDIR/"

# --- AppRun ---
cat > "$APPDIR/AppRun" << APPRUN
#!/bin/bash
set -e
APPDIR="\$(dirname "\$(readlink -f "\$0")")"
export PATH="\$APPDIR/usr/bin:\$PATH"
export LD_LIBRARY_PATH="\$APPDIR/usr/lib:\$APPDIR/lib:\$LD_LIBRARY_PATH"
export PYTHONHOME="\$APPDIR/usr"
export PYTHONPATH="\$APPDIR/usr/lib/python${PYTHON_VER}/site-packages"
export QT_QPA_PLATFORM=xcb
export QT_PLUGIN_PATH="\$APPDIR/usr/plugins"
export QTWEBENGINE_CHROMIUM_FLAGS="--disk-cache-dir=\$HOME/.cache/ddt4all"
exec "\$APPDIR/usr/bin/python3" -m ddt4all "\$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# --- Télécharger les outils ---
mkdir -p "$TOOLSDIR"
cd "$TOOLSDIR"

if [ ! -f linuxdeploy-x86_64.AppImage ]; then
  wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" -O linuxdeploy-x86_64.AppImage
fi
if [ ! -f linuxdeploy-plugin-qt-x86_64.AppImage ]; then
  wget -q "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage" -O linuxdeploy-plugin-qt-x86_64.AppImage
fi
if [ ! -f appimagetool-x86_64.AppImage ]; then
  wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool-x86_64.AppImage
fi

chmod +x *.AppImage

cd "$ROOT"

# --- Bundler Qt5 ---
echo "=== Bundling Qt5 ==="
# Extraire les AppImage tools pour éviter FUSE
for f in "$TOOLSDIR"/*.AppImage; do
  bn="$(basename "$f" .AppImage)"
  out="$TOOLSDIR/$bn"
  if [ ! -d "$out" ]; then
    (cd "$TOOLSDIR" && "$f" --appimage-extract && mv squashfs-root "$bn") || true
  fi
done

# Nettoyer les plugins QML non essentiels pour éviter les erreurs Qt5 manquants
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/Qt/labs/lottieqt" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/Qt/labs/sharedimage" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/Qt/labs/wavefrontmesh" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/QtQuick/Pdf" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/QtQuick/Scene2D" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/QtQuick/Particles.2" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/QtQuick/PrivateWidgets" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/QtQuick/Extras" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/qml/Qt3D" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/geometryloaders" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/sceneparsers" 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/renderplugins" 2>/dev/null || true
rm -f "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/imageformats/libqpdf.so" 2>/dev/null || true
rm -f "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/renderers/libopenglrenderer.so" 2>/dev/null || true
rm -f "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/sqldrivers/libqsqlodbc.so" 2>/dev/null || true
rm -f "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/sqldrivers/libqsqlpsql.so" 2>/dev/null || true
rm -f "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins/texttospeech/libqtexttospeech_speechd.so" 2>/dev/null || true

LDA="$TOOLSDIR/linuxdeploy-x86_64/AppRun"
if [ ! -x "$LDA" ]; then
  LDA="$TOOLSDIR/linuxdeploy-x86_64.AppImage"
fi

LD_LIBRARY_PATH="" "$LDA" --appdir "$APPDIR" --plugin qt 2>&1 || {
  echo "WARNING: linuxdeploy-qt a échoué mais on continue"
}

# --- Créer l'AppImage ---
echo "=== Creating AppImage ==="
if [ -x "$TOOLSDIR/appimagetool-x86_64/AppRun" ]; then
  ARCH=x86_64 "$TOOLSDIR/appimagetool-x86_64/AppRun" "$APPDIR" "$ROOT/ddt4all-${VERSION}-x86_64.AppImage"
else
  cd "$TOOLSDIR" && ARCH=x86_64 ./appimagetool-x86_64.AppImage --appimage-extract-and-run "$APPDIR" "$ROOT/ddt4all-${VERSION}-x86_64.AppImage"
  cd "$ROOT"
fi

echo ""
echo "=== Done: ddt4all-${VERSION}-x86_64.AppImage ==="
ls -lh "ddt4all-${VERSION}-x86_64.AppImage"
