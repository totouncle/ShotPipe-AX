@echo off
title 🎯 ShotPipe 초보자용 원클릭 빌드 시스템
chcp 65001 >nul
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              🚀 ShotPipe 초보자용 원클릭 빌드 시스템             ║
echo ║                    Windows 인스톨러 자동 생성                    ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 💡 이 스크립트는 초보자도 쉽게 ShotPipe 인스톨러를 만들 수 있습니다.
echo 📝 사전 준비: Python 3.8+, NSIS 설치 필요
echo.

:: 사용자 확인
set /p confirm="계속 진행하시겠습니까? (y/n): "
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🔍 시스템 환경 검사 중...

:: Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Python이 설치되어 있지 않습니다!
    echo.
    echo 📥 Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 접속
    echo 2. 최신 버전 다운로드
    echo 3. 설치 시 "Add Python to PATH" 체크 필수!
    echo 4. 설치 후 컴퓨터 재시작
    echo.
    set /p opensite="Python 다운로드 페이지를 열까요? (y/n): "
    if /i "%opensite%"=="y" (
        start https://www.python.org/downloads/
    )
    pause
    exit /b 1
)

:: NSIS 설치 확인
where makensis >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ NSIS가 설치되어 있지 않습니다!
    echo.
    echo 📥 NSIS 설치 방법:
    echo 1. https://nsis.sourceforge.io/Download 접속
    echo 2. NSIS 3.x 다운로드
    echo 3. 기본 설정으로 설치
    echo 4. 설치 후 컴퓨터 재시작
    echo.
    set /p opensite="NSIS 다운로드 페이지를 열까요? (y/n): "
    if /i "%opensite%"=="y" (
        start https://nsis.sourceforge.io/Download
    )
    pause
    exit /b 1
)

echo ✅ Python 설치 확인
python --version
echo ✅ NSIS 설치 확인
makensis /VERSION

echo.
echo 🎯 모든 사전 요구사항이 충족되었습니다!
echo.
echo 📦 이제 ShotPipe 인스톨러를 빌드합니다...
echo ⏱️  예상 소요시간: 5-10분 (커피 한 잔 ☕)
echo.

set /p final_confirm="최종 빌드를 시작하시겠습니까? (y/n): "
if /i not "%final_confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🚀 빌드 시작!
echo ═══════════════════════════════════════
echo.

:: 실제 빌드 실행
call build_all_distributions.bat

:: 결과 확인
echo.
echo ═══════════════════════════════════════
echo 🎊 빌드 완료 확인
echo ═══════════════════════════════════════

if exist "release_packages\ShotPipe_Setup.exe" (
    echo.
    echo ✅ 성공! ShotPipe 인스톨러가 생성되었습니다!
    echo.
    echo 📁 생성된 파일 위치:
    echo    %cd%\release_packages\ShotPipe_Setup.exe
    echo.
    
    for %%A in ("release_packages\ShotPipe_Setup.exe") do (
        set /a "filesize=%%~zA / 1048576"
    )
    echo 📏 파일 크기: %filesize% MB
    echo.
    echo 🎯 이제 이 파일을 사용자에게 전달하면 됩니다!
    echo.
    echo 💡 사용자 안내사항:
    echo    1. ShotPipe_Setup.exe 더블클릭
    echo    2. "알 수 없는 게시자" 경고 시 → "추가 정보" → "실행"
    echo    3. 설치 완료 후 바탕화면 바로가기로 실행
    echo.
    
    set /p open_folder="📂 결과 폴더를 열어볼까요? (y/n): "
    if /i "%open_folder%"=="y" (
        explorer release_packages
    )
    
) else (
    echo.
    echo ❌ 빌드 실패했습니다.
    echo.
    echo 🔍 문제 해결 방법:
    echo 1. 위의 에러 메시지 확인
    echo 2. 관리자 권한으로 다시 실행
    echo 3. 디스크 공간 확인 (최소 2GB 필요)
    echo 4. 바이러스 백신 프로그램 일시 비활성화
    echo.
)

echo.
echo 🎬 빌드 작업이 완료되었습니다!
echo.
pause