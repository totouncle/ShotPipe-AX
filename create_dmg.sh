#!/bin/bash

# ============================================================================
# ShotPipe DMG Creator for macOS
# Creates a distributable DMG file for ShotPipe
# ============================================================================

set -e  # Exit on error

APP_NAME="ShotPipe"
VERSION="1.3.0"
DMG_NAME="${APP_NAME}_v${VERSION}_macOS.dmg"
VOLUME_NAME="${APP_NAME} ${VERSION}"
SOURCE_APP="${APP_NAME}.app"

echo "📀 Creating DMG for ${APP_NAME} v${VERSION}"
echo "=================================="
echo ""

# Check if app exists
if [ ! -d "${SOURCE_APP}" ]; then
    echo "❌ Error: ${SOURCE_APP} not found"
    echo "Please run ./build_macos.sh first"
    exit 1
fi

# Clean up any existing DMG
if [ -f "${DMG_NAME}" ]; then
    echo "🧹 Removing existing DMG..."
    rm "${DMG_NAME}"
fi

# Create temporary directory for DMG contents
echo "📁 Creating temporary DMG directory..."
DMG_TEMP="dmg_temp"
rm -rf "${DMG_TEMP}"
mkdir "${DMG_TEMP}"

# Copy app to temporary directory
echo "📋 Copying ${SOURCE_APP}..."
cp -R "${SOURCE_APP}" "${DMG_TEMP}/"

# Create symbolic link to Applications folder
echo "🔗 Creating Applications folder link..."
ln -s /Applications "${DMG_TEMP}/Applications"

# Add README and LICENSE if they exist
if [ -f "README.md" ]; then
    cp "README.md" "${DMG_TEMP}/"
    echo "📄 Added README.md"
fi

if [ -f "LICENSE.txt" ]; then
    cp "LICENSE.txt" "${DMG_TEMP}/"
    echo "📄 Added LICENSE.txt"
fi

# Create .DS_Store for custom DMG appearance (optional)
# This requires additional tools like create-dmg or dmgcanvas

# Create DMG
echo ""
echo "💿 Creating DMG file..."
hdiutil create -volname "${VOLUME_NAME}" \
    -srcfolder "${DMG_TEMP}" \
    -ov \
    -format UDZO \
    "${DMG_NAME}"

# Clean up temporary directory
echo "🧹 Cleaning up..."
rm -rf "${DMG_TEMP}"

# Get DMG size
DMG_SIZE=$(du -h "${DMG_NAME}" | cut -f1)

echo ""
echo "✅ DMG created successfully!"
echo "=================================="
echo ""
echo "📀 File: ${DMG_NAME}"
echo "📏 Size: ${DMG_SIZE}"
echo ""
echo "🔐 Next steps for distribution:"
echo "1. Code sign the DMG:"
echo "   codesign --sign 'Developer ID Application: Your Name' ${DMG_NAME}"
echo ""
echo "2. Notarize the DMG:"
echo "   xcrun altool --notarize-app --file ${DMG_NAME} --type osx --primary-bundle-id com.shotpipe.app"
echo ""
echo "3. Staple the notarization:"
echo "   xcrun stapler staple ${DMG_NAME}"
echo ""