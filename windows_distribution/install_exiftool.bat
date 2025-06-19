@echo off
title 📷 ExifTool 자동 설치 도구
chcp 65001 >nul
color 0D

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              📷 ExifTool 자동 설치 도구                         ║
echo ║            ShotPipe 메타데이터 처리 도구 설치                    ║
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

echo 🎯 ExifTool은 ShotPipe가 이미지/비디오 메타데이터를 처리하는 데 필요합니다.
echo.

:: 기존 설치 확인
where exiftool >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ExifTool이 이미 설치되어 있습니다!
    exiftool -ver
    echo.
    echo 💡 재설치나 업데이트가 필요한 경우만 계속 진행하세요.
    echo.
)

set /p confirm="ExifTool 설치를 진행하시겠습니까? (y/n): "
if /i not "%confirm%"=="y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 📥 ExifTool 설치 시작...

:: 임시 폴더 생성
if not exist "%TEMP%\exiftool_install" mkdir "%TEMP%\exiftool_install"
cd /d "%TEMP%\exiftool_install"

:: 최신 버전 다운로드
echo [1/4] 최신 ExifTool 다운로드 중...
echo 📡 서버에서 파일을 가져오는 중... (약 1-2분 소요)

:: PowerShell을 사용하여 최신 버전 다운로드
powershell -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://exiftool.org/exiftool-12.70.exe' -OutFile 'exiftool-k.exe' -UserAgent 'Mozilla/5.0' } catch { Write-Host '다운로드 실패: ' $_.Exception.Message; exit 1 }"

if not exist "exiftool-k.exe" (
    echo ❌ 다운로드 실패!
    echo.
    echo 🔧 수동 설치 방법:
    echo    1. https://exiftool.org/ 접속
    echo    2. Windows Executable 다운로드
    echo    3. exiftool(-k).exe를 exiftool.exe로 이름 변경
    echo    4. C:\Windows\ 폴더에 복사
    echo.
    start https://exiftool.org/
    pause
    exit /b 1
)

echo ✅ 다운로드 완료

:: ExifTool 설치 (여러 위치에 설치)
echo.
echo [2/4] ExifTool 설치 중...

:: 1. Windows 시스템 폴더에 설치 (전역 접근)
echo 📂 시스템 폴더에 설치 중...
copy "exiftool-k.exe" "C:\Windows\exiftool.exe" >nul 2>&1
if exist "C:\Windows\exiftool.exe" (
    echo ✅ C:\Windows\exiftool.exe 설치 완료
) else (
    echo ⚠️  시스템 폴더 설치 실패
)

:: 2. Program Files 폴더에 설치
echo 📂 Program Files에 설치 중...
if not exist "C:\Program Files\ExifTool" mkdir "C:\Program Files\ExifTool"
copy "exiftool-k.exe" "C:\Program Files\ExifTool\exiftool.exe" >nul 2>&1
if exist "C:\Program Files\ExifTool\exiftool.exe" (
    echo ✅ C:\Program Files\ExifTool\exiftool.exe 설치 완료
) else (
    echo ⚠️  Program Files 설치 실패
)

:: 3. ShotPipe 폴더에 설치 (있는 경우)
if exist "%PROGRAMFILES%\ShotPipe" (
    echo 📂 ShotPipe 폴더에 설치 중...
    copy "exiftool-k.exe" "%PROGRAMFILES%\ShotPipe\exiftool.exe" >nul 2>&1
    if exist "%PROGRAMFILES%\ShotPipe\exiftool.exe" (
        echo ✅ ShotPipe 폴더에 설치 완료
    )
)

:: 4. 현재 프로젝트 vendor 폴더에 설치
if exist "%~dp0vendor" (
    echo 📂 Vendor 폴더에 설치 중...
    copy "exiftool-k.exe" "%~dp0vendor\exiftool.exe" >nul 2>&1
    if exist "%~dp0vendor\exiftool.exe" (
        echo ✅ Vendor 폴더에 설치 완료
    )
)

:: PATH 환경변수에 추가
echo.
echo [3/4] PATH 환경변수 설정 중...

:: Program Files\ExifTool을 PATH에 추가
powershell -Command "$env:PATH += ';C:\Program Files\ExifTool'; [Environment]::SetEnvironmentVariable('PATH', $env:PATH, 'Machine')" 2>nul

echo ✅ PATH 환경변수 설정 완료

:: 설치 확인
echo.
echo [4/4] 설치 확인 중...

:: 환경변수 새로고침
set "PATH=%PATH%;C:\Program Files\ExifTool;C:\Windows"

:: ExifTool 실행 테스트
where exiftool >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ExifTool 설치 성공!
    echo.
    echo 📋 설치된 버전 정보:
    exiftool -ver 2>nul
    echo.
) else (
    :: 직접 실행 테스트
    if exist "C:\Windows\exiftool.exe" (
        echo ✅ ExifTool 설치 성공!
        echo.
        echo 📋 설치된 버전 정보:
        "C:\Windows\exiftool.exe" -ver 2>nul
        echo.
    ) else (
        echo ❌ ExifTool 설치 실패
        echo.
        echo 🔧 문제 해결:
        echo    1. 컴퓨터 재시작
        echo    2. 환경변수 새로고침
        echo    3. 수동 설치 시도
        echo.
    )
)

:: 정리
echo 🧹 임시 파일 정리 중...
cd /d "%~dp0"
rmdir /s /q "%TEMP%\exiftool_install" 2>nul

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    ✅ 설치 완료!                                ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 ExifTool 설치가 완료되었습니다!
echo.
echo 📍 설치 위치:
if exist "C:\Windows\exiftool.exe" echo    • C:\Windows\exiftool.exe
if exist "C:\Program Files\ExifTool\exiftool.exe" echo    • C:\Program Files\ExifTool\exiftool.exe
if exist "%PROGRAMFILES%\ShotPipe\exiftool.exe" echo    • %PROGRAMFILES%\ShotPipe\exiftool.exe
echo.
echo 💡 이제 ShotPipe가 이미지/비디오 메타데이터를 정상적으로 처리할 수 있습니다!
echo.
echo 🔄 중요: 컴퓨터를 재시작하거나 새 명령 프롬프트에서 환경변수가 적용됩니다.
echo.

:: 테스트 실행 옵션
set /p test="간단한 테스트를 실행하시겠습니까? (y/n): "
if /i "%test%"=="y" (
    echo.
    echo 🧪 ExifTool 테스트 중...
    if exist "C:\Windows\exiftool.exe" (
        "C:\Windows\exiftool.exe" -ver
        echo ✅ 테스트 성공!
    ) else (
        echo ⚠️  PATH에서 exiftool을 찾을 수 없습니다. 재시작 후 다시 시도해주세요.
    )
)

echo.
echo 🎬 ExifTool 설치가 완료되었습니다!
pause 