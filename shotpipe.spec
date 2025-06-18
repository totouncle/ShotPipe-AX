# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# 현재 디렉토리 - Windows 호환성 개선
current_dir = os.path.dirname(os.path.abspath(SPEC))

# 데이터 파일들 수집 - Windows 호환성 개선
datas = []

# ShotPipe 모듈 전체 - 존재 여부 확인
shotpipe_path = os.path.join(current_dir, 'shotpipe')
if os.path.exists(shotpipe_path):
    datas.append((shotpipe_path, 'shotpipe'))
    print(f"[OK] Found shotpipe module at: {shotpipe_path}")
else:
    print(f"[ERROR] shotpipe module not found at: {shotpipe_path}")

# 필수 문서 파일들만 포함 (용량 최적화)
essential_docs = [
    'WINDOWS_USER_GUIDE.md',
    'README.md',
    'LICENSE.txt'
]

for doc_file in essential_docs:
    doc_path = os.path.join(current_dir, doc_file)
    if os.path.exists(doc_path):
        datas.append((doc_path, '.'))
        print(f"[OK] Found document: {doc_file}")
    else:
        print(f"[WARN] Document not found: {doc_file}")

# Vendor 폴더 - ExifTool만 포함 (용량 최적화)
vendor_path = os.path.join(current_dir, 'vendor')
if os.path.exists(vendor_path):
    datas.append((vendor_path, 'vendor'))
    print(f"[OK] Found vendor directory: {vendor_path}")

# .env 예제 파일 포함
env_example_path = os.path.join(current_dir, '.env.example')
if os.path.exists(env_example_path):
    datas.append((env_example_path, '.'))
    print(f"[OK] Found .env.example: {env_example_path}")

print(f"[INFO] Total data files to include: {len(datas)}")

# Analysis 설정 - Windows 환경 최적화
a = Analysis(
    [os.path.join(current_dir, 'main.py')],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5 관련 - Windows에서 필수
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'PyQt5.sip',
        'sip',
        
        # ShotPipe 모듈들 - 전체 경로 명시
        'shotpipe',
        'shotpipe.ui',
        'shotpipe.ui.main_window',
        'shotpipe.ui.file_tab',
        'shotpipe.ui.file_tab_enhanced', 
        'shotpipe.ui.enhanced_shotgrid_tab',
        'shotpipe.ui.shotgrid_tab',
        'shotpipe.ui.about_dialog',
        'shotpipe.ui.manual_dialog',
        'shotpipe.ui.project_settings_dialog',
        'shotpipe.ui.welcome_wizard',
        'shotpipe.ui.styles',
        'shotpipe.ui.styles.dark_theme',
        'shotpipe.file_processor',
        'shotpipe.file_processor.metadata',
        'shotpipe.file_processor.naming',
        'shotpipe.file_processor.processor',
        'shotpipe.file_processor.scanner',
        'shotpipe.file_processor.task_assigner',
        'shotpipe.shotgrid',
        'shotpipe.shotgrid.api_connector',
        'shotpipe.shotgrid.entity_manager',
        'shotpipe.shotgrid.sg_compat',
        'shotpipe.shotgrid.uploader',
        'shotpipe.shotgrid.link_manager',
        'shotpipe.shotgrid.link_manager.link_browser',
        'shotpipe.shotgrid.link_manager.link_manager',
        'shotpipe.shotgrid.link_manager.link_selector',
        'shotpipe.utils',
        'shotpipe.utils.hash_utils',
        'shotpipe.utils.history_manager',
        'shotpipe.utils.log_handler',
        'shotpipe.utils.processed_files_tracker',
        'shotpipe.utils.version_utils',
        'shotpipe.config',
        
        # 외부 라이브러리 - Windows 호환성
        'shotgun_api3',
        'dotenv',
        'exifread',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'yaml',
        'markdown',
        
        # Windows 시스템 관련
        'platform',
        'subprocess',
        'logging',
        'logging.handlers',
        'json',
        'csv',
        'datetime',
        'pathlib',
        'os',
        'sys',
        'tempfile',
        'shutil',
        'winreg',
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

# 용량 최적화를 위한 바이너리 필터링 - Windows 호환성 개선
print("[INFO] Filtering binaries for optimization...")
initial_count = len(a.binaries)

# 불필요한 바이너리 제거
exclude_patterns = [
    'tcl', 'tk', '_tkinter',
    'Qt5Network', 'Qt5WebEngine', 'Qt5Multimedia', 'Qt5OpenGL',
    'Qt5Quick', 'Qt5Qml', 'Qt5Positioning', 'Qt5Sensors',
    'msvcp', 'msvcr'  # Windows에서는 일부 Visual C++ 런타임 필요
]

filtered_binaries = []
for binary in a.binaries:
    binary_name = binary[0].lower()
    should_exclude = any(pattern.lower() in binary_name for pattern in exclude_patterns)
    
    # Windows에서 중요한 DLL은 유지
    if binary_name.endswith('.dll') and any(keep in binary_name for keep in ['python', 'pyqt5', 'api-ms-win']):
        should_exclude = False
    
    if not should_exclude:
        filtered_binaries.append(binary)

a.binaries = filtered_binaries
print(f"[INFO] Binary filtering: {initial_count} -> {len(a.binaries)} files ({initial_count - len(a.binaries)} removed)")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 아이콘 파일 경로 확인
icon_path = None
for icon_name in ['shotpipe.ico', 'icon.ico', 'app.ico']:
    icon_full_path = os.path.join(current_dir, icon_name)
    if os.path.exists(icon_full_path):
        icon_path = icon_full_path
        print(f"[OK] Found icon: {icon_name}")
        break

# 버전 정보 파일 경로 확인  
version_path = None
version_full_path = os.path.join(current_dir, 'version_info.txt')
if os.path.exists(version_full_path):
    version_path = version_full_path
    print(f"[OK] Found version info: version_info.txt")

# 매니페스트 파일 경로 확인
manifest_path = None
manifest_full_path = os.path.join(current_dir, 'ShotPipe.manifest')
if os.path.exists(manifest_full_path):
    manifest_path = manifest_full_path
    print(f"[OK] Found manifest: ShotPipe.manifest")

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
    strip=False,  # Windows에서 strip 비활성화 (호환성 문제 방지)
    upx=False,    # Windows에서 UPX 비활성화 (안티바이러스 오탐 방지)
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=version_path,
    manifest=manifest_path,
    # Windows 호환성 개선
    uac_admin=False,  # 관리자 권한 불필요
    uac_uiaccess=False,
)
