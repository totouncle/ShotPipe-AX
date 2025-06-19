@echo off
title 🎬 ShotPipe 초보자용 완전 자동 설치
chcp 65001 >nul
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              🚀 ShotPipe 초보자용 원클릭 설치                   ║
echo ║        AI Generated File → Shotgrid Automation Tool             ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 💡 이 스크립트는 ShotPipe를 완전히 자동으로 설치합니다.
echo 📝 관리자 권한이 필요할 수 있습니다.
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

:: 사용자 확인
echo 🎯 이 스크립트는 다음을 자동으로 수행합니다:
echo    1. Python 자동 설치 (필요시)
echo    2. NSIS 자동 설치 (필요시)  
echo    3. ExifTool 자동 설치
echo    4. ShotPipe 빌드 및 설치
echo    5. 바탕화면 바로가기 생성
echo.
set /p confirm="계속 진행하시겠습니까? (y/n): "
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🔍 시스템 환경 검사 중...

:: 1. Python 설치 확인 및 자동 설치
echo [1/5] Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo 📥 Python 자동 설치를 시도합니다...
    
    :: Chocolatey 설치 확인
    choco --version >nul 2>&1
    if errorlevel 1 (
        echo 📦 Chocolatey 패키지 관리자 설치 중...
        powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    )
    
    echo 🐍 Python 설치 중... (약 5분 소요)
    choco install python3 -y
    
    :: PATH 새로고침
    call refreshenv
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python 자동 설치 실패. 수동 설치가 필요합니다.
        echo 🌐 Python 다운로드 페이지를 엽니다...
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
)
echo ✅ Python 설치 확인됨
python --version

:: 2. NSIS 설치 확인 및 자동 설치
echo.
echo [2/5] NSIS 설치 확인 중...
where makensis >nul 2>&1
if errorlevel 1 (
    echo ❌ NSIS가 설치되어 있지 않습니다.
    echo 📥 NSIS 자동 설치 중...
    choco install nsis -y
    call refreshenv
    
    where makensis >nul 2>&1
    if errorlevel 1 (
        echo ❌ NSIS 자동 설치 실패. 수동 설치가 필요합니다.
        echo 🌐 NSIS 다운로드 페이지를 엽니다...
        start https://nsis.sourceforge.io/Download
        pause
        exit /b 1
    )
)
echo ✅ NSIS 설치 확인됨

:: 3. ExifTool 자동 설치
echo.
echo [3/5] ExifTool 설치 확인 중...
where exiftool >nul 2>&1
if errorlevel 1 (
    echo ❌ ExifTool이 설치되어 있지 않습니다.
    echo 📥 ExifTool 자동 설치 중...
    
    :: ExifTool 다운로드 및 설치
    if not exist "C:\Windows\exiftool.exe" (
        echo 📥 ExifTool 다운로드 중...
        powershell -Command "Invoke-WebRequest -Uri 'https://exiftool.org/exiftool-12.70.exe' -OutFile 'C:\Windows\exiftool.exe'"
        
        if exist "C:\Windows\exiftool.exe" (
            echo ✅ ExifTool 설치 완료
        ) else (
            echo ⚠️  ExifTool 자동 설치 실패. 수동 설치가 필요할 수 있습니다.
        )
    )
) else (
    echo ✅ ExifTool 설치 확인됨
)

:: 4. ShotPipe 빌드
echo.
echo [4/5] ShotPipe 빌드 중...
echo 📦 이 과정은 5-10분 정도 소요됩니다...
call build_all_distributions.bat

:: 5. 설치 검증
echo.
echo [5/5] 설치 검증 중...
if exist "release_packages\ShotPipe_Setup.exe" (
    echo ✅ ShotPipe 빌드 성공!
    
    echo 🎯 자동 설치를 진행합니다...
    "release_packages\ShotPipe_Setup.exe" /S
    
    timeout /t 3 >nul
    
    if exist "%PROGRAMFILES%\ShotPipe\ShotPipe.exe" (
        echo ✅ ShotPipe 설치 완료!
        
        :: 추가 바탕화면 바로가기 생성 (보험용)
        if not exist "%USERPROFILE%\Desktop\ShotPipe.lnk" (
            powershell -Command "$WScriptShell = New-Object -ComObject WScript.Shell; $Shortcut = $WScriptShell.CreateShortcut('%USERPROFILE%\Desktop\ShotPipe.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\ShotPipe\ShotPipe.exe'; $Shortcut.WorkingDirectory = '%PROGRAMFILES%\ShotPipe'; $Shortcut.Description = 'AI Generated File to Shotgrid Automation Tool'; $Shortcut.Save()"
        )
        
        echo.
        echo ╔══════════════════════════════════════════════════════════════════╗
        echo ║                    🎉 설치 완료!                                ║
        echo ╚══════════════════════════════════════════════════════════════════╝
        echo.
        echo ✅ ShotPipe가 성공적으로 설치되었습니다!
        echo.
        echo 📍 설치 위치: %PROGRAMFILES%\ShotPipe\
        echo 🖥️  바탕화면 바로가기: ShotPipe.lnk
        echo 📚 사용자 가이드: %PROGRAMFILES%\ShotPipe\WINDOWS_USER_GUIDE.md
        echo.
        echo 💡 다음 단계:
        echo    1. 바탕화면의 ShotPipe 아이콘을 더블클릭
        echo    2. 환영 마법사를 따라 초기 설정 완료
        echo    3. AI 생성 파일들을 업로드하고 Shotgrid에 연결!
        echo.
        
        set /p launch="지금 ShotPipe를 실행하시겠습니까? (y/n): "
        if /i "%launch%"=="y" (
            start "" "%PROGRAMFILES%\ShotPipe\ShotPipe.exe"
        )
        
    ) else (
        echo ⚠️  자동 설치 실패. 수동 설치를 시도하세요.
        echo 📂 release_packages\ShotPipe_Setup.exe를 수동으로 실행해주세요.
        explorer release_packages
    )
    
) else (
    echo ❌ ShotPipe 빌드 실패
    echo 📋 오류 로그를 확인하고 문제를 해결해주세요.
)

echo.
echo 🎬 ShotPipe 자동 설치가 완료되었습니다!
echo 💬 문제가 있으시면 WINDOWS_USER_GUIDE.md를 참조해주세요.
pause 