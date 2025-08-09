@echo off
echo ========================================
echo 🎬 ShotPipe Launcher
echo ========================================
echo.

REM Move to script directory
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
    echo.
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Check if packages are installed
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo 📦 Installing required packages...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install six
    echo ✅ Packages installed
    echo.
)

REM Run ShotPipe
echo 🚀 Starting ShotPipe...
echo ========================================
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ An error occurred. Check the message above.
    pause
)