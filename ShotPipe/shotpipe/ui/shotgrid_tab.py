"""
Shotgrid upload tab module for ShotPipe UI.
"""
import os
import json
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressBar, QComboBox, QGroupBox,
    QMessageBox, QDialog, QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QColor
from ..shotgrid.api_connector import ShotgridConnector
from ..shotgrid.entity_manager import EntityManager
from ..shotgrid.uploader import Uploader
from ..config import config
from dotenv import load_dotenv
from ..utils.history_manager import UploadHistoryManager

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)

class UploadThread(QThread):
    """Thread for uploading files to Shotgrid in the background."""
    
    progress_updated = pyqtSignal(int, int, object)
    upload_complete = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_infos, project_name, history_manager):
        """Initialize the upload thread."""
        super().__init__()
        self.file_infos = file_infos
        self.project_name = project_name
        self.uploader = Uploader()
        self.history_manager = history_manager
        
    def run(self):
        """Run the thread."""
        try:
            # Define progress callback
            def progress_callback(current, total, result):
                self.progress_updated.emit(current, total, result)
            
            # Upload files
            results = self.uploader.upload_files_batch(
                self.file_infos, self.project_name, progress_callback
            )
            
            # Emit complete signal
            self.upload_complete.emit(results)
            
        except Exception as e:
            logger.error(f"Error in upload thread: {e}")
            self.error_occurred.emit(str(e))

