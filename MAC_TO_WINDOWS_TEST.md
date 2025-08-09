# 🖥️ Mac에서 Windows 환경 테스트하는 방법

## 방법 1: **플랫폼 스푸핑** ✅ (가장 간단)

### 테스트 스크립트 실행
```bash
# Mac 터미널에서
source venv/bin/activate
python test_as_windows.py
```

### 실제 앱을 Windows 모드로 실행
```python
# run_as_windows.py
import sys
import platform
platform.system = lambda: "Windows"
sys.platform = "win32"

# 이제 main 실행
import main
```

## 방법 2: **Wine 사용** (Windows 프로그램 실행)

### 설치
```bash
# Homebrew로 Wine 설치
brew install --cask wine-stable

# Windows Python 설치
wine python-3.12.0.exe
```

### 실행
```bash
# Windows Python으로 실행
wine python.exe main.py
```

## 방법 3: **Virtual Machine** (완전한 Windows)

### UTM (무료, M1/M2 Mac 지원)
```bash
# UTM 설치
brew install --cask utm

# Windows 11 ARM 이미지 다운로드
# https://www.microsoft.com/software-download/windows11
```

### Parallels Desktop (유료, 최적화됨)
```bash
# 설치 후 Windows 11 자동 설치
brew install --cask parallels
```

## 방법 4: **Docker로 Windows 컨테이너**

### Dockerfile 생성
```dockerfile
# Dockerfile.windows
FROM python:3.12-windowsservercore
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### 실행 (Docker Desktop 필요)
```bash
docker build -f Dockerfile.windows -t shotpipe-win .
docker run shotpipe-win
```

## 방법 5: **크로스 플랫폼 테스트 코드**

### 플랫폼별 조건 테스트
```python
# cross_platform_test.py
import platform
import sys

def test_platform_specific():
    """플랫폼별 코드 경로 테스트"""
    
    # Windows 경로
    if platform.system() == "Windows" or "--test-windows" in sys.argv:
        print("Windows 코드 경로 실행")
        cmd = ["where", "exiftool"]
    else:
        print("Unix 코드 경로 실행")
        cmd = ["which", "exiftool"]
    
    return cmd

# 테스트
python cross_platform_test.py --test-windows
```

## 방법 6: **GitHub Actions 활용** (실제 Windows)

### 로컬에서 GitHub Actions 실행
```bash
# act 설치 (GitHub Actions 로컬 실행)
brew install act

# Windows 워크플로우 실행
act -j build-windows -P windows-latest=catthehacker/ubuntu:act-latest
```

## 🎯 추천 우선순위

### 빠른 테스트
1. **플랫폼 스푸핑** (`test_as_windows.py`) - ⚡ 즉시 실행
2. **크로스 플랫폼 테스트** - 코드 로직만 확인

### 실제 Windows 환경
1. **UTM/Parallels** - 완전한 Windows 환경
2. **GitHub Actions** - 실제 Windows 서버에서 테스트
3. **Wine** - 간단한 Windows 앱 실행

## 💻 현재 사용 가능한 테스트

### 1. Windows 시뮬레이션 테스트
```bash
python test_as_windows.py
```
✅ Windows 경로 처리 확인
✅ 플랫폼 감지 로직 테스트
✅ Windows 전용 명령어 시뮬레이션

### 2. 실제 크로스 플랫폼 동작 확인
```bash
python test_shotpipe.py
```
✅ 모든 모듈 임포트 테스트
✅ 설정 파일 확인
✅ 의존성 체크

### 3. GUI 없이 핵심 기능 테스트
```python
from shotpipe.file_processor.processor import FileProcessor
processor = FileProcessor()
# 파일 처리 로직 테스트
```

## 🔍 테스트 결과

`test_as_windows.py` 실행 결과:
- ✅ Windows로 플랫폼 위장 성공
- ✅ Windows 전용 경로 처리 확인
- ✅ PyInstaller spec Windows 설정 적용
- ✅ exiftool.exe 탐색 로직 작동

## 📝 참고사항

- **플랫폼 스푸핑**은 코드 로직만 테스트 (실제 Windows API는 사용 불가)
- **Wine**은 GUI 앱 실행에 적합
- **VM**은 완전한 Windows 환경이지만 리소스 소비 큼
- **GitHub Actions**는 무료로 실제 Windows 서버 사용 가능

---
**Mac에서도 Windows 환경을 충분히 테스트할 수 있습니다!** 🚀