"""
Main window module for ShotPipe UI.
"""
import os
import sys
import logging
import datetime
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
    QWidget, QStatusBar, QMenuBar, QMenu, QAction, QMessageBox,
    QTextEdit, QSplitter, QLabel
)
from PyQt5.QtCore import Qt, QSettings, QEvent, pyqtSlot
from PyQt5.QtGui import QIcon, QColor
from ..config import config
from .file_tab import FileTab
from .shotgrid_tab import ShotgridTab

logger = logging.getLogger(__name__)

# 로그 메시지를 UI로 전달하기 위한 핸들러
class QTextEditLogger(logging.Handler):
    """로그 메시지를 QTextEdit으로 리다이렉트하는 로그 핸들러"""
    
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
    def emit(self, record):
        msg = self.format(record)
        
        # Add color for different log levels
        if record.levelno >= logging.ERROR:
            msg = f'<span style="color: #FF6B68;">{msg}</span>'
        elif record.levelno >= logging.WARNING:
            msg = f'<span style="color: #FFCC00;">{msg}</span>'
        elif record.levelno >= logging.INFO:
            msg = f'<span style="color: #7CE8E6;">{msg}</span>'
        elif record.levelno >= logging.DEBUG:
            msg = f'<span style="color: #9B9B9B;">{msg}</span>'
        
        self.text_edit.append(msg)
        # 스크롤을 항상 최신 로그로 이동
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )

class ErrorDialog(QMessageBox):
    """Custom error dialog with more detailed information."""
    
    def __init__(self, parent=None, title="Error", message="An error occurred", details=None):
        super().__init__(parent)
        self.setIcon(QMessageBox.Critical)
        self.setWindowTitle(title)
        self.setText(message)
        if details:
            self.setDetailedText(details)
        self.setStandardButtons(QMessageBox.Ok)

