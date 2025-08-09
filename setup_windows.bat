@echo off
echo ========================================
echo 🔧 ShotPipe Windows Setup
echo ========================================
echo.

REM Move to script directory
cd /d "%~dp0"

REM Check Python installation
echo 📋 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed!
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo ✅ Virtual environment created
)
echo.

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo 📦 Installing requirements...
pip install -r requirements.txt
echo.

REM Install additional dependency
echo 📦 Installing additional dependencies...
pip install six
echo.

REM Test imports
echo 🧪 Testing imports...
python -c "import PyQt5; print('✅ PyQt5 installed successfully')"
python -c "import yaml; print('✅ PyYAML installed successfully')"
python -c "import PIL; print('✅ Pillow installed successfully')"
python -c "import dotenv; print('✅ python-dotenv installed successfully')"
echo.

echo ========================================
echo ✅ Setup complete!
echo.
echo To run ShotPipe:
echo   1. Double-click run_shotpipe.bat
echo   2. Or run: python main.py
echo ========================================
pause