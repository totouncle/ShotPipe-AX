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
    QTextEdit, QSplitter, QLabel, QDockWidget
)
from PyQt5.QtCore import Qt, QSettings, QEvent, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from shotpipe.config import config
from shotpipe.utils.log_handler import QTextEditLogger
from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker
from shotpipe.ui.file_tab import FileTab
from shotpipe.ui.shotgrid_tab import ShotgridTab
from shotpipe.ui.about_dialog import AboutDialog
from shotpipe.ui.manual_dialog import ManualDialog
from shotpipe.ui.project_settings_dialog import ProjectSettingsDialog
from shotpipe.shotgrid.sg_compat import Shotgun, SG_API_SCRIPT, SG_API_KEY, SG_URL
from shotpipe.file_processor.processor import FileProcessor
from shotpipe.file_processor.task_assigner import TaskAssigner
from shotpipe.utils.version_utils import get_version_info

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
            self.setWindowTitle("ShotPipe")
            self.resize(self.window_size[0], self.window_size[1])
            
            # Create status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # 버전 정보 라벨 생성 (오른쪽에 표시)
            version_string = get_version_info()
            self.version_label = QLabel(f"  {version_string}  ")
            self.version_label.setStyleSheet("""
                QLabel {
                    background-color: #007ACC;
                    color: #FFFFFF;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-weight: bold;
                    font-size: 9pt;
                }
            """)
            self.status_bar.addPermanentWidget(self.version_label)
            
            # 상태 메시지 표시
            self.status_bar.showMessage("준비")
            
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
            
            # Create shared ProcessedFilesTracker instance
            self.processed_files_tracker = ProcessedFilesTracker()
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create tabs and pass shared tracker
            self.file_tab = FileTab(self)
            self.shotgrid_tab = ShotgridTab()
            
            # Set the shared tracker for the application
            self.app = QApplication.instance()
            if self.app:
                self.app.processed_files_tracker = self.processed_files_tracker
            
            # Add tabs to tab widget
            self.tab_widget.addTab(self.file_tab, "파일 처리")
            self.tab_widget.addTab(self.shotgrid_tab, "Shotgrid 업로드")
            
            # Connect file tab to shotgrid tab - when files are processed, send them to shotgrid tab
            self.file_tab.files_processed.connect(self.shotgrid_tab.set_processed_files)
            
            # 로그 창 추가
            self.log_text_edit = self._create_log_widget()
            layout.addWidget(self.log_text_edit)
            
            # Create menu bar
            self._create_menu_bar()
            
            logger.info("ShotPipe UI initialized")
            
        except Exception as e:
            logger.critical(f"Error initializing UI: {e}", exc_info=True)
            self._show_error_dialog("UI Initialization Error", f"Failed to initialize UI: {str(e)}")
        
    def _create_menu_bar(self):
        """Creates the main menu bar for the application."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&파일")
        
        # 새 배치 액션
        new_batch_action = QAction("새 배치 시작", self)
        new_batch_action.setShortcut("Ctrl+N")
        new_batch_action.triggered.connect(self._start_new_batch)
        file_menu.addAction(new_batch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&보기")
        
        # 로그 지우기 액션
        clear_log_action = QAction("로그 지우기", self)
        clear_log_action.setShortcut("Ctrl+Shift+C")
        clear_log_action.triggered.connect(self._clear_log)
        view_menu.addAction(clear_log_action)
        
        # 전체화면 액션
        fullscreen_action = QAction("전체화면", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Settings Menu
        settings_menu = menu_bar.addMenu("&설정")
        
        # 프로젝트 설정 액션
        project_settings_action = QAction("프로젝트 설정...", self)
        project_settings_action.setShortcut("Ctrl+,")
        project_settings_action.triggered.connect(self.show_project_settings_dialog)
        settings_menu.addAction(project_settings_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&도움말")
        
        # 사용자 매뉴얼 액션
        manual_action = QAction("사용자 매뉴얼", self)
        manual_action.setShortcut("F1")
        manual_action.triggered.connect(self.show_manual_dialog)
        help_menu.addAction(manual_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("ShotPipe 정보...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_manual_dialog(self):
        """Shows the Manual dialog."""
        manual_dialog = ManualDialog(self)
        manual_dialog.exec_()

    def show_about_dialog(self):
        """Shows the About dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()
    
    def show_project_settings_dialog(self):
        """Shows the Project Settings dialog."""
        try:
            project_settings_dialog = ProjectSettingsDialog(self)
            project_settings_dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing project settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"프로젝트 설정 다이얼로그를 열 수 없습니다:\n{str(e)}")
    
    def _start_new_batch(self):
        """새 배치 시작 (현재 활성 탭에서)"""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'start_new_batch'):
            current_tab.start_new_batch()
    
    def _clear_log(self):
        """로그 지우기"""
        if hasattr(self, 'log_text_edit'):
            self.log_text_edit.clear()
            logger.info("로그가 지워졌습니다.")
    
    def _toggle_fullscreen(self):
        """전체화면 토글"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
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
            # 인라인 스타일 제거 - 전체 다크 테마 스타일시트 사용
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
        
        # 다크 테마 적용
        from shotpipe.ui.styles.dark_theme import apply_dark_theme
        apply_dark_theme(app)
        
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