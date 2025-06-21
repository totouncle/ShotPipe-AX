@echo off
title 🎬 ShotPipe 완전 자동 설치 (GitHub 다운로드)
chcp 65001 >nul
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              🚀 ShotPipe 완전 자동 설치                         ║
echo ║        GitHub에서 최신 코드 다운로드 + 빌드 + 설치               ║
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

echo 🎯 이 스크립트는 다음을 자동으로 수행합니다:
echo    1. Python 자동 설치 (필요시)
echo    2. Git 자동 설치 (필요시)
echo    3. NSIS 자동 설치 (필요시)  
echo    4. ExifTool 자동 설치
echo    5. GitHub에서 ShotPipe 소스코드 다운로드
echo    6. ShotPipe 빌드 및 설치
echo    7. 바탕화면 바로가기 생성
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
    echo [0/7] Chocolatey 패키지 관리자 설치 중...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    call refreshenv
)

:: 1. Python 설치
echo.
echo [1/7] Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo 📥 Python 설치 중... (약 5분)
    choco install python3 -y
    call refreshenv
)
echo ✅ Python 설치 완료

:: 2. Git 설치
echo.
echo [2/7] Git 설치 확인 중...
git --version >nul 2>&1
if errorlevel 1 (
    echo 📥 Git 설치 중... (약 3분)
    choco install git -y
    call refreshenv
)
echo ✅ Git 설치 완료

:: 3. NSIS 설치
echo.
echo [3/7] NSIS 설치 확인 중...
where makensis >nul 2>&1
if errorlevel 1 (
    echo 📥 NSIS 설치 중... (약 2분)
    choco install nsis -y
    call refreshenv
)
echo ✅ NSIS 설치 완료

:: 4. ExifTool 설치
echo.
echo [4/7] ExifTool 설치 중...
if not exist "C:\Windows\exiftool.exe" (
    echo 📥 ExifTool 다운로드 중...
    powershell -Command "Invoke-WebRequest -Uri 'https://exiftool.org/exiftool-12.70.exe' -OutFile 'C:\Windows\exiftool.exe'"
)
echo ✅ ExifTool 설치 완료

:: 5. ShotPipe 소스코드 다운로드
echo.
echo [5/7] ShotPipe 소스코드 다운로드 중...
set "INSTALL_DIR=C:\ShotPipe_Build"
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

echo 📡 GitHub에서 최신 코드 다운로드 중... (약 2분)
git clone https://github.com/lennonvfx/AX_pipe.git .
if errorlevel 1 (
    echo ❌ GitHub 다운로드 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
echo ✅ 소스코드 다운로드 완료

:: 6. Python 의존성 설치
echo.
echo [6/7] Python 패키지 설치 중...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
echo ✅ Python 패키지 설치 완료

:: 7. ShotPipe 빌드 및 설치
echo.
echo [7/7] ShotPipe 빌드 및 설치 중...
echo 📦 이 과정은 5-10분 정도 소요됩니다... ☕

:: Windows Defender 예외 설정
powershell -Command "Add-MpPreference -ExclusionPath '%INSTALL_DIR%' -ErrorAction SilentlyContinue"

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
        echo 📂 빌드 폴더: %INSTALL_DIR%
        echo.
        echo 💡 다음 단계:
        echo    1. 바탕화면의 ShotPipe 아이콘을 더블클릭
        echo    2. 환영 마법사를 따라 초기 설정 완료
        echo    3. AI 생성 파일들을 업로드하고 Shotgrid에 연결!
        echo.
        
        :: 빌드 폴더 정리 옵션
        set /p cleanup="빌드 폴더를 삭제하시겠습니까? (디스크 공간 절약) (y/n): "
        if /i "%cleanup%"=="y" (
            cd /d C:\
            rmdir /s /q "%INSTALL_DIR%"
            echo ✅ 빌드 폴더 정리 완료
        )
        
        set /p launch="지금 ShotPipe를 실행하시겠습니까? (y/n): "
        if /i "%launch%"=="y" (
            start "" "%PROGRAMFILES%\ShotPipe\ShotPipe.exe"
        )
        
    ) else (
        echo ⚠️  자동 설치 실패. 수동 설치를 시도하세요.
        echo 📂 %INSTALL_DIR%\release_packages\ShotPipe_Setup.exe를 수동으로 실행해주세요.
        explorer "%INSTALL_DIR%\release_packages"
    )
    
) else (
    echo ❌ ShotPipe 빌드 실패
    echo 📋 오류 로그를 확인하고 문제를 해결해주세요.
    echo 📂 빌드 폴더: %INSTALL_DIR%
    explorer "%INSTALL_DIR%"
)

echo.
echo 🎬 ShotPipe 자동 설치가 완료되었습니다!
echo 💬 문제가 있으시면 GitHub 이슈로 문의해주세요.
pause 