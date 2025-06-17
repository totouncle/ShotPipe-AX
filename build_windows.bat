@echo off
echo =====================================
echo ShotPipe Windows 빌드 스크립트
echo =====================================
echo.

:: Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요: https://python.org
    pause
    exit /b 1
)

echo [1/6] Python 버전 확인...
python --version

:: 가상환경 생성
echo.
echo [2/6] 가상환경 생성 중...
if not exist venv (
    python -m venv venv
)

:: 가상환경 활성화
echo [3/6] 가상환경 활성화...
call venv\Scripts\activate.bat

:: 의존성 설치
echo.
echo [4/6] 의존성 설치 중...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

:: PyInstaller로 빌드
echo.
echo [5/6] 실행파일 생성 중...
pyinstaller shotpipe.spec

:: 결과 확인
echo.
echo [6/6] 빌드 완료!
if exist "dist\ShotPipe.exe" (
    echo.
    echo ✅ 성공! ShotPipe.exe가 생성되었습니다.
    echo 📁 위치: %cd%\dist\ShotPipe.exe
    echo.
    echo 사용법:
    echo 1. dist 폴더의 ShotPipe.exe를 원하는 곳에 복사
    echo 2. 더블클릭으로 실행
    echo.
    set /p answer="지금 실행해보시겠습니까? (y/n): "
    if /i "%answer%"=="y" (
        start dist\ShotPipe.exe
    )
) else (
    echo.
    echo ❌ 오류: 빌드에 실패했습니다.
    echo 로그를 확인해주세요.
)

echo.
pause
