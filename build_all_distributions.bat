@echo off
title ShotPipe 전체 배포 패키지 빌드
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    🚀 ShotPipe 마스터 빌드                      ║
echo ║               원클릭 설치 배포 패키지 생성 도구                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: 시작 시간 기록
echo 🕐 빌드 시작: %date% %time%
echo.

:: 환경 확인
echo [1/7] 빌드 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

where makensis >nul 2>&1
if errorlevel 1 (
    echo ⚠️  NSIS가 설치되어 있지 않습니다. 인스톨러는 생성되지 않습니다.
    set NSIS_AVAILABLE=false
) else (
    echo ✅ NSIS 발견
    set NSIS_AVAILABLE=true
)

:: 기존 배포 폴더 정리
echo.
echo [2/7] 기존 배포 파일 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "release_packages" rmdir /s /q release_packages
mkdir release_packages

:: 독립형 실행파일 빌드
echo.
echo [3/7] 독립형 실행파일 빌드 중...
echo 이 과정은 5-10분 정도 소요됩니다...
call build_windows_standalone.bat
if not exist "dist\ShotPipe.exe" (
    echo ❌ 독립형 실행파일 빌드 실패
    pause
    exit /b 1
)

echo ✅ 독립형 실행파일 빌드 완료

:: 파일 크기 확인
for %%A in ("dist\ShotPipe.exe") do (
    set /a "exe_size=%%~zA / 1048576"
)

:: 포터블 버전 생성
echo.
echo [4/7] 포터블 버전 생성 중...
mkdir "release_packages\ShotPipe_Portable"
copy "dist\ShotPipe.exe" "release_packages\ShotPipe_Portable\"
copy "README.md" "release_packages\ShotPipe_Portable\"
copy "WINDOWS_USER_GUIDE.md" "release_packages\ShotPipe_Portable\"
copy "LICENSE.txt" "release_packages\ShotPipe_Portable\"

:: 포터블 실행 스크립트 생성
echo @echo off > "release_packages\ShotPipe_Portable\ShotPipe_Start.bat"
echo title ShotPipe ^| AI Generated File → Shotgrid >> "release_packages\ShotPipe_Portable\ShotPipe_Start.bat"
echo echo 🎬 ShotPipe 시작 중... >> "release_packages\ShotPipe_Portable\ShotPipe_Start.bat"
echo ShotPipe.exe >> "release_packages\ShotPipe_Portable\ShotPipe_Start.bat"

:: 포터블 README 생성
echo # 🎬 ShotPipe Portable v1.3.0 > "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo. >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo 🚀 빠른 시작: >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo 1. ShotPipe_Start.bat 더블클릭 >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo 2. 첫 실행 시 설정 마법사 진행 >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo 3. AI 생성 파일들을 처리하고 Shotgrid에 업로드! >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo. >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"
echo 💡 도움말: F1 키 또는 WINDOWS_USER_GUIDE.md 참조 >> "release_packages\ShotPipe_Portable\README_PORTABLE.txt"

echo ✅ 포터블 버전 생성 완료

:: 인스톨러 생성 (NSIS가 있는 경우)
echo.
if "%NSIS_AVAILABLE%"=="true" (
    echo [5/7] NSIS 인스톨러 생성 중...
    call build_installer.bat
    if exist "ShotPipe_Setup.exe" (
        move "ShotPipe_Setup.exe" "release_packages\"
        for %%A in ("release_packages\ShotPipe_Setup.exe") do (
            set /a "installer_size=%%~zA / 1048576"
        )
        echo ✅ 인스톨러 생성 완료
    ) else (
        echo ⚠️  인스톨러 생성 실패
    )
) else (
    echo [5/7] NSIS 인스톨러 생성 건너뛰기 (NSIS 없음)
)

:: 포터블 버전 압축
echo.
echo [6/7] 배포 패키지 압축 중...

