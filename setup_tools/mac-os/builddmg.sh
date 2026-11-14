#!/bin/bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -P "$SCRIPT_DIR/../.." && pwd)"
SPEC_FILE="$SCRIPT_DIR/main.spec"
PYTHON_BIN="${PYTHON:-python3}"
TARGET_ARCH=""
SMOKE_DIR=""
DMG_MOUNT=""
LOG_FILE=""

usage() {
    cat <<'EOF'
Usage: builddmg.sh [--arch arm64|x86_64] [--help]

Build a native-architecture DDT4ALL.app and verified DMG.
The target architecture must match the selected Python interpreter.
The application and DMG are intentionally unsigned; no Apple credentials are needed.
EOF
}

log() {
    printf '[INFO] %s\n' "$*"
}

warn() {
    printf '[WARN] %s\n' "$*" >&2
}

fail() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

on_error() {
    status=$?
    printf '[ERROR] Build failed at line %s (exit %s): %s\n' \
        "${BASH_LINENO[0]:-unknown}" "$status" "${BASH_COMMAND:-unknown}" >&2
    exit "$status"
}

cleanup_smoke_dir() {
    if [[ -n "$SMOKE_DIR" && -d "$SMOKE_DIR" ]]; then
        rm -rf -- "$SMOKE_DIR"
    fi
}

cleanup_temporary_dirs() {
    cleanup_smoke_dir
    if [[ -n "$DMG_MOUNT" && -d "$DMG_MOUNT" ]]; then
        hdiutil detach "$DMG_MOUNT" >/dev/null 2>&1 || true
        rmdir "$DMG_MOUNT" 2>/dev/null || true
    fi
}

trap on_error ERR
trap cleanup_temporary_dirs EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --arch)
            [[ $# -ge 2 ]] || fail "--arch requires arm64 or x86_64."
            TARGET_ARCH="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            fail "Unknown argument: $1"
            ;;
    esac
done

[[ "$(uname -s)" == "Darwin" ]] || fail "This build must run on macOS."
[[ -f "$SPEC_FILE" ]] || fail "PyInstaller spec not found: $SPEC_FILE"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python not found: $PYTHON_BIN"
for tool in brew hdiutil file lipo otool install_name_tool plutil ditto; do
    command -v "$tool" >/dev/null 2>&1 || fail "Required macOS tool not found: $tool"
done

PYTHON_INFO="$("$PYTHON_BIN" -c 'import platform, sys; print("{}.{}.{} {}".format(*sys.version_info[:3], platform.machine()))')"
PYTHON_VERSION="$("$PYTHON_BIN" -c 'import sys; print("{}.{}".format(sys.version_info[0], sys.version_info[1]))')"
PYTHON_ARCH="$("$PYTHON_BIN" -c 'import platform; print(platform.machine())')"
case "$PYTHON_ARCH" in
    aarch64) PYTHON_ARCH="arm64" ;;
    amd64) PYTHON_ARCH="x86_64" ;;
esac
if [[ -z "$TARGET_ARCH" ]]; then
    TARGET_ARCH="$PYTHON_ARCH"
fi
[[ "$TARGET_ARCH" == "arm64" || "$TARGET_ARCH" == "x86_64" ]] || \
    fail "Unsupported architecture '$TARGET_ARCH'; choose arm64 or x86_64."
[[ "$PYTHON_ARCH" == "$TARGET_ARCH" ]] || \
    fail "Python is $PYTHON_ARCH but --arch is $TARGET_ARCH. Use a matching native Python; PyInstaller cannot cross-compile."

BUILD_ROOT="$SCRIPT_DIR/build"
DIST_ROOT="$SCRIPT_DIR/dist"
BUILD_DIR="$BUILD_ROOT/$TARGET_ARCH"
DIST_DIR="$DIST_ROOT/$TARGET_ARCH"

"$PYTHON_BIN" -c 'import sys; sys.exit(0 if (3, 10) <= sys.version_info[:2] < (3, 13) else 1)' || \
    fail "Python 3.10, 3.11, or 3.12 is required (found $PYTHON_VERSION)."