class MainWindow(QMainWindow):
    """Main application window for ShotPipe."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        try:
            # Load window settings
            self.settings = QSettings("ShotPipe", "ShotPipe")
            self.window_size = config.get("ui", "window_size") or [1024, 768]
            
            # Set up window properties
            self.setWindowTitle("ShotPipe - AI 생성 파일 자동화 Shotgrid 업로드 솔루션")
            self.resize(self.window_size[0], self.window_size[1])
            
            # Initialize UI
            self._init_ui()
            
            # Restore window geometry
            self._restore_geometry()
            
            # Install event filter for global exception handling in UI
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
                
        except Exception as e:
            logger.critical(f"Failed to initialize main window: {e}", exc_info=True)
            self._show_error_dialog("Initialization Error", f"Failed to initialize application: {str(e)}")
        
    def eventFilter(self, obj, event):
        """Event filter to catch exceptions in event handlers."""
        try:
            return super().eventFilter(obj, event)
        except Exception as e:
            logger.critical(f"Unhandled exception in event: {e}", exc_info=True)
            self._show_error_dialog("Operation Error", f"An unexpected error occurred: {str(e)}")
            return True
        
    def _init_ui(self):
        """Initialize the user interface."""
        try:
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create layout
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create tabs
            self.file_tab = FileTab()
            self.shotgrid_tab = ShotgridTab()
            
            # Add tabs to tab widget
            self.tab_widget.addTab(self.file_tab, "파일 처리")
            self.tab_widget.addTab(self.shotgrid_tab, "Shotgrid 업로드")
            
            # Connect tab signals to enable/disable upload tab based on processed files
            self.file_tab.files_processed.connect(self.shotgrid_tab.set_processed_files)
            
            # 로그 창 추가
            self.log_text_edit = self._create_log_widget()
            layout.addWidget(self.log_text_edit)
            
            # Create status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("준비")
            
            # Create menu bar
            self._create_menu_bar()
            
        except Exception as e:
            logger.critical(f"Error initializing UI: {e}", exc_info=True)
            self._show_error_dialog("UI Initialization Error", f"Failed to initialize UI: {str(e)}")
        
    def _create_menu_bar(self):
        """Create the application menu bar."""
        try:
            menu_bar = self.menuBar()
            
            # File menu
            file_menu = menu_bar.addMenu("파일")
            
            # Open action
            open_action = QAction("폴더 열기", self)
            open_action.setShortcut("Ctrl+O")
            open_action.triggered.connect(self._safe_call(self.file_tab.select_source_directory))
            file_menu.addAction(open_action)
            
            # Exit action
            exit_action = QAction("종료", self)
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Settings menu
            settings_menu = menu_bar.addMenu("설정")
            
            # Shotgrid settings action
            shotgrid_settings_action = QAction("Shotgrid 설정", self)
            shotgrid_settings_action.triggered.connect(self._safe_call(self.shotgrid_tab.show_settings))
            settings_menu.addAction(shotgrid_settings_action)
            
            # Help menu
            help_menu = menu_bar.addMenu("도움말")
            
            # About action
            about_action = QAction("정보", self)
            about_action.triggered.connect(self._safe_call(self._show_about))
            help_menu.addAction(about_action)
            
            # Add log actions
            debug_menu = menu_bar.addMenu("디버그")
            
            # Clear log action
            clear_log_action = QAction("로그 지우기", self)
            clear_log_action.triggered.connect(self._safe_call(self._clear_log))
            debug_menu.addAction(clear_log_action)
            
        except Exception as e:
            logger.critical(f"Error creating menu bar: {e}", exc_info=True)
            self._show_error_dialog("Menu Creation Error", f"Failed to create menu bar: {str(e)}")
    
    def _safe_call(self, func):
        """Wrap a function call with exception handling."""
        @pyqtSlot()
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                self._show_error_dialog("Operation Error", 
                                       f"Error during operation: {str(e)}")
        return wrapper
    
    def _clear_log(self):
        """Clear the log text edit."""
        self.log_text_edit.clear()
        logger.info("Log cleared")
    
    def _show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "ShotPipe 정보",
            "ShotPipe - AI 생성 파일 자동화 Shotgrid 업로드 솔루션\n\n"
            "Version 1.0.0\n\n"
            "파일 처리와 업로드 과정을 모듈식으로 분리하여 안정적인 워크플로우를 제공합니다."
        )
        
    def _restore_geometry(self):
        """Restore window geometry from settings."""
        try:
            if self.settings.contains("geometry"):
                self.restoreGeometry(self.settings.value("geometry"))
        except Exception as e:
            logger.warning(f"Failed to restore window geometry: {e}")
        
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Save window geometry
            self.settings.setValue("geometry", self.saveGeometry())
            
            # Save window size to config
            config.set("ui", "window_size", [self.width(), self.height()])
            
            # Accept the event
            event.accept()
        except Exception as e:
            logger.error(f"Error during window close: {e}")
            event.accept()  # Still close the window despite errors
        
    def _create_log_widget(self):
        """로그 표시 위젯 생성"""
        try:
            log_text_edit = QTextEdit()
            log_text_edit.setReadOnly(True)
            log_text_edit.setFixedHeight(150)  # 로그 창 높이 제한
            log_text_edit.setStyleSheet("""
                font-family: Courier; 
                font-size: 12pt;
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                padding: 5px;
            """)
            log_text_edit.setAcceptRichText(True)  # Enable rich text for color formatting
            
            # 로그 핸들러 추가
            log_handler = QTextEditLogger(log_text_edit)
            log_handler.setLevel(logging.DEBUG)  # DEBUG 레벨로 변경
            
            # 루트 로거에 추가
            root_logger = logging.getLogger()
            root_logger.addHandler(log_handler)
            
            # 초기 메시지 추가
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_text_edit.append(f"{current_time} - INFO - ShotPipe 로그 창이 초기화되었습니다.")
            
            return log_text_edit
        except Exception as e:
            logger.critical(f"Failed to create log widget: {e}", exc_info=True)
            # Fall back to a simple text edit if creation fails
            fallback = QTextEdit()
            fallback.setReadOnly(True)
            fallback.append("Error creating log widget. See system logs for details.")
            return fallback
    
    def _show_error_dialog(self, title, message, details=None):
        """Show an error dialog with detailed information."""
        if not details and sys.exc_info()[0]:
            details = ''.join(traceback.format_exception(*sys.exc_info()))
        
        dialog = ErrorDialog(self, title, message, details)
        dialog.exec_()
    
    @staticmethod
    def run():
        """Run the application."""
        # Create application
        app = QApplication(sys.argv)
        
        try:
            # Set up exception handling for PyQt
            def excepthook(exc_type, exc_value, exc_tb):
                logger.critical("Unhandled Qt exception", exc_info=(exc_type, exc_value, exc_tb))
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("An unhandled error occurred:")
                msg.setInformativeText(str(exc_value))
                msg.setWindowTitle("Error")
                msg.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                
            sys.excepthook = excepthook
            
            # Create and show main window
            window = MainWindow()
            window.show()
            
            # Run application
            sys.exit(app.exec_())
        except Exception as e:
            logger.critical(f"Application failed to start: {e}", exc_info=True)
            
            # Show a simple error dialog if we can't even create the main window
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Failed to start application")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Fatal Error")
            msg.setDetailedText(''.join(traceback.format_exception(*sys.exc_info())))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            sys.exit(1)