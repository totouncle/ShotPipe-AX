@echo off
title ShotPipe 인스톨러 빌드
chcp 65001 >nul
echo ================================================================
echo 🎯 ShotPipe 인스톨러 빌드 스크립트
echo ================================================================
echo.

:: NSIS 설치 확인
echo [1/5] NSIS 설치 확인 중...
where makensis >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ NSIS 설치 확인 완료
    makensis /VERSION
) else (
    echo ❌ NSIS가 설치되어 있지 않습니다.
    echo.
    echo 📥 NSIS 다운로드 및 설치:
    echo    https://nsis.sourceforge.io/Download
    echo.
    echo 💡 설치 후 시스템 재시작이 필요할 수 있습니다.
    echo.
    
    set /p download="NSIS 다운로드 페이지를 열시겠습니까? (y/n): "
    if /i "%download%"=="y" (
        start https://nsis.sourceforge.io/Download
    )
    pause
    exit /b 1
)

:: ShotPipe.exe 확인
echo.
echo [2/5] 실행파일 확인 중...
if exist "dist\ShotPipe.exe" (
    echo ✅ ShotPipe.exe 발견
    for %%A in ("dist\ShotPipe.exe") do (
        set /a "filesize=%%~zA / 1048576"
    )
    echo 📏 파일 크기: %filesize% MB
) else (
    echo ❌ dist\ShotPipe.exe를 찾을 수 없습니다.
    echo.
    echo 💡 먼저 다음을 실행하세요:
    echo    build_windows_standalone.bat
    echo.
    pause
    exit /b 1
)

:: 아이콘 파일 확인
echo.
echo [3/5] 리소스 파일 확인 중...
if exist "shotpipe.ico" (
    echo ✅ 아이콘 파일 발견
) else (
    echo ⚠️  아이콘 파일 없음 - 기본 아이콘 사용
)

if exist "LICENSE.txt" (
    echo ✅ 라이센스 파일 발견
) else (
    echo ⚠️  라이센스 파일 없음
)

:: 인스톨러 빌드
echo.
echo [4/5] 인스톨러 빌드 중...
echo 이 과정은 1-2분 정도 소요됩니다...
echo.

makensis ShotPipe_Installer.nsi

:: 빌드 결과 확인
echo.
echo [5/5] 빌드 결과 확인 중...
if exist "ShotPipe_Setup.exe" (
    echo ✅ 인스톨러 빌드 성공!
    
    :: 파일 크기 확인
    for %%A in ("ShotPipe_Setup.exe") do (
        set /a "installer_size=%%~zA / 1048576"
    )
    echo 📏 인스톨러 크기: %installer_size% MB
    
    echo.
    echo ================================================================
    echo 🎉 ShotPipe 인스톨러 빌드 완료!
    echo ================================================================
    echo.
    echo 📦 생성된 파일: ShotPipe_Setup.exe
    echo 💾 파일 크기: %installer_size% MB
    echo 🖥️  지원 OS: Windows 7/8/10/11 (64-bit)
    echo.
    echo 🚀 배포 방법:
    echo   1. ShotPipe_Setup.exe를 사용자에게 전달
    echo   2. 사용자는 더블클릭만으로 설치 완료
    echo   3. Windows Defender 경고 시 "추가 정보" → "실행" 안내
    echo.
    echo 💡 인스톨러 기능:
    echo   ✓ 원클릭 설치
    echo   ✓ 바탕화면 바로가기 생성
    echo   ✓ 시작메뉴 등록
    echo   ✓ 작업 폴더 자동 생성
    echo   ✓ 깔끔한 제거 기능
    echo.
    
    :: 테스트 실행 제안
    set /p test="인스톨러를 테스트해보시겠습니까? (y/n): "
    if /i "%test%"=="y" (
        echo.
        echo 🧪 인스톨러 테스트 실행...
        echo ⚠️  주의: 실제로 설치됩니다!
        timeout /t 3
        start "" "ShotPipe_Setup.exe"
    )
    
) else (
    echo ❌ 인스톨러 빌드 실패
    echo.
    echo 🔍 문제 해결 방법:
    echo 1. NSIS 스크립트 문법 오류 확인
    echo 2. 필요한 파일들이 모두 있는지 확인
    echo 3. NSIS 로그에서 오류 메시지 확인
    echo 4. 관리자 권한으로 실행해보기
    echo.
    pause
    exit /b 1
)

:: 최종 안내
echo.
set /p open_folder="현재 폴더를 열어서 인스톨러를 확인하시겠습니까? (y/n): "
if /i "%open_folder%"=="y" (
    explorer .
)

echo.
echo 즐거운 배포 되세요! 🚀
pause