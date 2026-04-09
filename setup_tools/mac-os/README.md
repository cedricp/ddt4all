# DDT4ALL macOS Build Instructions

This directory contains the build configuration for creating a distributable DMG installer for DDT4ALL on macOS.

## Files Overview

- **main.spec** - PyInstaller specification file for building the .app bundle
- **builddmg.sh** - Shell script for creating the final DMG installer
- **entitlements.plist** - macOS app entitlements for hardware access

## Prerequisites

1. **Python 3.8+** with required dependencies:
   ```bash
   pip install pyinstaller PyQt5 pyserial pyusb crcmod
   ```

2. **Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```

3. **Homebrew** (for create-dmg):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

4. **create-dmg**:
   ```bash
   brew install create-dmg
   ```

## Build Process

### Quick Build
```bash
cd setup_tools/mac-os
chmod +x builddmg.sh
./builddmg.sh
```

### Manual Build Steps

1. **Build the app bundle**:
   ```bash
   pyinstaller --noconfirm main.spec
   ```

2. **Create DMG installer**:
   ```bash
   create-dmg \
     --volname "DDT4ALL" \
     --volicon "../../resources/icons/obd.icns" \
     --window-pos 200 120 \
     --window-size 600 300 \
     --icon-size 100 \
     --no-internet-enable \
     --icon "DDT4ALL.app" 175 120 \
     --hide-extension "DDT4ALL.app" \
     --eula "../../license.txt" \
     --app-drop-link 425 120 \
     --hdiutil-verbose \
     "dist/DDT4ALL.dmg" \
     "dist/dmg/"
   ```

## Code Signing (Optional)

For distribution outside the App Store, you can code sign the application:

```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
./builddmg.sh
```

## Notarization (Optional)

For distribution on macOS Catalina and later:

```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
export NOTARIZE_USERNAME="your-apple-id@example.com"
export NOTARIZE_PASSWORD="app-specific-password"
export TEAM_ID="XXXXXXXXXX"
./builddmg.sh
```

## Project Structure

The build expects the following project structure:
```
ddt4all/
|-- src/ddt4all/main.py          # Main application entry point
|-- resources/icons/obd.icns     # Application icon
|-- locales/                     # Translation files
|-- src/ddt4all/plugins/         # Plugin files
|-- ecu.zip                      # ECU database
|-- config.json                  # Configuration file
|-- license.txt                   # License file
|-- README.md                     # Documentation
|-- setup_tools/mac-os/          # Build scripts (current directory)
```

## Architecture Support

The build configuration supports:
- **Intel Macs** (x86_64)
- **Apple Silicon** (arm64) 
- **Universal Binary** (both architectures)

## Troubleshooting

### Common Issues

1. **"PyInstaller not found"**:
   ```bash
   pip install pyinstaller
   ```

2. **"create-dmg not found"**:
   ```bash
   brew install create-dmg
   ```

3. **"Icon file not found"**:
   - Ensure `resources/icons/obd.icns` exists in the project root

4. **Build fails with missing dependencies**:
   - Install all required packages from `pyproject.toml`

### Debug Mode

For debugging build issues, modify `main.spec`:
```python
console=True  # Set to True to see console output
debug=True    # Enable debug symbols
```

## Output

The build process creates:
- `dist/DDT4ALL.app` - The macOS application bundle
- `dist/DDT4ALL.dmg` - The distributable DMG installer

## Version Information

The build automatically uses version 3.0.7 from `pyproject.toml`. To update:
1. Modify version in `pyproject.toml`
2. Update version strings in `main.spec`

## Support

For build issues, check:
1. All dependencies are installed
2. File paths are correct
3. macOS permissions allow code signing (if used)
4. Sufficient disk space for build artifacts
