# 🚀 ShotPipe 크로스 플랫폼 빌드 개선 사항

## ✅ 완료된 개선 작업

### 1. **플랫폼 호환성 개선**
- ✅ `main.py` - Windows에서 `where`, Unix에서 `which` 명령어 사용하도록 수정
- ✅ Windows에서 `where` 명령어가 여러 경로 반환 시 첫 번째 경로만 사용하도록 처리
- ✅ ExifTool 경로 탐색 로직 개선

### 2. **PyInstaller Spec 파일 최적화**
- ✅ 플랫폼별 조건부 설정 추가
- ✅ macOS용 앱 번들 설정 완성
  - Bundle identifier 추가: `com.shotpipe.app`
  - Info.plist 메타데이터 추가
  - 다크 모드 지원 설정
  - argv_emulation 활성화 (macOS 드래그앤드롭 지원)
- ✅ 플랫폼별 아이콘 파일 자동 감지
- ✅ Hidden imports 추가로 빌드 안정성 향상

### 3. **macOS 빌드 인프라 구축**
- ✅ `build_macos.sh` - macOS 전용 빌드 스크립트 생성
  - 가상환경 자동 생성 및 활성화
  - 의존성 자동 설치
  - ExifTool 설치 확인 (Homebrew)
  - 빌드 검증 및 결과 보고
- ✅ `create_dmg.sh` - DMG 배포 파일 생성 스크립트
  - Applications 폴더 심볼릭 링크 포함
  - README/LICENSE 자동 포함
  - 코드 서명 및 공증 가이드 제공

### 4. **GitHub Actions 멀티플랫폼 CI/CD**
- ✅ `.github/workflows/build-multiplatform.yml` 생성
- ✅ 지원 플랫폼:
  - Windows (최신)
  - macOS Intel (x86_64)
  - macOS Apple Silicon (ARM64)
  - Linux (Ubuntu)
- ✅ 각 플랫폼별 최적화된 빌드 프로세스
- ✅ 자동 아티팩트 생성 및 업로드
- ✅ 태그 푸시 시 자동 릴리스 생성

### 5. **아이콘 및 리소스 관리**
- ✅ `assets/` 디렉토리 구조 생성
- ✅ 플랫폼별 아이콘 가이드 업데이트
  - Windows: `.ico` (멀티 해상도)
  - macOS: `.icns` (Retina 지원)
  - Linux: `.png` (512x512)
- ✅ 아이콘 생성 도구 및 방법 문서화

## 🎯 사용 방법

### macOS에서 빌드
```bash
# 빌드 스크립트 실행
./build_macos.sh

# DMG 생성 (배포용)
./create_dmg.sh

# 앱 실행
open ShotPipe.app
```

### Windows에서 빌드
```batch
# 기존 스크립트 사용
build_windows.bat
```

### GitHub Actions로 자동 빌드
```bash
# 태그 푸시로 릴리스 생성
git tag v1.3.1
git push origin v1.3.1
```

## 📝 추가 권장 사항

### 단기 개선
1. **테스트 자동화**
   - 각 플랫폼별 단위 테스트
   - UI 자동화 테스트 (pytest-qt)

2. **코드 서명**
   - Windows: Authenticode 인증서
   - macOS: Developer ID 인증서

3. **자동 업데이트**
   - Sparkle (macOS)
   - Squirrel (Windows)

### 장기 개선
1. **패키징 최적화**
   - 바이너리 크기 축소
   - 시작 시간 개선
   - 메모리 사용 최적화

2. **플랫폼별 기능**
   - macOS: 터치바 지원
   - Windows: 점프 리스트
   - Linux: 시스템 트레이 통합

3. **국제화**
   - 다국어 지원 확대
   - RTL 언어 지원

## 🔧 문제 해결

### macOS 빌드 실패 시
```bash
# PyQt5 재설치
pip uninstall PyQt5
pip install PyQt5==5.15.10

# 권한 문제 해결
xattr -cr ShotPipe.app
```

### Windows 빌드 실패 시
```batch
# Windows Defender 예외 추가
powershell -Command "Add-MpPreference -ExclusionPath '%CD%'"

# Visual C++ 재배포 패키지 설치
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

## 📚 참고 자료
- [PyInstaller Documentation](https://pyinstaller.org)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Apple Developer - Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Microsoft - Code Signing](https://docs.microsoft.com/windows/win32/seccrypto/cryptography-tools)