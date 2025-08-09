# 🎬 ShotPipe

> AI 생성 파일 자동화 Shotgrid 업로드 솔루션

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/your-repo/shotpipe)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/your-repo/shotpipe)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)

AI 서비스로 생성된 로컬 파일들을 자동으로 처리하고 Shotgrid에 효율적으로 업로드하는 크로스 플랫폼 솔루션입니다.

![ShotPipe Screenshot](screenshot.png)

## 🚀 빠른 시작

### Windows 사용자 (추천)

#### 방법 1: 실행파일 다운로드 ⭐
```
1. 최신 릴리스에서 ShotPipe.exe 다운로드
2. 더블클릭으로 실행
3. F1으로 매뉴얼 확인
4. 완료! 🎉
```

#### 방법 2: 포터블 버전
```
1. 소스코드 압축파일 다운로드
2. 압축 해제 후 setup_portable.bat 실행
3. ShotPipe_Start.bat으로 실행
```

#### 방법 3: 개발자 설치
```bash
git clone https://github.com/your-repo/shotpipe.git
cd shotpipe
build_windows.bat
```

### macOS/Linux 사용자

```bash
git clone https://github.com/your-repo/shotpipe.git
cd shotpipe
pip install -r requirements.txt
python main.py
```

## ✨ 주요 기능

### 🔄 **파일 처리**
- **자동 스캔**: 지정된 폴더에서 이미지/비디오 파일 자동 탐색
- **메타데이터 관리**: 원본 파일의 메타데이터 추출 및 보존
- **네이밍 규칙**: `[시퀀스]_c001_[task]_v0001` 형식으로 구조화
- **자동 태스크 할당**: 파일 유형 기반 자동 태스크 할당
- **버전 관리**: 동일 시퀀스/샷/태스크에 대한 버전 자동 증가

### 📤 **Shotgrid 업로드**
- **API 연동**: shotgun_api3 라이브러리 활용
- **엔티티 관리**: 프로젝트, 시퀀스, 샷 자동 생성/매핑
- **진행 상태 추적**: 실시간 업로드 진행 상황 모니터링
- **에러 처리**: 실패한 업로드 로깅 및 재시도

### 🎨 **사용자 인터페이스**
- **다크 테마**: 눈에 편한 다크 모드
- **탭 기반 UI**: 파일 처리와 업로드 분리된 인터페이스
- **실시간 로그**: 하단 로그 창에서 실시간 상태 확인
- **매뉴얼 내장**: F1으로 언제든 사용법 확인

## 🎯 자동 태스크 할당

| 파일 형식 | 자동 할당 태스크 | 설명 |
|-----------|------------------|------|
| `.png`, `.jpg`, `.jpeg` | `txtToImage` | 텍스트-이미지 생성 |
| `.mp4`, `.mov`, `.avi` | `imgToVideo` | 이미지-비디오 변환 |
| 기타 | `comp` | 컴포지팅 태스크 |

*태스크는 UI에서 수동으로 수정 가능합니다*

## 📋 시스템 요구사항

### 최소 사양
- **OS**: Windows 10+ / macOS 10.14+ / Linux
- **Python**: 3.7+ (소스코드 실행 시)
- **RAM**: 4GB
- **저장공간**: 1GB

### 권장 사양
- **OS**: Windows 11 / macOS 12+ / Ubuntu 20.04+
- **RAM**: 8GB
- **저장공간**: 5GB (대용량 미디어 처리 시)

## 🛠️ 개발자 가이드

### 로컬 개발 환경

```bash
# 저장소 클론
git clone https://github.com/your-repo/shotpipe.git
cd shotpipe

# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate
# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 개발 모드 실행
python main.py
```

### Windows 빌드

```bash
# Windows에서 실행파일 생성
build_windows.bat

# 또는 수동 빌드
pip install pyinstaller
pyinstaller shotpipe.spec
```

### 테스트

```bash
# 단위 테스트 실행
pytest tests/

# 커버리지 확인
pytest --cov=shotpipe tests/
```

## 📖 문서

- **사용자 매뉴얼**: 프로그램 내에서 F1 또는 [여기](docs/manual.md)
- **Windows 사용자 가이드**: [WINDOWS_USER_GUIDE.md](WINDOWS_USER_GUIDE.md)
- **배포 가이드**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **API 문서**: [docs/api.md](docs/api.md)

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 🐛 버그 신고

버그를 발견하셨나요? [Issues](https://github.com/your-repo/shotpipe/issues)에서 신고해주세요.

**포함해야 할 정보:**
- OS 및 버전
- ShotPipe 버전 (상태바에서 확인)
- 재현 단계
- 오류 메시지
- 로그 파일 (`~/.shotpipe/logs/`)

## 📞 지원

- **문서**: 프로그램 내 F1 키
- **이슈 트래킹**: [GitHub Issues](https://github.com/your-repo/shotpipe/issues)
- **이메일**: support@yourcompany.com

## 📜 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🎉 감사의 말

- [Shotgun API](https://github.com/shotgunsoftware/python-api) - Shotgrid 연동
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크
- [ExifTool](https://exiftool.org/) - 메타데이터 처리

---

<div align="center">

**ShotPipe로 더 빠르고 효율적인 미디어 파이프라인을 경험하세요!** 🚀

[다운로드](https://github.com/your-repo/shotpipe/releases) | [문서](docs/) | [버그 신고](https://github.com/your-repo/shotpipe/issues)

</div>
