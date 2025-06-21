"""
File processing tab module for ShotPipe UI.
"""
import os
import sys
import logging
import traceback
import re
import json
import time
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressBar, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QMenu, QAction, QDialog, QInputDialog, QStyledItemDelegate,
    QApplication, QButtonGroup, QRadioButton, QAbstractItemView, QStyle, QStyleOptionButton, QSizePolicy,
    QListView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QBrush
from ..file_processor.processor import ProcessingThread
from ..file_processor.scanner import FileScanner
from ..config import config
from ..file_processor.metadata import MetadataExtractor
from ..utils.processed_files_tracker import ProcessedFilesTracker
from ..ui.styles.dark_theme import get_color_palette

logger = logging.getLogger(__name__)

class CellEditorDelegate(QStyledItemDelegate):
    """
    테이블 셀 편집을 위한 커스텀 델리게이트.
    컬럼에 따라 QComboBox 또는 QLineEdit를 에디터로 제공합니다.
    """
    
    def __init__(self, parent_tab):
        super().__init__()
        self.parent_tab = parent_tab
    
    def createEditor(self, parent, option, index):
        """컬럼 유형에 따라 적절한 편집 위젯을 생성합니다."""
        
        # 시퀀스(3) 또는 샷(4) 컬럼인 경우 QComboBox 생성
        if index.column() in [3, 4]:
            combo = QComboBox(parent)
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.setMinimumWidth(120)
            combo.setStyleSheet("""
                QComboBox { 
                    border: 1px solid #777; padding: 2px; background-color: #333;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding; subcontrol-position: top right;
                    width: 15px; border-left-width: 1px;
                    border-left-color: #777; border-left-style: solid;
                }
            """)
            
            font = self.parent_tab.file_table.font()
            combo.setFont(font)

            list_view = QListView(combo)
            list_view.setFont(font)
            list_view.setWordWrap(True)
            combo.setView(list_view)
            
            self._populate_combo_data(combo, index)
            return combo

        # 그 외 편집 가능한 모든 컬럼(예: 메시지)은 QLineEdit 생성
        else:
            editor = QLineEdit(parent)
            editor.setFont(option.font)
            editor.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #999;
                    padding: 1px;
                    background-color: #2E2E2E;
                    color: #E0E0E0;
                }
            """)
            return editor
    
    def setEditorData(self, editor, index):
        """에디터에 현재 셀의 데이터를 설정합니다."""
        current_value = index.model().data(index, Qt.DisplayRole)
        
        if isinstance(editor, QComboBox):
            if current_value:
                combo_index = editor.findText(current_value)
                if combo_index >= 0:
                    editor.setCurrentIndex(combo_index)
                else:
                    editor.setEditText(current_value)
        elif isinstance(editor, QLineEdit):
            editor.setText(str(current_value))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """에디터의 데이터를 모델(테이블 셀)에 저장합니다."""
        if isinstance(editor, QComboBox):
            value = editor.currentText()
            if value and value not in ["-- 시퀀스 선택 --", "-- Shot 선택 --"]:
                model.setData(index, value, Qt.EditRole)
        elif isinstance(editor, QLineEdit):
            model.setData(index, editor.text(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        """모든 에디터의 위치와 크기를 셀에 정확히 맞춥니다."""
        editor.setGeometry(option.rect)
    
    def _populate_combo_data(self, combo, index):
        """콤보박스에 데이터 채우기"""
        try:
            column = index.column()
            
            if column == 3:  # 시퀀스 컬럼
                self._load_sequence_data(combo)
            elif column == 4:  # 샷 컬럼
                self._load_shot_data(combo, index)
                
        except Exception as e:
            logger.error(f"콤보박스 데이터 로드 오류: {e}")
            # 기본 옵션 추가
            combo.addItem("직접 입력...")
    
    def _load_sequence_data(self, combo):
        """시퀀스 데이터 로드"""
        sequences = []
        
        # 1. Shotgrid에서 시퀀스 가져오기 (가능한 경우)
        if (hasattr(self.parent_tab, 'shotgrid_entity_manager') and 
            self.parent_tab.shotgrid_entity_manager and
            hasattr(self.parent_tab, 'fixed_project_name')):
            
            try:
                project_name = self.parent_tab.fixed_project_name
                if project_name and project_name != "-- 프로젝트 선택 --":
                    project = self.parent_tab.shotgrid_entity_manager.find_project(project_name)
                    if project:
                        sg_sequences = self.parent_tab.shotgrid_entity_manager.get_sequences_in_project(project)
                        sequences.extend([seq['code'] for seq in sg_sequences])
                        logger.debug(f"Shotgrid에서 {len(sg_sequences)}개 시퀀스 로드됨")
            except Exception as e:
                logger.warning(f"Shotgrid 시퀀스 로드 실패: {e}")
        
        # 2. 로컬에서 감지된 시퀀스 추가
        if hasattr(self.parent_tab, 'sequence_dict') and self.parent_tab.sequence_dict:
            local_sequences = list(self.parent_tab.sequence_dict.keys())
            sequences.extend(local_sequences)
            logger.debug(f"로컬에서 {len(local_sequences)}개 시퀀스 추가됨")
        
        # 3. 기본 시퀀스 추가
        default_sequences = ["LIG", "KIAP", "s01", "s02", "s03"]
        sequences.extend(default_sequences)
        
        # 4. 중복 제거 및 정렬
        unique_sequences = sorted(list(set(sequences)))
        
        # 5. 콤보박스에 추가
        combo.addItem("-- 시퀀스 선택 --")
        for seq in unique_sequences:
            if seq:  # 빈 문자열 제외
                combo.addItem(seq)
        
        logger.debug(f"시퀀스 콤보박스에 {len(unique_sequences)}개 항목 로드됨")
    
    def _load_shot_data(self, combo, index):
        """샷 데이터 로드"""
        shots = []
        
        # 같은 행의 시퀀스 값 가져오기
        sequence_item = self.parent_tab.file_table.item(index.row(), 3)
        sequence_code = sequence_item.text() if sequence_item else ""
        
        # 1. Shotgrid에서 Shot 가져오기 (가능한 경우)
        if (sequence_code and 
            hasattr(self.parent_tab, 'shotgrid_entity_manager') and 
            self.parent_tab.shotgrid_entity_manager and
            hasattr(self.parent_tab, 'fixed_project_name')):
            
            try:
                project_name = self.parent_tab.fixed_project_name
                if project_name and project_name != "-- 프로젝트 선택 --":
                    project = self.parent_tab.shotgrid_entity_manager.find_project(project_name)
                    if project:
                        sg_shots = self.parent_tab.shotgrid_entity_manager.get_shots_in_sequence(project, sequence_code)
                        shots.extend([shot['code'] for shot in sg_shots])
                        logger.debug(f"Shotgrid에서 시퀀스 '{sequence_code}'의 {len(sg_shots)}개 Shot 로드됨")
            except Exception as e:
                logger.warning(f"Shotgrid Shot 로드 실패: {e}")
        
        # 2. 로컬에서 감지된 Shot 추가
        if (sequence_code and 
            hasattr(self.parent_tab, 'sequence_dict') and 
            sequence_code in self.parent_tab.sequence_dict):
            
            local_shots = [shot for _, shot in self.parent_tab.sequence_dict[sequence_code]]
            shots.extend(local_shots)
            logger.debug(f"로컬에서 시퀀스 '{sequence_code}'의 {len(local_shots)}개 Shot 추가됨")
        
        # 3. 기본 Shot 패턴 추가
        default_shots = ["c001", "c002", "c003", "c010", "c020", "shot_001", "shot_010"]
        shots.extend(default_shots)
        
        # 4. 중복 제거 및 정렬
        unique_shots = sorted(list(set(shots)))
        
        # 5. 콤보박스에 추가
        combo.addItem("-- Shot 선택 --")
        for shot in unique_shots:
            if shot:  # 빈 문자열 제외
                combo.addItem(shot)
        
        logger.debug(f"Shot 콤보박스에 {len(unique_shots)}개 항목 로드됨")

# Shotgrid 연동을 위한 import 추가
try:
    from ..shotgrid.api_connector import ShotgridConnector
    from ..shotgrid.entity_manager import EntityManager
    SHOTGRID_AVAILABLE = True
except ImportError:
    SHOTGRID_AVAILABLE = False
    logger.warning("Shotgrid modules not available for file tab")

class FileTab(QWidget):
    """Tab for processing files."""
    
    # Signal to notify when files have been processed
    files_processed = pyqtSignal(list)
    
    def __init__(self, processed_files_tracker, parent=None):
        """Initialize the file tab."""
        super().__init__(parent)
        self.parent = parent
        self.source_directory = ""
        self.output_directory = ""  # 출력 디렉토리 경로 추가
        self.file_list = []
        self.file_info_dict = {}
        self.sequence_dict = {}
        self.processing_thread = None
        
        # 스캐너 초기화 및 트래커 주입
        self.processed_files_tracker = processed_files_tracker
        self.scanner = FileScanner()
        self.scanner.processed_files_tracker = self.processed_files_tracker
        self.metadata_extractor = MetadataExtractor()
        
        self.skipped_files = []  # 초기화
        
        # Shotgrid 연동 관련 초기화
        self.shotgrid_connector = None
        self.shotgrid_entity_manager = None
        
        # 고정 프로젝트 설정 로드
        self.fixed_project_name = config.get("shotgrid", "default_project") or "AXRD-296"
        self.auto_select_project = config.get("shotgrid", "auto_select_project") or True
        self.show_project_selector = config.get("shotgrid", "show_project_selector") or False
        
        if SHOTGRID_AVAILABLE:
            try:
                self.shotgrid_connector = ShotgridConnector()
                if self.shotgrid_connector.sg:
                    self.shotgrid_entity_manager = EntityManager(self.shotgrid_connector)
                    logger.info(f"Shotgrid 연동 초기화 성공 - 고정 프로젝트: {self.fixed_project_name}")
                else:
                    logger.warning("Shotgrid 연결에 실패하여 Entity Manager를 생성하지 않았습니다.")
                    self.shotgrid_connector = None
                    self.shotgrid_entity_manager = None
            except Exception as e:
                logger.warning(f"Shotgrid 연동 초기화 실패: {e}")
                self.shotgrid_connector = None
                self.shotgrid_entity_manager = None
        
        self._init_ui()
        
        # 시퀀스 콤보박스 초기화
        self.initialize_sequence_combo()
        
        # 저장된 시퀀스 로드
        self.load_custom_sequences()
        
        # 파일 처리 스레드
        self.file_processing_thread = None
        
        # 앱 시작 시 마지막으로 사용한 디렉토리가 있는지 확인하고 자동으로 로드
        self.load_last_directory()
    
    def _init_ui(self):
        """Initialize the UI."""
        try:
            # Main layout
            main_layout = QVBoxLayout()
            
            # Directory selection
            dir_layout = QHBoxLayout()
            dir_label = QLabel("소스 디렉토리:")
            self.source_edit = QLineEdit()
            self.source_edit.setReadOnly(True)
            self.source_edit.setPlaceholderText("선택된 디렉토리 없음")
            self.source_edit.setStyleSheet("font-weight: bold;")
            
            self.select_dir_btn = QPushButton("디렉토리 선택...")
            self.select_dir_btn.clicked.connect(self.select_source_directory)
            
            dir_layout.addWidget(dir_label)
            dir_layout.addWidget(self.source_edit, 1)
            dir_layout.addWidget(self.select_dir_btn)
            
            main_layout.addLayout(dir_layout)
            
            # Output directory selection
            output_layout = QHBoxLayout()
            output_label = QLabel("출력 폴더:")
            self.output_edit = QLineEdit()
            self.output_edit.setReadOnly(True)
            self.output_edit.setPlaceholderText("소스 디렉토리와 동일")
            self.output_edit.setStyleSheet("font-style: italic;")
            
            self.select_output_btn = QPushButton("출력 폴더 선택...")
            self.select_output_btn.clicked.connect(self.select_output_directory)
            
            # 'processed' 폴더 생성 옵션 체크박스
            self.create_processed_folder_cb = QCheckBox("processed 폴더 생성")
            self.create_processed_folder_cb.setChecked(True)
            
            output_layout.addWidget(output_label)
            output_layout.addWidget(self.output_edit, 1)
            output_layout.addWidget(self.select_output_btn)
            output_layout.addWidget(self.create_processed_folder_cb)
            
            main_layout.addLayout(output_layout)
            
            # Options group
            options_group = QGroupBox("옵션")
            options_inner_layout = QVBoxLayout()
            
            # Recursive option
            recursive_layout = QHBoxLayout()
            self.recursive_cb = QCheckBox("하위 폴더 포함")
            self.recursive_cb.setChecked(False)
            
            # Exclude processed files option
            self.exclude_processed_cb = QCheckBox("이미 처리된 파일 제외")
            self.exclude_processed_cb.setChecked(True)
            
            recursive_layout.addWidget(self.recursive_cb)
            recursive_layout.addWidget(self.exclude_processed_cb)
            recursive_layout.addStretch()
            
            options_inner_layout.addLayout(recursive_layout)
            
            # Sequence options
            sequence_layout = QHBoxLayout()
            self.use_sequence_cb = QCheckBox("시퀀스 설정:")
            self.use_sequence_cb.setChecked(True)
            self.use_sequence_cb.stateChanged.connect(self.toggle_sequence_combo)
            
            sequence_label = QLabel("시퀀스:")
            
            self.sequence_combo = QComboBox()
            self.sequence_combo.setEditable(True)
            self.sequence_combo.setInsertPolicy(QComboBox.InsertAtBottom)
            self.sequence_combo.currentTextChanged.connect(self.on_sequence_changed)
            
            self.save_sequence_btn = QPushButton("저장")
            self.save_sequence_btn.clicked.connect(self.add_custom_sequence)
            self.save_sequence_btn.setMaximumWidth(60)
            
            sequence_layout.addWidget(self.use_sequence_cb)
            sequence_layout.addWidget(sequence_label)
            sequence_layout.addWidget(self.sequence_combo)
            sequence_layout.addWidget(self.save_sequence_btn)
            sequence_layout.addStretch()
            
            options_inner_layout.addLayout(sequence_layout)
            options_group.setLayout(options_inner_layout)
            main_layout.addWidget(options_group)
            
            # Shotgrid 연동 그룹 추가
            if SHOTGRID_AVAILABLE and self.shotgrid_connector:
                shotgrid_group = QGroupBox("Shotgrid 연동")
                shotgrid_layout = QVBoxLayout()
                
                # 연결 상태 및 프로젝트 정보
                status_layout = QHBoxLayout()
                self.shotgrid_status_label = QLabel("연결 상태: 확인 중...")
                status_layout.addWidget(self.shotgrid_status_label)
                
                # 고정 프로젝트 정보 표시
                project_info_layout = QHBoxLayout()
                project_info_layout.addWidget(QLabel("고정 프로젝트:"))
                self.shotgrid_project_label = QLabel(self.fixed_project_name)
                self.shotgrid_project_label.setStyleSheet("""
                    QLabel {
                        font-weight: bold;
                        color: #2ECC71;
                        background-color: #34495E;
                        padding: 5px 10px;
                        border-radius: 3px;
                        border: 1px solid #2ECC71;
                    }
                """)
                project_info_layout.addWidget(self.shotgrid_project_label)
                
                self.refresh_shotgrid_btn = QPushButton("시퀀스/샷 새로고침")
                self.refresh_shotgrid_btn.clicked.connect(self.refresh_shotgrid_data)
                self.refresh_shotgrid_btn.setStyleSheet("""
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
                project_info_layout.addWidget(self.refresh_shotgrid_btn)
                
                # 프로젝트 설정 버튼 추가
                self.project_settings_btn = QPushButton("프로젝트 설정")
                self.project_settings_btn.clicked.connect(self.open_project_settings)
                self.project_settings_btn.setStyleSheet("""
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
                project_info_layout.addWidget(self.project_settings_btn)
                project_info_layout.addStretch()
                
                # 시퀀스/Shot 선택 (프로젝트는 숨김)
                selection_layout = QHBoxLayout()
                
                selection_layout.addWidget(QLabel("시퀀스:"))
                self.shotgrid_sequence_combo = QComboBox()
                self.shotgrid_sequence_combo.setMinimumWidth(200)
                self.shotgrid_sequence_combo.setStyleSheet("""
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
                self.shotgrid_sequence_combo.currentTextChanged.connect(self.on_fixed_project_sequence_changed)
                selection_layout.addWidget(self.shotgrid_sequence_combo)
                
                selection_layout.addWidget(QLabel("Shot:"))
                self.shotgrid_shot_combo = QComboBox()
                self.shotgrid_shot_combo.setMinimumWidth(150)
                self.shotgrid_shot_combo.setEditable(True)
                self.shotgrid_shot_combo.setStyleSheet("""
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
                selection_layout.addWidget(self.shotgrid_shot_combo)
                
                self.apply_shotgrid_btn = QPushButton("선택된 파일에 일괄 적용")
                self.apply_shotgrid_btn.clicked.connect(self.apply_shotgrid_to_selected)
                self.apply_shotgrid_btn.setStyleSheet("""
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
                selection_layout.addWidget(self.apply_shotgrid_btn)
                selection_layout.addStretch()
                
                shotgrid_layout.addLayout(status_layout)
                shotgrid_layout.addLayout(project_info_layout)
                shotgrid_layout.addLayout(selection_layout)
                shotgrid_group.setLayout(shotgrid_layout)
                main_layout.addWidget(shotgrid_group)
                
                # 초기 연결 상태 확인 및 고정 프로젝트 로드
                self.update_shotgrid_status()
                if self.auto_select_project:
                    QTimer.singleShot(1000, self.auto_load_fixed_project)
            else:
                logger.info("Shotgrid 연동 UI 비활성화")
            
            # Files table
            table_header_layout = QHBoxLayout()
            table_header_layout.addWidget(QLabel("파일 목록:"))
            
            # 검색 기능 추가
            search_layout = QHBoxLayout()
            search_label = QLabel("검색:")
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("파일명 검색...")
            self.search_edit.setClearButtonEnabled(True)
            self.search_edit.textChanged.connect(self.filter_files)
            
            # 필터 옵션
            filter_label = QLabel("필터:")
            self.filter_combo = QComboBox()
            self.filter_combo.addItem("모든 파일", "all")
            self.filter_combo.addItem("처리된 파일만", "processed")
            self.filter_combo.addItem("미처리 파일만", "unprocessed")
            self.filter_combo.currentIndexChanged.connect(self.filter_files)
            
            # 이력 관리 버튼
            self.export_history_btn = QPushButton("이력 내보내기")
            self.export_history_btn.clicked.connect(self.export_history)
            
            # 이력 통계 버튼
            self.show_stats_btn = QPushButton("이력 통계")
            self.show_stats_btn.clicked.connect(self.show_history_stats)
            
            # 이력 초기화 버튼 추가
            self.reset_history_btn = QPushButton("이력 초기화")
            self.reset_history_btn.clicked.connect(self.reset_history)
            
            search_layout.addWidget(search_label)
            search_layout.addWidget(self.search_edit, 1)
            search_layout.addWidget(filter_label)
            search_layout.addWidget(self.filter_combo)
            search_layout.addWidget(self.export_history_btn)
            search_layout.addWidget(self.show_stats_btn)
            search_layout.addWidget(self.reset_history_btn)
            
            table_header_layout.addLayout(search_layout)
            main_layout.addLayout(table_header_layout)
            
            # 파일 정보 표시 영역 추가
            self.file_info_label = QLabel("파일 스캔 결과: 준비 중...")
            main_layout.addWidget(self.file_info_label)
            
            # 편집 가이드 라벨 추가
            edit_guide_label = QLabel("🎯 팁: 시퀀스* 및 샷* 컬럼을 더블클릭하면 Shotgrid 데이터에서 선택할 수 있습니다!")
            edit_guide_label.setStyleSheet("color: #3498DB; font-style: italic; padding: 5px;")
            main_layout.addWidget(edit_guide_label)
            
            # 파일 보기 모드 라디오 버튼
            view_mode_layout = QHBoxLayout()
            view_mode_label = QLabel("보기 모드:")
            
            self.tab_radio_group = QButtonGroup(self)
            self.all_files_radio = QRadioButton("모든 파일")
            self.valid_files_radio = QRadioButton("유효 파일")
            self.skipped_files_radio = QRadioButton("스킵된 파일")
            
            self.tab_radio_group.addButton(self.all_files_radio)
            self.tab_radio_group.addButton(self.valid_files_radio)
            self.tab_radio_group.addButton(self.skipped_files_radio)
            
            self.valid_files_radio.setChecked(True)
            
            view_mode_layout.addWidget(view_mode_label)
            view_mode_layout.addWidget(self.all_files_radio)
            view_mode_layout.addWidget(self.valid_files_radio)
            view_mode_layout.addWidget(self.skipped_files_radio)
            view_mode_layout.addStretch()
            
            self.all_files_radio.toggled.connect(self._update_file_display)
            self.valid_files_radio.toggled.connect(self._update_file_display)
            self.skipped_files_radio.toggled.connect(self._update_file_display)
            
            main_layout.addLayout(view_mode_layout)
            
            self.file_table = QTableWidget(0, 7)
            self.file_table.setHorizontalHeaderLabels(["", "파일명", "상태", "시퀀스*", "샷*", "경과 시간", "메세지"])
            
            self.file_table.setAlternatingRowColors(True)
            self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
            
            self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.file_table.setColumnWidth(0, 40)
            self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
            self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
            self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)

            self.file_table.setColumnWidth(1, 350)
            self.file_table.setColumnWidth(3, 100)
            self.file_table.setColumnWidth(4, 120)
            self.file_table.setColumnWidth(6, 300)

            header = self.file_table.horizontalHeader()
            header.setToolTip("시퀀스*와 샷* 컬럼을 더블클릭하면 Shotgrid에서 선택할 수 있습니다")
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self._show_header_context_menu)
            
            self.file_table.setSortingEnabled(True)
            self.file_table.horizontalHeader().setSortIndicatorShown(True)
            self.file_table.sortItems(2, Qt.AscendingOrder)
            self.file_table.itemChanged.connect(self._on_table_item_changed)
            
            self.cell_editor_delegate = CellEditorDelegate(self)
            self.file_table.setItemDelegate(self.cell_editor_delegate)
            
            self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.file_table.setEditTriggers(QAbstractItemView.DoubleClicked)
            main_layout.addWidget(self.file_table)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%p% (%v/%m)")
            self.progress_bar.setVisible(False)
            main_layout.addWidget(self.progress_bar)
            
            btn_layout = QHBoxLayout()
            
            self.scan_btn = QPushButton("파일 스캔")
            self.scan_btn.clicked.connect(self.scan_files)
            
            self.process_btn = QPushButton("처리 시작")
            self.process_btn.clicked.connect(self.process_files)
            self.process_btn.setEnabled(False)
            
            self.new_batch_btn = QPushButton("새 배치 시작")
            self.new_batch_btn.clicked.connect(self.start_new_batch)
            self.new_batch_btn.setEnabled(True)
            
            btn_layout.addWidget(self.scan_btn)
            btn_layout.addWidget(self.process_btn)
            btn_layout.addWidget(self.new_batch_btn)
            btn_layout.addStretch()
            
            main_layout.addLayout(btn_layout)
            
            self.setLayout(main_layout)
        
        except Exception as e:
            logger.critical(f"Failed to initialize file tab UI: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"UI 초기화 중 오류가 발생했습니다: {str(e)}")
    
    def initialize_sequence_combo(self):
        self.sequence_combo.clear()
        self.sequence_combo.addItem("자동 감지")
        self.sequence_combo.addItem("LIG")
        self.sequence_combo.addItem("KIAP")
        self.sequence_combo.currentTextChanged.connect(self.on_sequence_changed)
        self.sequence_combo.setEditable(True)
        if hasattr(self, 'source_directory') and self.source_directory:
            if hasattr(self, 'update_sequence_combo_from_directory'):
                self.update_sequence_combo_from_directory(self.source_directory)
        else:
            self.sequence_combo.setCurrentIndex(0)
    def on_sequence_changed(self, text):
        if text and text != "자동 감지":
            if hasattr(self, 'update_recent_sequence'):
                self.update_recent_sequence(text)
            if text not in [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count())]:
                self.sequence_combo.addItem(text)
                self.sequence_combo.setCurrentText(text)
                if hasattr(self, 'save_custom_sequences'):
                    self.save_custom_sequences()
                logger.debug(f"Added new sequence: {text}")

    def update_sequence_combo_from_directory(self, directory):
        if not directory:
            return
        dir_name = os.path.basename(directory)
        if not dir_name:
            dir_name = os.path.basename(os.path.dirname(directory))
        if dir_name:
            self.add_sequence_if_not_exists(dir_name)
            index = self.sequence_combo.findText(dir_name)
            if index != -1:
                self.sequence_combo.setCurrentIndex(index)

    def add_sequence_if_not_exists(self, sequence_name):
        if self.sequence_combo.findText(sequence_name) == -1:
            self.sequence_combo.addItem(sequence_name)

    def add_custom_sequence(self):
        current_text = self.sequence_combo.currentText()
        if current_text and self.sequence_combo.findText(current_text) == -1:
            self.sequence_combo.addItem(current_text)
            self.save_custom_sequences()
            QMessageBox.information(self, "성공", f"시퀀스 '{current_text}'를 목록에 추가했습니다.")

    def save_custom_sequences(self):
        try:
            custom_sequences = []
            for i in range(self.sequence_combo.count()):
                text = self.sequence_combo.itemText(i)
                if text not in ["자동 감지", "LIG", "KIAP"]:
                    custom_sequences.append(text)
            config_dir = Path.home() / ".shotpipe"
            config_dir.mkdir(exist_ok=True)
            sequences_file = config_dir / "custom_sequences.json"
            with open(sequences_file, "w") as f:
                json.dump(custom_sequences, f)
            logger.debug(f"Saved custom sequences to {sequences_file}")
        except Exception as e:
            logger.error(f"Failed to save custom sequences: {e}")

    def load_custom_sequences(self):
        try:
            sequences_file = Path.home() / ".shotpipe" / "custom_sequences.json"
            if sequences_file.exists():
                with open(sequences_file, "r") as f:
                    custom_sequences = json.load(f)
                    for seq in custom_sequences:
                        if self.sequence_combo.findText(seq) == -1:
                            self.sequence_combo.addItem(seq)
                logger.debug(f"Loaded {len(custom_sequences)} custom sequences.")
        except Exception as e:
            logger.error(f"Failed to load custom sequences: {e}")
            
    def update_recent_sequence(self, sequence):
        if not sequence or sequence == "자동 감지":
            return
        try:
            config_dir = Path.home() / ".shotpipe"
            config_dir.mkdir(exist_ok=True)
            recent_file = config_dir / "recent_sequence.txt"
            with open(recent_file, "w") as f:
                f.write(sequence)
        except Exception as e:
            logger.error(f"Failed to save recent sequence: {e}")
            
    def _on_table_item_changed(self, item):
        row = item.row()
        col = item.column()
        file_name_item = self.file_table.item(row, 1)
        if not file_name_item:
            return
        file_name = file_name_item.text()
        if col == 3 or col == 4:
            new_value = item.text()
            logger.debug(f"Table item changed: Row={row}, Col={col}, File='{file_name}', New Value='{new_value}'")
            if file_name in self.file_info_dict:
                if col == 3:
                    self.file_info_dict[file_name]['sequence'] = new_value
                elif col == 4:
                    self.file_info_dict[file_name]['shot'] = new_value
                logger.debug(f"Updated file_info_dict for '{file_name}': {self.file_info_dict[file_name]}")
            else:
                logger.warning(f"File '{file_name}' not found in file_info_dict for update.")

    def select_source_directory(self):
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "소스 디렉토리 선택", self.source_edit.text() or os.path.expanduser("~")
            )
            if directory:
                self.source_directory = directory
                self.source_edit.setText(directory)
                self.output_directory = directory
                self.output_edit.setText(directory)
                self.scan_files()
                self.update_sequence_combo_from_directory(directory)
                self.save_last_directory()
        except Exception as e:
            logger.error(f"Error selecting source directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"소스 디렉토리 선택 중 오류가 발생했습니다: {str(e)}")
    
    def select_output_directory(self):
        try:
            directory = QFileDialog.getExistingDirectory(
                self, 
                "출력 디렉토리 선택",
                self.source_directory or os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            if not directory:
                return
            self.output_directory = directory
            self.output_edit.setText(directory)
        except Exception as e:
            logger.error(f"Error selecting output directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"출력 디렉토리 선택 중 오류가 발생했습니다: {str(e)}")
    
    def reset_ui(self):
        self.file_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.file_list = []
        self.file_info_dict = {}
        self.sequence_dict = {}
        self.initialize_sequence_combo()
    
    def toggle_sequence_combo(self, enabled):
        self.sequence_combo.setEnabled(enabled)
        self.save_sequence_btn.setEnabled(enabled)
        if enabled and self.sequence_combo.currentText():
            self.update_recent_sequence(self.sequence_combo.currentText())
        if enabled:
            logger.debug(f"Sequence combo enabled, current: {self.sequence_combo.currentText()}")
        else:
            logger.debug("Sequence combo disabled")
    
    def _show_header_context_menu(self, pos):
        header = self.file_table.horizontalHeader()
        index = header.logicalIndexAt(pos)
        menu = QMenu(self)
        reset_action = QAction("기본 너비로 초기화", self)
        reset_action.triggered.connect(lambda: self._reset_column_width(index))
        menu.addAction(reset_action)
        reset_all_action = QAction("모든 열 기본 너비로 초기화", self)
        reset_all_action.triggered.connect(self._reset_all_column_widths)
        menu.addAction(reset_all_action)
        menu.exec_(header.mapToGlobal(pos))
    
    def _reset_column_width(self, column_index):
        if column_index == 1:
            self.file_table.setColumnWidth(column_index, 350)
        elif column_index == 3:
            self.file_table.setColumnWidth(column_index, 100)
        elif column_index == 4:
            self.file_table.setColumnWidth(column_index, 120)
        elif column_index == 6:
            self.file_table.setColumnWidth(column_index, 300)
        else:
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Interactive)
    
    def _reset_all_column_widths(self):
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.file_table.setColumnWidth(0, 40)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.file_table.setColumnWidth(1, 350)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.file_table.setColumnWidth(3, 100)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        self.file_table.setColumnWidth(4, 120)
        self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)
        self.file_table.setColumnWidth(6, 300)
    
    def scan_files(self):
        try:
            if not self.source_directory:
                directory = QFileDialog.getExistingDirectory(
                    self, "소스 폴더 선택", os.path.expanduser("~"),
                    QFileDialog.ShowDirsOnly
                )
                if not directory:
                    return
                self.source_directory = directory
                self.source_edit.setText(self.source_directory)
                self.output_directory = self.source_directory
                self.output_edit.setText(self.output_directory)
                self.save_last_directory()
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.scan_btn.setEnabled(False)
            self.scan_btn.setText("스캔 중...")
            QApplication.processEvents()
            self.file_list = []
            self.file_info_dict = {}
            self.sequence_dict = {}
            self._scan_files_in_background()
        except Exception as e:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")
            logger.error(f"Error scanning directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"디렉토리 스캔 중 오류가 발생했습니다: {str(e)}")
    
    def _scan_files_in_background(self):
        class ScanThread(QThread):
            scan_completed = pyqtSignal(list, dict)
            scan_error = pyqtSignal(str)
            def __init__(self, directory, scanner, processed_files_tracker, recursive=True, exclude_processed=True):
                super().__init__()
                self.directory = directory
                self.scanner = scanner
                self.processed_files_tracker = processed_files_tracker
                self.recursive = recursive
                self.exclude_processed = exclude_processed
            def run(self):
                try:
                    start_time = time.time()
                    logger.info(f"스캔 스레드 시작 - 디렉토리: {self.directory}")
                    logger.debug(f"스캔 옵션: recursive={self.recursive}, exclude_processed={self.exclude_processed}")
                    files = self.scanner.scan_directory(
                        self.directory, 
                        recursive=self.recursive,
                        exclude_processed=self.exclude_processed
                    )
                    file_list = []
                    file_info_dict = {}
                    for file_info in files:
                        file_name = file_info["file_name"]
                        file_list.append(file_name)
                        file_info_dict[file_name] = file_info
                    elapsed_time = time.time() - start_time
                    logger.info(f"스캔 완료: 총 {len(file_list)}개 파일 발견 (소요 시간: {elapsed_time:.2f}초)")
                    self.scan_completed.emit(file_list, file_info_dict)
                except Exception as e:
                    logger.error(f"스캔 스레드 오류: {e}", exc_info=True)
                    self.scan_error.emit(str(e))
        recursive = self.recursive_cb.isChecked()
        exclude_processed = self.exclude_processed_cb.isChecked()
        self.scan_thread = ScanThread(
            self.source_directory,
            self.scanner, 
            self.processed_files_tracker,
            recursive=recursive,
            exclude_processed=exclude_processed
        )
        self.scan_thread.scan_completed.connect(self._handle_scan_completed)
        self.scan_thread.scan_error.connect(self._handle_scan_error)
        self.scan_thread.start()
    
    def _handle_scan_error(self, error_message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("파일 스캔")
        QMessageBox.critical(self, "오류", f"디렉토리 스캔 중 오류가 발생했습니다: {error_message}")
    
    def _handle_scan_completed(self, file_list, file_info_dict):
        try:
            self.file_list = file_list
            self.file_info_dict = file_info_dict
            self.skipped_files = self.scanner.get_skipped_files()
            self.sequence_dict = self.scanner.get_sequence_dict()
            if self.sequence_dict:
                sequence_names = list(self.sequence_dict.keys())
                for seq_name in sorted(sequence_names):
                    self.add_sequence_if_not_exists(seq_name)
            self._update_file_display()
            
            processed_files = self.processed_files_tracker.get_processed_files_in_directory(self.source_directory)
            processed_count = len(processed_files) if processed_files else 0
            unprocessed_count = len(self.file_list)
            total_scanned = unprocessed_count + len(self.skipped_files)
            status_message = f"총 {total_scanned}개 파일 스캔 완료 (유효: {unprocessed_count}, 스킵: {len(self.skipped_files)}, 이전에 처리됨: {processed_count})"
            QMessageBox.information(self, "스캔 완료", status_message)
        except Exception as e:
            logger.error(f"Error handling scan completion: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"스캔 결과 처리 중 오류가 발생했습니다: {e}")
        finally:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")
            self.process_btn.setEnabled(bool(self.file_list))

    def _update_file_display(self):
        try:
            self.file_table.setSortingEnabled(False)
            self.file_table.setUpdatesEnabled(False)
            
            current_filter = self.filter_combo.currentData()
            search_text = self.search_edit.text().lower()
            
            # 표시할 소스 리스트 결정
            if self.all_files_radio.isChecked():
                source_list = self.file_list + self.skipped_files
            elif self.skipped_files_radio.isChecked():
                source_list = self.skipped_files
            else: # 유효 파일
                source_list = self.file_list

            # 스킵된 파일 경로를 Set으로 만들어 빠른 조회를 지원
            skipped_paths = {f.get('file_path') for f in self.skipped_files if f.get('file_path')}

            files_to_show = []
            for item in source_list:
                # item이 dict가 아닌 경우를 대비
                if isinstance(item, str):
                    file_info = self.file_info_dict.get(item, {"file_name": item, "file_path": os.path.join(self.source_directory, item)})
                else:
                    file_info = item
                
                # 검색어 필터링
                if search_text and search_text not in file_info.get("file_name", "").lower():
                    continue
                
                # 처리 상태 필터링
                is_processed = self.processed_files_tracker.is_file_processed(file_info.get('file_path', ''))
                if current_filter == "processed" and not is_processed:
                    continue
                if current_filter == "unprocessed" and is_processed:
                    continue
                
                files_to_show.append(file_info)

            self.file_table.setRowCount(len(files_to_show))

            for row, file_info in enumerate(files_to_show):
                full_path = file_info.get("file_path", "")
                
                # 상태 결정 (처리됨 > 스킵됨 > 대기)
                is_processed = self.processed_files_tracker.is_file_processed(full_path)
                is_skipped = full_path in skipped_paths

                status_text = "대기"
                if is_skipped:
                    status_text = "스킵"
                if is_processed:
                    status_text = "✓ 처리됨"

                # 체크박스 위젯 생성
                check_box_widget = QWidget()
                check_box_layout = QHBoxLayout(check_box_widget)
                check_box = QCheckBox()
                check_box_layout.addWidget(check_box)
                check_box_layout.setAlignment(Qt.AlignCenter)
                check_box_layout.setContentsMargins(0, 0, 0, 0)
                self.file_table.setCellWidget(row, 0, check_box_widget)
                
                # 처리되지 않았고 스킵되지 않은 "유효 파일"만 기본으로 체크합니다.
                check_box.setChecked(not is_processed and not is_skipped)

                # 나머지 셀 데이터 채우기
                self.file_table.setItem(row, 1, QTableWidgetItem(file_info.get("file_name", "")))
                status_item = QTableWidgetItem(status_text)
                self.file_table.setItem(row, 2, status_item)
                self.file_table.setItem(row, 3, QTableWidgetItem(file_info.get("sequence", "")))
                self.file_table.setItem(row, 4, QTableWidgetItem(file_info.get("shot", "")))
                
                elapsed_time = file_info.get("elapsed_time")
                time_item = QTableWidgetItem(f"{elapsed_time:.2f}s" if elapsed_time is not None else "")
                self.file_table.setItem(row, 5, time_item)
                
                message = file_info.get("message", "")
                self.file_table.setItem(row, 6, QTableWidgetItem(message))
                
                # 상태에 따라 행 스타일 적용
                self._style_table_row(row, is_processed, status_text)

        except Exception as e:
            logger.error(f"Failed to update file display: {e}", exc_info=True)
        finally:
            self.file_table.setUpdatesEnabled(True)
            self.file_table.setSortingEnabled(True)
            self._update_file_info_label()

    def _style_table_row(self, row, is_processed, status_text):
        if is_processed:
            color = QColor("#5A5A5A")  # Dark gray for processed files
            font = self.file_table.item(row, 1).font()
            font.setItalic(True)
            for col in range(1, self.file_table.columnCount()):
                item = self.file_table.item(row, col)
                if item:
                    item.setForeground(QColor("gray"))
                    item.setFont(font)
        elif "스킵" in status_text:
            reason = self.file_info_dict.get(self.file_table.item(row, 1).text(), {}).get("skip_reason")
            display_text, color_name = self._get_skip_reason_display(reason)
            color = QColor(color_name)
            for col in range(1, self.file_table.columnCount()):
                item = self.file_table.item(row, col)
                if item:
                    item.setBackground(color)
                    item.setToolTip(f"스킵된 이유: {display_text}")
            status_item = self.file_table.item(row, 2)
            if status_item:
                status_item.setText(f"스킵됨 ({display_text})")
        else:
            for col in range(1, self.file_table.columnCount()):
                item = self.file_table.item(row, col)
                if item:
                    item.setBackground(QColor("transparent"))
                    item.setForeground(QColor(get_color_palette()['text_primary']))
                    font = item.font()
                    font.setItalic(False)
                    item.setFont(font)
                    item.setToolTip("")

    def process_files(self):
        try:
            selected_files = self.get_selected_files()
            if not selected_files:
                QMessageBox.warning(self, "경고", "처리할 파일을 선택하세요.")
                return
            self.progress_bar.setVisible(True)
            self.process_btn.setEnabled(False)
            self.process_btn.setText("처리 중...")
            output_dir = self.output_edit.text() or self.source_directory
            create_processed_folder = self.create_processed_folder_cb.isChecked()
            naming_options = {
                "use_sequence": self.use_sequence_cb.isChecked(),
                "sequence": self.sequence_combo.currentText(),
            }
            if self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.stop()
            self.processing_thread = ProcessingThread(
                selected_files,
                self.metadata_extractor,
                output_directory=output_dir,
                processed_files_tracker=self.processed_files_tracker
            )
            # 진도바 범위 설정
            self.progress_bar.setRange(0, len(selected_files))
            self.progress_bar.setValue(0)
            
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.file_processed.connect(self.update_file_status)
            self.processing_thread.processing_completed.connect(self.processing_completed)
            self.processing_thread.processing_error.connect(self.processing_error)
            self.processing_thread.start()
        except Exception as e:
            logger.error(f"Error starting file processing: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"파일 처리 시작 중 오류: {str(e)}")
            self.process_btn.setEnabled(True)
            self.process_btn.setText("처리 시작")

    def cancel_processing(self):
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            logger.info("File processing cancelled by user.")
            QMessageBox.information(self, "취소됨", "파일 처리가 중단되었습니다.")

    @pyqtSlot(int, int)
    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str, str, str, str, str, float)
    def update_file_status(self, file_name, status, sequence, shot, message, elapsed_time):
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 1).text() == file_name:
                self.file_table.setItem(row, 2, QTableWidgetItem(status))
                self.file_table.setItem(row, 3, QTableWidgetItem(sequence))
                self.file_table.setItem(row, 4, QTableWidgetItem(shot))
                self.file_table.setItem(row, 5, QTableWidgetItem(f"{elapsed_time:.2f}s"))
                self.file_table.setItem(row, 6, QTableWidgetItem(message))
                is_processed = "완료" in status or "성공" in status
                self._style_table_row(row, is_processed, status)
                if is_processed:
                    full_path = self.file_info_dict.get(file_name, {}).get("file_path", "")
                    if full_path:
                        self.processed_files_tracker.add_processed_file(full_path, {"status": status})
                break

    @pyqtSlot(list)
    def processing_completed(self, processed_files):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("처리 시작")
        self.files_processed.emit(processed_files)
        
        QMessageBox.information(self, "완료", f"{len(processed_files)}개 파일 처리가 완료되었습니다.")
        
        if SHOTGRID_AVAILABLE and self.shotgrid_connector:
            reply = QMessageBox.question(self, 'Shotgrid 업로드', 
                                         '처리된 파일을 Shotgrid에 업로드하시겠습니까?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                converted_files = self._convert_files_for_shotgrid(processed_files)
                if converted_files:
                    # Shotgrid 탭으로 파일 정보 전송
                    if hasattr(self.parent, 'shotgrid_tab'):
                        self.parent.shotgrid_tab.add_files_for_upload(converted_files)
                        self.parent.tabs.setCurrentWidget(self.parent.shotgrid_tab)
                        QMessageBox.information(self, "정보", "파일이 Shotgrid 탭으로 전송되었습니다. 내용을 확인 후 업로드 해주세요.")
                    else:
                        QMessageBox.warning(self, "경고", "Shotgrid 탭을 찾을 수 없습니다.")

    def _convert_files_for_shotgrid(self, processed_files):
        converted_files = []
        for file_info in processed_files:
            if file_info.get("success", False):
                converted_file = {
                    "file_name": file_info.get("file_name", ""),
                    "file_path": file_info.get("file_path", ""),
                    "project": self.fixed_project_name,
                    "sequence": file_info.get("sequence", ""),
                    "shot": file_info.get("shot", ""),
                    "task": self._assign_task_automatically(file_info.get("output_path", "")),
                    "version": file_info.get("version", "v001"),
                    "processed": True,
                    "metadata": file_info.get("metadata", {}),
                    "batch_path": file_info.get("batch_path", "")
                }
                converted_files.append(converted_file)
        return converted_files

    def on_shotgrid_project_changed(self, project_name):
        self.fixed_project_name = project_name
        self.shotgrid_project_label.setText(project_name)
        if project_name and project_name != "-- 프로젝트 선택 --":
            try:
                project = self.shotgrid_entity_manager.find_project(project_name)
                if project:
                    sequences = self.shotgrid_entity_manager.get_sequences_in_project(project)
                    self.shotgrid_sequence_combo.clear()
                    self.shotgrid_sequence_combo.addItem("-- 시퀀스 선택 --")
                    for seq in sequences:
                        self.shotgrid_sequence_combo.addItem(seq['code'])
            except Exception as e:
                logger.error(f"Error loading sequences for project '{project_name}': {e}")
                QMessageBox.warning(self, "오류", f"{project_name} 프로젝트의 시퀀스를 불러오는 데 실패했습니다.")
    
    @pyqtSlot(dict)
    def update_from_shotgrid_tab(self, info):
        file_name = info.get('file_name')
        if not file_name:
            return
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 1).text() == file_name:
                self.file_table.setItem(row, 2, QTableWidgetItem(info.get("status", "업로드됨")))
                # Update other relevant columns if needed
                break

    def scan_directory(self, directory=None, recursive=True, update_ui=True):
        if directory is None:
            directory = self.source_directory
        if not directory:
            self.select_source_directory()
            return
        
        start_time = time.time()
        self.file_list, self.file_info_dict, self.sequence_dict, self.skipped_files = self.scanner.scan_directory(
            directory, recursive, exclude_processed=self.exclude_processed_cb.isChecked()
        )
        elapsed_time = time.time() - start_time
        
        if update_ui:
            self._update_file_display()
            self.process_btn.setEnabled(len(self.file_list) > 0)
            
        logger.info(f"Scanned {directory} in {elapsed_time:.2f} seconds. Found {len(self.file_list)} files, skipped {len(self.skipped_files)}.")

    def _assign_task_automatically(self, file_path):
        """파일 경로를 기반으로 Task를 자동으로 할당 (예시)"""
        file_path_lower = file_path.lower()
        if "comp" in file_path_lower:
            return "comp"
        if "light" in file_path_lower or "lgt" in file_path_lower:
            return "lighting"
        if "fx" in file_path_lower:
            return "fx"
        if "ani" in file_path_lower or "anim" in file_path_lower:
            return "animation"
        return "comp" # 기본값

    def set_processed_files(self, processed_files):
        """Sets the list of processed files from an external source (e.g., main app)."""
        logger.debug(f"Received {len(processed_files)} processed files to update tracker.")
        for file_path in processed_files:
            file_info = {"status": "processed by other tab"}
            self.processed_files_tracker.add_processed_file(file_path, file_info)
        
        # Refresh the UI to reflect changes
        self._update_file_display()
        
    def get_selected_files(self, ignore_checkbox_state=False):
        selected_files = []
        for row in range(self.file_table.rowCount()):
            check_box = self.file_table.cellWidget(row, 0).findChild(QCheckBox)
            if ignore_checkbox_state or (check_box and check_box.isChecked()):
                file_name_item = self.file_table.item(row, 1)
                if file_name_item:
                    file_name = file_name_item.text()
                    file_info = self.file_info_dict.get(file_name, {}).copy()
                    if not file_info:
                        file_info['file_path'] = os.path.join(self.source_directory, file_name)
                        file_info['file_name'] = file_name
                    
                    seq_item = self.file_table.item(row, 3)
                    shot_item = self.file_table.item(row, 4)
                    
                    file_info['sequence'] = seq_item.text() if seq_item else ''
                    file_info['shot'] = shot_item.text() if shot_item else ''
                    
                    # 태스크 정보가 테이블에 있다면 추가 (현재는 자동 할당)
                    # 향후 태스크 컬럼이 추가되면 여기서 처리
                    
                    selected_files.append(file_info)
        return selected_files

    def start_new_batch(self):
        self.processed_files_tracker.start_new_batch()
        self.reset_ui()
        self.source_edit.clear()
        self.output_edit.clear()
        QMessageBox.information(self, "알림", "새로운 배치 작업을 시작합니다. 기존 처리 이력은 보존됩니다.")

    def filter_files(self):
        self._update_file_display()

    def select_all_files(self, select):
        for row in range(self.file_table.rowCount()):
            self.file_table.cellWidget(row, 0).findChild(QCheckBox).setChecked(select)
            
    def toggle_all_checkboxes(self, checked):
        for row in range(self.file_table.rowCount()):
            self.file_table.cellWidget(row, 0).findChild(QCheckBox).setChecked(checked)

    def select_unprocessed_files(self):
        self.file_table.setSortingEnabled(False)
        for row in range(self.file_table.rowCount()):
            status_item = self.file_table.item(row, 2)
            is_processed = status_item and ("완료" in status_item.text() or "성공" in status_item.text())
            self.file_table.cellWidget(row, 0).findChild(QCheckBox).setChecked(not is_processed)
        self.file_table.setSortingEnabled(True)

    def save_last_directory(self):
        try:
            config_dir = Path.home() / ".shotpipe"
            config_dir.mkdir(exist_ok=True)
            last_dir_file = config_dir / "last_directory.txt"
            with open(last_dir_file, "w") as f:
                f.write(self.source_directory)
        except Exception as e:
            logger.error(f"Failed to save last directory: {e}")

    def load_last_directory(self):
        try:
            last_dir_file = Path.home() / ".shotpipe" / "last_directory.txt"
            if last_dir_file.exists():
                with open(last_dir_file, "r") as f:
                    last_dir = f.read().strip()
                    if os.path.isdir(last_dir):
                        self.source_directory = last_dir
                        self.source_edit.setText(last_dir)
                        self.output_directory = last_dir
                        self.output_edit.setText(last_dir)
                        QTimer.singleShot(100, self.scan_files)
        except Exception as e:
            logger.error(f"Failed to load last directory: {e}")

    def _update_file_info_label(self, message=None):
        if message:
            self.file_info_label.setText(message)
            return
        
        valid_count = len(self.file_list)
        skipped_count = len(self.skipped_files)
        total_count = valid_count + skipped_count
        
        selected_count = 0
        for row in range(self.file_table.rowCount()):
            widget = self.file_table.cellWidget(row, 0)
            if widget and widget.findChild(QCheckBox) and widget.findChild(QCheckBox).isChecked():
                selected_count += 1
                
        self.file_info_label.setText(f"총 {total_count}개 파일 발견 (유효: {valid_count}, 스킵: {skipped_count}) | 선택됨: {selected_count}개")

    def export_history(self):
        self.processed_files_tracker.export_history()

    def show_history_stats(self):
        self.processed_files_tracker.show_stats_popup()

    def reset_history(self):
        reply = QMessageBox.question(self, '이력 초기화 확인',
                                     '정말로 모든 처리 이력을 초기화하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 1. 트래커의 이력을 리셋합니다.
            self.processed_files_tracker.reset_history()
            
            # 2. 스캐너가 가진 트래커도 동일한 인스턴스를 사용하지만, 
            #    만약을 위해 스캐너 내부 상태도 리셋하도록 지시합니다.
            if hasattr(self, 'scanner'):
                self.scanner.reset()
            
            # 3. FileTab의 파일 목록 관련 데이터도 초기화합니다.
            self.file_list = []
            self.skipped_files = []
            self.file_info_dict = {}
            self.sequence_dict = {}

            # 4. UI를 새로고침하여 변경사항을 즉시 반영합니다.
            self._update_file_display() 
            QMessageBox.information(self, '완료', '모든 처리 이력이 초기화되었습니다. 다시 스캔을 진행해주세요.')

    def update_shotgrid_status(self):
        if SHOTGRID_AVAILABLE and self.shotgrid_connector:
            if self.shotgrid_connector.sg and self.shotgrid_connector.get_user_info():
                self.shotgrid_status_label.setText(f"✅ Shotgrid 연결됨 (사용자: {self.shotgrid_connector.get_user_info()})")
                self.shotgrid_status_label.setStyleSheet("color: #2ECC71;")
            else:
                self.shotgrid_status_label.setText("❌ Shotgrid 연결 끊김")
                self.shotgrid_status_label.setStyleSheet("color: #E74C3C;")

    def auto_load_fixed_project(self):
        self.on_shotgrid_project_changed(self.fixed_project_name)

    def on_fixed_project_sequence_changed(self, sequence_name):
        if sequence_name and sequence_name != "-- 시퀀스 선택 --":
            try:
                project = self.shotgrid_entity_manager.find_project(self.fixed_project_name)
                if project:
                    shots = self.shotgrid_entity_manager.get_shots_in_sequence(project, sequence_name)
                    self.shotgrid_shot_combo.clear()
                    self.shotgrid_shot_combo.addItem("-- Shot 선택 --")
                    for shot in shots:
                        self.shotgrid_shot_combo.addItem(shot['code'])
            except Exception as e:
                logger.error(f"Error loading shots for sequence '{sequence_name}': {e}")
                QMessageBox.warning(self, "오류", f"시퀀스 '{sequence_name}'의 샷 목록을 불러오는 데 실패했습니다.")
        else:
            self.shotgrid_shot_combo.clear()
            self.shotgrid_shot_combo.addItem("-- 시퀀스를 먼저 선택하세요 --")

    def refresh_shotgrid_data(self):
        QMessageBox.information(self, "새로고침", "Shotgrid 데이터를 새로고침합니다...")
        self.auto_load_fixed_project()
        QMessageBox.information(self, "완료", "새로고침이 완료되었습니다.")

    def apply_shotgrid_to_selected(self):
        sequence = self.shotgrid_sequence_combo.currentText()
        shot = self.shotgrid_shot_combo.currentText()
        
        selected_rows = []
        for row in range(self.file_table.rowCount()):
            if self.file_table.cellWidget(row, 0).findChild(QCheckBox).isChecked():
                selected_rows.append(row)
        
        if not any(selected_rows):
            QMessageBox.warning(self, "경고", "정보를 적용할 파일을 하나 이상 선택해주세요.")
            return
            
        for row in range(self.file_table.rowCount()):
            if self.file_table.cellWidget(row, 0).findChild(QCheckBox).isChecked():
                if sequence and sequence != "-- 시퀀스 선택 --":
                    self.file_table.item(row, 3).setText(sequence)
                if shot and shot != "-- Shot 선택 --":
                    self.file_table.item(row, 4).setText(shot)

    def open_project_settings(self):
        from ..ui.project_settings_dialog import ProjectSettingsDialog
        
        dialog = ProjectSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.fixed_project_name = new_settings['project_name']
            self.auto_select_project = new_settings['auto_select']
            self.show_project_selector = new_settings['show_selector']
            
            # Update UI
            self.shotgrid_project_label.setText(self.fixed_project_name)
            
            # Save settings
            config.set('shotgrid', 'default_project', self.fixed_project_name)
            config.set('shotgrid', 'auto_select_project', str(self.auto_select_project))
            config.set('shotgrid', 'show_project_selector', str(self.show_project_selector))
            
            QMessageBox.information(self, "설정 저장", "프로젝트 설정이 저장되었습니다.")
            
            if self.auto_select_project:
                self.auto_load_fixed_project()

    @pyqtSlot(str)
    def processing_error(self, error_message):
        """ processing_thread에서 에러 발생 시 호출될 슬롯 """
        logger.error(f"An error occurred in processing thread: {error_message}")
        QMessageBox.critical(self, "처리 오류", f"파일 처리 중 오류가 발생했습니다:\n{error_message}")
        
        # UI 상태 복원
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.process_btn.setText("처리 시작")

    def closeEvent(self, event):
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(self, '확인',
                                         '파일 처리 작업이 아직 진행 중입니다. 종료하시겠습니까?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.processing_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _get_skip_reason_display(self, reason_code):
        reasons = {
            "ALREADY_PROCESSED": ("이미 처리됨", "#5D6D7E"),
            "UNSUPPORTED_TYPE": ("미지원 형식", "#F39C12"),
            "DUPLICATE_FILE": ("중복 파일", "#A569BD"),
            "EMPTY_FILE": ("빈 파일", "#E67E22"),
            "READ_ERROR": ("읽기 오류", "#E74C3C"),
            "UNKNOWN": ("알 수 없음", "#95A5A6")
        }
        return reasons.get(reason_code, ("기타", "#BDC3C7"))
