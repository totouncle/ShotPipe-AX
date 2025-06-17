@echo off
chcp 65001
cls
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🎬 ShotPipe v1.3.0 🎬                    ║
echo ║              AI Generated File → Shotgrid                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ShotPipe 실행
echo 🚀 ShotPipe 시작 중...
echo.

:: Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo.
    echo 📥 Python 다운로드: https://python.org/downloads/
    echo 💡 설치 시 "Add Python to PATH" 체크 필수!
    echo.
    echo 또는 setup_portable.bat를 먼저 실행해주세요.
    pause
    exit /b 1
)

:: 가상환경이 있으면 활성화
if exist "venv\Scripts\activate.bat" (
    echo 🔄 가상환경 활성화...
    call venv\Scripts\activate.bat
)

:: ShotPipe 실행
echo ✨ ShotPipe 실행!
python main.py

if errorlevel 1 (
    echo.
    echo ❌ 실행 중 오류가 발생했습니다.
    echo 💡 setup_portable.bat를 먼저 실행해보세요.
    echo.
    pause
)
