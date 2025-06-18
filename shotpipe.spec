# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# 현재 디렉토리
current_dir = os.path.dirname(os.path.abspath('main.py'))

# 데이터 파일들 수집 - 최적화된 버전
datas = [
    # ShotPipe 모듈 전체
    ('shotpipe', 'shotpipe'),
]

# 필수 문서 파일들만 포함 (용량 최적화)
essential_docs = [
    'WINDOWS_USER_GUIDE.md',
    'README.md'
]

for doc_file in essential_docs:
    if os.path.exists(doc_file):
        datas.append((doc_file, '.'))

# Vendor 폴더 - ExifTool만 포함 (용량 최적화)
if os.path.exists('vendor'):
    datas.append(('vendor', 'vendor'))

# .env 예제 파일 포함
if os.path.exists('.env.example'):
    datas.append(('.env.example', '.'))

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
        # 불필요한 패키지들 제외 - 대폭 확장
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
        # 추가 불필요 패키지들
        'sqlite3',
        'email',
        'html',
        'http',
        'urllib3',
        'curses',
        'distutils',
        'multiprocessing',
        'concurrent',
        'asyncio',
        'queue',
        'socket',
        'ssl',
        'webbrowser',
        'doctest',
        'pydoc',
        'xmlrpc',
        'xml.dom',
        'xml.sax',
        'lib2to3',
        # PyQt5 불필요 모듈들
        'PyQt5.QtNetwork',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtSql',
        'PyQt5.QtTest',
        'PyQt5.QtMultimedia',
        'PyQt5.QtOpenGL',
        'PyQt5.QtPositioning',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 용량 최적화를 위한 바이너리 필터링
a.binaries = [x for x in a.binaries if not x[0].startswith('tcl')]
a.binaries = [x for x in a.binaries if not x[0].startswith('tk')]
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt5Network')]
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt5WebEngine')]
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt5Multimedia')]
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt5OpenGL')]

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
    strip=True,  # 최적화를 위해 strip 활성화
    upx=True,    # UPX 압축 활성화
    upx_exclude=[
        # UPX 압축에서 제외할 중요한 파일들
        'vcruntime140.dll',
        'python38.dll',
        'python39.dll',
        'python310.dll',
        'python311.dll',
        'python312.dll',
    ],
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
    
    # 추가 최적화 옵션
    manifest='ShotPipe.manifest' if os.path.exists('ShotPipe.manifest') else None,
)
