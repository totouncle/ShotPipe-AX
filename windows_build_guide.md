# Windows 배포용 PyInstaller 설정

## 1. Windows 환경에서 빌드하기

### 필요한 것들
```bash
# Python 3.7+ 설치 (python.org에서 다운로드)
# Git 설치 (선택사항)

# 가상환경 생성
python -m venv shotpipe_env
shotpipe_env\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install pyinstaller

# PyInstaller로 실행파일 생성
pyinstaller --onefile --windowed --icon=icon.ico main.py --name="ShotPipe"
```

### PyInstaller 고급 설정 (shotpipe.spec 파일 생성)
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('shotpipe', 'shotpipe'),
        ('*.md', '.'),  # PRD 문서들
        ('vendor', 'vendor'),  # ExifTool 등
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'shotgun_api3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ShotPipe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    icon='icon.ico',
    version='version_info.txt'
)
```

### 빌드 명령어
```bash
# spec 파일 사용
pyinstaller shotpipe.spec

# 또는 간단한 명령어
pyinstaller --onefile --windowed main.py --name="ShotPipe" --add-data "shotpipe;shotpipe" --add-data "*.md;."
```
