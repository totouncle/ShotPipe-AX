#!/usr/bin/env python3
"""
ShotPipe 로그 모니터링 스크립트
"""
import os
import sys
import time
from pathlib import Path
import subprocess

# 로그 파일 위치
log_dir = Path.home() / ".shotpipe" / "logs"
log_file = log_dir / "shotpipe.log"

def show_logs():
    """로그 파일을 모니터링합니다."""
    if not log_file.exists():
        print(f"로그 파일이 존재하지 않습니다: {log_file}")
        print("ShotPipe를 한 번 실행한 후 다시 시도하세요.")
        return False
    
    # 운영체제에 따라 적절한 명령어 선택
    if sys.platform.startswith('darwin'):  # macOS
        cmd = ['tail', '-f', str(log_file)]
    elif sys.platform.startswith('win'):   # Windows
        cmd = ['powershell', '-command', f"Get-Content -Path '{log_file}' -Wait"]
    else:  # Linux 및 기타
        cmd = ['tail', '-f', str(log_file)]
    
    print(f"ShotPipe 로그 모니터링 중... ({log_file})")
    print("종료하려면 Ctrl+C를 누르세요.")
    try:
        subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\n로그 모니터링을 종료합니다.")
    
    return True

if __name__ == "__main__":
    show_logs()