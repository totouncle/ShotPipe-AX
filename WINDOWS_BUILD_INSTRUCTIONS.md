# 🎯 ShotPipe 초보자용 Windows 인스톨러 빌드 가이드

## 📋 1단계: 사전 준비 (Windows PC에서)

### 필수 프로그램 설치

#### A. Python 설치
```
1. https://www.python.org/downloads/ 접속
2. "Download Python 3.12.x" 클릭
3. 설치 시 중요: ✅ "Add Python to PATH" 체크박스 필수!
4. 설치 완료 후 재시작
```

#### B. NSIS 설치 (인스톨러 제작용)
```
1. https://nsis.sourceforge.io/Download 접속
2. "Download NSIS 3.x" 클릭
3. 기본 설정으로 설치
4. 설치 완료 후 재시작
```

#### C. Git 설치 (소스코드 다운로드용)
```
1. https://git-scm.com/download/win 접속
2. "64-bit Git for Windows Setup" 다운로드
3. 기본 설정으로 설치
```

## 📂 2단계: 소스코드 준비

### 방법 A: Git 사용 (권장)
```cmd
1. Windows 키 + R → "cmd" 입력 → Enter
2. 다음 명령어 실행:

cd C:\
git clone [프로젝트 URL]
cd AX_pipe
```

### 방법 B: ZIP 다운로드
```
1. GitHub에서 "Code" → "Download ZIP" 클릭
2. C:\ 에 압축 해제
3. 폴더명을 "AX_pipe"로 변경
```

## 🚀 3단계: 원클릭 빌드 실행

### 💡 슈퍼 간단 방법
```cmd
1. C:\AX_pipe 폴더 열기
2. "build_all_distributions.bat" 파일 더블클릭
3. 5-10분 대기 (커피 한 잔 ☕)
4. 완료!
```

### 🔧 수동 실행 방법
```cmd
1. Windows 키 + R → "cmd" 입력 → Enter
2. 다음 명령어 실행:

cd C:\AX_pipe
build_all_distributions.bat
```

## 📦 4단계: 결과 확인

### 생성된 파일들
빌드 완료 후 `C:\AX_pipe\release_packages\` 폴더에 생성됩니다:

```
release_packages\
├── 🎯 ShotPipe_Setup.exe          ← 이것만 있으면 OK!
├── 📦 ShotPipe_v1.3.0_Portable.zip
├── 📋 CHECKSUMS.txt
└── 📁 ShotPipe_Portable\
```

### 초보자용 배포 파일
**`ShotPipe_Setup.exe`** ← 이 파일만 사용자에게 전달하면 됩니다!

## 🎁 5단계: 사용자에게 배포

### 배포 방법
```
1. ShotPipe_Setup.exe 파일을 사용자에게 전달
   (이메일, USB, 클라우드 드라이브 등)

2. 사용자 실행 방법:
   - ShotPipe_Setup.exe 더블클릭
   - "알 수 없는 게시자" 경고 시 → "추가 정보" → "실행" 클릭
   - 설치 완료 후 바탕화면 바로가기로 실행

3. 끝! 🎉
```

### 사용자 안내 메시지 (복사해서 사용하세요)
```
📧 ShotPipe 설치 안내

안녕하세요! ShotPipe 설치파일을 보내드립니다.

🔧 설치 방법:
1. 첨부된 ShotPipe_Setup.exe 파일을 다운로드
2. 파일을 더블클릭하여 실행
3. Windows에서 "알 수 없는 게시자" 경고가 나오면:
   → "추가 정보" 클릭 → "실행" 클릭
4. 설치 마법사를 따라 진행 (약 1분 소요)
5. 설치 완료 후 바탕화면의 ShotPipe 아이콘을 클릭

💡 첫 실행 시:
- 환영 마법사가 나타납니다 (3분 설정)
- 작업 폴더와 Shotgrid 연결을 설정하세요

🆘 문제 발생 시:
- Windows Defender가 차단하면 예외 목록에 추가
- 설치 오류 시 "관리자 권한으로 실행" 시도

즐거운 작업 되세요! 🎬
```

## ⚡ 고급 옵션

### 파일 크기 최적화
UPX 압축으로 파일 크기를 50% 줄일 수 있습니다:
```cmd
1. https://upx.github.io/ 에서 UPX 다운로드
2. upx.exe를 C:\AX_pipe\ 폴더에 복사
3. 빌드 시 자동으로 압축 적용
```

### 디지털 서명 추가 (선택사항)
```cmd
1. 코드 사이닝 인증서 구매
2. SignTool을 사용하여 .exe 파일에 서명
3. Windows에서 신뢰할 수 있는 소프트웨어로 인식
```

## 🛠️ 문제 해결

### 빌드 실패 시
```cmd
# Python 버전 확인
python --version

# NSIS 설치 확인
where makensis

# 가상환경 재생성
rmdir /s build_env
python -m venv build_env
build_env\Scripts\activate
pip install -r requirements.txt
```

### 일반적인 오류들
```
❌ "Python을 찾을 수 없습니다"
   → Python 재설치 시 "Add to PATH" 체크

❌ "makensis를 찾을 수 없습니다" 
   → NSIS 재설치

❌ "PyInstaller 실행 실패"
   → pip install pyinstaller 실행

❌ "권한 거부됨"
   → 명령 프롬프트를 "관리자 권한으로 실행"
```

## 🎯 성공 체크리스트

- [ ] Python 3.8+ 설치 완료
- [ ] NSIS 설치 완료
- [ ] 소스코드 다운로드 완료
- [ ] build_all_distributions.bat 실행 성공
- [ ] ShotPipe_Setup.exe 생성 확인 (50-100MB)
- [ ] 다른 PC에서 설치 테스트 완료
- [ ] 첫 실행 시 환영 마법사 확인
- [ ] 바탕화면 바로가기 생성 확인

**모든 체크가 완료되면 배포 준비 완료! 🚀**

---

💡 **도움이 필요하시면 언제든 연락주세요!**