"$PYTHON_BIN" -c 'import sys; from PyInstaller import __version__; p=tuple(int(x) for x in __version__.split(".")[:2]); sys.exit(0 if (6, 11) <= p < (7, 0))' 2>/dev/null || \
    fail "PyInstaller 6.11 or newer, but earlier than 7.0, is required."
"$PYTHON_BIN" - "$SCRIPT_DIR/requirements-macos.txt" <<'PY' || \
    fail "Installed macOS build dependencies do not match requirements-macos.txt."
import importlib.metadata
import sys

requirements = []
with open(sys.argv[1], encoding="utf-8") as requirements_file:
    for line in requirements_file:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line.split("==", 1))

mismatches = []
for name, expected in requirements:
    try:
        actual = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        actual = "not installed"
    if actual != expected:
        mismatches.append("{}: expected {}, found {}".format(name, expected, actual))

if mismatches:
    print("\n".join(mismatches), file=sys.stderr)
    raise SystemExit(1)
PY
"$PYTHON_BIN" -c 'import PyQt5.QtCore, PyQt5.QtGui, PyQt5.QtWidgets, PyQt5.QtWebEngineWidgets, serial, usb, crcmod, platformdirs' || \
    fail "Required application dependencies are missing; install requirements-macos.txt."
"$PYTHON_BIN" -m pip check || fail "Python environment has incompatible package requirements."

for input in "$PROJECT_ROOT/src/ddt4all/main.py" \
    "$PROJECT_ROOT/src/ddt4all/version.py" \
    "$PROJECT_ROOT/src/ddt4all/resources/projects.json" \
    "$PROJECT_ROOT/resources/icons/obd.icns" \
    "$PROJECT_ROOT/license.txt"; do
    [[ -e "$input" ]] || fail "Required project input is missing: $input"
done
LIBUSB_PREFIX="$(brew --prefix libusb 2>/dev/null)" || \
    fail "Homebrew libusb is required to bundle direct USB-CAN support. Install it with: brew install libusb"
LIBUSB_DYLIB="$LIBUSB_PREFIX/lib/libusb-1.0.0.dylib"
[[ -f "$LIBUSB_DYLIB" ]] || fail "Homebrew libusb library not found: $LIBUSB_DYLIB"
LIBUSB_DYLIB="$("$PYTHON_BIN" -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())' "$LIBUSB_DYLIB")"
LIBUSB_ARCHS="$(lipo -archs "$LIBUSB_DYLIB")" || fail "Could not inspect libusb architectures."
printf '%s\n' "$LIBUSB_ARCHS" | grep -qw "$TARGET_ARCH" || \
    fail "libusb does not contain $TARGET_ARCH (found: $LIBUSB_ARCHS). Install the matching Homebrew architecture."

VERSION="$("$PYTHON_BIN" -c 'import ast, pathlib, sys; tree=ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")); values=[ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)]; print(values[0])' \
    "$PROJECT_ROOT/src/ddt4all/version.py")"
[[ -n "$VERSION" ]] || fail "Could not determine the app version from src/ddt4all/version.py."

for output_dir in "$BUILD_ROOT" "$DIST_ROOT" "$BUILD_DIR" "$DIST_DIR"; do
    [[ ! -L "$output_dir" ]] || fail "Refusing to clean symlinked build output: $output_dir"
done
[[ "$BUILD_DIR" == "$BUILD_ROOT/"* && "$DIST_DIR" == "$DIST_ROOT/"* ]] || \
    fail "Build output path escaped the macOS build directory."
rm -rf -- "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"
LOG_FILE="$DIST_DIR/build.log"
: >"$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

log "Project: $PROJECT_ROOT"
log "Python: $PYTHON_INFO"
log "Target architecture: $TARGET_ARCH (native build; no universal binary)"
log "Application version: $VERSION"
log "libusb: $LIBUSB_DYLIB"
log "Signing: $([[ "$SIGNING_ENABLED" == "1" ]] && printf enabled || printf disabled)"
log "Notarization: $NOTARIZE"

