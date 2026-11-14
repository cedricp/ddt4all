# DDT4ALL macOS build and distribution

The macOS build produces a standalone, architecture-specific `DDT4ALL.app` and
drag-to-Applications DMG. The ECU database is a separate user-installed
component: `ecu.zip` is not read by PyInstaller, placed in the app, or copied to
the DMG.

## Install the app and ECU database

1. Download `DDT4ALL-macOS-x86_64.dmg` for an Intel Mac or
   `DDT4ALL-macOS-arm64.dmg` for Apple Silicon from the GitHub Release.
2. Open the DMG and drag `DDT4ALL.app` to `Applications`.
3. Obtain the separately distributed, authorized `ecu.zip` database archive.
   The app and its GitHub Release do not contain or download this archive.
4. Copy `ecu.zip` to:

   ```text
   ~/Library/Application Support/ddt4all/ecu.zip
   ```

   Create the `ddt4all` directory if necessary. Keep the filename exactly
   `ecu.zip`; do not extract it.
5. Start or restart DDT4ALL. The app searches for `ecu.zip` in this per-user
   data directory. When it is missing, DDT4ALL opens without crashing and
   displays the expected install location. ECU database changes take effect
   after restarting the app; replacing this file does not require reinstalling
   DDT4ALL.

This follows the existing Windows installer model: the application installer
does not ship the database and prompts users to install it separately. The
Linux AppImage release likewise does not bundle it. There is currently no
database downloader in the application or a database asset attached to GitHub
releases; use the project's existing authorized database distribution channel.

The application still supports XML ECU lists in the writable application data
directory. The macOS runtime hook sets the working directory to the app's
Application Support directory and creates the expected `ecus/`, `json/`,
`graphics/`, and `vehicles/` directories, so Finder launch does not depend on
the shell's current directory. If `vehicles/` data is present at build time it
is also packaged; source releases do not include this ignored dataset.

## Architectures and Rosetta 2

| DMG | Supported Mac | Build runner |
|---|---|---|
| `DDT4ALL-macOS-x86_64.dmg` | Intel Macs; Apple Silicon with Rosetta 2 | Intel `macos-15-intel` |
| `DDT4ALL-macOS-arm64.dmg` | Apple Silicon Macs | Apple Silicon `macos-15` |

These are separate native builds. Python, PyQt5, Qt, libusb, and all bundled
native extensions must match the requested architecture; the build verifies
this and does not create a mixed or universal application. The app uses PyQt5
directly, not QtPy. Both targets require macOS 11 or later.

Prefer the arm64 DMG on Apple Silicon. To run the Intel app on Apple Silicon,
Rosetta 2 must be installed. DDT4ALL does not install it or assume it is
available. If macOS prompts to install Rosetta, approve that prompt, or install
it explicitly after choosing to do so:

```bash
softwareupdate --install-rosetta
```

An Intel Mac cannot run the arm64 build.

## Local builds

Build on macOS with a matching native Python and Homebrew architecture. Install
Xcode Command Line Tools, Homebrew, and libusb:

```bash
xcode-select --install
brew install libusb
```

From the repository root, prepare the build environment:

```bash
python3.11 -m venv .venv-macos
source .venv-macos/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r setup_tools/mac-os/requirements-macos.txt
```

Build one architecture at a time:

```bash
bash setup_tools/mac-os/builddmg.sh --arch x86_64
bash setup_tools/mac-os/builddmg.sh --arch arm64
```

Select a non-default Python with `PYTHON=/path/to/python3`. An x86_64 build on
Apple Silicon needs an x86_64 Python and Homebrew running under Rosetta; building
on an Intel Mac is also supported. Do not mix arm64 and x86_64 dependencies.

Outputs are isolated by architecture so one build cannot overwrite the other:

```text
setup_tools/mac-os/dist/x86_64/DDT4ALL-macOS-x86_64.dmg
setup_tools/mac-os/dist/arm64/DDT4ALL-macOS-arm64.dmg
```

The build requires the tracked application sources and icon, but does not
require `ecu.zip` or `vehicles/`. If `ecu.zip` happens to exist locally, it is
still excluded. Before building the DMG the script checks app structure,
architecture, Qt Cocoa and image plugins, WebEngine helper, bundled native
dependencies, and launches the frozen executable with `--help` from an unrelated
directory. It explicitly fails if `ecu.zip` appears anywhere in the app or the
mounted DMG, and runs `hdiutil verify`.

To confirm the separate database install path:

```bash
test -f "$HOME/Library/Application Support/ddt4all/ecu.zip"
```

The app's warning dialog shows this location when no database is available.

## Automated tagged releases

The `Build macOS Installers` GitHub Actions workflow follows the project's tag
conventions (`v*` and unprefixed semantic-version tags). Push a version tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The workflow builds x86_64 on the Intel `macos-15-intel` runner and arm64 on the
native Apple Silicon `macos-15` runner. Each job sets up Python 3.11, installs
the pinned packaging dependencies and Homebrew libusb, runs all bundle and DMG
checks, then uploads its named installer as an Actions artifact. The release
job runs only after both matrix builds and both artifact checks succeed, then
creates or updates the tag's GitHub Release with:

- `DDT4ALL-macOS-x86_64.dmg`
- `DDT4ALL-macOS-arm64.dmg`

Build artifacts can also be downloaded from the workflow run's **Artifacts**
section. The release notes explain architecture selection and separate ECU
database installation. The existing Linux workflow remains unchanged and
continues to upload its AppImage to the same tag's Release.

The app and DMG are intentionally unsigned and not notarized, both for local
builds and GitHub releases. No Apple Developer account, signing certificate,
App Store key, or Apple credential is needed. The build script does not invoke
`codesign`, `notarytool`, or `stapler`, even if signing-related environment
variables happen to be set.

Because the app is unsigned, macOS Gatekeeper may warn that Apple cannot check
the app for malicious software or block the first launch. To open an app you
trust, use Finder's **Control-click > Open** and confirm the prompt. Depending
on the macOS version, you may instead need to open **System Settings > Privacy
& Security** and choose **Open Anyway** after the first blocked launch. This
user-approved override does not sign the app or disable Gatekeeper globally.

## Troubleshooting and test scope

- **Architecture mismatch:** match `python -c 'import platform;
  print(platform.machine())'` and `brew --prefix` to the requested architecture.
- **Intel app on Apple Silicon does not launch:** install Rosetta 2 with the
  user's approval, or use the native arm64 DMG.
- **No ECU database:** copy the separately obtained archive intact to
  `~/Library/Application Support/ddt4all/ecu.zip`, then restart the app.
- **Qt platform plugin error:** check the build log for `libqcocoa.dylib` and
  avoid globally setting `QT_PLUGIN_PATH` or `QT_QPA_PLATFORM_PLUGIN_PATH`.
- **Missing libusb:** run `brew install libusb` for the same architecture as
  Python and rebuild.
- **Gatekeeper blocks the app:** use Finder's **Control-click > Open**, or
  approve **Open Anyway** in **System Settings > Privacy & Security**. The app
  is intentionally unsigned and is not notarized.

Automated checks cover Python database absence/install behavior, packaged
executable startup with `--help` and no database, native architecture,
resources, exclusion of the ECU archive from the bundle and DMG, and DMG
integrity. Actual GUI/Finder launch, hardware adapters and drivers, and
first-launch Gatekeeper behavior and hardware adapters require physical Macs.
