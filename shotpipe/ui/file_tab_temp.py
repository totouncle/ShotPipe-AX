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
    QApplication, QButtonGroup, QRadioButton, QAbstractItemView, QStyle, QStyleOptionButton, QSizePolicy
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

class HeaderCheckbox(QWidget):
    """
    A custom QWidget with a QCheckBox to be used in the QTableWidget header.
    Allows for "select all" functionality.
    """
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkbox = QCheckBox(self)
        layout = QHBoxLayout(self)
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.checkbox.toggled.connect(self.toggled.emit)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)


class SequenceShotDelegate(QStyledItemDelegate):
    """시퀀스와 샷 컬럼용 커스텀 드롭다운 에디터"""

    def __init__(self, parent_tab):
        super().__init__()
        self.parent_tab = parent_tab

    def createEditor(self, parent, option, index):
        """에디터 생성 - QComboBox 드롭다운"""
        if index.column() not in [3, 4]:  # 시퀀스(3), 샷(4) 컬럼만
            return super().createEditor(parent, option, index)

        combo = QComboBox(parent)
        combo.setEditable(True)  # 직접 입력도 가능하게
        combo.setInsertPolicy(QComboBox.NoInsert)  # 새 항목 추가 방지

        # 데이터 로드
        self._populate_combo_data(combo, index)

        return combo

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

    def setEditorData(self, editor, index):
        """에디터에 현재 값 설정"""
        if not isinstance(editor, QComboBox):
            return super().setEditorData(editor, index)

        current_value = index.model().data(index, Qt.DisplayRole)
        if current_value:
            # 현재 값이 콤보박스에 있으면 선택
            combo_index = editor.findText(current_value)
            if combo_index >= 0:
                editor.setCurrentIndex(combo_index)
            else:
                # 없으면 직접 입력된 값으로 설정
                editor.setEditText(current_value)

    def setModelData(self, editor, model, index):
        """에디터의 값을 모델에 저장"""
        if not isinstance(editor, QComboBox):
            return super().setModelData(editor, model, index)

        value = editor.currentText()
        if value and value not in ["-- 시퀀스 선택 --", "-- Shot 선택 --"]:
            model.setData(index, value, Qt.EditRole)

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

    def __init__(self, parent=None):
        """Initialize the file tab."""
        super().__init__(parent)
        self.parent = parent
        self.source_directory = ""
        self.output_directory = ""  # 출력 디렉토리 경로 추가
        self.file_list = []
        self.file_info_dict = {}
        self.sequence_dict = {}
        self.processing_thread = None
        self.scanner = FileScanner()
        self.metadata_extractor = MetadataExtractor()
        self.processed_files_tracker = ProcessedFilesTracker()  # 초기화

        # 스캐너에 ProcessedFilesTracker 설정
        self.scanner.processed_files_tracker = self.processed_files_tracker

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
            # 인라인 스타일 제거 - 전체 다크 테마 사용

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

            # 라디오 버튼 연결
            self.all_files_radio.toggled.connect(self._update_file_display)
            self.valid_files_radio.toggled.connect(self._update_file_display)
            self.skipped_files_radio.toggled.connect(self._update_file_display)

            main_layout.addLayout(view_mode_layout)

            self.file_table = QTableWidget(0, 7)
            self.file_table.setHorizontalHeaderLabels(["", "파일명", "상태", "시퀀스*", "샷*", "경과 시간", "메세지"])

            # 다크 테마 테이블 스타일 설정 (전역 스타일시트로 대체)
            # 기본 테이블 설정만 유지
            self.file_table.setAlternatingRowColors(True)
            self.file_table.setSelectionBehavior(QTableWidget.SelectRows)

            # 헤더에 전체 선택 체크박스 추가
            self.header_checkbox = HeaderCheckbox(self.file_table.horizontalHeader())
            self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.file_table.setColumnWidth(0, 40) # 체크박스 너비
            self.file_table.horizontalHeader().setCellWidget(0, self.header_checkbox)
            self.header_checkbox.toggled.connect(self.toggle_all_checkboxes)


            self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)      # 파일명
            self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 상태
            self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)      # 시퀀스 (편집 가능)
            self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)      # 샷 (편집 가능)
            self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 경과 시간
            self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)      # 메세지

            # 초기 열 너비 설정
            self.file_table.setColumnWidth(1, 350) # 파일명
            self.file_table.setColumnWidth(3, 100) # 시퀀스
            self.file_table.setColumnWidth(4, 120) # 샷
            self.file_table.setColumnWidth(6, 300) # 메세지

            # 헤더 툴팁 설정
            header = self.file_table.horizontalHeader()
            header.setToolTip("시퀀스*와 샷* 컬럼을 더블클릭하면 Shotgrid에서 선택할 수 있습니다")

            # 헤더의 컨텍스트 메뉴 활성화
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self._show_header_context_menu)

            # 정렬 기능 활성화
            self.file_table.setSortingEnabled(True)
            self.file_table.horizontalHeader().setSortIndicatorShown(True)

            # 상태 열을 기준으로 내림차순 정렬 (처리되지 않은 파일이 먼저 표시되도록)
            self.file_table.sortItems(2, Qt.AscendingOrder)

            # 테이블 아이템 변경 시그널 연결 (시퀀스, 샷 편집 반영)
            self.file_table.itemChanged.connect(self._on_table_item_changed)

            # 커스텀 델리게이트 설정 (시퀀스, 샷 컬럼용 드롭다운)
            self.sequence_shot_delegate = SequenceShotDelegate(self)
            self.file_table.setItemDelegateForColumn(3, self.sequence_shot_delegate)  # 시퀀스 컬럼
            self.file_table.setItemDelegateForColumn(4, self.sequence_shot_delegate)  # 샷 컬럼

            self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
            # 더블클릭으로 편집 가능하게 설정 (시퀀스와 샷 컬럼)
            self.file_table.setEditTriggers(QAbstractItemView.DoubleClicked)
            main_layout.addWidget(self.file_table)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("%p% (%v/%m)")
            self.progress_bar.setVisible(False)
            main_layout.addWidget(self.progress_bar)

            # Action buttons
            btn_layout = QHBoxLayout()

            self.scan_btn = QPushButton("파일 스캔")
            self.scan_btn.clicked.connect(self.scan_files)

            self.process_btn = QPushButton("처리 시작")
            self.process_btn.clicked.connect(self.process_files)
            self.process_btn.setEnabled(False)

            # 새 배치 시작 버튼 추가
            self.new_batch_btn = QPushButton("새 배치 시작")
            self.new_batch_btn.clicked.connect(self.start_new_batch)
            self.new_batch_btn.setEnabled(True)

            btn_layout.addWidget(self.scan_btn)
            btn_layout.addWidget(self.process_btn)
            btn_layout.addWidget(self.new_batch_btn)
            btn_layout.addStretch()

            main_layout.addLayout(btn_layout)

            # Set the main layout
            self.setLayout(main_layout)

        except Exception as e:
            logger.critical(f"Failed to initialize file tab UI: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"UI 초기화 중 오류가 발생했습니다: {str(e)}")

    def initialize_sequence_combo(self):
        """시퀀스 콤보박스 초기화."""
        # 기존 항목 모두 지우기
        self.sequence_combo.clear()

        # 기본 항목 추가
        self.sequence_combo.addItem("자동 감지")
        self.sequence_combo.addItem("LIG")
        self.sequence_combo.addItem("KIAP")

        # 콤보박스 현재 텍스트 변경 시그널을 on_sequence_changed 메서드에 연결
        self.sequence_combo.currentTextChanged.connect(self.on_sequence_changed)

        # 콤보박스를 편집 가능하게 설정 (사용자가 직접 시퀀스 입력 가능)
        self.sequence_combo.setEditable(True)

        # 디렉토리가 이미 선택되어 있으면 해당 디렉토리명으로 시퀀스 설정
        if hasattr(self, 'source_directory') and self.source_directory:
            if hasattr(self, 'update_sequence_combo_from_directory'):
                self.update_sequence_combo_from_directory(self.source_directory)
        else:
            # 첫 번째 항목 선택 (자동 감지)
            self.sequence_combo.setCurrentIndex(0)

    def on_sequence_changed(self, text):
        """시퀀스 콤보박스의 값이 변경되면 호출"""
        if text and text != "자동 감지":
            # 현재 시퀀스 저장
            if hasattr(self, 'update_recent_sequence'):
                self.update_recent_sequence(text)

            # 사용자가 새 시퀀스를 입력한 경우 콤보박스에 추가
            if text not in [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count())]:
                self.sequence_combo.addItem(text)
                self.sequence_combo.setCurrentText(text)
                # 커스텀 시퀀스 저장
                if hasattr(self, 'save_custom_sequences'):
                    self.save_custom_sequences()
                logger.debug(f"Added new sequence: {text}")

    def update_sequence_combo_from_directory(self, directory):
        """디렉토리명을 시퀀스 콤보박스에 추가하고 선택합니다."""
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
        """콤보박스에 시퀀스가 없으면 추가합니다."""
        if self.sequence_combo.findText(sequence_name) == -1:
            self.sequence_combo.addItem(sequence_name)

    def add_custom_sequence(self):
        """사용자가 입력한 시퀀스를 콤보박스에 추가하고 저장합니다."""
        current_text = self.sequence_combo.currentText()
        if current_text and self.sequence_combo.findText(current_text) == -1:
            self.sequence_combo.addItem(current_text)
            self.save_custom_sequences()
            QMessageBox.information(self, "성공", f"시퀀스 '{current_text}'를 목록에 추가했습니다.")

    def save_custom_sequences(self):
        """콤보박스의 사용자 정의 시퀀스를 파일에 저장합니다."""
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
        """파일에서 사용자 정의 시퀀스를 불러와 콤보박스에 추가합니다."""
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
        """최근 사용 시퀀스를 저장합니다."""
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
        """
        테이블 아이템이 변경되었을 때 호출됩니다.
        (예: 사용자가 시퀀스나 샷을 수동으로 편집했을 때)
        """
        row = item.row()
        col = item.column()
        file_name_item = self.file_table.item(row, 1)

        if not file_name_item:
            return  # 파일명 아이템이 없으면 아무것도 하지 않음

        file_name = file_name_item.text()

        # 시퀀스(3) 또는 샷(4) 컬럼이 변경된 경우
        if col == 3 or col == 4:
            new_value = item.text()
            logger.debug(f"Table item changed: Row={row}, Col={col}, File='{file_name}', New Value='{new_value}'")

            # file_info_dict 업데이트
            if file_name in self.file_info_dict:
                if col == 3:
                    self.file_info_dict[file_name]['sequence'] = new_value
                elif col == 4:
                    self.file_info_dict[file_name]['shot'] = new_value
                logger.debug(f"Updated file_info_dict for '{file_name}': {self.file_info_dict[file_name]}")
            else:
                logger.warning(f"File '{file_name}' not found in file_info_dict for update.")

    def select_source_directory(self):
        """Browse for source directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "소스 디렉토리 선택", self.source_edit.text() or os.path.expanduser("~")
            )
            if directory:
                self.source_directory = directory
                self.source_edit.setText(directory)

                # 소스 디렉토리가 선택되면 기본적으로 output_directory도 동일하게 설정
                self.output_directory = directory
                self.output_edit.setText(directory)

                # 디렉토리 변경 시 자동 스캔
                self.scan_files()

                # 디렉토리 이름을 시퀀스 콤보박스에 추가
                self.update_sequence_combo_from_directory(directory)

                # 현재 디렉토리 저장
                self.save_last_directory()

        except Exception as e:
            logger.error(f"Error selecting source directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"소스 디렉토리 선택 중 오류가 발생했습니다: {str(e)}")

    def select_output_directory(self):
        """Select an output directory."""
        try:
            # Open file dialog
            directory = QFileDialog.getExistingDirectory(
                self,
                "출력 디렉토리 선택",
                self.source_directory or os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )

            # If user cancels, directory will be empty
            if not directory:
                return

            self.output_directory = directory
            self.output_edit.setText(directory)

        except Exception as e:
            logger.error(f"Error selecting output directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"출력 디렉토리 선택 중 오류가 발생했습니다: {str(e)}")

    def reset_ui(self):
        """Reset the UI state."""
        # Clear the file table
        self.file_table.setRowCount(0)

        # Reset the progress bar
        self.progress_bar.setValue(0)

        # Disable processing buttons
        self.process_btn.setEnabled(False)

        # Clear file paths
        self.file_list = []
        self.file_info_dict = {}

        # Clear sequence dictionary
        self.sequence_dict = {}

        # Clear sequence combo box
        self.initialize_sequence_combo()

    def toggle_sequence_combo(self, enabled):
        """Toggle sequence combo box enabled state based on source selection."""
        self.sequence_combo.setEnabled(enabled)
        self.save_sequence_btn.setEnabled(enabled)

        # 선택된 시퀀스가 있고 활성화 상태일 때만 최근 시퀀스 업데이트
        if enabled and self.sequence_combo.currentText():
            self.update_recent_sequence(self.sequence_combo.currentText())

        # 상태 로깅
        if enabled:
            logger.debug(f"Sequence combo enabled, current: {self.sequence_combo.currentText()}")
        else:
            logger.debug("Sequence combo disabled")

    def _show_header_context_menu(self, pos):
        """테이블 헤더의 컨텍스트 메뉴를 표시합니다."""
        header = self.file_table.horizontalHeader()

        # 클릭한 컬럼 인덱스 가져오기
        index = header.logicalIndexAt(pos)

        # 컨텍스트 메뉴 생성
        menu = QMenu(self)

        # 열 너비 초기화 액션
        reset_action = QAction("기본 너비로 초기화", self)
        reset_action.triggered.connect(lambda: self._reset_column_width(index))
        menu.addAction(reset_action)

        # 모든 열 너비 초기화 액션
        reset_all_action = QAction("모든 열 기본 너비로 초기화", self)
        reset_all_action.triggered.connect(self._reset_all_column_widths)
        menu.addAction(reset_all_action)

        # 메뉴 표시
        menu.exec_(header.mapToGlobal(pos))

    def _reset_column_width(self, column_index):
        """특정 열의 너비를 기본값으로 초기화합니다."""
        if column_index == 1:  # 파일명 컬럼
            self.file_table.setColumnWidth(column_index, 350)
        elif column_index == 3:  # 시퀀스 컬럼
            self.file_table.setColumnWidth(column_index, 100)
        elif column_index == 4:  # 샷 컬럼
            self.file_table.setColumnWidth(column_index, 120)
        elif column_index == 6:  # 메세지 컬럼
            self.file_table.setColumnWidth(column_index, 300)
        else:
            # 기타 열은 ResizeToContents로 설정된 컬럼이므로 자동 조정
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Interactive)

    def _reset_all_column_widths(self):
        """모든 열의 너비를 기본값으로 초기화합니다."""
        # 선택 열
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.file_table.setColumnWidth(0, 40)

        # 파일명 열
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.file_table.setColumnWidth(1, 350)

        # 상태 열
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # 시퀀스 열 (편집 가능)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.file_table.setColumnWidth(3, 100)

        # 샷 열 (편집 가능)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        self.file_table.setColumnWidth(4, 120)

        # 경과 시간 열
        self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        # 메세지 열
        self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)
        self.file_table.setColumnWidth(6, 300)

    def scan_files(self):
        """Scan files in the source directory."""
        try:
            # 처리된 파일 트래커 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                self.processed_files_tracker = ProcessedFilesTracker()
                logger.debug("ProcessedFilesTracker 인스턴스 새로 생성")

            # Get the source directory
            if not self.source_directory:
                directory = QFileDialog.getExistingDirectory(
                    self, "소스 폴더 선택", os.path.expanduser("~"),
                    QFileDialog.ShowDirsOnly
                )
                if not directory:
                    return
                self.source_directory = directory
                self.source_edit.setText(self.source_directory)

                # 소스 디렉토리가 지정되면 기본적으로 output_directory도 동일하게 설정
                self.output_directory = self.source_directory
                self.output_edit.setText(self.output_directory)

                # 현재 디렉토리 저장
                self.save_last_directory()

            # 스캔 중임을 표시
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 불확정 프로그레스 바
            self.scan_btn.setEnabled(False)
            self.scan_btn.setText("스캔 중...")
            QApplication.processEvents()  # UI 업데이트

            # Clear previous data
            self.file_list = []
            self.file_info_dict = {}
            self.sequence_dict = {}

            # Scan for files (별도 스레드에서 처리)
            self._scan_files_in_background()

        except Exception as e:
            # 에러 발생 시 UI 복원
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")

            logger.error(f"Error scanning directory: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"디렉토리 스캔 중 오류가 발생했습니다: {str(e)}")

    def _scan_files_in_background(self):
        """파일 스캔을 백그라운드에서 처리하는 스레드 생성"""
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

                    # 생성자에서 전달받은 옵션 사용
                    files = self.scanner.scan_directory(
                        self.directory,
                        recursive=self.recursive,
                        exclude_processed=self.exclude_processed
                    )

                    # 파일 이름 및 정보 딕셔너리 생성
                    file_list = []
                    file_info_dict = {}
                    
                    for file_info in files:
                        file_name = file_info["file_name"]
                        file_list.append(file_name)
                        file_info_dict[file_name] = file_info

                    elapsed_time = time.time() - start_time
                    logger.info(f"스캔 완료: 총 {len(file_list)}개 파일 발견 (소요 시간: {elapsed_time:.2f}초)")
                    
                    # 결과 전송
                    self.scan_completed.emit(file_list, file_info_dict)

                except Exception as e:
                    logger.error(f"스캔 스레드 오류: {e}", exc_info=True)
                    self.scan_error.emit(str(e))

        # 체크박스 상태 확인
        recursive = self.recursive_cb.isChecked()
        exclude_processed = self.exclude_processed_cb.isChecked()

        # 스캔 스레드 생성 및 시작 (체크박스 상태 전달)
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
        """스캔 스레드에서 오류 발생 시 처리"""
        # UI 복원
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("파일 스캔")

        QMessageBox.critical(self, "오류", f"디렉토리 스캔 중 오류가 발생했습니다: {error_message}")

    def _handle_scan_completed(self, file_list, file_info_dict):
        """스캔 완료 후 UI 업데이트."""
        try:
            self.file_list = file_list
            self.file_info_dict = file_info_dict
            self.skipped_files = self.scanner.get_skipped_files()
            self.sequence_dict = self.scanner.get_sequence_dict()

            # 시퀀스 콤보박스 업데이트
            if self.sequence_dict:
                sequence_names = list(self.sequence_dict.keys())
                for seq_name in sorted(sequence_names):
                    self.add_sequence_if_not_exists(seq_name)

            # UI 업데이트
            self._update_file_display()

            # UI 복원
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")
            self.process_btn.setEnabled(True if file_list else False)
            
            # 스캔 결과 메시지
            processed_count = self.processed_files_tracker.get_processed_count_in_directory(self.source_directory)
            unprocessed_count = len(self.file_list)
            total_scanned = unprocessed_count + len(self.skipped_files)
            
            status_message = f"총 {total_scanned}개 파일 스캔 완료 (유효: {unprocessed_count}, 스킵: {len(self.skipped_files)}, 이전에 처리됨: {processed_count})"
            QMessageBox.information(self, "스캔 완료", status_message)

        except Exception as e:
            logger.error(f"Error handling scan completion: {e}", exc_info=True)
            self._handle_scan_error(str(e))
            
    def _update_file_display(self):
        """현재 선택된 뷰 모드와 필터에 따라 파일 목록을 업데이트합니다."""
        try:
            self.file_table.setSortingEnabled(False)
            self.file_table.setUpdatesEnabled(False)
            
            current_filter = self.filter_combo.currentData()
            search_text = self.search_edit.text().lower()

            # 원본 목록 결정
            if self.all_files_radio.isChecked():
                source_list = self.file_list + self.skipped_files
            elif self.skipped_files_radio.isChecked():
                source_list = self.skipped_files
            else: # self.valid_files_radio.isChecked()
                source_list = self.file_list
            
            files_to_show = []
            for item in source_list:
                # 파일 정보 일관성 있게 처리
                if isinstance(item, str):
                    file_info = self.file_info_dict.get(item, {"file_name": item, "full_path": os.path.join(self.source_directory, item)})
                else:
                    file_info = item
                
                # 검색 필터
                if search_text and search_text not in file_info.get("file_name", "").lower():
                    continue

                # 처리 상태 필터
                is_processed = self.processed_files_tracker.is_file_processed(file_info.get('full_path', ''))
                if current_filter == "processed" and not is_processed:
                    continue
                if current_filter == "unprocessed" and is_processed:
                    continue

                files_to_show.append(file_info)

            self.file_table.setRowCount(len(files_to_show))
            
            for row, file_info in enumerate(files_to_show):
                full_path = file_info.get("full_path", "")
                is_processed = self.processed_files_tracker.is_file_processed(full_path)
                status_text = "✓ 처리됨" if is_processed else "대기"
                
                # 체크박스
                check_box_widget = QWidget()
                check_box_layout = QHBoxLayout(check_box_widget)
                check_box = QCheckBox()
                check_box_layout.addWidget(check_box)
                check_box_layout.setAlignment(Qt.AlignCenter)
                check_box_layout.setContentsMargins(0, 0, 0, 0)
                self.file_table.setCellWidget(row, 0, check_box_widget)
                check_box.setChecked(not is_processed and "스킵" not in status_text)

                # 파일명
                self.file_table.setItem(row, 1, QTableWidgetItem(file_info.get("file_name", "")))
                
                # 상태
                status_item = QTableWidgetItem(status_text)
                self.file_table.setItem(row, 2, status_item)

                # 시퀀스
                sequence = file_info.get("sequence", "")
                sequence_item = QTableWidgetItem(sequence)
                self.file_table.setItem(row, 3, sequence_item)
                
                # 샷
                shot = file_info.get("shot", "")
                shot_item = QTableWidgetItem(shot)
                self.file_table.setItem(row, 4, shot_item)
                
                # 경과 시간
                elapsed_time = file_info.get("elapsed_time")
                time_item = QTableWidgetItem(f"{elapsed_time:.2f}s" if elapsed_time is not None else "")
                self.file_table.setItem(row, 5, time_item)
                
                # 메시지
                message = file_info.get("message", "")
                message_item = QTableWidgetItem(message)
                self.file_table.setItem(row, 6, message_item)
                
                self._style_table_row(row, is_processed, status_text)

        finally:
            self.file_table.setUpdatesEnabled(True)
            self.file_table.setSortingEnabled(True)
            self._update_file_info_label()

    def _style_table_row(self, row, is_processed, status_text):
        """테이블 행의 스타일을 지정합니다 (색상, 툴팁 등)."""
        palette = get_color_palette()
        editable_bg_color = QColor(palette.get("selection_bg", "#4C566A"))
        processed_color = QColor(palette.get("success", "#A3BE8C"))
        unprocessed_color = QColor(palette.get("warning", "#D08770"))
        error_color = QColor(palette.get("error", "#BF616A"))

        # 시퀀스 및 샷 컬럼 스타일 지정
        sequence_item = self.file_table.item(row, 3)
        shot_item = self.file_table.item(row, 4)
        if sequence_item:
            sequence_item.setBackground(editable_bg_color)
            sequence_item.setToolTip("더블클릭하여 시퀀스를 선택하거나 직접 입력하세요.")
        if shot_item:
            shot_item.setBackground(editable_bg_color)
            shot_item.setToolTip("더블클릭하여 샷을 선택하거나 직접 입력하세요.")

        # 상태에 따른 전체 행 글자색 변경
        color_to_apply = unprocessed_color
        if status_text == "✓ 처리됨":
            color_to_apply = processed_color
        elif "오류" in status_text or "스킵" in status_text:
            color_to_apply = error_color

        for col in range(1, self.file_table.columnCount()): # 체크박스 제외
            item = self.file_table.item(row, col)
            if item:
                item.setForeground(QBrush(color_to_apply))

    def process_files(self):
        """Process selected files."""
        try:
            # 처리된 파일 트래커 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("process_files에서 부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                self.processed_files_tracker = ProcessedFilesTracker()
                logger.debug("process_files에서 ProcessedFilesTracker 인스턴스 새로 생성")

            # Check source directory
            if not self.source_directory or not os.path.isdir(self.source_directory):
                QMessageBox.warning(self, "경고", "유효한 소스 디렉토리를 선택해주세요.")
                return

            # 선택된 파일만 처리
            selected_files = self.get_selected_files()
            if not selected_files:
                QMessageBox.warning(self, "경고", "처리할 파일을 선택해주세요.")
                return

            logger.info(f"Processing {len(selected_files)} selected files")

            # Set up output directory
            if not self.output_directory:
                self.output_directory = self.source_directory

            # 사용자가 선택한 시퀀스
            selected_sequence = None
            if self.use_sequence_cb.isChecked():
                selected_text = self.sequence_combo.currentText()
                if selected_text != "자동 감지":
                    selected_sequence = selected_text

            # Update UI
            self.progress_bar.setVisible(True)
            self.process_btn.setText("처리 중지")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.cancel_processing)
            self.scan_btn.setEnabled(False)

            # Clear file statuses
            for i in range(self.file_table.rowCount()):
                check_box = self.file_table.cellWidget(i, 0).findChild(QCheckBox)
                if check_box and check_box.isChecked():
                    self.file_table.setItem(i, 2, QTableWidgetItem("대기중"))
                    self.file_table.setItem(i, 6, QTableWidgetItem(""))

            # 'processed' 폴더 생성 옵션에 따라 출력 디렉토리 설정
            if self.create_processed_folder_cb.isChecked():
                output_dir = os.path.join(self.output_directory, "processed")
            else:
                output_dir = self.output_directory

            # 스레드 생성
            self.processing_thread = ProcessingThread(
                selected_files,
                self.metadata_extractor,
                sequence_dict=self.sequence_dict,
                selected_sequence=selected_sequence,
                output_directory=output_dir,
                processed_files_tracker=self.processed_files_tracker
            )

            # 시그널 연결
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.file_processed.connect(self.update_file_status)
            self.processing_thread.processing_completed.connect(self.processing_completed)
            self.processing_thread.processing_error.connect(self.processing_error)

            logger.info("Starting file processing thread...")
            self.processing_thread.start()

        except Exception as e:
            logger.error(f"Error starting file processing: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"파일 처리 시작 중 오류가 발생했습니다: {str(e)}")

    def cancel_processing(self):
        """Cancel file processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            logger.info("Canceling file processing")
            self.processing_thread.cancel = True
            self.process_btn.setEnabled(False)
            self.process_btn.setText("취소 중...")

    @pyqtSlot(int, int)
    def update_progress(self, value, total):
        """Update the progress bar."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(value)

    @pyqtSlot(str, str, str, str, str, float)
    def update_file_status(self, file_name, status, sequence, shot, message, elapsed_time):
        """Update the status of a file in the table."""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 1)
            if item and item.text() == file_name:
                self.file_table.setItem(row, 2, QTableWidgetItem(status))
                self.file_table.setItem(row, 3, QTableWidgetItem(sequence))
                self.file_table.setItem(row, 4, QTableWidgetItem(shot))
                time_str = f"{elapsed_time:.2f}s" if elapsed_time > 0 else ""
                self.file_table.setItem(row, 5, QTableWidgetItem(time_str))
                self.file_table.setItem(row, 6, QTableWidgetItem(message))
                
                is_processed = (status == "완료")
                self._style_table_row(row, is_processed, status)
                break

    @pyqtSlot(list)
    def processing_completed(self, processed_files):
        """Handle processing completion."""
        try:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.process_btn.setText("처리 시작")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.process_files)
            self.scan_btn.setEnabled(True)

            success_count = len([f for f in processed_files if f.get("success", False)])
            selected_files_count = len(processed_files)
            logger.info(f"Processing completed: {success_count}/{selected_files_count} files processed successfully")
            
            self._update_file_display() # Refresh table display
            
            # Emit signal
            converted_files = self._convert_files_for_shotgrid(processed_files)
            if converted_files:
                self.files_processed.emit(converted_files)

            QMessageBox.information(
                self, "처리 완료", 
                f"{selected_files_count}개 파일 중 {success_count}개가 성공적으로 처리되었습니다."
            )

        except Exception as e:
            logger.error(f"Error handling processing completion: {e}", exc_info=True)
            
    def _convert_files_for_shotgrid(self, processed_files):
        """Converts processed file info to the format expected by ShotgridTab."""
        converted_files = []
        for file_info in processed_files:
            if file_info.get("success", False):
                converted_file = {
                    "file_name": file_info.get("file_name", ""),
                    "file_path": file_info.get("file_path", ""),
                    "processed_path": file_info.get("output_path", ""),
                    "metadata_path": file_info.get("metadata_path", ""),
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
        """Shotgrid 프로젝트가 변경되었을 때 시퀀스 목록을 업데이트합니다."""
        if not project_name or project_name == "-- 프로젝트 선택 --" or not self.shotgrid_entity_manager:
            return

        try:
            project = self.shotgrid_entity_manager.find_project(project_name)
            if not project:
                logger.warning(f"프로젝트 '{project_name}'을 찾을 수 없습니다")
                return

            sequences = self.shotgrid_entity_manager.get_sequences_in_project(project)
            self.shotgrid_sequence_combo.clear()
            self.shotgrid_sequence_combo.addItem("-- 시퀀스 선택 --")
            for sequence in sequences:
                self.shotgrid_sequence_combo.addItem(sequence['code'])
            logger.info(f"프로젝트 '{project_name}'에서 {len(sequences)}개 시퀀스 로드됨")

        except Exception as e:
            logger.error(f"Shotgrid 프로젝트 변경 처리 중 오류: {e}")

    def scan_directory(self, directory=None, recursive=True, update_ui=True):
        """디렉토리에서 지원하는 파일 스캔"""
        try:
            if not directory:
                directory = self.source_directory

            if not directory or not os.path.isdir(directory):
                logger.error(f"스캔할 디렉토리가 없음: {directory}")
                if update_ui:
                    self._update_file_info_label("유효한 디렉토리를 선택하세요")
                return []

            exclude_processed = self.exclude_processed_cb.isChecked()
            recursive = self.recursive_cb.isChecked()

            logger.info(f"디렉토리 스캔 시작: {directory} (recursive={recursive}, exclude_processed={exclude_processed})")
            if update_ui:
                self._update_file_info_label(f"스캔 중: {directory}...")

            file_infos = self.scanner.scan_directory(directory, recursive, exclude_processed)
            self.skipped_files = self.scanner.get_skipped_files()
            self.file_list = [f for f in file_infos if f not in self.skipped_files]
            
            for info in file_infos:
                self.file_info_dict[info['file_name']] = info

            self.sequence_dict = self.scanner.get_sequence_dict()

            if self.sequence_dict:
                for seq_name in self.sequence_dict.keys():
                    self.add_sequence_if_not_exists(seq_name)

            if update_ui:
                self._update_file_display()

            return file_infos

        except Exception as e:
            if update_ui:
                self._update_file_info_label(f"스캔 오류: {e}")
            logger.error(f"디렉토리 스캔 중 오류 발생: {e}", exc_info=True)
            return []

    def _assign_task_automatically(self, file_path):
        """파일 확장자를 기반으로 자동으로 태스크를 할당합니다."""
        try:
            if not file_path:
                return "comp"  # 기본값

            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.exr', '.hdr'}
            video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}

            if ext in image_extensions:
                return "txtToImage"  # Text to Image
            elif ext in video_extensions:
                return "imgToVideo"  # Image to Video
            else:
                return "comp"  # 기본 컴포지팅 태스크

        except Exception as e:
            logger.error(f"자동 태스크 할당 중 오류 발생: {e}")
            return "comp"  # 오류 발생 시 기본값

    def set_processed_files(self, processed_files):
        """
        Update the status of multiple files after they have been processed,
        typically called from another tab like the Shotgrid upload tab.
        """
        for info in processed_files:
            file_name = info.get("file_name") or os.path.basename(info.get("file_path", ""))
            if not file_name:
                continue

            for row in range(self.file_table.rowCount()):
                if self.file_table.item(row, 1).text() == file_name:
                    self.file_table.setItem(row, 2, QTableWidgetItem(info.get("status", "업로드됨")))
                    self._style_table_row(row, True, "업로드됨")
                    
                    check_box = self.file_table.cellWidget(row, 0).findChild(QCheckBox)
                    if check_box:
                        check_box.setChecked(False)
                    break
                    
    def get_selected_files(self, ignore_checkbox_state=False):
        """테이블에서 선택된 파일 목록을 가져옵니다."""
        selected_files = []
        for row in range(self.file_table.rowCount()):
            check_box = self.file_table.cellWidget(row, 0).findChild(QCheckBox)
            if ignore_checkbox_state or (check_box and check_box.isChecked()):
                file_name_item = self.file_table.item(row, 1)
                if file_name_item:
                    file_name = file_name_item.text()
                    file_info = self.file_info_dict.get(file_name, {}).copy()
                    if not file_info:
                         file_info['full_path'] = os.path.join(self.source_directory, file_name)
                         file_info['file_name'] = file_name

                    # 테이블에서 직접 시퀀스/샷 정보 업데이트
                    seq_item = self.file_table.item(row, 3)
                    shot_item = self.file_table.item(row, 4)
                    if seq_item:
                        file_info['sequence'] = seq_item.text()
                    if shot_item:
                        file_info['shot'] = shot_item.text()
                    selected_files.append(file_info)
        return selected_files
        
    def start_new_batch(self):
        """새로운 배치 작업을 시작합니다 (UI 초기화)."""
        reply = QMessageBox.question(self, '새 배치 시작', 
                                     "현재 파일 목록과 상태를 초기화하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.reset_ui()

    def filter_files(self):
        """검색어와 필터에 따라 파일 목록을 업데이트합니다."""
        self._update_file_display()
        
    def select_all_files(self, select):
        """테이블의 모든 파일 체크박스를 선택/해제합니다."""
        for row in range(self.file_table.rowCount()):
            check_box = self.file_table.cellWidget(row, 0).findChild(QCheckBox)
            if check_box:
                check_box.setChecked(select)
                
    def toggle_all_checkboxes(self, checked):
        """헤더 체크박스 상태에 따라 모든 행의 체크박스 상태를 변경합니다."""
        self.select_all_files(checked)

    def select_unprocessed_files(self):
        """처리되지 않은 모든 파일을 선택합니다."""
        for row in range(self.file_table.rowCount()):
            status_item = self.file_table.item(row, 2)
            check_box = self.file_table.cellWidget(row, 0).findChild(QCheckBox)
            if status_item and check_box:
                is_processed = "처리됨" in status_item.text()
                check_box.setChecked(not is_processed)

    def save_last_directory(self):
        """마지막으로 사용한 디렉토리를 저장합니다."""
        try:
            config_dir = Path.home() / ".shotpipe"
            config_dir.mkdir(exist_ok=True)
            last_dir_file = config_dir / "last_directory.txt"
            with open(last_dir_file, "w") as f:
                f.write(self.source_directory)
        except Exception as e:
            logger.error(f"마지막 디렉토리 저장 실패: {e}")

    def load_last_directory(self):
        """마지막으로 사용한 디렉토리를 불러옵니다."""
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
                        QTimer.singleShot(100, self.scan_files) # UI 로드 후 스캔
        except Exception as e:
            logger.error(f"마지막 디렉토리 로드 실패: {e}")
            
    def _update_file_info_label(self, message=None):
        """파일 스캔 결과 라벨을 업데이트합니다."""
        if message:
            self.file_info_label.setText(message)
            return
            
        valid_count = len(self.file_list)
        skipped_count = len(self.skipped_files)
        total_count = valid_count + skipped_count
        self.file_info_label.setText(
            f"스캔된 총 파일: {total_count} (유효: {valid_count}, 스킵: {skipped_count})"
        )
        
    def export_history(self):
        """처리 이력을 JSON 파일로 내보냅니다."""
        self.processed_files_tracker.export_history()
        QMessageBox.information(self, "성공", f"처리 이력을 {self.processed_files_tracker.history_file_path} 에 저장했습니다.")
        
    def show_history_stats(self):
        """처리 이력 통계를 보여줍니다."""
        stats = self.processed_files_tracker.get_stats()
        stats_str = "\n".join([f"{key}: {value}" for key, value in stats.items()])
        QMessageBox.information(self, "처리 이력 통계", stats_str)

    def reset_history(self):
        """처리 이력을 초기화합니다."""
        reply = QMessageBox.warning(self, "경고", "모든 처리 이력을 영구적으로 삭제하시겠습니까?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.processed_files_tracker.reset_history()
            QMessageBox.information(self, "성공", "처리 이력을 초기화했습니다.")
            self._update_file_display()
            
    # --- Shotgrid Related Methods ---
    def update_shotgrid_status(self):
        """Shotgrid 연결 상태를 확인하고 UI를 업데이트합니다."""
        if self.shotgrid_connector and self.shotgrid_connector.sg:
            self.shotgrid_status_label.setText(f"✅ Shotgrid 연결됨 (사용자: {self.shotgrid_connector.get_user_info()})")
            self.shotgrid_status_label.setStyleSheet("color: #2ECC71;")
        else:
            self.shotgrid_status_label.setText("❌ Shotgrid 연결 끊김")
            self.shotgrid_status_label.setStyleSheet("color: #E74C3C;")

    def auto_load_fixed_project(self):
        """고정된 프로젝트의 시퀀스 및 샷 정보를 자동으로 로드합니다."""
        if self.fixed_project_name:
            self.on_shotgrid_project_changed(self.fixed_project_name)

    def on_fixed_project_sequence_changed(self, sequence_name):
        """고정 프로젝트의 시퀀스가 변경되었을 때 샷 목록을 업데이트합니다."""
        if not sequence_name or sequence_name == "-- 시퀀스 선택 --" or not self.shotgrid_entity_manager:
            self.shotgrid_shot_combo.clear()
            self.shotgrid_shot_combo.addItem("-- 샷 선택 --")
            return

        try:
            project = self.shotgrid_entity_manager.find_project(self.fixed_project_name)
            if project:
                shots = self.shotgrid_entity_manager.get_shots_in_sequence(project, sequence_name)
                self.shotgrid_shot_combo.clear()
                self.shotgrid_shot_combo.addItem("-- 샷 선택 --")
                for shot in shots:
                    self.shotgrid_shot_combo.addItem(shot['code'])
                logger.info(f"시퀀스 '{sequence_name}'에서 {len(shots)}개 샷 로드됨")
        except Exception as e:
            logger.error(f"Shotgrid 샷 로드 중 오류: {e}")
            
    def refresh_shotgrid_data(self):
        """Shotgrid에서 최신 데이터를 새로고침합니다."""
        QMessageBox.information(self, "새로고침", "Shotgrid 데이터를 새로고침합니다...")
        self.auto_load_fixed_project()
        QMessageBox.information(self, "완료", "새로고침이 완료되었습니다.")

    def apply_shotgrid_to_selected(self):
        """선택된 파일들에 Shotgrid 시퀀스/샷 정보를 일괄 적용합니다."""
        selected_sequence = self.shotgrid_sequence_combo.currentText()
        selected_shot = self.shotgrid_shot_combo.currentText()

        if selected_sequence == "-- 시퀀스 선택 --":
            QMessageBox.warning(self, "경고", "적용할 시퀀스를 선택해주세요.")
            return

        selected_rows = [self.file_table.cellWidget(r, 0).findChild(QCheckBox).isChecked() for r in range(self.file_table.rowCount())]
        if not any(selected_rows):
            QMessageBox.warning(self, "경고", "정보를 적용할 파일을 하나 이상 선택해주세요.")
            return

        for row in range(self.file_table.rowCount()):
            if self.file_table.cellWidget(row, 0).findChild(QCheckBox).isChecked():
                self.file_table.setItem(row, 3, QTableWidgetItem(selected_sequence))
                if selected_shot != "-- 샷 선택 --":
                    self.file_table.setItem(row, 4, QTableWidgetItem(selected_shot))
        QMessageBox.information(self, "성공", "선택된 파일에 시퀀스/샷 정보가 적용되었습니다.")
        
    def open_project_settings(self):
        """프로젝트 설정을 위한 다이얼로그를 엽니다."""
        # This can be expanded to a full settings dialog
        text, ok = QInputDialog.getText(self, '고정 프로젝트 설정', 'Shotgrid 프로젝트명을 입력하세요:', text=self.fixed_project_name)
        if ok and text:
            self.fixed_project_name = text
            self.shotgrid_project_label.setText(text)
            # 설정 파일에 저장
            config.set('shotgrid', 'default_project', text)
            config.save()
            QMessageBox.information(self, "저장됨", "프로젝트 설정이 저장되었습니다. 데이터를 새로고침합니다.")
            self.refresh_shotgrid_data()
            
    @pyqtSlot(str)
    def processing_error(self, error_message):
        """Handle processing errors."""
        logger.error(f"File processing error: {error_message}")
        self.progress_bar.setVisible(False)
        self.process_btn.setText("처리 시작")
        self.process_btn.setEnabled(True)
        try:
            self.process_btn.clicked.disconnect()
        except TypeError:
            pass  # 이미 연결이 끊어진 경우
        self.process_btn.clicked.connect(self.process_files)
        self.scan_btn.setEnabled(True)
        QMessageBox.critical(self, "처리 오류", error_message)

    def closeEvent(self, event):
        """Ensure background threads are stopped when the widget is closed."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel = True
            self.processing_thread.wait()  # Wait for thread to finish
        event.accept()

    def _get_skip_reason_display(self, reason_code):
        """스킵 이유 코드에 대한 사용자 친화적인 문자열을 반환합니다."""
        reasons = {
            "processed": "이미 처리됨",
            "unsupported": "지원하지 않는 확장자",
            "temp_file": "임시 파일",
            "small_file": "너무 작은 파일",
            "no_media_stream": "미디어 스트림 없음"
        }
        return reasons.get(reason_code, "알 수 없는 이유")

</rewritten_file> 