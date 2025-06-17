"""
Enhanced Shotgrid upload tab with link management functionality.
"""
import os
import json
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressBar, QComboBox, QGroupBox,
    QMessageBox, QDialog, QFormLayout, QCheckBox, QTextEdit,
    QSplitter, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QIcon, QFont
from ..shotgrid.api_connector import ShotgridConnector
from ..shotgrid.entity_manager import EntityManager
from ..shotgrid.uploader import Uploader
from ..shotgrid.link_manager import LinkManager, LinkBrowser, LinkSelector
from ..config import config
from dotenv import load_dotenv

# 기존 import 유지
try:
    from ..utils.history_manager import UploadHistoryManager
except ImportError:
    from shotpipe.utils.history_manager import UploadHistoryManager

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)

class LinkInfoDialog(QDialog):
    """Dialog to display link information for a file."""
    
    def __init__(self, file_info: dict, project_name: str, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.project_name = project_name
        self.link_manager = LinkManager()
        
        self.setWindowTitle(f"링크 정보 - {os.path.basename(file_info.get('processed_path', ''))}")
        self.setMinimumSize(800, 600)
        
        self._init_ui()
        self._load_link_info()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # File info
        file_group = QGroupBox("파일 정보")
        file_layout = QVBoxLayout(file_group)
        
        file_name = os.path.basename(self.file_info.get('processed_path', ''))
        sequence = self.file_info.get('sequence', '')
        shot = self.file_info.get('shot', '')
        task = self.file_info.get('task', '')
        
        file_info_text = f"파일명: {file_name}\n"
        file_info_text += f"시퀀스: {sequence}\n"
        file_info_text += f"샷: {shot}\n"
        file_info_text += f"태스크: {task}\n"
        
        file_info_label = QLabel(file_info_text)
        file_layout.addWidget(file_info_label)
        layout.addWidget(file_group)
        
        # Tab widget for different link types
        self.tab_widget = QTabWidget()
        
        # Existing versions tab
        self.versions_tab = QWidget()
        self._init_versions_tab()
        self.tab_widget.addTab(self.versions_tab, "기존 버전")
        
        # Related assets tab
        self.assets_tab = QWidget()
        self._init_assets_tab()
        self.tab_widget.addTab(self.assets_tab, "관련 에셋")
        
        # Similar files tab
        self.similar_tab = QWidget()
        self._init_similar_tab()
        self.tab_widget.addTab(self.similar_tab, "유사 파일")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_selector_button = QPushButton("링크 선택기 열기")
        open_selector_button.clicked.connect(self._open_link_selector)
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(open_selector_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def _init_versions_tab(self):
        """Initialize the versions tab."""
        layout = QVBoxLayout(self.versions_tab)
        
        self.versions_table = QTableWidget()
        self.versions_table.setColumnCount(6)
        self.versions_table.setHorizontalHeaderLabels([
            "버전", "태스크", "생성일", "생성자", "설명", "링크"
        ])
        self.versions_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("기존 버전:"))
        layout.addWidget(self.versions_table)
        
    def _init_assets_tab(self):
        """Initialize the assets tab."""
        layout = QVBoxLayout(self.assets_tab)
        
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(5)
        self.assets_table.setHorizontalHeaderLabels([
            "에셋", "타입", "설명", "버전 수", "링크"
        ])
        self.assets_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("관련 에셋:"))
        layout.addWidget(self.assets_table)
        
    def _init_similar_tab(self):
        """Initialize the similar files tab."""
        layout = QVBoxLayout(self.similar_tab)
        
        self.similar_table = QTableWidget()
        self.similar_table.setColumnCount(6)
        self.similar_table.setHorizontalHeaderLabels([
            "파일명", "엔티티", "태스크", "유사도", "생성일", "링크"
        ])
        self.similar_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(QLabel("유사한 파일:"))
        layout.addWidget(self.similar_table)
        
    def _load_link_info(self):
        """Load link information."""
        if not self.link_manager.connector.is_connected():
            QMessageBox.warning(self, "연결 오류", "Shotgrid에 연결되지 않았습니다.")
            return
            
        try:
            # Load existing versions
            sequence = self.file_info.get('sequence', '')
            shot = self.file_info.get('shot', '')
            task = self.file_info.get('task', '')
            
            if shot:
                versions = self.link_manager.get_existing_versions(
                    self.project_name, "Shot", shot, task
                )
                self._populate_versions_table(versions)
                
                # Load related assets
                assets = self.link_manager.get_related_assets(self.project_name, shot)
                self._populate_assets_table(assets)
            
            # Load similar files
            file_name = os.path.basename(self.file_info.get('processed_path', ''))
            similar_files = self.link_manager.search_similar_files(
                file_name, self.project_name, sequence
            )
            self._populate_similar_table(similar_files)
            
        except Exception as e:
            logger.error(f"Error loading link info: {e}")
            QMessageBox.critical(self, "로딩 오류", f"링크 정보를 로드하는 중 오류가 발생했습니다:\n{str(e)}")
            
    def _populate_versions_table(self, versions):
        """Populate the versions table."""
        self.versions_table.setRowCount(len(versions))
        
        for row, version in enumerate(versions):
            self.versions_table.setItem(row, 0, QTableWidgetItem(version.get("code", "")))
            
            task_name = ""
            if version.get("sg_task"):
                task_name = version["sg_task"].get("name", "")
            self.versions_table.setItem(row, 1, QTableWidgetItem(task_name))
            
            self.versions_table.setItem(row, 2, QTableWidgetItem(str(version.get("created_at", ""))))
            
            creator_name = ""
            if version.get("created_by"):
                creator_name = version["created_by"].get("name", "")
            self.versions_table.setItem(row, 3, QTableWidgetItem(creator_name))
            
            self.versions_table.setItem(row, 4, QTableWidgetItem(version.get("description", "")))
            self.versions_table.setItem(row, 5, QTableWidgetItem(version.get("shotgrid_url", "")))
            
    def _populate_assets_table(self, assets):
        """Populate the assets table."""
        self.assets_table.setRowCount(len(assets))
        
        for row, asset in enumerate(assets):
            self.assets_table.setItem(row, 0, QTableWidgetItem(asset.get("code", "")))
            
            asset_type = ""
            if asset.get("sg_asset_type"):
                asset_type = asset["sg_asset_type"]
            self.assets_table.setItem(row, 1, QTableWidgetItem(asset_type))
            
            self.assets_table.setItem(row, 2, QTableWidgetItem(asset.get("description", "")))
            self.assets_table.setItem(row, 3, QTableWidgetItem(str(len(asset.get("versions", [])))))
            self.assets_table.setItem(row, 4, QTableWidgetItem(asset.get("shotgrid_url", "")))
            
    def _populate_similar_table(self, similar_files):
        """Populate the similar files table."""
        self.similar_table.setRowCount(len(similar_files))
        
        for row, similar_file in enumerate(similar_files):
            self.similar_table.setItem(row, 0, QTableWidgetItem(similar_file.get("code", "")))
            
            entity_info = ""
            if similar_file.get("entity"):
                entity = similar_file["entity"]
                entity_info = f"{entity.get('type', '')} {entity.get('name', '')}"
            self.similar_table.setItem(row, 1, QTableWidgetItem(entity_info))
            
            task_name = ""
            if similar_file.get("sg_task"):
                task_name = similar_file["sg_task"].get("name", "")
            self.similar_table.setItem(row, 2, QTableWidgetItem(task_name))
            
            similarity = similar_file.get("similarity_score", 0)
            self.similar_table.setItem(row, 3, QTableWidgetItem(f"{similarity:.2f}"))
            
            self.similar_table.setItem(row, 4, QTableWidgetItem(str(similar_file.get("created_at", ""))))
            self.similar_table.setItem(row, 5, QTableWidgetItem(similar_file.get("shotgrid_url", "")))
            
    def _open_link_selector(self):
        """Open the link selector dialog."""
        file_name = os.path.basename(self.file_info.get('processed_path', ''))
        
        selector = LinkSelector(self.project_name, self)
        selector.set_current_file_name(file_name)
        
        if selector.exec_() == QDialog.Accepted:
            selected_links = selector.get_selected_links()
            if selected_links:
                self._show_selected_links_info(selected_links)
                
    def _show_selected_links_info(self, selected_links):
        """Show information about selected links."""
        info_text = f"{len(selected_links)}개의 링크가 선택되었습니다:\n\n"
        
        for i, link in enumerate(selected_links, 1):
            link_type = link["type"]
            link_data = link["data"]
            name = link_data.get("code", link_data.get("name", link_data.get("title", "")))
            url = link_data.get("url", "")
            
            info_text += f"{i}. {link_type}: {name}\n"
            info_text += f"   URL: {url}\n\n"
            
        QMessageBox.information(self, "선택된 링크", info_text)

