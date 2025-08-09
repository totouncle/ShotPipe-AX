#!/usr/bin/env python3
"""
Mac에서 ShotPipe를 Windows 모드로 실행
플랫폼을 Windows로 위장하여 Windows 전용 코드 경로를 테스트
"""
import sys
import os
import platform as _platform

print("=" * 50)
print("🪟 ShotPipe Windows Mode on Mac")
print("=" * 50)
print()

# 원래 플랫폼 정보 저장
original_system = _platform.system()
original_platform = sys.platform
original_name = os.name

print(f"📱 실제 시스템: {original_system}")
print(f"🔄 Windows 모드로 전환 중...")

# Windows로 위장
class WindowsPlatform:
    """Windows 플랫폼을 시뮬레이션하는 모킹 클래스"""
    @staticmethod
    def system():
        return "Windows"
    
    @staticmethod
    def release():
        return "10"
    
    @staticmethod
    def version():
        return "10.0.19041"
    
    @staticmethod
    def machine():
        return "AMD64"
    
    @staticmethod
    def processor():
        return "Intel64 Family 6 Model 142 Stepping 10, GenuineIntel"
    
    @staticmethod
    def python_version():
        return _platform.python_version()
    
    def __getattr__(self, name):
        # 다른 모든 속성은 원래 platform 모듈로 전달
        return getattr(_platform, name)

# platform 모듈 교체
sys.modules['platform'] = WindowsPlatform()
import platform
platform.system = WindowsPlatform.system
platform.release = WindowsPlatform.release

# sys.platform도 변경
sys.platform = "win32"
os.name = "nt"

print(f"✅ Windows 모드 활성화: {platform.system()} ({sys.platform})")
print()

# Windows 전용 경로 설정
if original_system == "Darwin":  # Mac
    # Mac 경로를 Windows 스타일로 매핑
    import pathlib
    original_pathlib_path = pathlib.Path
    
    class WindowsPath(original_pathlib_path):
        """Windows 스타일 경로를 시뮬레이션"""
        def __str__(self):
            s = super().__str__()
            # Mac 경로를 Windows 스타일로 변환
            if s.startswith('/'):
                # /Users/name/... -> C:\Users\name\...
                s = 'C:' + s.replace('/', '\\')
            return s
    
    # Path 클래스 교체 (선택적)
    # pathlib.Path = WindowsPath

print("🚀 ShotPipe 시작 (Windows 모드)...")
print("-" * 50)

try:
    # main.py 실행
    import main
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 GUI 오류인 경우 정상입니다.")
    print("   SSH나 터미널에서는 GUI를 실행할 수 없습니다.")
    print("\n대신 핵심 모듈만 테스트:")
    
    try:
        # GUI 없이 핵심 모듈만 테스트
        from shotpipe.config import config
        from shotpipe.file_processor.processor import FileProcessor
        from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker
        
        print("✅ Config 모듈 로드 성공")
        print("✅ FileProcessor 모듈 로드 성공")
        print("✅ ProcessedFilesTracker 모듈 로드 성공")
        
        # Windows 전용 코드 경로 테스트
        processor = FileProcessor()
        print("✅ FileProcessor 인스턴스 생성 성공")
        
        # 플랫폼 체크 테스트
        print(f"\n📊 플랫폼 감지 결과:")
        print(f"   platform.system(): {platform.system()}")
        print(f"   sys.platform: {sys.platform}")
        print(f"   os.name: {os.name}")
        
        # ExifTool 경로 확인
        from pathlib import Path
        vendor_dir = Path(__file__).parent / "vendor"
        if platform.system() == "Windows":
            exiftool_name = "exiftool.exe"
        else:
            exiftool_name = "exiftool"
        print(f"\n📷 ExifTool 설정:")
        print(f"   예상 파일명: {exiftool_name}")
        print(f"   검색 경로: {vendor_dir / exiftool_name}")
        
    except Exception as e:
        print(f"❌ 모듈 테스트 실패: {e}")

finally:
    # 원래 설정 복원
    print("\n" + "=" * 50)
    print("🔄 원래 플랫폼으로 복원 중...")
    sys.platform = original_platform
    os.name = original_name
    # platform 모듈은 재시작 필요
    print(f"✅ 복원 완료")
    print("=" * 50)