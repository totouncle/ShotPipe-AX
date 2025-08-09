# 🍎 macOS 설치 가이드

> ShotPipe를 macOS에서 설치하고 실행하는 완전 가이드

## 🚀 설치 방법

### 🥇 방법 1: DMG 패키지 설치 (권장)

**특징**: 가장 간단하고 안전한 설치

```
1. 📥 ShotPipe.dmg 다운로드
   - GitHub Releases에서 최신 DMG 파일 다운로드

2. 🖱️ DMG 파일 더블클릭
   - 마운트된 디스크 이미지 확인

3. 📁 Applications 폴더로 드래그
   - ShotPipe.app을 Applications 폴더로 드래그

4. 🚀 Launchpad에서 실행
   - Launchpad에서 ShotPipe 아이콘 클릭
```

**장점**: 
- ✅ 자동 의존성 해결
- ✅ 시스템 통합
- ✅ 자동 업데이트 지원

---

### 🥈 방법 2: 소스 코드 설치

**특징**: 개발자용, 최신 기능 사용 가능

```bash
# 1. Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python 및 의존성 설치
brew install python@3.11
brew install exiftool

# 3. ShotPipe 다운로드
git clone https://github.com/your-repo/shotpipe.git
cd shotpipe

# 4. Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 5. 의존성 설치
pip install -r requirements.txt

# 6. 실행
python main.py
```

**장점**: 
- ✅ 최신 개발 버전
- ✅ 커스터마이징 가능
- ✅ 디버깅 정보 접근

---

## 🛡️ macOS 보안 설정

### Gatekeeper 설정

**증상**: "ShotPipe.app은 확인되지 않은 개발자가 배포했기 때문에 열 수 없습니다"

```
🔧 해결법 1: 수동 허용
1. ShotPipe.app 우클릭
2. "열기" 선택
3. "열기" 버튼 클릭하여 확인

🔧 해결법 2: 시스템 설정
1. 시스템 환경설정 → 보안 및 개인 정보 보호
2. "일반" 탭
3. "확인되지 않은 개발자의 앱 허용"에서 "열기" 클릭

🔧 해결법 3: 터미널 명령어
sudo spctl --master-disable
# 주의: 보안 위험이 있으므로 사용 후 다시 활성화 권장
sudo spctl --master-enable
```

### 권한 설정

**목적**: 파일 접근 및 네트워크 사용 권한

```
📁 파일 시스템 접근:
1. 시스템 환경설정 → 보안 및 개인 정보 보호
2. "개인 정보 보호" 탭
3. "파일 및 폴더" 선택
4. ShotPipe에 필요한 폴더 접근 허용

🌐 네트워크 접근:
1. "네트워크" 권한 허용
2. 방화벽에서 ShotPipe 허용
3. Shotgrid API 연결 테스트
```

### 코드 서명 확인

```bash
# 앱 서명 상태 확인
codesign -dv --verbose=4 /Applications/ShotPipe.app

# 서명 검증
spctl -a -v /Applications/ShotPipe.app
```

---

## 📋 시스템 요구사항

### 최소 사양
- **OS**: macOS 10.14 (Mojave) 이상
- **RAM**: 4GB
- **저장공간**: 2GB
- **인터넷**: Shotgrid 연결용

### 권장 사양
- **OS**: macOS 12 (Monterey) 이상
- **RAM**: 8GB 이상
- **저장공간**: 5GB 이상
- **SSD**: 성능 향상을 위해 권장

### 호환성 매트릭스
| macOS 버전 | 지원 상태 | 참고사항 |
|-----------|----------|---------|
| 14.x (Sonoma) | ✅ 완전 지원 | 최신 기능 모두 사용 가능 |
| 13.x (Ventura) | ✅ 완전 지원 | 권장 버전 |
| 12.x (Monterey) | ✅ 완전 지원 | 안정적 동작 |
| 11.x (Big Sur) | ⚠️ 제한적 지원 | 일부 기능 제한 |
| 10.15 (Catalina) | ⚠️ 제한적 지원 | 32bit 앱 미지원 |
| 10.14 (Mojave) | ❌ 최소 지원 | 보안 업데이트 권장 |

---

## 🔧 의존성 및 도구 설치

### ExifTool 설치

**목적**: 메타데이터 추출 및 처리

```bash
# Homebrew로 설치 (권장)
brew install exiftool

# 또는 MacPorts로 설치
sudo port install p5-image-exiftool

# 설치 확인
exiftool -ver
```

### Python 환경 설정

**ShotPipe는 Python 3.8-3.12를 지원합니다**