class ShotgridTab(QWidget):
    """Tab for Shotgrid upload functionality."""
    
    def __init__(self):
        """Initialize the Shotgrid tab."""
        super().__init__()
        
        # Initialize variables
        self.processed_files = []
        self.connector = ShotgridConnector()
        self.entity_manager = EntityManager(self.connector)
        self.uploader = Uploader(self.connector, self.entity_manager)
        
        # 환경 변수에서 Shotgrid 연결 정보 가져오기
        self.server_url = os.getenv("SHOTGRID_URL", "")
        self.script_name = os.getenv("SHOTGRID_SCRIPT_NAME", "")
        self.api_key = os.getenv("SHOTGRID_API_KEY", "")
        
        # Set up UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create connection group
        connection_group = QGroupBox("Shotgrid 연결")
        connection_layout = QHBoxLayout(connection_group)
        
        self.connection_status_label = QLabel("연결 상태: 연결되지 않음")
        
        self.connect_button = QPushButton("연결 설정")
        self.connect_button.clicked.connect(self.show_settings)
        
        self.test_connection_button = QPushButton("연결 테스트")
        self.test_connection_button.clicked.connect(self.test_connection)
        
        connection_layout.addWidget(self.connection_status_label)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.test_connection_button)
        
        # Create project group
        project_group = QGroupBox("프로젝트")
        project_layout = QHBoxLayout(project_group)
        
        self.project_label = QLabel("프로젝트:")
        
        # 하드코딩된 프로젝트 사용
        self.project_name_label = QLabel("AXRD-296")
        self.project_name_label.setStyleSheet("font-weight: bold;")
        
        project_layout.addWidget(self.project_label)
        project_layout.addWidget(self.project_name_label)
        project_layout.addStretch()

        # 시퀀스 선택 UI는 파일 처리 탭으로 이동
        
        # Create file load group
        file_load_group = QGroupBox("파일 로드")
        file_load_layout = QHBoxLayout(file_load_group)
        
        self.load_button = QPushButton("처리된 파일 로드")
        self.load_button.clicked.connect(self.load_processed_files)
        
        self.load_file_button = QPushButton("파일에서 로드")
        self.load_file_button.clicked.connect(self.load_from_file)
        
        file_load_layout.addWidget(self.load_button)
        file_load_layout.addWidget(self.load_file_button)
        
        # Create upload button and progress bar
        upload_layout = QHBoxLayout()
        
        self.upload_button = QPushButton("Shotgrid 업로드")
        self.upload_button.clicked.connect(self.upload_files)
        self.upload_button.setEnabled(False)
        
        upload_layout.addWidget(self.upload_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        # Create table widget for displaying files
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(7)  # 컬럼 수 7개로 변경
        self.files_table.setHorizontalHeaderLabels(["", "파일명", "시퀀스", "샷", "태스크", "버전", "상태"]) # 첫 번째 컬럼 추가
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # 체크박스 컬럼
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # 파일명 컬럼
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Add header checkbox for select/deselect all
        self.header_checkbox = QCheckBox()
        self.header_checkbox.stateChanged.connect(self.toggle_all_rows)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.files_table.horizontalHeader().resizeSection(0, 30) # 체크박스 컬럼 폭 고정
        self.files_table.horizontalHeader().setStyleSheet("QHeaderView::section:horizontal#0 { padding-left: 10px; }")
        # Place checkbox in header
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setMinimumSectionSize(30)
        header.setMaximumSectionSize(30)
        # Header에 checkbox를 직접 추가하는 것은 표준적이지 않음. 대신 QHeaderView를 서브클래싱하거나
        # 별도 레이아웃을 사용해야 함. 여기서는 간단하게 기능 구현.

        # 파일 타입 필터 버튼 추가
        filter_layout = QHBoxLayout()
        filter_label = QLabel("선택 필터:")
        self.filter_all_btn = QPushButton("모두")
        self.filter_image_btn = QPushButton("이미지")
        self.filter_video_btn = QPushButton("비디오")
        
        self.filter_all_btn.clicked.connect(lambda: self.filter_rows("all"))
        self.filter_image_btn.clicked.connect(lambda: self.filter_rows("image"))
        self.filter_video_btn.clicked.connect(lambda: self.filter_rows("video"))
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_all_btn)
        filter_layout.addWidget(self.filter_image_btn)
        filter_layout.addWidget(self.filter_video_btn)
        filter_layout.addStretch()

        # Add widgets to layout
        layout.addWidget(connection_group)
        layout.addWidget(project_group)
        layout.addWidget(file_load_group)
        layout.addLayout(upload_layout)
        layout.addLayout(filter_layout) # 필터 레이아웃 추가
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.files_table)
        
        # Initialize connection status
        self.update_connection_status()
        
        # Add History Manager instance
        self.history_manager = UploadHistoryManager()
        
    def update_connection_status(self):
        """Update the connection status label."""
        # .env 파일에서 설정된 값이 있는지 확인
        env_url = os.getenv("SHOTGRID_URL", "")
        env_script = os.getenv("SHOTGRID_SCRIPT_NAME", "")
        env_key = os.getenv("SHOTGRID_API_KEY", "")
        
        if env_url and env_script and env_key:
            self.connection_status_label.setText(f"연결 상태: 준비됨 ({env_url})")
            self.connection_status_label.setStyleSheet("color: orange")
        elif self.connector.is_connected():
            self.connection_status_label.setText(f"연결 상태: 연결됨 ({self.connector.server_url})")
            self.connection_status_label.setStyleSheet("color: green")
        else:
            self.connection_status_label.setText("연결 상태: 연결되지 않음")
            self.connection_status_label.setStyleSheet("color: red")
            
    def show_settings(self):
        """Show the Shotgrid connection settings dialog."""
        # Create dialog
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Shotgrid 연결 설정")
        settings_dialog.setMinimumWidth(400)
        
        # Create layout
        dialog_layout = QVBoxLayout(settings_dialog)
        form_layout = QFormLayout()
        
        # Create widgets
        server_url_label = QLabel("서버 URL:")
        server_url_edit = QLineEdit()
        
        # .env 파일에서 가져온 값 사용
        server_url_edit.setText(os.getenv("SHOTGRID_URL", ""))
        
        script_name_label = QLabel("스크립트 이름:")
        script_name_edit = QLineEdit()
        script_name_edit.setText(os.getenv("SHOTGRID_SCRIPT_NAME", ""))
        
        api_key_label = QLabel("API 키:")
        api_key_edit = QLineEdit()
        api_key_edit.setText(os.getenv("SHOTGRID_API_KEY", ""))
        api_key_edit.setEchoMode(QLineEdit.Password)
        
        # Add widgets to form layout
        form_layout.addRow(server_url_label, server_url_edit)
        form_layout.addRow(script_name_label, script_name_edit)
        form_layout.addRow(api_key_label, api_key_edit)
        
        # Create buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        
        save_button.clicked.connect(settings_dialog.accept)
        cancel_button.clicked.connect(settings_dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Add layouts to dialog layout
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(button_layout)
        
        # Show dialog
        if settings_dialog.exec_() == QDialog.Accepted:
            try:
                # .env 파일 업데이트
                with open(os.path.join(os.getcwd(), '.env'), 'w') as f:
                    f.write(f"# Shotgrid 연결 정보\n")
                    f.write(f"SHOTGRID_URL={server_url_edit.text()}\n")
                    f.write(f"SHOTGRID_SCRIPT_NAME={script_name_edit.text()}\n")
                    f.write(f"SHOTGRID_API_KEY={api_key_edit.text()}\n")
                
                # 환경 변수 업데이트
                os.environ["SHOTGRID_URL"] = server_url_edit.text()
                os.environ["SHOTGRID_SCRIPT_NAME"] = script_name_edit.text()
                os.environ["SHOTGRID_API_KEY"] = api_key_edit.text()
                
                # Connector 업데이트
                if hasattr(self.connector, 'update_credentials'):
                    # Connector가 초기화되었으면 업데이트
                    self.connector.update_credentials(
                        server_url_edit.text(),
                        script_name_edit.text(),
                        api_key_edit.text()
                    )
                
                # 저장 성공 메시지
                QMessageBox.information(self, "설정 저장", "Shotgrid 연결 설정이 저장되었습니다.")
                
                # Connection 상태 업데이트
                self.update_connection_status()
                
            except Exception as e:
                logger.error(f"Error saving settings: {e}")
                QMessageBox.critical(self, "설정 저장 오류", f"설정을 저장하는 중 오류가 발생했습니다: {str(e)}")
            
    def test_connection(self):
        """Test the connection to Shotgrid."""
        try:
            if self.connector.test_connection():
                QMessageBox.information(self, "연결 성공", "Shotgrid 연결에 성공했습니다.")
            else:
                # 직접 API 키 확인
                QMessageBox.information(self, "연결 정보 확인", 
                                        f"서버 URL: {os.getenv('SHOTGRID_URL', '')}\n"
                                        f"스크립트 이름: {os.getenv('SHOTGRID_SCRIPT_NAME', '')}\n"
                                        f"API 키: {'*' * (len(os.getenv('SHOTGRID_API_KEY', '')) - 4) + os.getenv('SHOTGRID_API_KEY', '')[-4:] if os.getenv('SHOTGRID_API_KEY', '') else ''}\n\n"
                                        "Shotgrid API 모듈에 문제가 있어 연결 테스트를 실행할 수 없습니다.\n"
                                        "shotgun_api3 라이브러리를 올바르게 설치하세요.")
        except Exception as e:
            logger.error(f"Error in test_connection: {e}")
            QMessageBox.critical(self, "연결 테스트 오류", f"연결 테스트 중 오류가 발생했습니다: {str(e)}")
            
    def refresh_projects(self):
        """Refresh the list of projects from Shotgrid."""
        if not self.connector.is_connected():
            QMessageBox.warning(self, "경고", "Shotgrid에 연결되지 않았습니다. 연결 설정을 확인하세요.")
            return
            
        # Get projects
        projects = self.entity_manager.get_projects()
        
        # Clear and update combo box
        self.project_combo.clear()
        
        if projects:
            for project in projects:
                self.project_combo.addItem(project["name"])
                
            QMessageBox.information(self, "프로젝트 로드", f"{len(projects)}개 프로젝트를 로드했습니다.")
        else:
            QMessageBox.warning(self, "경고", "프로젝트를 찾을 수 없습니다.")
            
    def set_processed_files(self, file_infos):
        """Set the processed files from the file tab."""
        try:
            logger.info(f"Received {len(file_infos)} processed files from file tab")
            self.processed_files = file_infos
            self.update_files_table()
        except Exception as e:
            logger.error(f"Error setting processed files: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"처리된 파일 설정 중 오류가 발생했습니다: {str(e)}")
        
    def load_processed_files(self):
        """Load the processed files from memory."""
        if not self.processed_files:
            QMessageBox.warning(self, "경고", "처리된 파일이 없습니다. 파일 처리 탭에서 먼저 파일을 처리하세요.")
            return
            
        self.update_files_table()
        
    def load_from_file(self):
        """Load processed files from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "처리된 파일 데이터 로드", "", "JSON 파일 (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, "r") as f:
                file_infos = json.load(f)
                
            self.processed_files = file_infos
            self.update_files_table()
            
        except Exception as e:
            QMessageBox.critical(self, "파일 로드 오류", f"파일을 로드하는 중 오류가 발생했습니다:\n{e}")
            
    def update_files_table(self):
        """Update the files table with processed files."""
        try:
            # Clear the table
            self.files_table.setRowCount(0)
            
            if not self.processed_files:
                logger.warning("No processed files to display in table")
                return
                
            logger.info(f"Updating table with {len(self.processed_files)} files")
            
            # Populate the table
            self.files_table.setRowCount(len(self.processed_files))
            uploaded_count = 0
            for row, file_info in enumerate(self.processed_files):
                try:
                    # Create checkbox item for selection
                    checkbox_widget = QCheckBox()
                    checkbox_widget.setChecked(True) # 기본적으로 선택된 상태
                    self.files_table.setCellWidget(row, 0, checkbox_widget)
                    
                    # 처리된 파일 경로에서 파일명 가져오기 (우선순위 변경)
                    if file_info.get("processed_path"):
                        file_name = os.path.basename(file_info.get("processed_path"))
                    # 후순위: 직접 file_name 필드 또는 원본 경로에서 가져오기
                    elif file_info.get("file_name"):
                        file_name = file_info.get("file_name")
                    elif file_info.get("file_path"):
                        file_name = os.path.basename(file_info.get("file_path"))
                    else:
                        file_name = "Unknown"
                    
                    file_name_item = QTableWidgetItem(file_name)
                    self.files_table.setItem(row, 1, file_name_item)
                    
                    # Sequence
                    sequence_item = QTableWidgetItem(str(file_info.get("sequence", "")))
                    self.files_table.setItem(row, 2, sequence_item)
                    
                    # Shot
                    shot_item = QTableWidgetItem(str(file_info.get("shot", "")))
                    self.files_table.setItem(row, 3, shot_item)
                    
                    # Task
                    task_item = QTableWidgetItem(str(file_info.get("task", "")))
                    self.files_table.setItem(row, 4, task_item)
                    
                    # Version
                    version_item = QTableWidgetItem(str(file_info.get("version", "")))
                    self.files_table.setItem(row, 5, version_item)
                    
                    # Check upload status
                    is_uploaded = self.history_manager.is_file_uploaded(file_info)
                    status_text = "대기"
                    status_color = QColor(255, 255, 255) # Default white
                    if is_uploaded:
                        status_text = "이미 업로드됨"
                        status_color = QColor(200, 200, 200) # Gray
                        checkbox_widget.setChecked(False) # 중복 파일은 기본적으로 해제
                        uploaded_count += 1
                        
                    status_item = QTableWidgetItem(status_text)
                    status_item.setBackground(status_color)
                    self.files_table.setItem(row, 6, status_item)
                    
                    # Set items as non-editable
                    for col in range(1, 7):
                        item = self.files_table.item(row, col)
                        if item:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            
                except Exception as e:
                    logger.error(f"Error adding row {row} to table: {e}")
                
            # Enable the upload button
            self.upload_button.setEnabled(True)
            logger.info("Files table updated successfully")
            if uploaded_count > 0:
                QMessageBox.information(self, "중복 파일 감지", f"{uploaded_count}개의 파일이 이미 업로드된 것으로 감지되었습니다. 해당 파일은 기본적으로 선택 해제됩니다.")
                
        except Exception as e:
            logger.error(f"Error updating files table: {e}", exc_info=True)
        
    # update_shot_prefix 메소드 제거 - 파일 처리 단계에서 시퀀스가 적용됨
    
    def upload_files(self):
        """Upload the files to Shotgrid."""
        if not self.connector.is_connected():
            QMessageBox.warning(self, "경고", "Shotgrid에 연결되지 않았습니다. 연결 설정을 확인하세요.")
            return
            
        if not self.processed_files:
            QMessageBox.warning(self, "경고", "업로드할 파일이 없습니다.")
            return
            
        # Get selected files from table
        selected_files = []
        for i in range(self.files_table.rowCount()):
            checkbox_widget = self.files_table.cellWidget(i, 0)
            status_item = self.files_table.item(i, 6) # 상태 컬럼
            
            is_checked = checkbox_widget and checkbox_widget.checkState() == Qt.Checked
            is_already_uploaded = status_item and status_item.text() == "이미 업로드됨"
            
            if is_checked and not is_already_uploaded:
                # Ensure the file index is within bounds
                if i < len(self.processed_files):
                    selected_files.append(self.processed_files[i])
                else:
                    logger.warning(f"Row index {i} out of bounds for processed_files list")
            
        if not selected_files:
            QMessageBox.warning(self, "경고", "업로드할 파일이 선택되지 않았습니다.")
            return
            
        # 하드코딩된 프로젝트 이름 사용
        project_name = "AXRD-296"
            
        # Confirm upload
        message = f"{len(selected_files)}개 파일을 프로젝트 '{project_name}'에 업로드하시겠습니까?"
        if QMessageBox.question(self, "업로드 확인", message) != QMessageBox.Yes:
            return
            
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Disable buttons during upload
        self.upload_button.setEnabled(False)
        
        # Create and start upload thread
        self.upload_thread = UploadThread(selected_files, project_name, self.history_manager) # History manager 전달
        self.upload_thread.progress_updated.connect(self.update_progress)
        self.upload_thread.upload_complete.connect(self.upload_complete)
        self.upload_thread.error_occurred.connect(self.upload_error)
        self.upload_thread.start()
        
    @pyqtSlot(int, int, object)
    def update_progress(self, current, total, result):
        """Update the progress bar and table during upload."""
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))
            
            # Find the corresponding row for the processed item
            processed_file_info = result.get("file_info")
            row = -1
            if processed_file_info:
                processed_path = processed_file_info.get("processed_path")
                for i in range(self.files_table.rowCount()):
                    # Find row by matching processed path
                    try:
                        # 테이블에서 파일명 가져오기 (컬럼 인덱스 확인 필요 - 현재 1)
                        filename_item = self.files_table.item(i, 1)
                        if filename_item and os.path.basename(processed_path) == filename_item.text():
                            row = i
                            break
                    except Exception as e:
                        logger.error(f"Error finding row for progress update: {e}")
            
            # Update status in table for current item
            if row >= 0:
                success = result.get("success", False)
                status_text = "성공" if success else "실패"
                status_color = QColor(0, 255, 0) if success else QColor(255, 0, 0)  # Green or Red
                
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(status_color)
                self.files_table.setItem(row, 6, status_item)
                
                # 성공 시 체크박스 해제
                if success:
                    checkbox_widget = self.files_table.cellWidget(row, 0)
                    if checkbox_widget:
                        checkbox_widget.setChecked(False)
                        checkbox_widget.setEnabled(False) # 재선택 방지
                
    @pyqtSlot(object)
    def upload_complete(self, results):
        """Handle upload completion."""
        # Re-enable buttons
        self.upload_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Show success message
        success_count = results.get("success", 0)
        failure_count = results.get("failure", 0)
        message = f"업로드 완료: {success_count}개 성공, {failure_count}개 실패"
        
        if failure_count > 0:
            QMessageBox.warning(self, "업로드 완료", message)
        else:
            QMessageBox.information(self, "업로드 완료", message)
            
    @pyqtSlot(str)
    def upload_error(self, error_message):
        """Handle upload error."""
        # Re-enable buttons
        self.upload_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Show error message
        QMessageBox.critical(self, "업로드 오류", f"파일 업로드 중 오류가 발생했습니다:\n{error_message}")

    def toggle_all_rows(self, state):
        """Select or deselect all rows based on header checkbox state."""
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        for i in range(self.files_table.rowCount()):
            widget_item = self.files_table.cellWidget(i, 0)
            if widget_item:
                widget_item.setCheckState(check_state)
                
    def filter_rows(self, file_type):
        """Filter table rows based on file type."""
        for i in range(self.files_table.rowCount()):
            task_item = self.files_table.item(i, 4) # Task column
            if task_item:
                task = task_item.text().lower()
                is_image = task == "txttoimage"
                is_video = task == "imgtovideo"
                
                should_show = False
                if file_type == "all":
                    should_show = True
                elif file_type == "image" and is_image:
                    should_show = True
                elif file_type == "video" and is_video:
                    should_show = True
                    
                self.files_table.setRowHidden(i, not should_show)
            else:
                # Task 정보가 없는 경우 일단 숨김
                self.files_table.setRowHidden(i, True)