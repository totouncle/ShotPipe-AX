#!/usr/bin/env python3
"""
ShotPipe History Reset Script

이 스크립트는 ShotPipe에서 처리된 모든 파일 이력을 초기화합니다.
"""
import os
import sys
import logging
from pathlib import Path

# 현재 디렉토리를 ShotPipe 모듈을 포함하는 경로로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """메인 함수: 처리된 파일 이력을 초기화합니다."""
    try:
        # ProcessedFilesTracker 가져오기
        from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker
        
        # 이력 파일 경로 확인
        history_file = os.path.join(os.path.expanduser("~/.shotpipe"), "processed_files.json")
        
        # 현재 이력 파일 확인
        if os.path.exists(history_file):
            logger.info(f"기존 이력 파일 발견: {history_file}")
            backup_file = f"{history_file}.backup-{Path(history_file).stat().st_mtime:.0f}"
            
            # 백업 파일 생성
            try:
                import shutil
                shutil.copy2(history_file, backup_file)
                logger.info(f"이력 파일이 백업되었습니다: {backup_file}")
            except Exception as e:
                logger.warning(f"이력 파일 백업 중 오류 발생: {e}")
        else:
            logger.info("이력 파일이 존재하지 않습니다. 새로 생성됩니다.")
        
        # 이력 초기화
        tracker = ProcessedFilesTracker()
        result = tracker.reset_history()
        
        if result:
            logger.info("모든 처리된 파일 이력이 성공적으로 초기화되었습니다.")
            return 0
        else:
            logger.error("이력 초기화에 실패했습니다.")
            return 1
            
    except ImportError as e:
        logger.error(f"필요한 모듈을 가져올 수 없습니다: {e}")
        return 1
    except Exception as e:
        logger.error(f"이력 초기화 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 