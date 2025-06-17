# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# 현재 디렉토리
current_dir = os.path.dirname(os.path.abspath('main.py'))

# 데이터 파일들 수집
datas = [
    # ShotPipe 모듈 전체
    ('shotpipe', 'shotpipe'),
    # 문서 파일들 (존재하는 경우만)
]

# 문서 파일들 조건부 추가
doc_files = [
    'ShotPipe - AI 생성 파일 자동화 Shotgrid 업로드 솔루션 PRD.md',
    'AI 서비스 태스크 매핑 표.md',
    'WINDOWS_USER_GUIDE.md',
    'README.md'
]

for doc_file in doc_files:
    if os.path.exists(doc_file):
        datas.append((doc_file, '.'))

# Vendor 폴더 (있는 경우)
if os.path.exists('vendor'):
    datas.append(('vendor', 'vendor'))

# .env 파일 (있는 경우)
if os.path.exists('.env'):
    datas.append(('.env', '.'))

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5 관련
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'PyQt5.sip',
        
        # ShotPipe 모듈들
        'shotpipe',
        'shotpipe.ui',
        'shotpipe.ui.main_window',
        'shotpipe.ui.file_tab',
        'shotpipe.ui.shotgrid_tab',
        'shotpipe.ui.about_dialog',
        'shotpipe.ui.manual_dialog',
        'shotpipe.ui.styles.dark_theme',
        'shotpipe.file_processor',
        'shotpipe.shotgrid',
        'shotpipe.utils',
        
        # 외부 라이브러리
        'shotgun_api3',
        'dotenv',
        'exifread',
        'PIL',
        'PIL.Image',
        'yaml',
        
        # 시스템 관련
        'platform',
        'subprocess',
        'logging',
        'json',
        'csv',
        'datetime',
        'pathlib',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 패키지들 제외
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'tornado',
        'zmq',
        'tkinter',
        'tcl',
        'tk',
        '_tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'unittest',
        'test',
        'tests',
        'setuptools',
        'pkg_resources',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 불필요한 파일들 제거
a.binaries = [x for x in a.binaries if not x[0].startswith('tcl')]
a.binaries = [x for x in a.binaries if not x[0].startswith('tk')]

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
    console=False,  # GUI 앱이므로 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 아이콘 추가 (있는 경우)
    icon='shotpipe.ico' if os.path.exists('shotpipe.ico') else None,
    
    # 버전 정보
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)
