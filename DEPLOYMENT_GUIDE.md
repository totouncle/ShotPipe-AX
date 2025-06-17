# 📦 ShotPipe Windows 배포 가이드

## 🎯 배포 방법 추천 순서

### 1️⃣ **PyInstaller 실행파일** (가장 추천! ⭐)

**사용자 관점**: 가장 쉬움 - 다운로드 후 바로 실행
**개발자 관점**: 한 번 빌드하면 배포 완료

#### 장점 ✅
- Python 설치 불필요
- 의존성 걱정 없음
- 더블클릭만으로 실행
- 전문적인 느낌

#### 단점 ❌
- 파일 크기 큼 (100-200MB)
- Windows에서 빌드 필요

#### 빌드 방법
```bash
# Windows PC에서 실행
git clone [repository]
cd AX_pipe
build_windows.bat
```

---

### 2️⃣ **Portable 패키지** (두 번째 추천)

**사용자 관점**: 가벼움 - 압축파일 하나로 해결
**개발자 관점**: 크로스 플랫폼 배포 가능

#### 장점 ✅
- 작은 파일 크기 (10-20MB)
- 업데이트 쉬움
- 모든 OS에서 패키징 가능

#### 단점 ❌
- 초기 설정 과정 필요
- Python 설치 여부 확인 필요

#### 패키지 방법
```bash
# 압축파일에 포함할 것들
- 전체 소스코드
- setup_portable.bat
- requirements.txt
- WINDOWS_USER_GUIDE.md
```

---

### 3️⃣ **Git + Python 직접 설치** (개발자용)

**사용자 관점**: 최신 버전 - 항상 업데이트된 기능
**개발자 관점**: 배포 작업 최소

#### 장점 ✅
- 항상 최신 버전
- 커스터마이징 가능
- 개발 참여 가능

#### 단점 ❌
- 기술적 지식 필요
- 환경 설정 복잡

---

## 🛠️ 실제 배포 단계

### 단계 1: 윈도우 빌드 환경 준비

1. **Windows PC 또는 VM 준비**
2. **Python 3.7+ 설치**
3. **Git 설치** (선택사항)
4. **프로젝트 복사**

### 단계 2: 빌드 실행

```cmd
# 프로젝트 폴더에서
build_windows.bat
```

### 단계 3: 배포 패키지 생성

#### 옵션 A: 실행파일 패키지
```
ShotPipe_v1.3.0_Windows.zip
├── ShotPipe.exe                    # 메인 실행파일
├── WINDOWS_USER_GUIDE.md           # 사용자 가이드
├── README.txt                      # 간단한 설명
└── examples/                       # 예제 파일들
    ├── sample_files/
    └── shotgrid_setup_guide.pdf
```

#### 옵션 B: 포터블 패키지
```
ShotPipe_v1.3.0_Portable.zip
├── main.py                         # 메인 스크립트
├── shotpipe/                       # 소스코드
├── requirements.txt                # 의존성
├── setup_portable.bat              # 자동 설정
├── ShotPipe_Start.bat              # 실행 스크립트
├── WINDOWS_USER_GUIDE.md           # 사용자 가이드
└── examples/                       # 예제 파일들
```

### 단계 4: 사용자 가이드 작성

각 패키지에 포함될 README.txt:

```txt
===========================================
ShotPipe v1.3.0 - Windows 버전
===========================================

📋 빠른 시작:
1. ShotPipe.exe 더블클릭 (실행파일 버전)
   또는 setup_portable.bat 실행 (포터블 버전)
2. F1 키로 매뉴얼 열기
3. "파일 처리" 탭에서 작업 시작

🔧 Shotgrid 설정:
- 관리자에게 API 정보 요청
- "Shotgrid 업로드" 탭에서 연결 설정

📞 지원:
- 매뉴얼: F1 키 또는 도움말 메뉴
- 로그: 하단 로그 창 확인
- 문제 신고: 로그 파일과 함께 연락

즐거운 작업 되세요! 🎬
===========================================
```

---

## 📋 체크리스트

### 배포 전 확인사항
- [ ] Windows 10/11에서 테스트 완료
- [ ] Shotgrid 연결 테스트 완료
- [ ] 샘플 파일로 전체 워크플로우 테스트
- [ ] 사용자 가이드 작성 완료
- [ ] 아이콘 파일 추가 (선택사항)
- [ ] 디지털 서명 (선택사항)

### 사용자 피드백 수집
- [ ] 설치/실행 과정의 어려움
- [ ] UI/UX 개선점
- [ ] 추가 기능 요청
- [ ] 성능 이슈

---

## 🚀 배포 자동화 (향후 개선안)

### GitHub Actions 활용
```yaml
# .github/workflows/build-windows.yml
name: Build Windows Release
on:
  release:
    types: [created]
jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt pyinstaller
    - name: Build executable
      run: pyinstaller shotpipe.spec
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: ShotPipe-Windows
        path: dist/ShotPipe.exe
```

### 자동 배포 스크립트
```powershell
# deploy.ps1
# 버전 태그 생성, 빌드, 압축, 배포까지 자동화
```

---

## 🎉 마무리

가장 **추천하는 방법**은 **PyInstaller 실행파일**입니다!

사용자 입장에서 가장 편하고, 별도 설치 없이 바로 사용할 수 있어서 채택률이 높습니다. 

Windows에서 한 번만 빌드하면 누구나 쉽게 사용할 수 있는 프로그램이 완성됩니다! 🎊
