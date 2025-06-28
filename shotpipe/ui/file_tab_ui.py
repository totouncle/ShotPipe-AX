"""
FileTab UI components module.
"""
import logging
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QCheckBox, QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush

logger = logging.getLogger(__name__)

class FileTabUI:
    """UI 컴포넌트 관리 클래스"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def setup_ui(self):
        """UI 초기화"""
        try:
            # Main layout
            main_layout = QVBoxLayout()
            
            # Directory selection
            main_layout.addLayout(self._create_directory_layout())
            
            # Output directory selection
            main_layout.addLayout(self._create_output_layout())
            
            # Options group
            main_layout.addWidget(self._create_options_group())
            
            # Shotgrid group (if available)
            shotgrid_group = self._create_shotgrid_group()
            if shotgrid_group:
                main_layout.addWidget(shotgrid_group)
            
            # Control buttons
            main_layout.addLayout(self._create_control_buttons())
            
            # File table and related components
            table_layout = self._create_file_table()
            main_layout.addLayout(table_layout)
            
            # Progress bar
            main_layout.addWidget(self._create_progress_bar())
            
            self.parent.setLayout(main_layout)
            
        except Exception as e:
            logger.error(f"UI 초기화 실패: {e}")
            raise
    
    def _create_directory_layout(self):
        """디렉토리 선택 레이아웃 생성"""
        dir_layout = QHBoxLayout()
        dir_label = QLabel("소스 디렉토리:")
        
        self.parent.source_edit = QLineEdit()
        self.parent.source_edit.setReadOnly(True)
        self.parent.source_edit.setPlaceholderText("선택된 디렉토리 없음")
        self.parent.source_edit.setStyleSheet("font-weight: bold;")
        
        self.parent.select_dir_btn = QPushButton("디렉토리 선택...")
        self.parent.select_dir_btn.clicked.connect(self.parent.select_source_directory)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.parent.source_edit, 1)
        dir_layout.addWidget(self.parent.select_dir_btn)
        
        return dir_layout
    
    def _create_output_layout(self):
        """출력 디렉토리 선택 레이아웃 생성"""
        output_layout = QHBoxLayout()
        output_label = QLabel("출력 폴더:")
        
        self.parent.output_edit = QLineEdit()
        self.parent.output_edit.setReadOnly(True)
        self.parent.output_edit.setPlaceholderText("소스 디렉토리와 동일")
        self.parent.output_edit.setStyleSheet("font-style: italic;")
        
        self.parent.select_output_btn = QPushButton("출력 폴더 선택...")
        self.parent.select_output_btn.clicked.connect(self.parent.select_output_directory)
        
        self.parent.create_processed_folder_cb = QCheckBox("processed 폴더 생성")
        self.parent.create_processed_folder_cb.setChecked(True)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.parent.output_edit, 1)
        output_layout.addWidget(self.parent.select_output_btn)
        output_layout.addWidget(self.parent.create_processed_folder_cb)
        
        return output_layout
    
    def _create_options_group(self):
        """옵션 그룹 생성"""
        options_group = QGroupBox("옵션")
        options_inner_layout = QVBoxLayout()
        
        # Recursive and exclude options
        recursive_layout = QHBoxLayout()
        self.parent.recursive_cb = QCheckBox("하위 폴더 포함")
        self.parent.recursive_cb.setChecked(False)
        
        self.parent.exclude_processed_cb = QCheckBox("이미 처리된 파일 제외")
        self.parent.exclude_processed_cb.setChecked(True)
        
        recursive_layout.addWidget(self.parent.recursive_cb)
        recursive_layout.addWidget(self.parent.exclude_processed_cb)
        recursive_layout.addStretch()
        
        options_inner_layout.addLayout(recursive_layout)
        
        # Sequence options
        sequence_layout = QHBoxLayout()
        self.parent.use_sequence_cb = QCheckBox("시퀀스 설정:")
        self.parent.use_sequence_cb.setChecked(True)
        self.parent.use_sequence_cb.stateChanged.connect(self.parent.toggle_sequence_combo)
        
        sequence_label = QLabel("시퀀스:")
        
        self.parent.sequence_combo = QComboBox()
        self.parent.sequence_combo.setEditable(True)
        self.parent.sequence_combo.setInsertPolicy(QComboBox.InsertAtBottom)
        self.parent.sequence_combo.currentTextChanged.connect(self.parent.on_sequence_changed)
        
        self.parent.save_sequence_btn = QPushButton("저장")
        self.parent.save_sequence_btn.clicked.connect(self.parent.add_custom_sequence)
        self.parent.save_sequence_btn.setMaximumWidth(60)
        
        sequence_layout.addWidget(self.parent.use_sequence_cb)
        sequence_layout.addWidget(sequence_label)
        sequence_layout.addWidget(self.parent.sequence_combo)
        sequence_layout.addWidget(self.parent.save_sequence_btn)
        sequence_layout.addStretch()
        
        options_inner_layout.addLayout(sequence_layout)
        options_group.setLayout(options_inner_layout)
        
        return options_group
    
    def _create_shotgrid_group(self):
        """Shotgrid 연동 그룹 생성"""
        try:
            from ..shotgrid.api_connector import ShotgridConnector
            SHOTGRID_AVAILABLE = True
        except ImportError:
            SHOTGRID_AVAILABLE = False
        
        if not (SHOTGRID_AVAILABLE and self.parent.shotgrid_connector):
            return None
        
        shotgrid_group = QGroupBox("Shotgrid 연동")
        shotgrid_layout = QVBoxLayout()
        
        # 연결 상태 및 프로젝트 정보
        status_layout = QHBoxLayout()
        self.parent.shotgrid_status_label = QLabel("연결 상태: 확인 중...")
        status_layout.addWidget(self.parent.shotgrid_status_label)
        
        # 고정 프로젝트 정보 표시
        project_info_layout = QHBoxLayout()
        project_info_layout.addWidget(QLabel("고정 프로젝트:"))
        self.parent.shotgrid_project_label = QLabel(self.parent.fixed_project_name)
        self.parent.shotgrid_project_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2ECC71;
                background-color: #34495E;
                padding: 5px 10px;
                border-radius: 3px;
                border: 1px solid #2ECC71;
            }
        """)
        project_info_layout.addWidget(self.parent.shotgrid_project_label)
        
        self.parent.refresh_shotgrid_btn = QPushButton("시퀀스/샷 새로고침")
        self.parent.refresh_shotgrid_btn.clicked.connect(self.parent.refresh_shotgrid_data)
        self.parent.refresh_shotgrid_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        project_info_layout.addWidget(self.parent.refresh_shotgrid_btn)
        
        self.parent.project_settings_btn = QPushButton("프로젝트 설정")
        self.parent.project_settings_btn.clicked.connect(self.parent.open_project_settings)
        self.parent.project_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #8E44AD;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7D3C98;
            }
        """)
        project_info_layout.addWidget(self.parent.project_settings_btn)
        project_info_layout.addStretch()
        
        # 시퀀스/Shot 선택
        selection_layout = QHBoxLayout()
        
        selection_layout.addWidget(QLabel("시퀀스:"))
        self.parent.shotgrid_sequence_combo = QComboBox()
        self.parent.shotgrid_sequence_combo.setMinimumWidth(200)
        self.parent.shotgrid_sequence_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 12px;
                border: 2px solid #3498DB;
                border-radius: 5px;
            }
            QComboBox:focus {
                border: 2px solid #2ECC71;
            }
        """)
        self.parent.shotgrid_sequence_combo.currentTextChanged.connect(self.parent.on_fixed_project_sequence_changed)
        selection_layout.addWidget(self.parent.shotgrid_sequence_combo)
        
        selection_layout.addWidget(QLabel("Shot:"))
        self.parent.shotgrid_shot_combo = QComboBox()
        self.parent.shotgrid_shot_combo.setMinimumWidth(150)
        self.parent.shotgrid_shot_combo.setEditable(True)
        self.parent.shotgrid_shot_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 12px;
                border: 2px solid #3498DB;
                border-radius: 5px;
            }
            QComboBox:focus {
                border: 2px solid #2ECC71;
            }
        """)
        selection_layout.addWidget(self.parent.shotgrid_shot_combo)
        
        self.parent.apply_shotgrid_btn = QPushButton("선택된 파일에 일괄 적용")
        self.parent.apply_shotgrid_btn.clicked.connect(self.parent.apply_shotgrid_to_selected)
        self.parent.apply_shotgrid_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
        """)
        selection_layout.addWidget(self.parent.apply_shotgrid_btn)
        selection_layout.addStretch()
        
        shotgrid_layout.addLayout(status_layout)
        shotgrid_layout.addLayout(project_info_layout)
        shotgrid_layout.addLayout(selection_layout)
        shotgrid_group.setLayout(shotgrid_layout)
        
        return shotgrid_group
    
    def _create_control_buttons(self):
        """제어 버튼 레이아웃 생성"""
        control_layout = QHBoxLayout()
        
        self.parent.scan_btn = QPushButton("파일 스캔")
        self.parent.scan_btn.clicked.connect(self.parent.scan_files)
        
        self.parent.process_btn = QPushButton("처리 시작")
        self.parent.process_btn.clicked.connect(self.parent.process_files)
        self.parent.process_btn.setEnabled(False)
        
        self.parent.new_batch_btn = QPushButton("새 배치 시작")
        self.parent.new_batch_btn.clicked.connect(self.parent.start_new_batch)
        self.parent.new_batch_btn.setEnabled(True)
        
        control_layout.addWidget(self.parent.scan_btn)
        control_layout.addWidget(self.parent.process_btn)
        control_layout.addWidget(self.parent.new_batch_btn)
        control_layout.addStretch()
        
        return control_layout
    
    def _create_file_table(self):
        """파일 테이블 생성"""
        from PyQt5.QtWidgets import QAbstractItemView, QButtonGroup, QRadioButton
        from .file_tab import CellEditorDelegate
        
        # 파일 정보 표시 영역 추가
        self.parent.file_info_label = QLabel("파일 스캔 결과: 준비 중...")
        
        # 편집 가이드 라벨 추가
        edit_guide_label = QLabel("🎯 팁: 시퀀스* 및 샷* 컬럼을 더블클릭하면 Shotgrid 데이터에서 선택할 수 있습니다!")
        edit_guide_label.setStyleSheet("color: #3498DB; font-style: italic; padding: 5px;")
        
        # 파일 보기 모드 라디오 버튼
        view_mode_layout = QHBoxLayout()
        view_mode_label = QLabel("보기 모드:")
        
        self.parent.tab_radio_group = QButtonGroup(self.parent)
        self.parent.all_files_radio = QRadioButton("모든 파일")
        self.parent.valid_files_radio = QRadioButton("유효 파일")
        self.parent.skipped_files_radio = QRadioButton("스킵된 파일")
        
        self.parent.tab_radio_group.addButton(self.parent.all_files_radio)
        self.parent.tab_radio_group.addButton(self.parent.valid_files_radio)
        self.parent.tab_radio_group.addButton(self.parent.skipped_files_radio)
        
        self.parent.valid_files_radio.setChecked(True)
        
        view_mode_layout.addWidget(view_mode_label)
        view_mode_layout.addWidget(self.parent.all_files_radio)
        view_mode_layout.addWidget(self.parent.valid_files_radio)
        view_mode_layout.addWidget(self.parent.skipped_files_radio)
        view_mode_layout.addStretch()
        
        self.parent.all_files_radio.toggled.connect(self.parent._update_file_display)
        self.parent.valid_files_radio.toggled.connect(self.parent._update_file_display)
        self.parent.skipped_files_radio.toggled.connect(self.parent._update_file_display)
        
        # 검색 기능 추가
        search_layout = QHBoxLayout()
        search_label = QLabel("검색:")
        self.parent.search_edit = QLineEdit()
        self.parent.search_edit.setPlaceholderText("파일명 검색...")
        self.parent.search_edit.setClearButtonEnabled(True)
        self.parent.search_edit.textChanged.connect(self.parent.filter_files)
        
        # 필터 옵션
        filter_label = QLabel("필터:")
        self.parent.filter_combo = QComboBox()
        self.parent.filter_combo.addItem("모든 파일", "all")
        self.parent.filter_combo.addItem("처리된 파일만", "processed")
        self.parent.filter_combo.addItem("미처리 파일만", "unprocessed")
        self.parent.filter_combo.currentIndexChanged.connect(self.parent.filter_files)
        
        # 이력 관리 버튼들
        self.parent.export_history_btn = QPushButton("이력 내보내기")
        self.parent.export_history_btn.clicked.connect(self.parent.export_history)
        
        self.parent.show_stats_btn = QPushButton("이력 통계")
        self.parent.show_stats_btn.clicked.connect(self.parent.show_history_stats)
        
        self.parent.reset_history_btn = QPushButton("이력 초기화")
        self.parent.reset_history_btn.clicked.connect(self.parent.reset_history)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.parent.search_edit, 1)
        search_layout.addWidget(filter_label)
        search_layout.addWidget(self.parent.filter_combo)
        search_layout.addWidget(self.parent.export_history_btn)
        search_layout.addWidget(self.parent.show_stats_btn)
        search_layout.addWidget(self.parent.reset_history_btn)
        
        # 파일 테이블 생성
        self.parent.file_table = QTableWidget(0, 7)
        self.parent.file_table.setHorizontalHeaderLabels(["", "파일명", "상태", "시퀀스*", "샷*", "경과 시간", "메세지"])
        
        self.parent.file_table.setAlternatingRowColors(True)
        self.parent.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.parent.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.parent.file_table.setColumnWidth(0, 40)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.parent.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)

        self.parent.file_table.setColumnWidth(1, 350)
        self.parent.file_table.setColumnWidth(3, 100)
        self.parent.file_table.setColumnWidth(4, 120)
        self.parent.file_table.setColumnWidth(6, 300)

        header = self.parent.file_table.horizontalHeader()
        header.setToolTip("시퀀스*와 샷* 컬럼을 더블클릭하면 Shotgrid에서 선택할 수 있습니다")
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.parent._show_header_context_menu)
        
        self.parent.file_table.setSortingEnabled(True)
        self.parent.file_table.horizontalHeader().setSortIndicatorShown(True)
        self.parent.file_table.sortItems(2, Qt.AscendingOrder)
        self.parent.file_table.itemChanged.connect(self.parent._on_table_item_changed)
        
        # 델리게이트 설정은 나중에 FileTab에서 처리됨
        
        self.parent.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parent.file_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        
        # 테이블과 관련 위젯들을 담은 레이아웃 반환
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.parent.file_info_label)
        table_layout.addWidget(edit_guide_label)
        table_layout.addLayout(view_mode_layout)
        table_layout.addLayout(search_layout)
        table_layout.addWidget(self.parent.file_table)
        
        return table_layout
    
    def _create_progress_bar(self):
        """진행 바 생성"""
        self.parent.progress_bar = QProgressBar()
        self.parent.progress_bar.setRange(0, 100)
        self.parent.progress_bar.setValue(0)
        self.parent.progress_bar.setTextVisible(True)
        self.parent.progress_bar.setFormat("%p% (%v/%m)")
        self.parent.progress_bar.setVisible(False)
        
        return self.parent.progress_bar
    
    def style_table_row(self, row, is_processed, status_text):
        """테이블 행 스타일링"""
        try:
            if is_processed:
                self.parent.file_table.item(row, 2).setBackground(QBrush(QColor("#2ECC71")))
                self.parent.file_table.item(row, 2).setForeground(QBrush(QColor("white")))
                
                font = QFont()
                font.setBold(True)
                self.parent.file_table.item(row, 2).setFont(font)
            elif "스킵" in status_text:
                self.parent.file_table.item(row, 2).setBackground(QBrush(QColor("#F39C12")))
                self.parent.file_table.item(row, 2).setForeground(QBrush(QColor("white")))
            else:
                self.parent.file_table.item(row, 2).setBackground(QBrush(QColor("#ECF0F1")))
                self.parent.file_table.item(row, 2).setForeground(QBrush(QColor("black")))
        except Exception as e:
            logger.error(f"테이블 행 스타일링 오류: {e}")