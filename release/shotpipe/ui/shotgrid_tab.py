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
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QIcon, QFont
from ..shotgrid.api_connector import ShotgridConnector
from ..shotgrid.entity_manager import EntityManager
from ..shotgrid.uploader import Uploader
from ..config import config
from dotenv import load_dotenv
try:
    from ..utils.history_manager import UploadHistoryManager
except ImportError:
    # 절대 경로로 시도
    from shotpipe.utils.history_manager import UploadHistoryManager

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
    
    files_processed = pyqtSignal(list)

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
        
        # 컬럼 너비 설정 변경
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 기본적으로 모든 컬럼 사용자 조절 가능
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 체크박스 컬럼은 고정
        header.resizeSection(0, 30)  # 체크박스 컬럼 폭 고정
        
        # 초기 열 너비 설정
        self.files_table.setColumnWidth(1, 250)  # 파일명 초기 너비: 250픽셀
        self.files_table.setColumnWidth(2, 80)   # 시퀀스 초기 너비: 80픽셀
        self.files_table.setColumnWidth(3, 80)   # 샷 초기 너비: 80픽셀
        self.files_table.setColumnWidth(4, 100)  # 태스크 초기 너비: 100픽셀
        self.files_table.setColumnWidth(5, 80)   # 버전 초기 너비: 80픽셀
        self.files_table.setColumnWidth(6, 80)   # 상태 초기 너비: 80픽셀
        
        # 헤더 툴팁 설정
        header.setToolTip("컬럼 경계를 드래그하여 너비를 조절할 수 있습니다")
        
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 테이블 아이템 변경 시그널 연결 (태스크 편집 반영)
        self.files_table.itemChanged.connect(self._on_table_item_changed)
        
        # Add header checkbox for select/deselect all
        self.header_checkbox = QCheckBox()
        self.header_checkbox.stateChanged.connect(self.toggle_all_rows)
        
        # 파일 타입 필터 버튼 추가
        filter_layout = QHBoxLayout()
        filter_label = QLabel("선택 필터:")
        self.filter_all_btn = QPushButton("모두")
        self.filter_image_btn = QPushButton("이미지")
        self.filter_video_btn = QPushButton("비디오")
        
        self.filter_all_btn.clicked.connect(lambda: self.filter_rows("all"))
        self.filter_image_btn.clicked.connect(lambda: self.filter_rows("image"))
        self.filter_video_btn.clicked.connect(lambda: self.filter_rows("video"))
        
        # 자동 열 너비 조절 버튼 추가
        self.resize_columns_btn = QPushButton("컬럼 너비 자동 조절")
        self.resize_columns_btn.clicked.connect(self.resize_columns_to_contents)
        
        # 태스크 도움말 버튼 추가
        self.task_help_btn = QPushButton("태스크 도움말")
        self.task_help_btn.clicked.connect(self._show_task_help)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_all_btn)
        filter_layout.addWidget(self.filter_image_btn)
        filter_layout.addWidget(self.filter_video_btn)
        filter_layout.addWidget(self.resize_columns_btn)
        filter_layout.addWidget(self.task_help_btn)
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
        
    def _show_task_help(self):
        """태스크 매핑 정보를 표시합니다."""
        help_title = "ShotPipe 태스크 매핑 정보"
        help_text = """
        <p><b>ShotPipe에서 지원하는 AI 서비스 태스크:</b></p>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr><th>태스크 코드</th><th>설명</th></tr>
        <tr><td>txtToImage</td><td>텍스트 프롬프트에서 이미지 생성</td></tr>
        <tr><td>imgToImage</td><td>기존 이미지를 기반으로 새 이미지 생성</td></tr>
        <tr><td>imgToVideo</td><td>이미지를 움직이는 비디오로 변환</td></tr>
        <tr><td>txtToVideo</td><td>텍스트 프롬프트에서 비디오 생성</td></tr>
        <tr><td>vidToVideo</td><td>기존 비디오를 변환/스타일 적용</td></tr>
        <tr><td>imgUpscale</td><td>이미지 해상도 향상</td></tr>
        <tr><td>vidUpscale</td><td>비디오 해상도 향상</td></tr>
        <tr><td>imgInpaint</td><td>이미지 부분 채우기/복원</td></tr>
        <tr><td>vidInpaint</td><td>비디오 부분 채우기/복원</td></tr>
        <tr><td>imgOutpaint</td><td>이미지 확장/경계 바깥 생성</td></tr>
        <tr><td>vidOutpaint</td><td>비디오 확장/경계 바깥 생성</td></tr>
        <tr><td>imgCorrect</td><td>이미지 색상/구도 보정</td></tr>
        <tr><td>vidCorrect</td><td>비디오 색상/안정화 보정</td></tr>
        <tr><td>gen3D</td><td>3D 모델/에셋 생성</td></tr>
        <tr><td>txtToAudio</td><td>텍스트에서 음성/음향 생성</td></tr>
        <tr><td>txtToMusic</td><td>텍스트 설명에서 음악 생성</td></tr>
        <tr><td>audToAudio</td><td>오디오 변환/향상</td></tr>
        <tr><td>charAnimate</td><td>캐릭터 애니메이션 생성</td></tr>
        <tr><td>mocapGen</td><td>모션 캡처 데이터 생성</td></tr>
        <tr><td>bgRemove</td><td>배경 제거/투명화</td></tr>
        <tr><td>comp</td><td>기본 컴포지팅 태스크</td></tr>
        </table>
        <p><b>자동 할당 규칙:</b></p>
        <ul>
        <li>이미지 파일 (.png, .jpg, .jpeg 등): <b>txtToImage</b></li>
        <li>비디오 파일 (.mp4, .mov, .avi 등): <b>imgToVideo</b></li>
        <li>기타 파일: <b>comp</b> (기본값)</li>
        </ul>
        <p>태스크 컬럼을 클릭하여 직접 수정할 수 있습니다.</p>
        """
        QMessageBox.information(self, help_title, help_text)

    def _on_table_item_changed(self, item):
        """테이블 아이템이 변경되었을 때 처리합니다."""
        if item.column() == 4:  # 태스크 컬럼
            row = item.row()
            new_task = item.text()
            
            # processed_files 리스트에도 변경사항 반영
            if 0 <= row < len(self.processed_files):
                old_task = self.processed_files[row].get("task", "")
                self.processed_files[row]["task"] = new_task
                logger.info(f"태스크 변경됨 (행 {row}): '{old_task}' → '{new_task}'")

    def _assign_task_automatically(self, file_info):
        """자동으로 파일 유형에 따라 태스크를 할당합니다."""
        try:
            # 이미 태스크가 할당되어 있으면 건너뛰기
            if file_info.get("task"):
                return
            
            # 파일 경로에서 확장자 추출
            file_path = file_info.get("processed_path") or file_info.get("file_path", "")
            if not file_path:
                logger.warning("파일 경로가 없어 태스크 자동 할당을 건너뜁니다.")
                return
            
            # 확장자 추출 및 소문자 변환
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # 파일 유형별 자동 태스크 매핑
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.exr', '.hdr'}
            video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}
            
            if ext in image_extensions:
                file_info["task"] = "txtToImage"
                logger.debug(f"이미지 파일로 인식하여 txtToImage 태스크 할당: {os.path.basename(file_path)}")
            elif ext in video_extensions:
                file_info["task"] = "imgToVideo"
                logger.debug(f"비디오 파일로 인식하여 imgToVideo 태스크 할당: {os.path.basename(file_path)}")
            else:
                # 기본 태스크 할당
                file_info["task"] = "comp"  # 기본 컴포지팅 태스크
                logger.debug(f"알 수 없는 파일 유형으로 기본 comp 태스크 할당: {os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"자동 태스크 할당 중 오류 발생: {e}")
            # 오류 발생 시 기본값 설정
            file_info["task"] = "comp"

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
        settings_dialog.setMinimumWidth(450)
        
        dialog_layout = QVBoxLayout(settings_dialog)
        form_layout = QFormLayout()
        
        server_url_edit = QLineEdit(os.getenv("SHOTGRID_URL", ""))
        script_name_edit = QLineEdit(os.getenv("SHOTGRID_SCRIPT_NAME", ""))
        api_key_edit = QLineEdit(os.getenv("SHOTGRID_API_KEY", ""))
        api_key_edit.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("서버 URL:", server_url_edit)
        form_layout.addRow("스크립트 이름:", script_name_edit)
        form_layout.addRow("API 키:", api_key_edit)
        
        # Help button
        help_layout = QHBoxLayout()
        help_layout.addStretch()
        help_button = QPushButton("이 정보는 어떻게 얻나요?")
        help_button.setStyleSheet("text-decoration: underline; color: #a9a9a9; border: none;")
        help_button.clicked.connect(self._show_api_help)
        help_layout.addWidget(help_button)
        
        # Buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        button_box.addStretch()
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        
        save_button.clicked.connect(settings_dialog.accept)
        cancel_button.clicked.connect(settings_dialog.reject)
        
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(help_layout)
        dialog_layout.addLayout(button_box)
        
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
            
    def _show_api_help(self):
        """Display a message box with instructions on how to get API credentials."""
        help_title = "Shotgrid API 정보 얻는 방법"
        help_text = """
        <p>Shotgrid API 정보는 Shotgrid 사이트 관리자가 직접 생성해야 합니다.</p>
        <p><b>1. 스크립트 생성:</b></p>
        <ul>
            <li>Shotgrid 우측 상단 프로필 메뉴 > <b>Scripts</b> 페이지로 이동합니다.</li>
            <li><b>+ Add Script</b> 버튼을 클릭하여 새 스크립트를 추가합니다.</li>
            <li><b>Script Name</b>에 'AX_shotPipe' 와 같이 원하는 스크립트 이름을 입력합니다.</li>
            <li>필요한 권한(Permissions)을 설정합니다.</li>
            <li><b>Save</b>를 눌러 스크립트를 생성합니다.</li>
        </ul>
        <p><b>2. API 키 확인:</b></p>
        <ul>
            <li>생성된 스크립트의 'API Key' 필드에 있는 값이 <b>API 키</b>입니다.</li>
            <li><b>서버 URL</b>은 현재 사용 중인 Shotgrid 사이트 주소입니다 (예: https://mystudio.shotgrid.autodesk.com).</li>
            <li><b>스크립트 이름</b>은 위에서 지정한 이름입니다.</li>
        </ul>
        <p>이 정보들을 복사하여 ShotPipe 설정 창에 입력하세요.</p>
        """
        QMessageBox.information(self, help_title, help_text)
            
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
            
            # 자동 태스크 할당 수행
            for file_info in file_infos:
                self._assign_task_automatically(file_info)
            
            # 중복 제거를 위해 processed_path를 기준으로 기존 항목을 필터링
            if hasattr(self, 'processed_files') and self.processed_files:
                # 기존 파일의 processed_path 목록 생성
                existing_paths = {info.get('processed_path', '') for info in self.processed_files}
                
                # 중복되지 않은 새 파일만 추가
                new_files = [info for info in file_infos if info.get('processed_path', '') not in existing_paths]
                
                # 기존 목록에 새 파일 추가
                self.processed_files.extend(new_files)
                logger.info(f"Added {len(new_files)} new files, filtered {len(file_infos) - len(new_files)} duplicates")
            else:
                # 처음 설정할 때는 그대로 할당
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
                    
                    # Task (편집 가능하게 설정)
                    task_item = QTableWidgetItem(str(file_info.get("task", "")))
                    task_item.setFlags(task_item.flags() | Qt.ItemIsEditable)  # 편집 가능하게 설정
                    self.files_table.setItem(row, 4, task_item)
                    
                    # Version
                    version_item = QTableWidgetItem(str(file_info.get("version", "")))
                    self.files_table.setItem(row, 5, version_item)
                    
                    # Check upload status and set item style
                    is_uploaded = self.history_manager.is_file_uploaded(file_info)
                    status_item = QTableWidgetItem()
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                    
                    if is_uploaded:
                        status_item.setText("이미 업로드됨")
                        status_item.setForeground(QColor("#808080"))  # 회색 텍스트
                        checkbox_widget.setChecked(False)
                        uploaded_count += 1
                    else:
                        status_item.setText("대기")
                        status_item.setForeground(QColor("#E0E0E0"))  # 밝은 텍스트
                    
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
                # Ensure the file index is within bounds and add file_info for progress tracking
                if i < len(self.processed_files):
                    file_info = self.processed_files[i].copy()
                    file_info["file_info"] = file_info  # Add self-reference for progress tracking
                    selected_files.append(file_info)
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
                status_color = QColor("#27AE60") if success else QColor("#E74C3C")  # Green or Red text
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(status_color)
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

    def resize_columns_to_contents(self):
        """컬럼 너비를 내용에 맞게 자동 조절"""
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 체크박스 컬럼은 고정 크기 유지
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.files_table.horizontalHeader().resizeSection(0, 30)
        
        # 잠시 후 Interactive 모드로 다시 변경 (자동 조절 후 사용자가 다시 조절할 수 있도록)
        QTimer.singleShot(100, self._reset_resize_mode)
    
    def _reset_resize_mode(self):
        """컬럼 크기 조절 모드를 Interactive로 되돌림"""
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)