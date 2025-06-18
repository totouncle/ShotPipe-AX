@echo off
title ShotPipe 독립형 실행파일 빌드
echo ================================================================
echo ShotPipe 독립형 실행파일 빌드 스크립트
echo ================================================================
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 관리자 권한으로 실행 중
) else (
    echo ⚠️  일반 사용자 권한으로 실행 중 (일부 기능 제한될 수 있음)
)

:: 환경 정리
echo [1/8] 빌드 환경 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "__pycache__" rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

:: Python 설치 확인
echo.
echo [2/8] Python 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요: https://python.org
    pause
    exit /b 1
)

python --version
echo ✅ Python 환경 확인 완료

:: 가상환경 생성/활성화
echo.
echo [3/8] 가상환경 설정 중...
if not exist "build_env" (
    echo 가상환경 생성 중...
    python -m venv build_env
)

echo 가상환경 활성화...
call build_env\Scripts\activate.bat

:: 의존성 업그레이드 및 설치
echo.
echo [4/8] 의존성 설치 중...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

:: PyInstaller 버전 확인
echo.
echo [5/8] 빌드 도구 확인 중...
pyinstaller --version
echo ✅ PyInstaller 설치 확인 완료

:: UPX 확인 (선택사항)
where upx >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ UPX 압축 도구 발견 - 최적화된 빌드 가능
) else (
    echo ⚠️  UPX 압축 도구 없음 - 일반 빌드로 진행
)

:: 빌드 실행
echo.
echo [6/8] 독립형 실행파일 빌드 중...
echo 이 과정은 5-10분 정도 소요될 수 있습니다...
echo.

pyinstaller shotpipe.spec

:: 빌드 결과 확인
echo.
echo [7/8] 빌드 결과 확인 중...
if exist "dist\ShotPipe.exe" (
    echo ✅ 빌드 성공!
    
    :: 파일 크기 확인
    for %%A in ("dist\ShotPipe.exe") do set filesize=%%~zA
    set /a "filesize_mb=%filesize% / 1048576"
    echo 📏 파일 크기: %filesize_mb% MB
    
    echo.
    echo 🎯 생성된 파일:
    echo    📁 dist\ShotPipe.exe
    echo.
    
    :: 실행 테스트 제안
    set /p test="빌드된 실행파일을 테스트하시겠습니까? (y/n): "
    if /i "%test%"=="y" (
        echo.
        echo 🧪 실행파일 테스트 중...
        echo 잠시 후 ShotPipe가 실행됩니다. 정상 작동하면 창을 닫아주세요.
        timeout /t 3
        start "" "dist\ShotPipe.exe"
    )
    
) else (
    echo ❌ 빌드 실패
    echo.
    echo 🔍 문제 해결 방법:
    echo 1. Python 가상환경이 올바르게 설정되었는지 확인
    echo 2. requirements.txt의 모든 패키지가 설치되었는지 확인
    echo 3. 빌드 로그에서 오류 메시지 확인
    echo 4. 디스크 공간이 충분한지 확인 (최소 2GB 필요)
    
    echo.
    pause
    exit /b 1
)

:: 최종 정리
echo.
echo [8/8] 빌드 완료 정리...
echo.
echo ================================================================
echo 🎉 ShotPipe 독립형 실행파일 빌드 완료!
echo ================================================================
echo.
echo 📦 배포 파일: dist\ShotPipe.exe
echo 💾 파일 크기: %filesize_mb% MB
echo 🖥️  요구사항: Windows 10/11 (64-bit)
echo 🚀 실행방법: 더블클릭으로 바로 실행
echo.
echo 💡 배포 시 주의사항:
echo - Windows Defender에서 차단될 수 있음 (정상 현상)
echo - 첫 실행 시 "알 수 없는 게시자" 경고 나타날 수 있음
echo - 사용자에게 "추가 정보" → "실행" 클릭하도록 안내
echo.

set /p open_folder="탐색기에서 dist 폴더를 열시겠습니까? (y/n): "
if /i "%open_folder%"=="y" (
    explorer dist
)

echo.
echo 즐거운 작업 되세요! 🎬
pause