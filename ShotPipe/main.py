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
    try:
        exiftool_version = subprocess.run(
            ["exiftool", "-ver"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if exiftool_version.returncode == 0:
            logger.info(f"ExifTool found: version {exiftool_version.stdout.strip()}")
        else:
            logger.warning("ExifTool not found in PATH. Metadata extraction will be limited.")
    except FileNotFoundError:
        logger.warning("ExifTool not found in PATH. Metadata extraction will be limited.")
    
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
    """Main function to start the application."""
    # Set up logging
    logger = setup_logging()
    
    try:
        # Check dependencies
        logger.info("Checking dependencies...")
        check_dependencies()
        
        # Add parent directory to path for imports
        parent_dir = str(Path(__file__).parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Import after logging is set up
        from shotpipe.ui.main_window import MainWindow
        
        logger.info("Starting ShotPipe application...")
        MainWindow.run()
        
    except ImportError as e:
        logger.critical(f"Failed to import required module: {e}")
        print(f"Critical error: Failed to import required module: {e}", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        print(f"Critical error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()