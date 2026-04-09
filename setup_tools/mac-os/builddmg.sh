#!/bin/bash

# DDT4ALL macOS DMG Build Script
# Creates a distributable DMG file for macOS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
print_status "Checking dependencies..."

if ! command -v pyinstaller &> /dev/null; then
    print_error "PyInstaller not found. Please install it with: pip install pyinstaller"
    exit 1
fi

if ! command -v create-dmg &> /dev/null; then
    print_error "create-dmg not found. Please install it with: brew install create-dmg"
    exit 1
fi

# Verify we're in the correct directory
if [ ! -f "main.spec" ]; then
    print_error "main.spec not found. Please run this script from the ddt4all_data/mac-os directory."
    exit 1
fi

# Verify icon files exist
if [ ! -f "../icons/obd.icns" ]; then
    print_error "Icon file ../icons/obd.icns not found."
    exit 1
fi

if [ ! -f "../../license.txt" ]; then
    print_error "License file ../../license.txt not found."
    exit 1
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.spec.bak

# Build the application
print_status "Building DDT4ALL.app with PyInstaller..."
pyinstaller --noconfirm main.spec

# Verify the build was successful
if [ ! -d "dist/DDT4ALL.app" ]; then
    print_error "PyInstaller build failed. DDT4ALL.app not found in dist/"
    exit 1
fi

print_status "Build successful. App size: $(du -sh dist/DDT4ALL.app | cut -f1)"

# Create DMG preparation directory
print_status "Preparing DMG creation..."
mkdir -p dist/dmg

# Clean the dmg folder (only if it exists and has contents)
if [ -d "dist/dmg" ] && [ "$(ls -A dist/dmg)" ]; then
    rm -rf dist/dmg/*
fi

# Copy the app bundle to the dmg folder
cp -r "dist/DDT4ALL.app" dist/dmg/

# Remove any existing DMG
if [ -f "dist/DDT4ALL.dmg" ]; then
    print_warning "Removing existing DDT4ALL.dmg"
    rm "dist/DDT4ALL.dmg"
fi

# Create the DMG
print_status "Creating DMG..."
create-dmg \
  --volname "DDT4ALL" \
  --volicon "../icons/obd.icns" \
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

# Verify DMG creation
if [ -f "dist/DDT4ALL.dmg" ]; then
    dmg_size=$(du -sh dist/DDT4ALL.dmg | cut -f1)
    print_status "DMG created successfully: dist/DDT4ALL.dmg (${dmg_size})"
    
    # Optional: Verify DMG can be mounted
    print_status "Verifying DMG integrity..."
    if hdiutil verify "dist/DDT4ALL.dmg" > /dev/null 2>&1; then
        print_status "DMG verification passed"
    else
        print_warning "DMG verification failed, but file was created"
    fi
    
    print_status "Build complete! You can find the installer at: $(pwd)/dist/DDT4ALL.dmg"
else
    print_error "DMG creation failed"
    exit 1
fi

# Optional: Code signing information
if [ -n "$CODESIGN_IDENTITY" ]; then
    print_status "Code signing with identity: $CODESIGN_IDENTITY"
    codesign --force --verify --verbose --sign "$CODESIGN_IDENTITY" "dist/DDT4ALL.app"
    
    # Verify code signature
    if codesign --verify --verbose "dist/DDT4ALL.app"; then
        print_status "Code signing successful"
    else
        print_error "Code signing failed"
        exit 1
    fi
    
    # Optional: Notarization (requires Apple Developer account)
    if [ -n "$NOTARIZE_USERNAME" ] && [ -n "$NOTARIZE_PASSWORD" ]; then
        print_status "Submitting for notarization..."
        xcrun notarytool submit "dist/DDT4ALL.dmg" \
            --apple-id "$NOTARIZE_USERNAME" \
            --password "$NOTARIZE_PASSWORD" \
            --team-id "$TEAM_ID" \
            --wait
    fi
else
    print_warning "No code signing identity set. Set CODESIGN_IDENTITY environment variable for signed builds."
    print_warning "Example: export CODESIGN_IDENTITY='Developer ID Application: Your Name (XXXXXXXXXX)'"
fi

print_status "All done! 🎉"