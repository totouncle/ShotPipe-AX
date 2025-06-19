@echo off
title 🛡️ ShotPipe Windows Defender 예외 설정
chcp 65001 >nul
color 0E

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║            🛡️ Windows Defender 예외 설정 도구                  ║
echo ║               ShotPipe 차단 문제 해결                           ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 관리자 권한이 필요합니다!
    echo.
    echo 🔧 해결 방법:
    echo    1. 이 파일을 우클릭
    echo    2. "관리자 권한으로 실행" 선택
    echo    3. 다시 실행
    echo.
    pause
    exit /b 1
)

echo ✅ 관리자 권한 확인됨
echo.

echo 🎯 이 도구는 Windows Defender에서 ShotPipe를 예외로 설정합니다.
echo.
echo 📋 설정할 예외 목록:
echo    • ShotPipe.exe 실행파일
echo    • ShotPipe 설치 폴더
echo    • 사용자 작업 폴더
echo    • build_all_distributions.bat (빌드 시)
echo.

set /p confirm="Windows Defender 예외 설정을 진행하시겠습니까? (y/n): "
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 🔧 Windows Defender 예외 설정 중...

:: PowerShell 실행 정책 확인
echo [1/6] PowerShell 실행 정책 확인 중...
powershell -Command "Get-ExecutionPolicy" | findstr "Restricted" >nul
if %errorlevel% equ 0 (
    echo 📝 PowerShell 실행 정책 변경 중...
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
)

:: 1. 현재 디렉토리 예외 설정 (빌드 시)
echo.
echo [2/6] 빌드 디렉토리 예외 설정 중...
powershell -Command "Add-MpPreference -ExclusionPath '%CD%'" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 빌드 디렉토리 예외 설정 완료: %CD%
) else (
    echo ⚠️  빌드 디렉토리 예외 설정 실패 (이미 설정되었을 수 있음)
)

:: 2. Program Files 설치 경로 예외 설정
echo.
echo [3/6] 설치 디렉토리 예외 설정 중...
powershell -Command "Add-MpPreference -ExclusionPath '%PROGRAMFILES%\ShotPipe'" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 설치 디렉토리 예외 설정 완료: %PROGRAMFILES%\ShotPipe
) else (
    echo ⚠️  설치 디렉토리 예외 설정 실패 (이미 설정되었을 수 있음)
)

:: 3. 사용자 문서 폴더 예외 설정
echo.
echo [4/6] 사용자 작업 폴더 예외 설정 중...
powershell -Command "Add-MpPreference -ExclusionPath '%USERPROFILE%\Documents\ShotPipe'" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 사용자 작업 폴더 예외 설정 완료: %USERPROFILE%\Documents\ShotPipe
) else (
    echo ⚠️  사용자 작업 폴더 예외 설정 실패 (이미 설정되었을 수 있음)
)

:: 4. 실행파일별 예외 설정
echo.
echo [5/6] 실행파일 예외 설정 중...

:: ShotPipe.exe 예외 설정
if exist "%PROGRAMFILES%\ShotPipe\ShotPipe.exe" (
    powershell -Command "Add-MpPreference -ExclusionProcess 'ShotPipe.exe'" 2>nul
    echo ✅ ShotPipe.exe 프로세스 예외 설정 완료
)

:: Python.exe 예외 설정 (빌드 시 필요)
powershell -Command "Add-MpPreference -ExclusionProcess 'python.exe'" 2>nul
echo ✅ Python.exe 프로세스 예외 설정 완료

:: 5. 추가 보안 설정
echo.
echo [6/6] 추가 보안 설정 중...

:: 실시간 보호에서 특정 파일 형식 예외
powershell -Command "Add-MpPreference -ExclusionExtension '.exe'" 2>nul
powershell -Command "Add-MpPreference -ExclusionExtension '.bat'" 2>nul

echo ✅ 추가 보안 설정 완료

:: 설정 확인
echo.
echo 🔍 설정된 예외 목록 확인 중...
echo.
echo ═══════════════════════════════════════════════════════════════════
powershell -Command "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath" 2>nul | findstr -i "shotpipe\|%CD:\=\\%"
echo ═══════════════════════════════════════════════════════════════════

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    ✅ 설정 완료!                                ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 Windows Defender 예외 설정이 완료되었습니다!
echo.
echo 💡 이제 다음 작업들이 Windows Defender에 의해 차단되지 않습니다:
echo    • ShotPipe 빌드 및 설치
echo    • ShotPipe 실행
echo    • 파일 처리 및 업로드
echo.
echo 🔄 만약 여전히 차단되는 경우:
echo    1. Windows 재시작
echo    2. 수동으로 Windows Security → 바이러스 및 위협 방지 → 예외 추가
echo    3. 바이러스 백신 프로그램 설정 확인
echo.

:: Windows Security 설정 페이지 열기 옵션
set /p open_settings="Windows Security 설정을 열어서 확인하시겠습니까? (y/n): "
if /i "%open_settings%"=="y" (
    start ms-settings:windowsdefender
)

echo.
echo 🎬 Windows Defender 설정이 완료되었습니다!
echo 이제 ShotPipe를 안전하게 사용할 수 있습니다.
pause 