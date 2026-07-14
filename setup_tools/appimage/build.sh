#!/bin/bash
set -e

VERSION="${1:-$(git describe --tags --always 2>/dev/null || echo "dev")}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ARCH="${2:-x86_64}"
APPDIR="$ROOT/build/AppDir"
TOOLSDIR="$ROOT/build/tools"

PYTHON_BIN="$(which python3)"
PYTHON_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
# Trouver la bibliothèque libpython (peut être dans un sous-répertoire architecture)
PYTHON_LIB_PATH="$(python3 -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
PYTHON_LIB="$(ls ${PYTHON_LIB_PATH}/libpython${PYTHON_VER}.so.1.0 2>/dev/null || echo "")"
PYTHON_SITE_PACKAGES="$(python3 -c 'import site; print(site.getsitepackages()[0])')"
PYTHON_STDLIB="$(python3 -c "import os; print(os.path.dirname(os.__file__))")"

echo "=== Build AppImage ==="
echo "Version:   $VERSION"
echo "Arch:      $ARCH"
echo "Python:    $PYTHON_BIN ($PYTHON_VER)"
echo "Output:    ddt4all-${VERSION}-${ARCH}.AppImage"

rm -rf "$APPDIR" "$TOOLSDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# --- Python binaire ---
cp "$PYTHON_BIN" "$APPDIR/usr/bin/python${PYTHON_VER}"
ln -sf "python${PYTHON_VER}" "$APPDIR/usr/bin/python3"

# --- libpython ---
if [ -n "$PYTHON_LIB" ] && [ -f "$PYTHON_LIB" ]; then
  cp "$PYTHON_LIB" "$APPDIR/usr/lib/"
  cp -a "$(dirname "$PYTHON_LIB")/libpython${PYTHON_VER}.so" "$APPDIR/usr/lib/" 2>/dev/null || true
fi

# --- stdlib + site-packages ---
# Créer le répertoire site-packages d'abord
mkdir -p "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages"

# D'abord copier le site-packages (contient PyQt5, pyserial, etc.)
# Peut être dans /usr/local/lib (pip) ou /usr/lib (apt) ou dist-packages
if [ -d "$PYTHON_SITE_PACKAGES" ]; then
  cp -r "$PYTHON_SITE_PACKAGES" "$APPDIR/usr/lib/python${PYTHON_VER}/"
  echo "Copied site-packages from $PYTHON_SITE_PACKAGES"
else
  echo "WARNING: site-packages not found at $PYTHON_SITE_PACKAGES"
