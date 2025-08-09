# 🎨 ShotPipe 크로스 플랫폼 아이콘 생성 가이드

## 📋 플랫폼별 아이콘 요구사항

### Windows (.ico)
- 포맷: ICO
- 크기: 16x16, 32x32, 48x48, 256x256 (멀티 해상도)
- 파일명: `shotpipe.ico`

### macOS (.icns)
- 포맷: ICNS
- 크기: 16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024
- 파일명: `shotpipe.icns`

### Linux (.png)
- 포맷: PNG
- 크기: 512x512 권장
- 파일명: `shotpipe.png`

## 🎨 아이콘 생성 방법

### 방법 1: 온라인 멀티 플랫폼 생성기 (추천) 🌟
1. **https://www.iconifier.net/** 방문
2. 1024x1024 PNG 이미지 업로드
3. 모든 플랫폼 아이콘 자동 생성
4. 다운로드 후 assets 폴더에 저장

### 방법 2: 전문 도구 사용

#### Windows ICO 생성
1. **https://icoconvert.com/** 방문
2. PNG 이미지 업로드 (최소 256x256)
3. 멀티 해상도 선택
4. `shotpipe.ico`로 저장

#### macOS ICNS 생성
터미널에서:
```bash
# 1024x1024 PNG 파일이 있다고 가정
mkdir shotpipe.iconset
sips -z 16 16     shotpipe_1024.png --out shotpipe.iconset/icon_16x16.png
sips -z 32 32     shotpipe_1024.png --out shotpipe.iconset/icon_16x16@2x.png
sips -z 32 32     shotpipe_1024.png --out shotpipe.iconset/icon_32x32.png
sips -z 64 64     shotpipe_1024.png --out shotpipe.iconset/icon_32x32@2x.png
sips -z 128 128   shotpipe_1024.png --out shotpipe.iconset/icon_128x128.png
sips -z 256 256   shotpipe_1024.png --out shotpipe.iconset/icon_128x128@2x.png
sips -z 256 256   shotpipe_1024.png --out shotpipe.iconset/icon_256x256.png
sips -z 512 512   shotpipe_1024.png --out shotpipe.iconset/icon_256x256@2x.png
sips -z 512 512   shotpipe_1024.png --out shotpipe.iconset/icon_512x512.png
cp shotpipe_1024.png shotpipe.iconset/icon_512x512@2x.png
iconutil -c icns shotpipe.iconset
rm -rf shotpipe.iconset
```

### 방법 3: 디자인 도구 사용
1. **Figma/Sketch/Adobe XD**에서 1024x1024 아트보드 생성
2. 디자인 제작
3. PNG로 내보내기
4. 위 방법으로 변환

## 🎯 아이콘 적용 방법

### 자동 적용 (아이콘 파일이 있는 경우)
```python
# shotpipe.spec 파일에서 자동으로 감지
icon='shotpipe.ico',  # 이 줄이 활성화됨
```

### 수동 적용
```python
# shotpipe.spec 파일 수정
exe = EXE(
    # ... 기존 설정들 ...
    icon='shotpipe.ico',  # 이 줄 주석 해제
    # ...
)
```

## 📁 파일 위치
```
AX_pipe/
├── assets/
│   ├── shotpipe.ico      # Windows 아이콘
│   ├── shotpipe.icns     # macOS 아이콘
│   └── shotpipe.png      # Linux 아이콘 / 원본 이미지
├── shotpipe.spec         # 자동으로 아이콘 감지 및 적용
└── ...
```

## 🎨 디자인 제안

### 옵션 1: 텍스트 기반
- 텍스트: "SP" (ShotPipe)
- 폰트: 굵은 산세리프
- 색상: 흰색 글자, 다크 블루 배경

### 옵션 2: 아이콘 기반  
- 카메라 + 화살표 (업로드) 조합
- 파이프라인을 나타내는 연결된 점들
- 미니멀한 스타일

### 옵션 3: 영화/미디어 테마
- 필름 릴 + 업로드 화살표
- 클래퍼보드 스타일
- 그라데이션 효과

## 💡 주의사항
- ICO 파일은 여러 해상도 포함 (16x16, 32x32, 48x48, 256x256)
- 투명 배경 사용 시 윈도우에서 더 깔끔함
- 너무 복잡한 디자인은 작은 크기에서 알아보기 어려움

아이콘이 준비되면 프로젝트 루트에 `shotpipe.ico`로 저장하세요!