export DDT4ALL_TARGET_ARCH="$TARGET_ARCH"
export DDT4ALL_LIBUSB_DYLIB="$LIBUSB_DYLIB"

log "Building the application bundle with PyInstaller..."
"$PYTHON_BIN" -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR" \
    "$SPEC_FILE"

APP="$DIST_DIR/DDT4ALL.app"
EXECUTABLE="$APP/Contents/MacOS/DDT4ALL"
RESOURCES="$APP/Contents/Resources"
[[ -d "$APP" ]] || fail "PyInstaller did not create $APP."
[[ -x "$EXECUTABLE" ]] || fail "Application executable is missing or not executable: $EXECUTABLE"
[[ -f "$APP/Contents/Info.plist" ]] || fail "Application Info.plist is missing."
plutil -lint "$APP/Contents/Info.plist" >/dev/null || fail "Application Info.plist is invalid."
if find "$APP" -iname ecu.zip -print -quit | grep -q .; then
    fail "ecu.zip must remain external to the macOS application."
fi
EXECUTABLE_ARCHS="$(lipo -archs "$EXECUTABLE")" || fail "Could not inspect the application executable."
printf '%s\n' "$EXECUTABLE_ARCHS" | grep -qw "$TARGET_ARCH" || \
    fail "Application executable lacks $TARGET_ARCH (found: $EXECUTABLE_ARCHS)."
if [[ -d "$PROJECT_ROOT/vehicles" && ! -d "$RESOURCES/vehicles" ]]; then
    fail "Local vehicles/ data was present but not included in the application."
fi
[[ -f "$RESOURCES/license.txt" ]] || fail "Bundled license file is missing."
[[ -f "$RESOURCES/ddt4all/resources/projects.json" ]] || \
    fail "Bundled ddt4all/resources/projects.json is missing."
[[ -f "$RESOURCES/ddt4all/generated/locales/fr/LC_MESSAGES/ddt4all.mo" ]] || \
    fail "Compiled gettext catalogs were not included."
[[ -f "$APP/Contents/Frameworks/libusb-1.0.0.dylib" ]] || \
    fail "Bundled libusb dylib is missing from Contents/Frameworks."
install_name_tool -id "@rpath/libusb-1.0.0.dylib" \
    "$APP/Contents/Frameworks/libusb-1.0.0.dylib"

QT_COCOA_PLUGIN="$(find "$APP/Contents" -type f -name libqcocoa.dylib -print -quit)"
[[ -n "$QT_COCOA_PLUGIN" ]] || fail "Qt Cocoa platform plugin (libqcocoa.dylib) is missing."
QT_IMAGE_PLUGIN="$(find "$APP/Contents" -type f -name libqjpeg.dylib -print -quit)"
[[ -n "$QT_IMAGE_PLUGIN" ]] || fail "Qt image-format plugin (libqjpeg.dylib) is missing."
QT_WEBENGINE_HELPER="$(find "$APP/Contents" -type f -name QtWebEngineProcess -perm -111 -print -quit)"
[[ -n "$QT_WEBENGINE_HELPER" ]] || fail "QtWebEngineProcess is missing or not executable."
log "Qt Cocoa plugin: $QT_COCOA_PLUGIN"
log "Qt image plugin: $QT_IMAGE_PLUGIN"
log "QtWebEngine helper: $QT_WEBENGINE_HELPER"