```bash
# 시스템 Python 확인
python3 --version

# Homebrew로 Python 설치 (권장)
brew install python@3.11

# pyenv를 이용한 버전 관리 (선택사항)
brew install pyenv
pyenv install 3.11.7
pyenv global 3.11.7
```

### Qt 라이브러리 (GUI용)

```bash
# PyQt5 의존성 설치
brew install qt@5

# 또는 Conda 환경 사용
conda install pyqt=5

# 설치 확인
python3 -c "import PyQt5; print('PyQt5 설치 완료')"
```

---

## 🎯 첫 실행 가이드

### 1단계: 앱 실행
```
1. Finder에서 Applications 폴더 열기
2. ShotPipe.app 더블클릭
3. Gatekeeper 경고 시 "열기" 클릭
4. 환영 화면 확인
```

### 2단계: 환경 설정
```
1. "환경설정" (⌘,) 열기
2. "일반" 탭에서:
   - 언어: 한국어
   - 테마: 다크/라이트 선택
   - 시작 시 자동 실행 설정

3. "경로" 탭에서:
   - 작업 폴더: ~/ShotPipe_Work
   - 백업 폴더: ~/ShotPipe_Backup
   - 로그 폴더: ~/ShotPipe_Logs
```

### 3단계: Shotgrid 연결
```
1. "Shotgrid" 탭 클릭
2. 연결 정보 입력:
   - 서버 URL: https://your-studio.shotgrid.autodesk.com
   - 스크립트 이름: (관리자에게 문의)
   - API 키: (관리자에게 문의)

3. "연결 테스트" 버튼으로 확인
4. 성공 시 설정 저장
```

---

## 📁 권장 폴더 구조

### 기본 디렉토리 설정
```
~/ShotPipe/                     ← 메인 폴더
├── Work/                      ← 작업 폴더
│   ├── Input/                ← AI 생성 원본
│   ├── Processing/           ← 처리 중
│   ├── Processed/            ← 처리 완료
│   └── Upload/               ← 업로드 대기
├── Backup/                    ← 백업 폴더
│   ├── Original/             ← 원본 백업
│   └── Settings/             ← 설정 백업
├── Templates/                 ← 템플릿
└── Logs/                     ← 로그 파일
```

### 권한 설정
```bash
# 적절한 권한 설정
chmod 755 ~/ShotPipe
chmod -R 644 ~/ShotPipe/Work/*
chmod -R 755 ~/ShotPipe/Work/*/

# 소유권 확인
chown -R $(whoami):staff ~/ShotPipe
```

---

## 🔧 고급 설정

### 환경 변수 설정

**~/.zshrc 또는 ~/.bash_profile에 추가**

```bash
# ShotPipe 관련 환경 변수
export SHOTPIPE_HOME=~/ShotPipe
export SHOTPIPE_WORK=$SHOTPIPE_HOME/Work
export SHOTPIPE_BACKUP=$SHOTPIPE_HOME/Backup

# ExifTool 경로 (필요시)
export PATH=/usr/local/bin:$PATH

# Python 경로 (가상환경 사용 시)
export PATH=$SHOTPIPE_HOME/venv/bin:$PATH
```

### 자동 시작 설정

**Login Items에 추가**

```
1. 시스템 환경설정 → 사용자 및 그룹
2. 현재 사용자 선택
3. "로그인 항목" 탭
4. "+" 버튼으로 ShotPipe.app 추가
5. "숨김"에 체크하여 백그라운드 시작
```

### Dock 설정

```
1. ShotPipe.app을 Dock에 드래그
2. 우클릭 → 옵션 → "로그인 시 열기"
3. 아이콘 사용자화 (선택사항)
```

---

## 🚀 성능 최적화

### 시스템 최적화
```bash
# 불필요한 백그라운드 프로세스 확인
sudo launchctl list | grep -v com.apple

# 디스크 공간 확보
sudo rm -rf ~/.Trash/*
sudo periodic daily weekly monthly

# 권한 복구
sudo diskutil repairPermissions /
```

### ShotPipe 최적화
```
⚙️ 성능 설정:
- 처리 스레드: CPU 코어 수 - 1
- 메모리 제한: 시스템 RAM의 70%
- 캐시 크기: 1GB
- 미리보기 품질: 중간

🎯 워크플로 최적화:
- SSD에 작업 폴더 설정
- 배치 크기: 20-50개
- 자동 백업 활성화
- 정기적인 로그 정리
```

