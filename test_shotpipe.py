#!/usr/bin/env python3
"""
ShotPipe 테스트 스크립트
GUI 없이 핵심 기능을 테스트합니다.
"""
import sys
import os

# 테스트 시작
print("=" * 50)
print("🧪 ShotPipe Test Suite")
print("=" * 50)
print()

# 1. Python 버전 확인
print("📋 Python 버전 확인...")
print(f"   Python {sys.version}")
if sys.version_info < (3, 7):
    print("   ❌ Python 3.7+ 필요")
    sys.exit(1)
print("   ✅ Python 버전 OK")
print()

# 2. 필수 모듈 임포트 테스트
print("📦 필수 모듈 확인...")
modules_to_test = [
    ("PyQt5", "PyQt5"),
    ("PIL", "Pillow"),
    ("yaml", "PyYAML"),
    ("dotenv", "python-dotenv"),
    ("shotgun_api3", "shotgun_api3"),
]

all_modules_ok = True
for module_name, package_name in modules_to_test:
    try:
        if module_name == "shotgun_api3":
            # sg_compat 패치 사용
            from shotpipe.shotgrid import sg_compat
            print(f"   ✅ {package_name} (with compatibility patch)")
        else:
            __import__(module_name)
            print(f"   ✅ {package_name}")
    except ImportError as e:
        print(f"   ❌ {package_name}: {e}")
        all_modules_ok = False

if not all_modules_ok:
    print("\n❌ 일부 모듈이 누락되었습니다. requirements.txt를 확인하세요.")
    sys.exit(1)
print()

# 3. ShotPipe 모듈 임포트 테스트
print("🎬 ShotPipe 모듈 확인...")
try:
    from shotpipe.config import config
    print("   ✅ Config 모듈")
    
    from shotpipe.file_processor.processor import FileProcessor
    print("   ✅ File Processor 모듈")
    
    from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker
    print("   ✅ Files Tracker 모듈")
    
    from shotpipe.shotgrid.api_connector import ShotgridConnector
    print("   ✅ ShotGrid Connector 모듈")
    
except ImportError as e:
    print(f"   ❌ ShotPipe 모듈 임포트 실패: {e}")
    sys.exit(1)
print()

# 4. 설정 파일 확인
print("⚙️  설정 파일 확인...")
config_path = os.path.expanduser("~/.shotpipe/config.yaml")
if os.path.exists(config_path):
    print(f"   ✅ 설정 파일 존재: {config_path}")
else:
    print(f"   ℹ️  설정 파일 없음 (첫 실행 시 자동 생성됨)")

env_file = ".env"
if os.path.exists(env_file):
    print(f"   ✅ .env 파일 존재")
else:
    print(f"   ⚠️  .env 파일 없음 (ShotGrid 연동에 필요)")
print()

# 5. ExifTool 확인
print("📷 ExifTool 확인...")
import platform
import subprocess

vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
if platform.system() == "Windows":
    exiftool_path = os.path.join(vendor_dir, "exiftool.exe")
else:
    exiftool_path = os.path.join(vendor_dir, "exiftool")

if os.path.exists(exiftool_path):
    print(f"   ✅ 번들된 ExifTool: {exiftool_path}")
else:
    # 시스템 PATH에서 확인
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "exiftool"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "exiftool"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ 시스템 ExifTool: {result.stdout.strip()}")
        else:
            print("   ⚠️  ExifTool이 설치되지 않음 (메타데이터 기능 제한)")
    except:
        print("   ⚠️  ExifTool 확인 실패")
print()

# 6. 요약
print("=" * 50)
print("📊 테스트 결과 요약")
print("=" * 50)
print("✅ 모든 핵심 모듈이 정상적으로 로드됩니다.")
print("✅ ShotPipe를 실행할 준비가 되었습니다.")
print()
print("🚀 실행 방법:")
if platform.system() == "Windows":
    print("   - run_shotpipe.bat 더블클릭")
    print("   - 또는: python main.py")
else:
    print("   - ./build_macos.sh (앱 빌드)")
    print("   - 또는: python main.py")
print()
print("💡 ShotGrid 연동을 위해서는 .env 파일 설정이 필요합니다.")
print("   .env.example을 .env로 복사하고 API 정보를 입력하세요.")
print("=" * 50)