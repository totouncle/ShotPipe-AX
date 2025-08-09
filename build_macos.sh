#!/bin/bash

# ============================================================================
# ShotPipe macOS Build Script
# AI Generated File → Shotgrid Automation Tool
# ============================================================================

set -e  # Exit on error

echo "🎬 ShotPipe macOS Build Script"
echo "=================================="
echo ""

# Check Python version
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.7+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Check for ExifTool
echo ""
echo "🔍 Checking for ExifTool..."
if ! command -v exiftool &> /dev/null; then
    echo "⚠️  ExifTool not found in PATH"
    echo "Installing ExifTool via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed"
        echo "Please install Homebrew from https://brew.sh"
        echo "Then run: brew install exiftool"
        exit 1
    fi
    
    brew install exiftool
    echo "✅ ExifTool installed"
else
    EXIFTOOL_VERSION=$(exiftool -ver)
    echo "✅ ExifTool $EXIFTOOL_VERSION found"
fi

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build dist
rm -rf ShotPipe.app
echo "✅ Previous builds cleaned"

# Build the application
echo ""
echo "🔨 Building ShotPipe.app..."
echo "This may take a few minutes..."

pyinstaller shotpipe.spec --clean --noconfirm

# Check if build was successful
if [ -f "dist/ShotPipe.app/Contents/MacOS/ShotPipe" ]; then
    echo ""
    echo "✅ Build successful!"
    
    # Get app size
    APP_SIZE=$(du -sh dist/ShotPipe.app | cut -f1)
    echo "📏 App size: $APP_SIZE"
    
    # Move app to root directory for easier access
    mv dist/ShotPipe.app .
    echo "📁 ShotPipe.app moved to project root"
    
    echo ""
    echo "🎉 Build completed successfully!"
    echo "=================================="
    echo ""
    echo "📱 To run the app:"
    echo "   open ShotPipe.app"
    echo ""
    echo "📦 To distribute:"
    echo "   Create a DMG file with: ./create_dmg.sh"
    echo ""
    echo "🔐 For distribution outside Mac App Store:"
    echo "   You'll need to code sign and notarize the app"
    echo "   See: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the error messages above"
    exit 1
fi

# Deactivate virtual environment
deactivate