# 🎬 ShotPipe v1.3.0 - Portable Edition

**AI Generated File → Shotgrid Automation Tool**

---

## 🚀 빠른 시작 (3단계)

### 1️⃣ 환경 설정 (최초 1회만)
```cmd
setup_portable.bat
```

### 2️⃣ 프로그램 실행
```cmd
ShotPipe_Portable_Start.bat
```

### 3️⃣ 사용법 학습
- **F1 키**: 내장 매뉴얼 열기
- **"파일 처리"** 탭에서 시작
- **"Shotgrid 업로드"** 탭에서 업로드

---

## 📋 시스템 요구사항

- **Windows 10/11** (64-bit)
- **Python 3.7+** (자동 설치 옵션 있음)
- **인터넷 연결** (의존성 설치용)
- **2GB 디스크 공간**

---

## 🛠️ 설치 과정 상세

### 자동 설치 (추천)
1. `setup_portable.bat` 더블클릭
2. 자동으로 Python 및 의존성 설치
3. `ShotPipe_Portable_Start.bat`로 실행

### 수동 설치 (고급 사용자)
```cmd
# Python 설치 확인
python --version

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

---

## 🎯 주요 기능

### 파일 처리
- **자동 스캔**: AI 생성 파일 탐지
- **네이밍 규칙**: `[시퀀스]_c001_[task]_v0001` 형식
- **메타데이터**: 원본 정보 보존
- **태스크 할당**: 파일 유형 기반 자동 분류

### Shotgrid 연동
- **API 연결**: 안전한 인증 시스템
- **엔티티 관리**: 프로젝트/시퀀스/샷 자동 생성
- **파일 업로드**: 진행상황 실시간 모니터링
- **에러 처리**: 실패 시 자동 재시도

---

## 🔧 Shotgrid 설정

### 필요한 정보 (관리자에게 요청)
- **서버 URL**: `https://your-studio.shotgunstudio.com`
- **스크립트 이름**: 예) `ShotPipe_API`
- **API 키**: 긴 문자열 키

### 설정 방법
1. ShotPipe 실행
2. "Shotgrid 업로드" 탭 클릭
3. "연결 설정" 버튼 클릭
4. 정보 입력 후 "연결 테스트"

---

## 📞 지원 및 문제 해결

### 자주 묻는 질문

**Q: Python이 설치되어 있지 않다고 나옵니다**
A: setup_portable.bat를 실행하거나, https://python.org 에서 직접 설치

**Q: "python을 인식할 수 없습니다" 오류**
A: Python 설치 시 "Add Python to PATH" 체크박스를 선택해야 합니다

**Q: Shotgrid 연결이 안 됩니다**
A: 관리자에게 정확한 API 정보를 요청하고, 방화벽 설정을 확인하세요

**Q: 파일 업로드가 실패합니다**
A: 파일 크기와 인터넷 연결을 확인하고, 로그 창에서 오류 메시지를 확인하세요

### 로그 확인
- **프로그램 내**: 하단 로그 창
- **파일 위치**: `~/.shotpipe/logs/`
- **F1 매뉴얼**: 상세한 사용법 안내

### 지원 요청 시 포함할 정보
1. 운영체제 버전
2. Python 버전 (`python --version`)
3. 오류 메시지 (로그 창 복사)
4. 문제가 발생한 파일 정보

---

## 📁 파일 구조

```
ShotPipe_Portable/
├── 📄 README.md                     (이 파일)
├── 🔧 setup_portable.bat            (초기 설정)
├── 🚀 ShotPipe_Portable_Start.bat   (프로그램 실행)
├── 🐍 main.py                       (메인 애플리케이션)
├── 📋 requirements.txt              (Python 의존성)
├── 📚 WINDOWS_USER_GUIDE.md         (상세 사용자 가이드)
├── 📂 shotpipe/                     (소스코드)
└── 📂 examples/                     (예제 파일들)
```

---

## 🔄 업데이트

새 버전이 출시되면:
1. 새 포터블 패키지 다운로드
2. 기존 설정 파일 백업 (선택사항)
3. 새 폴더에서 `setup_portable.bat` 실행

---

## 🎊 마무리

**ShotPipe로 AI 생성 파일 관리가 쉬워집니다!**

- ⚡ **빠른 처리**: 대량 파일 자동 처리
- 🎯 **정확한 분류**: AI 기반 태스크 할당
- 🔗 **완벽한 연동**: Shotgrid 완전 호환
- 💡 **사용자 친화**: 직관적 인터페이스

즐거운 작업 되세요! 🎬✨

---

**ShotPipe Team** | v1.3.0 | 2025
