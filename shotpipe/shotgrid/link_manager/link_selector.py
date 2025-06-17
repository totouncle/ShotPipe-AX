"""
Link Selector UI component for selecting Shotgrid entities and links.
Provides interactive interface for users to browse and select links.
"""
import logging
from typing import List, Dict, Optional, Any, Callable
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget, QTreeWidget, QTreeWidgetItem,
    QComboBox, QTextEdit, QSplitter, QGroupBox, QMessageBox,
    QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QIcon, QFont, QPixmap
from .link_browser import LinkBrowser
from .link_manager import LinkManager

logger = logging.getLogger(__name__)

class LinkSearchThread(QThread):
    """Thread for searching links in the background."""
    
    search_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, link_browser: LinkBrowser, project_name: str, search_term: str):
        super().__init__()
        self.link_browser = link_browser
        self.project_name = project_name
        self.search_term = search_term
        
    def run(self):
        try:
            results = self.link_browser.search_entities(self.project_name, self.search_term)
            self.search_complete.emit(results)
        except Exception as e:
            logger.error(f"Error in search thread: {e}")
            self.error_occurred.emit(str(e))

class LinkSelector(QDialog):
    """Dialog for selecting Shotgrid links and entities."""
    
    link_selected = pyqtSignal(dict)  # Emitted when a link is selected
    
    def __init__(self, project_name: str = "AXRD-296", parent=None):
        """
        Initialize the link selector dialog.
        
        Args:
            project_name: Project name to browse
            parent: Parent widget
        """
        super().__init__(parent)
        self.project_name = project_name
        self.link_manager = LinkManager()
        self.link_browser = LinkBrowser(self.link_manager)
        self.selected_links = []
        
        self.setWindowTitle(f"Shotgrid Link 선택 - {project_name}")
        self.setMinimumSize(1000, 700)
        
        self._init_ui()
        self._load_project_structure()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Browse tab
        self.browse_tab = self._create_browse_tab()
        self.tab_widget.addTab(self.browse_tab, "프로젝트 탐색")
        
        # Search tab
        self.search_tab = self._create_search_tab()
        self.tab_widget.addTab(self.search_tab, "검색")
        
        # Recent activity tab
        self.activity_tab = self._create_activity_tab()
        self.tab_widget.addTab(self.activity_tab, "최근 활동")
        
        # Similar files tab
        self.similar_tab = self._create_similar_tab()
        self.tab_widget.addTab(self.similar_tab, "유사 파일")
        
        layout.addWidget(self.tab_widget)
        
        # Selected links display
        selected_group = QGroupBox("선택된 링크")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selected_list = QTableWidget()
        self.selected_list.setColumnCount(4)
        self.selected_list.setHorizontalHeaderLabels(["타입", "이름", "설명", "URL"])
        self.selected_list.horizontalHeader().setStretchLastSection(True)
        self.selected_list.setMaximumHeight(150)
        
        selected_layout.addWidget(self.selected_list)
        layout.addWidget(selected_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("선택 해제")
        self.clear_button.clicked.connect(self.clear_selection)
        
        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def _create_browse_tab(self) -> QWidget:
        """Create the browse tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Project structure tree
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels(["이름", "타입", "상태", "버전 수"])
        self.project_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        
        layout.addWidget(QLabel("프로젝트 구조:"))
        layout.addWidget(self.project_tree)
        
        # Details panel
        details_group = QGroupBox("상세 정보")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        
        details_layout.addWidget(self.details_text)
        layout.addWidget(details_group)
        
        # Add to selection button
        add_button = QPushButton("선택에 추가")
        add_button.clicked.connect(self._add_current_browse_selection)
        layout.addWidget(add_button)
        
        return tab
        
    def _create_search_tab(self) -> QWidget:
        """Create the search tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("검색:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("시퀀스, 샷, 에셋 이름을 입력하세요...")
        self.search_edit.returnPressed.connect(self._perform_search)
        search_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self._perform_search)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Entity type filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("타입 필터:"))
        
        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItems(["전체", "Shot", "Asset", "Sequence"])
        filter_layout.addWidget(self.entity_type_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Search results
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(6)
        self.search_results.setHorizontalHeaderLabels(["타입", "코드", "설명", "상태", "버전 수", "URL"])
        self.search_results.horizontalHeader().setStretchLastSection(True)
        self.search_results.itemDoubleClicked.connect(self._on_search_result_double_clicked)
        
        layout.addWidget(QLabel("검색 결과:"))
        layout.addWidget(self.search_results)
        
        # Search progress
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        layout.addWidget(self.search_progress)
        
        # Add selected results button
        add_search_button = QPushButton("선택된 항목 추가")
        add_search_button.clicked.connect(self._add_selected_search_results)
        layout.addWidget(add_search_button)
        
        return tab
        
    def _create_activity_tab(self) -> QWidget:
        """Create the recent activity tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self._load_recent_activity)
        refresh_layout.addWidget(refresh_button)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Activity list
        self.activity_list = QTableWidget()
        self.activity_list.setColumnCount(5)
        self.activity_list.setHorizontalHeaderLabels(["제목", "엔티티", "태스크", "생성자", "생성일"])
        self.activity_list.horizontalHeader().setStretchLastSection(True)
        self.activity_list.itemDoubleClicked.connect(self._on_activity_item_double_clicked)
        
        layout.addWidget(QLabel("최근 활동:"))
        layout.addWidget(self.activity_list)
        
        # Add activity selection button
        add_activity_button = QPushButton("선택된 활동 추가")
        add_activity_button.clicked.connect(self._add_selected_activity)
        layout.addWidget(add_activity_button)
        
        return tab
        
    def _create_similar_tab(self) -> QWidget:
        """Create the similar files tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File name input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("파일명:"))
        
        self.file_name_edit = QLineEdit()
        self.file_name_edit.setPlaceholderText("파일명을 입력하여 유사한 파일을 찾으세요...")
        self.file_name_edit.returnPressed.connect(self._find_similar_files)
        input_layout.addWidget(self.file_name_edit)
        
        find_button = QPushButton("유사 파일 찾기")
        find_button.clicked.connect(self._find_similar_files)
        input_layout.addWidget(find_button)
        
        layout.addLayout(input_layout)
        
        # Similar files list
        self.similar_list = QTableWidget()
        self.similar_list.setColumnCount(5)
        self.similar_list.setHorizontalHeaderLabels(["파일명", "엔티티", "태스크", "유사도", "생성일"])
        self.similar_list.horizontalHeader().setStretchLastSection(True)
        self.similar_list.itemDoubleClicked.connect(self._on_similar_item_double_clicked)
        
        layout.addWidget(QLabel("유사한 파일:"))
        layout.addWidget(self.similar_list)
        
        # Add similar files button
        add_similar_button = QPushButton("선택된 유사 파일 추가")
        add_similar_button.clicked.connect(self._add_selected_similar)
        layout.addWidget(add_similar_button)
        
        return tab
        
    def _load_project_structure(self):
        """Load the project structure into the tree."""
        if not self.link_manager.connector.is_connected():
            QMessageBox.warning(self, "연결 오류", "Shotgrid에 연결되지 않았습니다.")
            return
            
        try:
            structure = self.link_browser.browse_project_structure(self.project_name)
            
            if not structure:
                QMessageBox.warning(self, "프로젝트 오류", f"프로젝트 '{self.project_name}'를 찾을 수 없습니다.")
                return
                
            self.project_tree.clear()
            
            # Add project root
            project_item = QTreeWidgetItem([structure["project"]["name"], "Project", "", ""])
            project_item.setData(0, Qt.UserRole, {
                "type": "Project",
                "data": structure["project"]
            })
            self.project_tree.addTopLevelItem(project_item)
            
            # Add sequences
            for seq_code, seq_data in structure["sequences"].items():
                seq_info = seq_data["info"]
                seq_item = QTreeWidgetItem([
                    seq_code, "Sequence", "", 
                    str(sum(shot["info"]["version_count"] for shot in seq_data["shots"].values()))
                ])
                seq_item.setData(0, Qt.UserRole, {
                    "type": "Sequence",
                    "data": seq_info
                })
                project_item.addChild(seq_item)
                
                # Add shots
                for shot_code, shot_data in seq_data["shots"].items():
                    shot_info = shot_data["info"]
                    shot_item = QTreeWidgetItem([
                        shot_code, "Shot", shot_info["status"], 
                        str(shot_info["version_count"])
                    ])
                    shot_item.setData(0, Qt.UserRole, {
                        "type": "Shot",
                        "data": shot_info
                    })
                    seq_item.addChild(shot_item)
                    
                    # Add tasks
                    for task_name, task_data in shot_data["tasks"].items():
                        task_item = QTreeWidgetItem([
                            task_name, "Task", task_data["status"],
                            str(task_data["version_count"])
                        ])
                        task_item.setData(0, Qt.UserRole, {
                            "type": "Task",
                            "data": task_data
                        })
                        shot_item.addChild(task_item)
            
            # Expand project and sequences
            project_item.setExpanded(True)
            for i in range(project_item.childCount()):
                project_item.child(i).setExpanded(True)
                
        except Exception as e:
            logger.error(f"Error loading project structure: {e}")
            QMessageBox.critical(self, "로딩 오류", f"프로젝트 구조를 로드하는 중 오류가 발생했습니다:\n{str(e)}")
            
    def _load_recent_activity(self):
        """Load recent activity."""
        try:
            activities = self.link_browser.get_recent_activity(self.project_name)
            
            self.activity_list.setRowCount(len(activities))
            
            for row, activity in enumerate(activities):
                self.activity_list.setItem(row, 0, QTableWidgetItem(activity["title"]))
                self.activity_list.setItem(row, 1, QTableWidgetItem(activity["entity"]))
                self.activity_list.setItem(row, 2, QTableWidgetItem(activity["task"]))
                self.activity_list.setItem(row, 3, QTableWidgetItem(activity["created_by"]))
                self.activity_list.setItem(row, 4, QTableWidgetItem(str(activity["created_at"])))
                
                # Store activity data
                for col in range(5):
                    item = self.activity_list.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, activity)
                        
        except Exception as e:
            logger.error(f"Error loading recent activity: {e}")
            QMessageBox.critical(self, "로딩 오류", f"최근 활동을 로드하는 중 오류가 발생했습니다:\n{str(e)}")
            
    def _perform_search(self):
        """Perform entity search."""
        search_term = self.search_edit.text().strip()
        if not search_term:
            return
            
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)  # Indeterminate progress
        
        # Start search thread
        entity_types = []
        selected_type = self.entity_type_combo.currentText()
        if selected_type != "전체":
            entity_types = [selected_type]
            
        self.search_thread = LinkSearchThread(self.link_browser, self.project_name, search_term)
        self.search_thread.search_complete.connect(self._on_search_complete)
        self.search_thread.error_occurred.connect(self._on_search_error)
        self.search_thread.start()
        
    @pyqtSlot(list)
    def _on_search_complete(self, results):
        """Handle search completion."""
        self.search_progress.setVisible(False)
        
        self.search_results.setRowCount(len(results))
        
        for row, result in enumerate(results):
            self.search_results.setItem(row, 0, QTableWidgetItem(result["type"]))
            self.search_results.setItem(row, 1, QTableWidgetItem(result["code"]))
            self.search_results.setItem(row, 2, QTableWidgetItem(result["description"]))
            self.search_results.setItem(row, 3, QTableWidgetItem(result["status"]))
            self.search_results.setItem(row, 4, QTableWidgetItem(str(result["version_count"])))
            self.search_results.setItem(row, 5, QTableWidgetItem(result["url"]))
            
            # Store result data
            for col in range(6):
                item = self.search_results.item(row, col)
                if item:
                    item.setData(Qt.UserRole, result)
                    
    @pyqtSlot(str)
    def _on_search_error(self, error_message):
        """Handle search error."""
        self.search_progress.setVisible(False)
        QMessageBox.critical(self, "검색 오류", f"검색 중 오류가 발생했습니다:\n{error_message}")
        
    def _find_similar_files(self):
        """Find similar files."""
        file_name = self.file_name_edit.text().strip()
        if not file_name:
            return
            
        try:
            similar_files = self.link_manager.search_similar_files(file_name, self.project_name)
            
            self.similar_list.setRowCount(len(similar_files))
            
            for row, similar_file in enumerate(similar_files):
                entity_info = ""
                if similar_file.get("entity"):
                    entity_info = f"{similar_file['entity']['type']} {similar_file['entity']['name']}"
                
                task_info = ""
                if similar_file.get("sg_task"):
                    task_info = similar_file["sg_task"]["name"]
                
                self.similar_list.setItem(row, 0, QTableWidgetItem(similar_file["code"]))
                self.similar_list.setItem(row, 1, QTableWidgetItem(entity_info))
                self.similar_list.setItem(row, 2, QTableWidgetItem(task_info))
                self.similar_list.setItem(row, 3, QTableWidgetItem(f"{similar_file.get('similarity_score', 0):.2f}"))
                self.similar_list.setItem(row, 4, QTableWidgetItem(str(similar_file.get("created_at", ""))))
                
                # Store similar file data
                for col in range(5):
                    item = self.similar_list.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, similar_file)
                        
        except Exception as e:
            logger.error(f"Error finding similar files: {e}")
            QMessageBox.critical(self, "검색 오류", f"유사 파일을 찾는 중 오류가 발생했습니다:\n{str(e)}")
            
    def _on_tree_item_double_clicked(self, item, column):
        """Handle tree item double click."""
        item_data = item.data(0, Qt.UserRole)
        if item_data:
            self._show_entity_details(item_data)
            
    def _on_search_result_double_clicked(self, item):
        """Handle search result double click."""
        result_data = item.data(Qt.UserRole)
        if result_data:
            self._show_entity_details({"type": result_data["type"], "data": result_data})
            
    def _on_activity_item_double_clicked(self, item):
        """Handle activity item double click."""
        activity_data = item.data(Qt.UserRole)
        if activity_data:
            self._show_activity_details(activity_data)
            
    def _on_similar_item_double_clicked(self, item):
        """Handle similar item double click."""
        similar_data = item.data(Qt.UserRole)
        if similar_data:
            self._show_version_details(similar_data)
            
    def _show_entity_details(self, item_data):
        """Show entity details in the details panel."""
        entity_type = item_data["type"]
        entity_data = item_data["data"]
        
        details = f"타입: {entity_type}\n"
        details += f"이름: {entity_data.get('code', entity_data.get('name', ''))}\n"
        details += f"설명: {entity_data.get('description', '')}\n"
        details += f"URL: {entity_data.get('url', '')}\n"
        
        if entity_type == "Shot":
            details += f"상태: {entity_data.get('status', '')}\n"
            details += f"버전 수: {entity_data.get('version_count', 0)}\n"
        elif entity_type == "Task":
            details += f"상태: {entity_data.get('status', '')}\n"
            details += f"담당자: {', '.join(entity_data.get('assignees', []))}\n"
            details += f"버전 수: {entity_data.get('version_count', 0)}\n"
            
        self.details_text.setPlainText(details)
        
    def _show_activity_details(self, activity_data):
        """Show activity details."""
        details = f"제목: {activity_data['title']}\n"
        details += f"설명: {activity_data['description']}\n"
        details += f"엔티티: {activity_data['entity']}\n"
        details += f"태스크: {activity_data['task']}\n"
        details += f"생성자: {activity_data['created_by']}\n"
        details += f"생성일: {activity_data['created_at']}\n"
        details += f"URL: {activity_data['url']}\n"
        
        self.details_text.setPlainText(details)
        
    def _show_version_details(self, version_data):
        """Show version details."""
        details = f"버전: {version_data['code']}\n"
        details += f"설명: {version_data.get('description', '')}\n"
        details += f"유사도: {version_data.get('similarity_score', 0):.2f}\n"
        details += f"생성일: {version_data.get('created_at', '')}\n"
        details += f"URL: {version_data.get('shotgrid_url', '')}\n"
        
        self.details_text.setPlainText(details)
        
    def _add_current_browse_selection(self):
        """Add current browse selection to selected links."""
        current_item = self.project_tree.currentItem()
        if current_item:
            item_data = current_item.data(0, Qt.UserRole)
            if item_data:
                self._add_link_to_selection(item_data)
                
    def _add_selected_search_results(self):
        """Add selected search results to selected links."""
        for item in self.search_results.selectedItems():
            result_data = item.data(Qt.UserRole)
            if result_data:
                self._add_link_to_selection({"type": result_data["type"], "data": result_data})
                
    def _add_selected_activity(self):
        """Add selected activity to selected links."""
        for item in self.activity_list.selectedItems():
            activity_data = item.data(Qt.UserRole)
            if activity_data:
                self._add_link_to_selection({"type": "Version", "data": activity_data})
                
    def _add_selected_similar(self):
        """Add selected similar files to selected links."""
        for item in self.similar_list.selectedItems():
            similar_data = item.data(Qt.UserRole)
            if similar_data:
                self._add_link_to_selection({"type": "Version", "data": similar_data})
                
    def _add_link_to_selection(self, link_data):
        """Add a link to the selection list."""
        # Check if already selected
        for existing_link in self.selected_links:
            if (existing_link["type"] == link_data["type"] and 
                existing_link["data"].get("id") == link_data["data"].get("id")):
                return  # Already selected
                
        self.selected_links.append(link_data)
        self._update_selected_links_display()
        
    def _update_selected_links_display(self):
        """Update the selected links display."""
        self.selected_list.setRowCount(len(self.selected_links))
        
        for row, link in enumerate(self.selected_links):
            link_type = link["type"]
            link_data = link["data"]
            
            self.selected_list.setItem(row, 0, QTableWidgetItem(link_type))
            self.selected_list.setItem(row, 1, QTableWidgetItem(
                link_data.get("code", link_data.get("name", link_data.get("title", "")))
            ))
            self.selected_list.setItem(row, 2, QTableWidgetItem(link_data.get("description", "")))
            self.selected_list.setItem(row, 3, QTableWidgetItem(link_data.get("url", "")))
            
    def clear_selection(self):
        """Clear all selected links."""
        self.selected_links.clear()
        self._update_selected_links_display()
        
    def get_selected_links(self) -> List[Dict]:
        """Get the list of selected links."""
        return self.selected_links.copy()
        
    def set_current_file_name(self, file_name: str):
        """Set current file name for similar file search."""
        self.file_name_edit.setText(file_name)
        
    def accept(self):
        """Accept the dialog and emit selected links."""
        if self.selected_links:
            for link in self.selected_links:
                self.link_selected.emit(link)
        super().accept()