:: PowerShell을 사용하여 ZIP 생성
powershell -command "Compress-Archive -Path 'release_packages\ShotPipe_Portable' -DestinationPath 'release_packages\ShotPipe_v1.3.0_Portable.zip' -Force"
if exist "release_packages\ShotPipe_v1.3.0_Portable.zip" (
    echo ✅ 포터블 ZIP 생성 완료
) else (
    echo ⚠️  ZIP 생성 실패 - 수동으로 압축해주세요
)

:: 체크섬 생성
echo.
echo [7/7] 배포 패키지 검증 정보 생성 중...
echo # ShotPipe v1.3.0 배포 패키지 > "release_packages\CHECKSUMS.txt"
echo 생성일시: %date% %time% >> "release_packages\CHECKSUMS.txt"
echo. >> "release_packages\CHECKSUMS.txt"

if exist "release_packages\ShotPipe_Setup.exe" (
    echo ## Windows 인스톨러 >> "release_packages\CHECKSUMS.txt"
    echo 파일명: ShotPipe_Setup.exe >> "release_packages\CHECKSUMS.txt"
    echo 크기: %installer_size% MB >> "release_packages\CHECKSUMS.txt"
    echo 설명: 원클릭 설치, 관리자 권한 필요 >> "release_packages\CHECKSUMS.txt"
    echo. >> "release_packages\CHECKSUMS.txt"
)

echo ## 포터블 버전 >> "release_packages\CHECKSUMS.txt"
echo 파일명: ShotPipe_v1.3.0_Portable.zip >> "release_packages\CHECKSUMS.txt"
echo 크기: 약 %exe_size% MB (압축 후) >> "release_packages\CHECKSUMS.txt"
echo 설명: 압축 해제 후 바로 실행 가능 >> "release_packages\CHECKSUMS.txt"
echo. >> "release_packages\CHECKSUMS.txt"

echo ## 사용법 >> "release_packages\CHECKSUMS.txt"
echo 1. 초보자: ShotPipe_Setup.exe 사용 (권장) >> "release_packages\CHECKSUMS.txt"
echo 2. 고급 사용자: 포터블 버전 사용 >> "release_packages\CHECKSUMS.txt"
echo 3. 문제 발생 시: WINDOWS_USER_GUIDE.md 참조 >> "release_packages\CHECKSUMS.txt"

:: 빌드 완료 요약
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    🎉 빌드 완료!                                ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 📦 생성된 배포 패키지:
echo.

if exist "release_packages\ShotPipe_Setup.exe" (
    echo ✅ ShotPipe_Setup.exe (%installer_size% MB)
    echo    → 초보자용 원클릭 인스톨러
    echo    → 바탕화면 바로가기, 시작메뉴 등록
    echo    → Windows 10/11 지원
    echo.
)

if exist "release_packages\ShotPipe_v1.3.0_Portable.zip" (
    echo ✅ ShotPipe_v1.3.0_Portable.zip (~%exe_size% MB)
    echo    → 설치 없이 바로 실행
    echo    → USB 등에 복사하여 이동 가능
    echo    → ShotPipe_Start.bat으로 실행
    echo.
)

echo 📋 사용자 가이드:
echo    • WINDOWS_USER_GUIDE.md - 상세 사용법
echo    • 프로그램 내 F1 키 - 즉시 도움말
echo.

echo 💡 배포 시 유의사항:
echo    • Windows Defender에서 차단될 수 있음 (정상)
echo    • "추가 정보" → "실행" 클릭하도록 안내
echo    • 첫 실행 시 설정 마법사가 나타남
echo.

echo 🕐 총 빌드 시간: %time%
echo.

:: 탐색기에서 결과 폴더 열기
set /p open_result="release_packages 폴더를 열어서 결과를 확인하시겠습니까? (y/n): "
if /i "%open_result%"=="y" (
    explorer release_packages
)

echo.
echo 🎬 ShotPipe 배포 준비 완료! 즐거운 배포 되세요!
pause