### 모니터링
```bash
# 시스템 리소스 모니터링
top -pid $(pgrep ShotPipe)

# 메모리 사용량
ps aux | grep ShotPipe

# 디스크 I/O
sudo iotop -P
```

---

## 🔄 업데이트 및 관리

### 자동 업데이트 설정
```
1. ShotPipe → 환경설정 → 업데이트
2. "자동으로 업데이트 확인" 활성화
3. 업데이트 주기: 주간
4. 백업 생성 후 업데이트: 활성화
```

### 수동 업데이트
```bash
# Git 저장소에서 업데이트 (소스 설치 시)
cd ~/shotpipe
git pull origin main
pip install -r requirements.txt --upgrade

# DMG 패키지 업데이트
# 1. 새 DMG 다운로드
# 2. 기존 앱 백업
# 3. 새 앱으로 교체
```

### 백업 및 복원
```bash
# 설정 백업
cp ~/Library/Preferences/com.shotpipe.plist ~/ShotPipe/Backup/
cp -R ~/.shotpipe ~/ShotPipe/Backup/

# 설정 복원
cp ~/ShotPipe/Backup/com.shotpipe.plist ~/Library/Preferences/
cp -R ~/ShotPipe/Backup/.shotpipe ~/
```

---

## 🐛 macOS 특화 문제 해결

### Rosetta 2 관련 (Apple Silicon)
```
# Intel 앱을 Apple Silicon에서 실행
arch -x86_64 /Applications/ShotPipe.app/Contents/MacOS/ShotPipe

# Rosetta 2 설치 확인
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
```

### 권한 문제
```bash
# 앱 권한 리셋
sudo tccutil reset All com.shotpipe

# 파일 권한 복구
sudo chown -R $(whoami):staff ~/ShotPipe
sudo chmod -R 755 ~/ShotPipe
```

### 네트워크 연결 문제
```bash
# DNS 캐시 정리
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 방화벽 상태 확인
sudo pfctl -s rules | grep shotpipe
```

### 메모리 문제
```bash
# 메모리 압박 상황 확인
sudo memory_pressure

# 페이지 파일 정리
sudo purge

# 앱 메모리 사용량
sudo vmmap -summary $(pgrep ShotPipe)
```

---

## 📞 지원 및 커뮤니티

### 로그 파일 위치
```
~/Library/Logs/ShotPipe/          ← 앱 로그
~/ShotPipe/Logs/                  ← 사용자 로그
/var/log/system.log               ← 시스템 로그 (ShotPipe 관련)
```

### 진단 정보 수집
```bash
# 시스템 정보 수집
system_profiler SPSoftwareDataType > ~/Desktop/system_info.txt
system_profiler SPHardwareDataType >> ~/Desktop/system_info.txt

# ShotPipe 환경 정보
echo "Python Version: $(python3 --version)" > ~/Desktop/shotpipe_env.txt
echo "ExifTool Version: $(exiftool -ver)" >> ~/Desktop/shotpipe_env.txt
echo "Qt Version: $(python3 -c 'import PyQt5.QtCore; print(PyQt5.QtCore.QT_VERSION_STR)')" >> ~/Desktop/shotpipe_env.txt
```

### 터미널 디버깅
```bash
# 터미널에서 ShotPipe 실행 (디버그 모드)
/Applications/ShotPipe.app/Contents/MacOS/ShotPipe --debug

# 상세 로그 출력
export SHOTPIPE_DEBUG=1
/Applications/ShotPipe.app/Contents/MacOS/ShotPipe
```

---

## ✅ 설치 확인

### 정상 설치 체크리스트
```
□ ShotPipe.app이 Applications에 정상 설치
□ 실행 시 오류 없이 시작
□ Shotgrid 연결 테스트 성공
□ ExifTool 명령어 실행 가능
□ 파일 처리 테스트 성공
□ 로그 파일 정상 생성
```

### 기능 테스트
```
1. 📁 파일 스캔 기능 테스트
2. 🏷️ 파일명 변경 기능 테스트
3. 📤 Shotgrid 업로드 테스트
4. ⚙️ 설정 저장/로드 테스트
5. 📊 로그 및 이력 확인
```

---

## 🎉 설치 완료!

축하합니다! macOS에서 ShotPipe 설치가 완료되었습니다.

**다음 단계**:
1. [빠른 시작 가이드](../user-guides/quick-start.md) 읽기
2. [파일 처리 가이드](../user-guides/file-processing.md) 확인
3. 첫 번째 파일 업로드 시도하기

**Mac다운 효율적인 워크플로를 경험하세요!** 🍎🚀
