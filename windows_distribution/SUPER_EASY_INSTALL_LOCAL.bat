@echo off
title 🎬 ShotPipe 로컬 소스 설치
chcp 65001 >nul
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              🚀 ShotPipe 로컬 소스 설치                         ║
echo ║        포함된 소스코드로 빌드 + 설치 (인터넷 불필요)              ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  관리자 권한이 필요합니다. 
    echo 우클릭 → "관리자 권한으로 실행"을 선택해주세요.
    pause
    exit /b 1
)

echo ✅ 관리자 권한 확인됨
echo.

:: 소스코드 폴더 확인
if not exist "source" (
    echo ❌ source 폴더를 찾을 수 없습니다!
    echo 📂 이 파일은 반드시 source 폴더와 같은 위치에 있어야 합니다.
    echo.
    echo 📋 폴더 구조:
    echo    windows_distribution/
    echo    ├── SUPER_EASY_INSTALL_LOCAL.bat  ← 이 파일
    echo    └── source/                       ← 소스코드 폴더
    echo        ├── main.py
    echo        ├── shotpipe/
    echo        └── ...
    pause
    exit /b 1
)

echo ✅ 소스코드 폴더 확인됨
echo.

echo 🎯 이 스크립트는 다음을 자동으로 수행합니다:
echo    1. Python 자동 설치 (필요시)
echo    2. NSIS 자동 설치 (필요시)  
echo    3. ExifTool 자동 설치
echo    4. 포함된 소스코드로 ShotPipe 빌드
echo    5. ShotPipe 설치 및 바탕화면 바로가기 생성
echo.
set /p confirm="계속 진행하시겠습니까? (y/n): "
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🔍 시스템 환경 검사 중...

:: Chocolatey 설치 (패키지 관리용)
choco --version >nul 2>&1
if errorlevel 1 (
    echo [0/5] Chocolatey 패키지 관리자 설치 중...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    call refreshenv
)

:: 1. Python 설치
echo.
echo [1/5] Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo 📥 Python 설치 중... (약 5분)
    choco install python3 -y
    call refreshenv
)
echo ✅ Python 설치 완료

:: 2. NSIS 설치
echo.
echo [2/5] NSIS 설치 확인 중...
where makensis >nul 2>&1
if errorlevel 1 (
    echo 📥 NSIS 설치 중... (약 2분)
    choco install nsis -y
    call refreshenv
)
echo ✅ NSIS 설치 완료

:: 3. ExifTool 설치
echo.
echo [3/5] ExifTool 설치 중...
if exist "source\vendor\exiftool.exe" (
    echo 📥 포함된 ExifTool 사용
    copy "source\vendor\exiftool.exe" "C:\Windows\exiftool.exe" >nul 2>&1
) else (
    if not exist "C:\Windows\exiftool.exe" (
        echo 📥 ExifTool 다운로드 중...
        powershell -Command "Invoke-WebRequest -Uri 'https://exiftool.org/exiftool-12.70.exe' -OutFile 'C:\Windows\exiftool.exe'"
    )
)
echo ✅ ExifTool 설치 완료

:: 4. 빌드 폴더 준비
echo.
echo [4/5] 빌드 환경 준비 중...
set "BUILD_DIR=%cd%\build_temp"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"

:: 소스코드 복사
echo 📂 소스코드 복사 중...
xcopy "source\*" "%BUILD_DIR%\" /E /I /Q /Y
cd /d "%BUILD_DIR%"

:: Windows Defender 예외 설정
powershell -Command "Add-MpPreference -ExclusionPath '%BUILD_DIR%' -ErrorAction SilentlyContinue"

:: Python 의존성 설치
echo 📦 Python 패키지 설치 중...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo ✅ 빌드 환경 준비 완료

:: 5. ShotPipe 빌드 및 설치
echo.
echo [5/5] ShotPipe 빌드 및 설치 중...
echo 📦 이 과정은 5-10분 정도 소요됩니다... ☕

call build_all_distributions.bat

:: 설치 검증 및 실행
if exist "release_packages\ShotPipe_Setup.exe" (
    echo ✅ ShotPipe 빌드 성공!
    
    echo 🎯 자동 설치를 진행합니다...
    "release_packages\ShotPipe_Setup.exe" /S
    
    timeout /t 5 >nul
    
    if exist "%PROGRAMFILES%\ShotPipe\ShotPipe.exe" (
        echo.
        echo ╔══════════════════════════════════════════════════════════════════╗
        echo ║                    🎉 설치 완료!                                ║
        echo ╚══════════════════════════════════════════════════════════════════╝
        echo.
        echo ✅ ShotPipe가 성공적으로 설치되었습니다!
        echo.
        echo 📍 설치 위치: %PROGRAMFILES%\ShotPipe\
        echo 🖥️  바탕화면 바로가기: ShotPipe.lnk
        echo 📂 빌드 폴더: %BUILD_DIR%
        echo.
        echo 💡 다음 단계:
        echo    1. 바탕화면의 ShotPipe 아이콘을 더블클릭
        echo    2. 환영 마법사를 따라 초기 설정 완료
        echo    3. AI 생성 파일들을 업로드하고 Shotgrid에 연결!
        echo.
        
        :: 빌드 폴더 정리 옵션
        set /p cleanup="빌드 폴더를 삭제하시겠습니까? (디스크 공간 절약) (y/n): "
        if /i "%cleanup%"=="y" (
            cd /d "%~dp0"
            rmdir /s /q "%BUILD_DIR%"
            echo ✅ 빌드 폴더 정리 완료
        )
        
        set /p launch="지금 ShotPipe를 실행하시겠습니까? (y/n): "
        if /i "%launch%"=="y" (
            start "" "%PROGRAMFILES%\ShotPipe\ShotPipe.exe"
        )
        
    ) else (
        echo ⚠️  자동 설치 실패. 수동 설치를 시도하세요.
        echo 📂 %BUILD_DIR%\release_packages\ShotPipe_Setup.exe를 수동으로 실행해주세요.
        explorer "%BUILD_DIR%\release_packages"
    )
    
) else (
    echo ❌ ShotPipe 빌드 실패
    echo 📋 오류 로그를 확인하고 문제를 해결해주세요.
    echo 📂 빌드 폴더: %BUILD_DIR%
    explorer "%BUILD_DIR%"
)

echo.
echo 🎬 ShotPipe 로컬 설치가 완료되었습니다!
pause 