log "Checking native library architectures and linked dependencies..."
while IFS= read -r -d '' binary; do
    if file -b "$binary" | grep -q "Mach-O"; then
        architectures="$(lipo -archs "$binary")" || fail "Could not inspect native binary: $binary"
        printf '%s\n' "$architectures" | grep -qw "$TARGET_ARCH" || \
            fail "Native binary lacks $TARGET_ARCH: $binary ($architectures)"

        while IFS= read -r dependency; do
            [[ -n "$dependency" ]] || continue
            case "$dependency" in
                @rpath/*|@loader_path/*|@executable_path/*|/System/Library/*|/usr/lib/*)
                    ;;
                *)
                    fail "Native dependency is not self-contained: $binary -> $dependency"
                    ;;
            esac
        done < <(otool -L "$binary" | sed -n '2,$s/^[[:space:]]*//; s/ (compatibility version.*$//p')
    fi
done < <(find "$APP/Contents" -type f -print0)

log "Running the bundled executable from an unrelated working directory..."
SMOKE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ddt4all-smoke.XXXXXX")"
mkdir -p "$SMOKE_DIR/home"
"$PYTHON_BIN" - "$EXECUTABLE" "$SMOKE_DIR" 2>&1 <<'PY'
import os
import subprocess
import sys
from pathlib import Path

from platformdirs import PlatformDirs

executable, smoke_dir = sys.argv[1:]
environment = os.environ.copy()
environment["HOME"] = os.path.join(smoke_dir, "home")
environment["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
for name in (
    "PYTHONHOME",
    "PYTHONPATH",
    "DYLD_LIBRARY_PATH",
    "DYLD_FRAMEWORK_PATH",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    "QT_QPA_PLATFORM",
):
    environment.pop(name, None)

result = subprocess.run(
    [executable, "--help"],
    cwd=smoke_dir,
    env=environment,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    timeout=90,
)
print(result.stdout, end="")
if result.returncode != 0 or "usage:" not in result.stdout.lower():
    raise SystemExit("Packaged executable smoke test failed (exit {}).".format(result.returncode))

database_path = Path(
    PlatformDirs("ddt4all", home_dir=os.path.join(smoke_dir, "home")).user_data_dir
) / "ecu.zip"
if database_path.exists():
    raise SystemExit("Smoke test unexpectedly created or copied ecu.zip.")
PY
cleanup_smoke_dir
SMOKE_DIR=""

warn "This app and DMG are unsigned and not notarized. macOS Gatekeeper may require a user-approved override on first launch."

DMG_NAME="DDT4ALL-macOS-${TARGET_ARCH}.dmg"
DMG="$DIST_DIR/$DMG_NAME"
DMG_TEMP="$DIST_DIR/.${DMG_NAME}.tmp"
STAGING_DIR="$BUILD_DIR/dmg-staging"
mkdir -p "$STAGING_DIR"
ditto "$APP" "$STAGING_DIR/DDT4ALL.app"
cp "$PROJECT_ROOT/license.txt" "$STAGING_DIR/LICENSE.txt"
cp "$PROJECT_ROOT/resources/icons/obd.icns" "$STAGING_DIR/DDT4ALL.icns"
ln -s /Applications "$STAGING_DIR/Applications"
if find "$STAGING_DIR" -iname ecu.zip -print -quit | grep -q .; then
    fail "ecu.zip must not be copied into the DMG staging directory."
fi

log "Creating the DMG..."
hdiutil create -quiet -volname "DDT4ALL" -srcfolder "$STAGING_DIR" \
    -ov -format UDZO "$DMG_TEMP"
[[ -s "$DMG_TEMP" ]] || fail "hdiutil did not create the DMG."
mv "$DMG_TEMP" "$DMG"

hdiutil verify "$DMG"
log "DMG integrity verified: $DMG"

DMG_MOUNT="$(mktemp -d "${TMPDIR:-/tmp}/ddt4all-dmg.XXXXXX")"
hdiutil attach -readonly -nobrowse -mountpoint "$DMG_MOUNT" "$DMG"
[[ -d "$DMG_MOUNT/DDT4ALL.app" ]] || fail "DMG does not contain DDT4ALL.app."
if find "$DMG_MOUNT" -iname ecu.zip -print -quit | grep -q .; then
    fail "ecu.zip must not be included in the generated DMG."
fi
hdiutil detach "$DMG_MOUNT"
rmdir "$DMG_MOUNT"
DMG_MOUNT=""

log "Build complete: $DMG"
log "Application bundle: $APP"
