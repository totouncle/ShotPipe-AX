@echo off
chcp 65001
cls
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    ShotPipe Windows Builder                  ║
echo ║                         v1.3.0                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ 관리자 권한으로 실행 중
) else (
    echo ⚠️  일반 사용자 권한으로 실행 중 (권장: 관리자 권한)
)
echo.

:: Python 설치 확인
echo [1/8] Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo.
    echo 📥 Python 다운로드: https://python.org/downloads/
    echo 💡 설치 시 "Add Python to PATH" 체크 필수!
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
    echo ✅ Python %PYTHON_VERSION% 발견
)
echo.

:: Git 확인 (선택사항)
echo [2/8] Git 확인 중...
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git이 설치되어 있지 않습니다 (선택사항)
) else (
    echo ✅ Git 발견
)
echo.

:: 디렉토리 확인
echo [3/8] 프로젝트 파일 확인 중...
if not exist "main.py" (
    echo ❌ main.py 파일을 찾을 수 없습니다.
    echo 💡 ShotPipe 소스코드가 있는 폴더에서 실행해주세요.
    echo.
    pause
    exit /b 1
)
if not exist "shotpipe" (
    echo ❌ shotpipe 폴더를 찾을 수 없습니다.
    echo 💡 완전한 소스코드가 필요합니다.
    echo.
    pause
    exit /b 1
)
echo ✅ 프로젝트 파일 확인 완료

:: 가상환경 생성
echo.
echo [4/8] 가상환경 설정 중...
if exist "venv" (
    echo ♻️  기존 가상환경 발견, 재사용합니다.
) else (
    echo 🔨 새 가상환경 생성 중...
    python -m venv venv
)

:: 가상환경 활성화
echo 🔄 가상환경 활성화...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화 완료

:: 의존성 설치
echo.
echo [5/8] 의존성 설치 중...
echo 📦 pip 업그레이드...
python -m pip install --upgrade pip --quiet

echo 📦 기본 의존성 설치...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ 의존성 설치 실패
    echo 💡 인터넷 연결과 requirements.txt 파일을 확인해주세요.
    pause
    exit /b 1
)

echo 📦 PyInstaller 설치...
pip install pyinstaller --quiet
echo ✅ 의존성 설치 완료

:: 빌드 디렉토리 정리
echo.
echo [6/8] 빌드 환경 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo ✅ 이전 빌드 파일 정리 완료

:: PyInstaller 실행
echo.
echo [7/8] 실행파일 생성 중... ⏳
echo 💡 이 과정은 몇 분이 걸릴 수 있습니다.
echo.

pyinstaller shotpipe.spec --clean --noconfirm
if errorlevel 1 (
    echo ❌ 빌드 실패
    echo 💡 로그를 확인하여 문제를 해결해주세요.
    pause
    exit /b 1
)

:: 결과 확인
echo.
echo [8/8] 빌드 결과 확인 중...
if exist "dist\ShotPipe.exe" (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║                        🎉 빌드 성공! 🎉                      ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    
    :: 파일 크기 확인
    for %%A in ("dist\ShotPipe.exe") do set SIZE=%%~zA
    set /a SIZEMB=SIZE/1024/1024
    
    echo 📁 생성된 파일: dist\ShotPipe.exe
    echo 📏 파일 크기: %SIZEMB%MB
    echo 📍 전체 경로: %CD%\dist\ShotPipe.exe
    echo.
    
    :: 추가 파일들 복사
    echo 📋 사용자 가이드 복사 중...
    if exist "WINDOWS_USER_GUIDE.md" copy "WINDOWS_USER_GUIDE.md" "dist\" >nul
    if exist "README.md" copy "README.md" "dist\" >nul
    
    :: 배포 패키지 생성
    echo 📦 배포 패키지 생성 중...
    cd dist
    
    echo @echo off > README.txt
    echo ShotPipe v1.3.0 - Windows Edition >> README.txt
    echo ================================== >> README.txt
    echo. >> README.txt
    echo 🚀 Quick Start: >> README.txt
    echo 1. Double-click ShotPipe.exe >> README.txt
    echo 2. Press F1 for manual >> README.txt
    echo 3. Start with "File Processing" tab >> README.txt
    echo. >> README.txt
    echo 📞 Support: Check logs for troubleshooting >> README.txt
    echo 💡 User Guide: WINDOWS_USER_GUIDE.md >> README.txt
    echo. >> README.txt
    echo Happy editing! 🎬 >> README.txt
    
    cd ..
    
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║                     배포 준비 완료! 📦                       ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    echo 📂 배포할 파일들:
    echo    - dist\ShotPipe.exe           (메인 실행파일)
    echo    - dist\README.txt             (빠른 시작 가이드)
    echo    - dist\WINDOWS_USER_GUIDE.md  (상세 사용자 가이드)
    echo.
    echo 🎯 배포 방법:
    echo    1. dist 폴더 전체를 압축
    echo    2. 사용자에게 전달
    echo    3. 사용자는 ShotPipe.exe 실행
    echo.
    
    set /p TEST_RUN="지금 ShotPipe를 테스트 실행하시겠습니까? (y/n): "
    if /i "%TEST_RUN%"=="y" (
        echo.
        echo 🚀 ShotPipe 실행 중...
        start "" "dist\ShotPipe.exe"
        echo ✅ 실행 완료! 프로그램을 확인해보세요.
    )
    
) else (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║                      ❌ 빌드 실패 ❌                         ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    echo 💡 문제 해결 방법:
    echo    1. Python 버전 확인 (3.7+ 필요)
    echo    2. 인터넷 연결 상태 확인
    echo    3. requirements.txt 파일 존재 확인
    echo    4. 디스크 공간 확인 (최소 2GB 필요)
    echo    5. 바이러스 백신 일시 비활성화
    echo.
    echo 📋 로그 파일을 확인하여 자세한 오류 내용을 확인하세요.
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo 빌드 과정 완료! 
echo 문제가 있으면 로그를 확인하거나 개발팀에 문의하세요.
echo ═══════════════════════════════════════════════════════════════
pause
