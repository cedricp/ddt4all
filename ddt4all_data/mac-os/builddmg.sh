#!/bin/sh
pyinstaller --noconfirm main.spec
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/DDT4ALL.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/DDT4ALL.dmg" && rm "dist/DDT4ALL.dmg"
create-dmg \
  --volname "DDT4ALL" \
  --volicon "../icons/obd.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "DDT4ALL.app" 175 120 \
  --hide-extension "DDT4ALL.app" \
  --app-drop-link 425 120 \
  "dist/DDT4ALL.dmg" \
  "dist/dmg/"