fi
# Vérifier aussi dist-packages (cas des paquets apt comme python3-pyqt5)
# Sur Debian, les paquets apt sont souvent dans /usr/lib/python3/dist-packages (sans version mineure)
PYTHON_DIST_PACKAGES="/usr/lib/python${PYTHON_VER%.*}/dist-packages"
if [ -d "$PYTHON_DIST_PACKAGES" ]; then
  # Copier les packages qui ne sont pas déjà dans site-packages
  for pkg in "$PYTHON_DIST_PACKAGES"/*; do
    bn="$(basename "$pkg")"
    if [ ! -d "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/$bn" ]; then
      cp -r "$pkg" "$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/" 2>/dev/null || true
    fi
  done
  echo "Merged dist-packages from $PYTHON_DIST_PACKAGES"
fi
# Puis la stdlib système (encodings, os.py, etc.) depuis l'interpréteur courant
for item in "$PYTHON_STDLIB"/*; do
  bn="$(basename "$item")"
  if [ "$bn" != "site-packages" ] && [ "$bn" != "__pycache__" ] && [ "$bn" != "dist-packages" ]; then
    cp -rn "$item" "$APPDIR/usr/lib/python${PYTHON_VER}/" 2>/dev/null || true
  fi
done

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

# Déterminer l'architecture des outils (linuxdeploy/appimagetool)
# Note: appimagetool utilise i686 pour l'architecture 32-bit, pas i386
if [ "$ARCH" = "i386" ]; then
  LINUXDEPLOY_ARCH="i386"
  IMAGEMAGET_ARCH="i686"
else
  LINUXDEPLOY_ARCH="x86_64"
  IMAGEMAGET_ARCH="x86_64"
fi

if [ ! -f "linuxdeploy-${LINUXDEPLOY_ARCH}.AppImage" ]; then
  wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${LINUXDEPLOY_ARCH}.AppImage" -O "linuxdeploy-${LINUXDEPLOY_ARCH}.AppImage"
fi
if [ ! -f "appimagetool-${IMAGEMAGET_ARCH}.AppImage" ]; then
  wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${IMAGEMAGET_ARCH}.AppImage" -O "appimagetool-${IMAGEMAGET_ARCH}.AppImage"
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

LDA="$TOOLSDIR/linuxdeploy-${LINUXDEPLOY_ARCH}/AppRun"
if [ ! -x "$LDA" ]; then
  LDA="$TOOLSDIR/linuxdeploy-${LINUXDEPLOY_ARCH}.AppImage"
fi

# NOTE: on n'utilise volontairement PAS --plugin qt ici.
# Ce plugin cherche une installation Qt système via qmake, ce qui n'a pas de
# sens pour nous : PyQt5 (installé via pip) embarque déjà son propre Qt5
# complet (libs + plugins) dans le wheel. Le plugin s'est aussi révélé
# fragile en environnement Docker/i386 (échec d'exécution de l'AppImage
# brut, absence de FUSE). On laisse donc linuxdeploy faire uniquement son
# travail de base : scanner les dépendances ELF (ldd) des binaires déjà
# présents dans l'AppDir et les bundler. Les plugins Qt sont copiés
# manuellement juste après, depuis le wheel PyQt5.
LD_LIBRARY_PATH="" "$LDA" --appdir "$APPDIR" 2>&1 || {
  echo "WARNING: linuxdeploy a échoué mais on continue"
}

# --- Garantir la présence des plugins Qt attendus par AppRun ---
# Copie systématique depuis le wheel PyQt5 (qui embarque son propre Qt5),
# vers l'emplacement pointé par QT_PLUGIN_PATH dans AppRun.
PYQT5_PLUGINS="$APPDIR/usr/lib/python${PYTHON_VER}/site-packages/PyQt5/Qt5/plugins"
DEST_PLUGINS="$APPDIR/usr/plugins"

if [ -d "$PYQT5_PLUGINS" ]; then
  echo "=== Copie des plugins Qt depuis PyQt5 vers usr/plugins ==="
  mkdir -p "$DEST_PLUGINS"
  cp -r "$PYQT5_PLUGINS"/* "$DEST_PLUGINS/"
else
  echo "WARNING: dossier plugins PyQt5 introuvable ($PYQT5_PLUGINS), l'AppImage risque de ne pas démarrer"
fi

# --- Créer l'AppImage ---
echo "=== Creating AppImage ==="
if [ -x "$TOOLSDIR/appimagetool-${IMAGEMAGET_ARCH}/AppRun" ]; then
  ARCH="$ARCH" "$TOOLSDIR/appimagetool-${IMAGEMAGET_ARCH}/AppRun" "$APPDIR" "$ROOT/ddt4all-${VERSION}-${ARCH}.AppImage"
else
  cd "$TOOLSDIR" && ARCH="$ARCH" ./appimagetool-${IMAGEMAGET_ARCH}.AppImage --appimage-extract-and-run "$APPDIR" "$ROOT/ddt4all-${VERSION}-${ARCH}.AppImage"
  cd "$ROOT"
fi

echo ""
echo "=== Done: ddt4all-${VERSION}-${ARCH}.AppImage ==="
ls -lh "ddt4all-${VERSION}-${ARCH}.AppImage"