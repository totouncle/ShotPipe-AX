@echo off
title ShotPipe Portable Setup
echo ================================================
echo ShotPipe Portable 설정
echo ================================================
echo.

:: 필요한 폴더 생성
echo [1/4] 폴더 구조 생성 중...
if not exist "work" mkdir work
if not exist "work\input" mkdir work\input
if not exist "work\processed" mkdir work\processed
if not exist "backup" mkdir backup
if not exist "logs" mkdir logs

:: Python 경로 확인
echo.
echo [2/4] Python 경로 확인 중...
set PYTHON_PATH=python.exe
if exist "python\python.exe" (
    set PYTHON_PATH=python\python.exe
    echo ✅ Portable Python 발견
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python이 설치되어 있지 않습니다.
        echo.
        echo 다음 중 하나를 선택하세요:
        echo 1. Python Portable 다운로드: https://portablepython.com/
        echo 2. Python 공식 버전 설치: https://python.org
        echo.
        pause
        exit /b 1
    ) else (
        echo ✅ 시스템 Python 발견
    )
)

:: 가상환경 생성 (포터블의 경우)
echo.
echo [3/4] 의존성 확인 중...
if not exist "venv" (
    echo 가상환경 생성 중...
    %PYTHON_PATH% -m venv venv
)

:: 의존성 설치
call venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

:: 시작 스크립트 생성
echo.
echo [4/4] 실행 스크립트 생성 중...

:: ShotPipe 시작 스크립트 생성
echo @echo off > ShotPipe_Start.bat
echo title ShotPipe >> ShotPipe_Start.bat
echo cd /d "%%~dp0" >> ShotPipe_Start.bat
echo call venv\Scripts\activate.bat >> ShotPipe_Start.bat
echo python main.py >> ShotPipe_Start.bat
echo pause >> ShotPipe_Start.bat

:: 빠른 설정 스크립트 생성
echo @echo off > Quick_Setup.bat
echo title ShotPipe Quick Setup >> Quick_Setup.bat
echo cd /d "%%~dp0" >> Quick_Setup.bat
echo echo ShotPipe 빠른 설정 >> Quick_Setup.bat
echo echo ===================== >> Quick_Setup.bat
echo echo 1. 작업 폴더: work\input >> Quick_Setup.bat
echo echo 2. 출력 폴더: work\processed >> Quick_Setup.bat
echo echo 3. 백업 폴더: backup >> Quick_Setup.bat
echo echo. >> Quick_Setup.bat
echo echo 시작하려면 ShotPipe_Start.bat를 실행하세요. >> Quick_Setup.bat
echo pause >> Quick_Setup.bat

echo.
echo ================================================
echo ✅ 설정 완료!
echo ================================================
echo.
echo 📁 생성된 파일들:
echo   - ShotPipe_Start.bat  (ShotPipe 실행)
echo   - Quick_Setup.bat     (빠른 설정 가이드)
echo.
echo 📂 생성된 폴더들:
echo   - work\input\         (AI 생성 파일 넣는 곳)
echo   - work\processed\     (처리된 파일 저장)
echo   - backup\             (백업용)
echo   - logs\               (로그 파일)
echo.
echo 🚀 사용법:
echo   1. AI 생성 파일들을 work\input\ 폴더에 복사
echo   2. ShotPipe_Start.bat 더블클릭으로 실행
echo   3. 프로그램에서 작업 진행
echo.

set /p answer="지금 ShotPipe를 실행하시겠습니까? (y/n): "
if /i "%answer%"=="y" (
    start ShotPipe_Start.bat
)

echo.
echo 즐거운 작업 되세요! 🎬
pause
