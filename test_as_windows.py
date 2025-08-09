#!/usr/bin/env python3
"""
Mac에서 Windows 환경으로 위장하여 테스트
"""
import sys
import os
import platform as _platform

print("=" * 50)
print("🪟 Windows 환경 시뮬레이션 테스트")
print("=" * 50)
print()

# 원래 플랫폼 정보 저장
original_system = _platform.system()
original_platform = sys.platform

print(f"📱 실제 시스템: {original_system} ({sys.platform})")
print("🔄 Windows로 위장 중...")
print()

# Windows로 위장하는 모킹 함수
def mock_windows_system():
    return "Windows"

def mock_windows_release():
    return "10"

# platform 모듈 패치
_platform.system = mock_windows_system
_platform.release = mock_windows_release
sys.platform = "win32"
os.name = "nt"

print(f"✅ 위장 완료: {_platform.system()} ({sys.platform})")
print()

# 테스트할 코드
print("🧪 Windows 전용 코드 경로 테스트:")
print("-" * 40)

# main.py의 ExifTool 경로 탐색 로직 테스트
from pathlib import Path
import subprocess

def test_exiftool_detection():
    """main.py의 ExifTool 감지 로직 테스트"""
    print("📷 ExifTool 경로 감지 테스트:")
    
    vendor_dir = Path(__file__).parent / "vendor"
    exiftool_name = "exiftool.exe" if _platform.system() == "Windows" else "exiftool"
    bundled_exiftool_path = vendor_dir / exiftool_name
    
    print(f"   플랫폼: {_platform.system()}")
    print(f"   예상 파일명: {exiftool_name}")
    print(f"   번들 경로: {bundled_exiftool_path}")
    
    if bundled_exiftool_path.is_file():
        print(f"   ✅ 번들된 ExifTool 발견")
    else:
        print(f"   ℹ️  번들된 ExifTool 없음 (예상된 동작)")
        
        # Windows 'where' 명령어 시뮬레이션
        if _platform.system() == "Windows":
            print("   🔍 'where' 명령어 사용 (Windows)")
            # Mac에서는 실제로 where가 없으므로 대체
            try:
                # Mac의 which를 where처럼 사용
                result = subprocess.run(["which", "exiftool"], 
                                      capture_output=True, 
                                      text=True, 
                                      check=False)
                if result.returncode == 0:
                    print(f"   ✅ 시스템 PATH에서 발견: {result.stdout.strip()}")
                else:
                    print("   ⚠️  시스템 PATH에서 찾을 수 없음")
            except Exception as e:
                print(f"   ❌ 명령어 실행 실패: {e}")
    print()

def test_shotpipe_spec():
    """shotpipe.spec의 플랫폼 감지 테스트"""
    print("📦 PyInstaller Spec 플랫폼 감지:")
    
    is_windows = _platform.system() == 'Windows'
    is_macos = _platform.system() == 'Darwin'
    is_linux = _platform.system() == 'Linux'
    
    print(f"   is_windows: {is_windows}")
    print(f"   is_macos: {is_macos}")
    print(f"   is_linux: {is_linux}")
    
    if is_windows:
        print("   ✅ Windows 설정 사용됨")
        print("   - console=False (콘솔 창 숨김)")
        print("   - argv_emulation=False")
        print("   - icon: assets/shotpipe.ico")
    print()

def test_path_handling():
    """Windows 스타일 경로 처리 테스트"""
    print("📁 경로 처리 테스트:")
    
    # Windows 스타일 경로
    windows_path = r"C:\Users\onset\Documents\vscode\AX_pipe"
    print(f"   Windows 경로: {windows_path}")
    
    # Path 객체로 변환 (크로스 플랫폼)
    path_obj = Path(windows_path)
    print(f"   Path 객체: {path_obj}")
    
    # 현재 디렉토리 (Windows 스타일로 표시)
    current = Path.cwd()
    if _platform.system() == "Windows":
        # Windows 스타일로 변환 시뮬레이션
        fake_windows_path = str(current).replace("/", "\\")
        if not fake_windows_path.startswith("C:\\"):
            fake_windows_path = "C:" + fake_windows_path
        print(f"   현재 디렉토리 (Windows): {fake_windows_path}")
    else:
        print(f"   현재 디렉토리: {current}")
    print()

# 테스트 실행
test_exiftool_detection()
test_shotpipe_spec()
test_path_handling()

# 원래 설정 복원
print("=" * 50)
print("🔄 원래 플랫폼으로 복원")
_platform.system = lambda: original_system
sys.platform = original_platform
os.name = "posix" if original_system != "Windows" else "nt"
print(f"✅ 복원 완료: {_platform.system()} ({sys.platform})")
print("=" * 50)