# 기존 UploadThread 클래스는 그대로 유지...
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

class EnhancedShotgridTab(QWidget):
    """Enhanced Shotgrid tab with link management functionality."""
    
    files_processed = pyqtSignal(list)

    def __init__(self):
        """Initialize the enhanced Shotgrid tab."""
        super().__init__()
        
        # Initialize variables
        self.processed_files = []
        self.connector = ShotgridConnector()
        self.entity_manager = EntityManager(self.connector)
        self.uploader = Uploader(self.connector, self.entity_manager)
        self.link_manager = LinkManager(self.connector, self.entity_manager)
        
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
        self.files_table.setColumnCount(8)  # 링크 컬럼 추가
        self.files_table.setHorizontalHeaderLabels([
            "", "파일명", "시퀀스", "샷", "태스크", "버전", "상태", "링크"
        ])
        
        # 컬럼 너비 설정 변경
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 체크박스 컬럼은 고정
        header.resizeSection(0, 30)  # 체크박스 컬럼 폭 고정
        
        # 초기 열 너비 설정
        self.files_table.setColumnWidth(1, 250)  # 파일명
        self.files_table.setColumnWidth(2, 80)   # 시퀀스
        self.files_table.setColumnWidth(3, 80)   # 샷
        self.files_table.setColumnWidth(4, 100)  # 태스크
        self.files_table.setColumnWidth(5, 80)   # 버전
        self.files_table.setColumnWidth(6, 80)   # 상태
        self.files_table.setColumnWidth(7, 80)   # 링크
        
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.files_table.itemChanged.connect(self._on_table_item_changed)
        
        # Add header checkbox for select/deselect all
        self.header_checkbox = QCheckBox()
        self.header_checkbox.stateChanged.connect(self.toggle_all_rows)
        
        # 파일 타입 필터 및 링크 관련 버튼 추가
        filter_layout = QHBoxLayout()
        filter_label = QLabel("선택 필터:")
        self.filter_all_btn = QPushButton("모두")
        self.filter_image_btn = QPushButton("이미지")
        self.filter_video_btn = QPushButton("비디오")
        
        self.filter_all_btn.clicked.connect(lambda: self.filter_rows("all"))
        self.filter_image_btn.clicked.connect(lambda: self.filter_rows("image"))
        self.filter_video_btn.clicked.connect(lambda: self.filter_rows("video"))
        
        # 링크 관련 버튼들
        self.show_links_btn = QPushButton("링크 정보 보기")
        self.show_links_btn.clicked.connect(self._show_selected_file_links)
        
        self.browse_links_btn = QPushButton("링크 탐색기")
        self.browse_links_btn.clicked.connect(self._open_link_browser)
        
        # 자동 열 너비 조절 버튼
        self.resize_columns_btn = QPushButton("컬럼 너비 자동 조절")
        self.resize_columns_btn.clicked.connect(self.resize_columns_to_contents)
        
        # 태스크 도움말 버튼
        self.task_help_btn = QPushButton("태스크 도움말")
        self.task_help_btn.clicked.connect(self._show_task_help)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_all_btn)
        filter_layout.addWidget(self.filter_image_btn)
        filter_layout.addWidget(self.filter_video_btn)
        filter_layout.addWidget(self.show_links_btn)
        filter_layout.addWidget(self.browse_links_btn)
        filter_layout.addWidget(self.resize_columns_btn)
        filter_layout.addWidget(self.task_help_btn)
        filter_layout.addStretch()

        # Add widgets to layout
        layout.addWidget(connection_group)
        layout.addWidget(project_group)
        layout.addWidget(file_load_group)
        layout.addLayout(upload_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.files_table)
        
        # Initialize connection status
        self.update_connection_status()
        
        # Add History Manager instance
        self.history_manager = UploadHistoryManager()
        
    def _show_selected_file_links(self):
        """Show link information for selected file."""
        current_row = self.files_table.currentRow()
        if current_row >= 0 and current_row < len(self.processed_files):
            file_info = self.processed_files[current_row]
            project_name = "AXRD-296"  # 하드코딩된 프로젝트명
            
            dialog = LinkInfoDialog(file_info, project_name, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "선택 오류", "링크 정보를 보려면 파일을 선택하세요.")
            
    def _open_link_browser(self):
        """Open the link browser dialog."""
        project_name = "AXRD-296"  # 하드코딩된 프로젝트명
        
        selector = LinkSelector(project_name, self)
        selector.link_selected.connect(self._on_link_selected)
        
        # 현재 선택된 파일이 있으면 파일명을 설정
        current_row = self.files_table.currentRow()
        if current_row >= 0 and current_row < len(self.processed_files):
            file_info = self.processed_files[current_row]
            file_name = os.path.basename(file_info.get('processed_path', ''))
            selector.set_current_file_name(file_name)
        
        selector.exec_()
        
    def _on_link_selected(self, link_data):
        """Handle link selection from link browser."""
        link_type = link_data["type"]
        link_info = link_data["data"]
        name = link_info.get("code", link_info.get("name", link_info.get("title", "")))
        url = link_info.get("url", "")
        
        QMessageBox.information(self, "링크 선택됨", 
                              f"선택된 링크:\n타입: {link_type}\n이름: {name}\nURL: {url}")
        
    def update_files_table(self):
        """Update the files table with processed files (enhanced with link info)."""
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
                    checkbox_widget.setChecked(True)
                    self.files_table.setCellWidget(row, 0, checkbox_widget)
                    
                    # File name
                    if file_info.get("processed_path"):
                        file_name = os.path.basename(file_info.get("processed_path"))
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
                    task_item.setFlags(task_item.flags() | Qt.ItemIsEditable)
                    self.files_table.setItem(row, 4, task_item)
                    
                    # Version
                    version_item = QTableWidgetItem(str(file_info.get("version", "")))
                    self.files_table.setItem(row, 5, version_item)
                    
                    # Check upload status
                    is_uploaded = self.history_manager.is_file_uploaded(file_info)
                    status_item = QTableWidgetItem()
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                    
                    if is_uploaded:
                        status_item.setText("이미 업로드됨")
                        status_item.setForeground(QColor("#808080"))
                        checkbox_widget.setChecked(False)
                        uploaded_count += 1
                    else:
                        status_item.setText("대기")
                        status_item.setForeground(QColor("#E0E0E0"))
                    
                    self.files_table.setItem(row, 6, status_item)
                    
                    # Link button
                    link_button = QPushButton("링크 보기")
                    link_button.clicked.connect(lambda checked, r=row: self._show_file_links(r))
                    self.files_table.setCellWidget(row, 7, link_button)
                    
                    # Set items as non-editable (except task)
                    for col in range(1, 7):
                        if col != 4:  # Task column remains editable
                            item = self.files_table.item(row, col)
                            if item:
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                
                except Exception as e:
                    logger.error(f"Error adding row {row} to table: {e}")
                
            # Enable the upload button
            self.upload_button.setEnabled(True)
            logger.info("Files table updated successfully")
            if uploaded_count > 0:
                QMessageBox.information(self, "중복 파일 감지", 
                                      f"{uploaded_count}개의 파일이 이미 업로드된 것으로 감지되었습니다. 해당 파일은 기본적으로 선택 해제됩니다.")
                
        except Exception as e:
            logger.error(f"Error updating files table: {e}", exc_info=True)
            
    def _show_file_links(self, row):
        """Show links for a specific file row."""
        if row < len(self.processed_files):
            file_info = self.processed_files[row]
            project_name = "AXRD-296"  # 하드코딩된 프로젝트명
            
            dialog = LinkInfoDialog(file_info, project_name, self)
            dialog.exec_()
    
    # 나머지 메소드들은 기존 ShotgridTab에서 동일하게 유지
    # (show_settings, test_connection, _assign_task_automatically, etc.)
    
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
            
            if 0 <= row < len(self.processed_files):
                old_task = self.processed_files[row].get("task", "")
                self.processed_files[row]["task"] = new_task
                logger.info(f"태스크 변경됨 (행 {row}): '{old_task}' → '{new_task}'")

    def _assign_task_automatically(self, file_info):
        """자동으로 파일 유형에 따라 태스크를 할당합니다."""
        try:
            if file_info.get("task"):
                return
            
            file_path = file_info.get("processed_path") or file_info.get("file_path", "")
            if not file_path:
                logger.warning("파일 경로가 없어 태스크 자동 할당을 건너뜁니다.")
                return
            
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.exr', '.hdr'}
            video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}
            
            if ext in image_extensions:
                file_info["task"] = "txtToImage"
                logger.debug(f"이미지 파일로 인식하여 txtToImage 태스크 할당: {os.path.basename(file_path)}")
            elif ext in video_extensions:
                file_info["task"] = "imgToVideo"
                logger.debug(f"비디오 파일로 인식하여 imgToVideo 태스크 할당: {os.path.basename(file_path)}")
            else:
                file_info["task"] = "comp"
                logger.debug(f"알 수 없는 파일 유형으로 기본 comp 태스크 할당: {os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"자동 태스크 할당 중 오류 발생: {e}")
            file_info["task"] = "comp"

    def update_connection_status(self):
        """Update the connection status label."""
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
        
        button_box = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        button_box.addStretch()
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        
        save_button.clicked.connect(settings_dialog.accept)
        cancel_button.clicked.connect(settings_dialog.reject)
        
        dialog_layout.addLayout(form_layout)
        dialog_layout.addLayout(button_box)
        
        if settings_dialog.exec_() == QDialog.Accepted:
            try:
                with open(os.path.join(os.getcwd(), '.env'), 'w') as f:
                    f.write(f"# Shotgrid 연결 정보\n")
                    f.write(f"SHOTGRID_URL={server_url_edit.text()}\n")
                    f.write(f"SHOTGRID_SCRIPT_NAME={script_name_edit.text()}\n")
                    f.write(f"SHOTGRID_API_KEY={api_key_edit.text()}\n")
                
                os.environ["SHOTGRID_URL"] = server_url_edit.text()
                os.environ["SHOTGRID_SCRIPT_NAME"] = script_name_edit.text()
                os.environ["SHOTGRID_API_KEY"] = api_key_edit.text()
                
                if hasattr(self.connector, 'update_credentials'):
                    self.connector.update_credentials(
                        server_url_edit.text(),
                        script_name_edit.text(),
                        api_key_edit.text()
                    )
                
                QMessageBox.information(self, "설정 저장", "Shotgrid 연결 설정이 저장되었습니다.")
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
                QMessageBox.information(self, "연결 정보 확인", 
                                        f"서버 URL: {os.getenv('SHOTGRID_URL', '')}\n"
                                        f"스크립트 이름: {os.getenv('SHOTGRID_SCRIPT_NAME', '')}\n"
                                        f"API 키: {'*' * (len(os.getenv('SHOTGRID_API_KEY', '')) - 4) + os.getenv('SHOTGRID_API_KEY', '')[-4:] if os.getenv('SHOTGRID_API_KEY', '') else ''}\n\n"
                                        "Shotgrid API 모듈에 문제가 있어 연결 테스트를 실행할 수 없습니다.\n"
                                        "shotgun_api3 라이브러리를 올바르게 설치하세요.")
        except Exception as e:
            logger.error(f"Error in test_connection: {e}")
            QMessageBox.critical(self, "연결 테스트 오류", f"연결 테스트 중 오류가 발생했습니다: {str(e)}")
            
    def set_processed_files(self, file_infos):
        """Set the processed files from the file tab."""
        try:
            logger.info(f"Received {len(file_infos)} processed files from file tab")
            
            for file_info in file_infos:
                self._assign_task_automatically(file_info)
            
            if hasattr(self, 'processed_files') and self.processed_files:
                existing_paths = {info.get('processed_path', '') for info in self.processed_files}
                new_files = [info for info in file_infos if info.get('processed_path', '') not in existing_paths]
                self.processed_files.extend(new_files)
                logger.info(f"Added {len(new_files)} new files, filtered {len(file_infos) - len(new_files)} duplicates")
            else:
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
            status_item = self.files_table.item(i, 6)
            
            is_checked = checkbox_widget and checkbox_widget.checkState() == Qt.Checked
            is_already_uploaded = status_item and status_item.text() == "이미 업로드됨"
            
            if is_checked and not is_already_uploaded:
                if i < len(self.processed_files):
                    file_info = self.processed_files[i].copy()
                    file_info["file_info"] = file_info
                    selected_files.append(file_info)
                else:
                    logger.warning(f"Row index {i} out of bounds for processed_files list")
            
        if not selected_files:
            QMessageBox.warning(self, "경고", "업로드할 파일이 선택되지 않았습니다.")
            return
            
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
        self.upload_thread = UploadThread(selected_files, project_name, self.history_manager)
        self.upload_thread.progress_updated.connect(self.update_progress)
        self.upload_thread.upload_complete.connect(self.upload_complete)
        self.upload_thread.error_occurred.connect(self.upload_error)
        self.upload_thread.start()
        
    @pyqtSlot(int, int, object)
    def update_progress(self, current, total, result):
        """Update the progress bar and table during upload."""
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))
            
            processed_file_info = result.get("file_info")
            row = -1
            if processed_file_info:
                processed_path = processed_file_info.get("processed_path")
                for i in range(self.files_table.rowCount()):
                    try:
                        filename_item = self.files_table.item(i, 1)
                        if filename_item and os.path.basename(processed_path) == filename_item.text():
                            row = i
                            break
                    except Exception as e:
                        logger.error(f"Error finding row for progress update: {e}")
            
            if row >= 0:
                success = result.get("success", False)
                status_text = "성공" if success else "실패"
                status_color = QColor("#27AE60") if success else QColor("#E74C3C")
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(status_color)
                self.files_table.setItem(row, 6, status_item)
                
                if success:
                    checkbox_widget = self.files_table.cellWidget(row, 0)
                    if checkbox_widget:
                        checkbox_widget.setChecked(False)
                        checkbox_widget.setEnabled(False)
                
    @pyqtSlot(object)
    def upload_complete(self, results):
        """Handle upload completion."""
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
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
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)
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
            task_item = self.files_table.item(i, 4)
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
                self.files_table.setRowHidden(i, True)

    def resize_columns_to_contents(self):
        """컬럼 너비를 내용에 맞게 자동 조절"""
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.files_table.horizontalHeader().resizeSection(0, 30)
        
        QTimer.singleShot(100, self._reset_resize_mode)
    
    def _reset_resize_mode(self):
        """컬럼 크기 조절 모드를 Interactive로 되돌림"""
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
