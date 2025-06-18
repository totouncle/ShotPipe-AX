#!/usr/bin/env python3
"""
ShotPipe - AI Generated File Automation and Shotgrid Integration

This program automates file processing and uploading to Shotgrid.
It provides a user interface for selecting files, processing them,
and uploading them to Shotgrid with appropriate metadata.
"""
import os
import sys
import traceback
import platform
import logging
from pathlib import Path
import subprocess
from datetime import datetime
import argparse

from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication

from shotpipe.ui.main_window import MainWindow
from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker
from shotpipe.ui.styles.dark_theme import apply_dark_theme

# Set up logging before any other imports
def setup_logging():
    """Set up logging configuration."""
    try:
        # Create log directory
        log_dir = os.path.expanduser("~/.shotpipe/logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"shotpipe_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,  # 로깅 레벨을 DEBUG로 변경
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # 로거 초기화
        logger = logging.getLogger(__name__)
        logger.info(f"Log file created at: {log_file}")
        
        # Log platform information
        logger.info(f"Starting ShotPipe on {platform.system()} {platform.release()}")
        logger.info(f"Python version: {platform.python_version()}")
        
        return logger
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.DEBUG,  # 로깅 레벨을 DEBUG로 변경
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to set up logging: {e}")
        return logger

# Set up exception handler to log uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Let KeyboardInterrupt pass through
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Print exception to stderr as well
    print("An unhandled exception occurred:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

# Set up the exception handler
sys.excepthook = handle_exception

def check_dependencies():
    """Check for required external dependencies."""
    logger = logging.getLogger(__name__)
    
    # Check for ExifTool
    exiftool_path = None
    try:
        # Check for bundled exiftool first
        vendor_dir = Path(__file__).parent / "vendor"
        exiftool_name = "exiftool.exe" if platform.system() == "Windows" else "exiftool"
        bundled_exiftool_path = vendor_dir / exiftool_name
        
        if bundled_exiftool_path.is_file():
            exiftool_path = str(bundled_exiftool_path)
        else:
            # If not bundled, check PATH
            exiftool_path_which = subprocess.run(["which", "exiftool"], capture_output=True, text=True, check=False)
            if exiftool_path_which.returncode == 0:
                exiftool_path = exiftool_path_which.stdout.strip()

        if exiftool_path:
            exiftool_version = subprocess.run(
                [exiftool_path, "-ver"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if exiftool_version.returncode == 0:
                logger.info(f"ExifTool found at '{exiftool_path}': version {exiftool_version.stdout.strip()}")
            else:
                logger.warning(f"Found ExifTool at '{exiftool_path}' but it failed to run.")
        else:
            logger.warning("ExifTool not found in vendor directory or in PATH. Metadata extraction will be limited.")
            
    except Exception as e:
        logger.warning(f"An error occurred while checking for ExifTool: {e}")

    # Check for required Python packages
    try:
        import PyQt5
        # Debug information
        logger.info(f"PyQt5 found: module path: {PyQt5.__file__}")
        logger.info(f"PyQt5 dir: {dir(PyQt5)}")
        
        try:
            from PyQt5 import QtCore
            logger.info(f"PyQt5.QtCore found: version {QtCore.QT_VERSION_STR}")
        except (ImportError, AttributeError) as e:
            logger.critical(f"PyQt5.QtCore not accessible: {e}")
            print(f"Error: PyQt5.QtCore not accessible: {e}. Try reinstalling PyQt5 with: pip install --upgrade --force-reinstall PyQt5", file=sys.stderr)
            sys.exit(1)
    except ImportError:
        logger.critical("PyQt5 not found. This is required for the application to run.")
        print("Error: PyQt5 not found. Please install it using: pip install PyQt5", file=sys.stderr)
        sys.exit(1)
    
    # Check for Shotgrid API
    try:
        import shotgun_api3
        logger.info(f"Shotgun API found")
    except ImportError:
        logger.warning("Shotgun API not found. Shotgrid integration will be disabled.")

def main():
    """Run the main application."""
    try:
        # 로거 설정
        logger = logging.getLogger(__name__)
        
        parser = argparse.ArgumentParser(description='ShotPipe application')
        parser.add_argument('--reset-history', action='store_true', help='Reset processed files history')
        args = parser.parse_args()
        
        # 이력 초기화가 요청된 경우
        if args.reset_history:
            try:
                history_file = os.path.join(os.path.expanduser("~/.shotpipe"), "processed_files.json")
                if os.path.exists(history_file):
                    os.remove(history_file)
                    logger.info(f"처리된 파일 이력이 초기화되었습니다: {history_file}")
                else:
                    logger.info("처리된 파일 이력 파일이 존재하지 않습니다.")
            except Exception as e:
                logger.error(f"이력 초기화 중 오류 발생: {e}")
        
        # 처리된 파일 추적기 초기화 및 상태 확인
        try:
            tracker = ProcessedFilesTracker()
            processed_count = len(tracker.history.get("processed_files", {}))
            current_batch = tracker.history.get("batch_info", {}).get("current_batch", "batch01")
            last_batch = tracker.history.get("batch_info", {}).get("last_batch", 0)
            logger.info(f"처리된 파일 추적기 초기화: {processed_count}개 파일, 현재 배치: {current_batch}, 마지막 배치 번호: {last_batch}")
        except Exception as e:
            logger.error(f"처리된 파일 추적기 초기화 중 오류 발생: {e}")
            tracker = None # 초기화 실패 시 None으로 설정
        
        app = QApplication(sys.argv)
        
        # 다크 테마 적용
        apply_dark_theme(app)
        
        # MainWindow에 tracker 인스턴스 전달
        window = MainWindow(tracker)
        window.show()
        logger.info("Application started")
        return app.exec_()
        
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())