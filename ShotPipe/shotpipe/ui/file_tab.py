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
    QApplication, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QBrush
from ..file_processor.processor import ProcessingThread
from ..file_processor.scanner import FileScanner
from ..config import config
from ..file_processor.metadata import MetadataExtractor
from ..utils.processed_files_tracker import ProcessedFilesTracker

logger = logging.getLogger(__name__)

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
        self.processed_files_tracker = ProcessedFilesTracker()  # 초기화
        
        # 스캐너에 ProcessedFilesTracker 설정
        self.scanner.processed_files_tracker = self.processed_files_tracker
        
        self.skipped_files = []  # 초기화
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
            self.reset_history_btn.setStyleSheet("background-color: #FFCCCC;")
            
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
            
            self.file_table = QTableWidget(0, 7)  # 컬럼 수를 5에서 7으로 변경 (체크박스, 파일명, 상태, 시퀀스, 샷, 메세지, 스킵 이유)
            self.file_table.setHorizontalHeaderLabels(["선택", "파일명", "상태", "시퀀스", "샷", "메세지", "스킵 이유"])
            self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 체크박스 컬럼
            self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)  # 파일명 컬럼 - 사용자 조절 가능
            self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Interactive)  # 메세지 컬럼 - 사용자 조절 가능
            self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)  # 스킵 이유 컬럼 - 사용자 조절 가능
            
            # 초기 열 너비 설정 - 파일명과 메세지 열의 기본 너비를 설정
            self.file_table.setColumnWidth(1, 250)  # 파일명 초기 너비: 250픽셀
            self.file_table.setColumnWidth(5, 200)  # 메세지 초기 너비: 200픽셀
            self.file_table.setColumnWidth(6, 150)  # 스킵 이유 초기 너비: 150픽셀
            
            # 헤더 툴팁 설정
            header = self.file_table.horizontalHeader()
            header.setToolTip("컬럼 경계를 드래그하여 너비를 조절할 수 있습니다")
            
            # 헤더의 컨텍스트 메뉴 활성화
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self._show_header_context_menu)
            
            # 정렬 기능 활성화
            self.file_table.setSortingEnabled(True)
            self.file_table.horizontalHeader().setSortIndicatorShown(True)
            
            # 상태 열을 기준으로 내림차순 정렬 (처리되지 않은 파일이 먼저 표시되도록)
            self.file_table.sortItems(2, Qt.AscendingOrder)
            
            # 전체 선택/해제 버튼 추가
            select_layout = QHBoxLayout()
            self.select_all_btn = QPushButton("모두 선택")
            self.select_all_btn.clicked.connect(lambda: self.select_all_files(True))
            self.select_all_btn.setMaximumWidth(100)
            
            self.deselect_all_btn = QPushButton("모두 해제")
            self.deselect_all_btn.clicked.connect(lambda: self.select_all_files(False))
            self.deselect_all_btn.setMaximumWidth(100)
            
            # 처리되지 않은 파일만 선택 버튼 추가
            self.select_unprocessed_btn = QPushButton("미처리 파일만 선택")
            self.select_unprocessed_btn.clicked.connect(self.select_unprocessed_files)
            self.select_unprocessed_btn.setMaximumWidth(150)
            
            select_layout.addWidget(self.select_all_btn)
            select_layout.addWidget(self.deselect_all_btn)
            select_layout.addWidget(self.select_unprocessed_btn)
            select_layout.addStretch()
            
            main_layout.addLayout(select_layout)
            
            self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.file_table.setEditTriggers(QTableWidget.NoEditTriggers)
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
                dir_name = os.path.basename(directory)
                if dir_name:
                    self.add_sequence_if_not_exists(dir_name.upper())
                
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
        self.sequence_combo.clear()
    
    def toggle_sequence_combo(self, enabled):
        """Toggle sequence combo box enabled state based on source selection."""
        self.sequence_combo.setEnabled(enabled)
        
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
            self.file_table.setColumnWidth(column_index, 250)
        elif column_index == 5:  # 메세지 컬럼
            self.file_table.setColumnWidth(column_index, 200)
        elif column_index == 6:  # 스킵 이유 컬럼
            self.file_table.setColumnWidth(column_index, 150)
        else:
            # 기타 열은 ResizeToContents로 설정된 컬럼이므로 자동 조정
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Interactive)
    
    def _reset_all_column_widths(self):
        """모든 열의 너비를 기본값으로 초기화합니다."""
        # 선택 열
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # 파일명 열
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.file_table.setColumnWidth(1, 250)
        
        # 상태, 시퀀스, 샷 열
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 메세지 열
        self.file_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Interactive)
        self.file_table.setColumnWidth(5, 200)
        
        # 스킵 이유 열
        self.file_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)
        self.file_table.setColumnWidth(6, 150)
    
    def scan_files(self):
        """Scan files in the source directory."""
        try:
            # 처리된 파일 추적기 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
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
                    import time
                    start_time = time.time()
                    
                    logger.info(f"스캔 스레드 시작 - 디렉토리: {self.directory}")
                    logger.debug(f"스캔 옵션: recursive={self.recursive}, exclude_processed={self.exclude_processed}")
                    
                    # 생성자에서 전달받은 옵션 사용
                    files = self.scanner.scan_directory(
                        self.directory, 
                        recursive=self.recursive,
                        exclude_processed=self.exclude_processed
                    )
                    
                    # 파일 유형별 통계 계산
                    file_types = {}
                    total_size = 0
                    
                    # 파일 이름 및 정보 딕셔너리 생성
                    file_list = []
                    file_info_dict = {}
                    
                    for file_info in files:
                        file_name = file_info["file_name"]
                        file_list.append(file_name)
                        file_info_dict[file_name] = file_info
                        
                        # 통계 데이터 수집
                        file_type = file_info.get("file_type", "unknown")
                        file_size = file_info.get("file_size", 0)
                        
                        if file_type not in file_types:
                            file_types[file_type] = 0
                        file_types[file_type] += 1
                        total_size += file_size
                    
                    elapsed_time = time.time() - start_time
                    
                    # 상세 로그 추가
                    logger.info(f"스캔 완료: 총 {len(file_list)}개 파일 발견 (소요 시간: {elapsed_time:.2f}초)")
                    
                    if file_types:
                        logger.info(f"파일 유형 통계: {file_types}")
                    
                    # 총 파일 크기를 MB 단위로 변환
                    total_size_mb = total_size / (1024 * 1024)
                    logger.info(f"총 파일 크기: {total_size_mb:.2f} MB")
                    
                    # 첫 10개 파일 목록 출력 (너무 많은 로그 방지)
                    if file_list:
                        sample_files = file_list[:min(10, len(file_list))]
                        logger.debug(f"발견된 파일 샘플: {sample_files}")
                        if len(file_list) > 10:
                            logger.debug(f"... 외 {len(file_list) - 10}개 파일")
                    
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
        """스캔 완료 후 테이블 업데이트"""
        try:
            # 처리된 파일 트래커 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("_handle_scan_completed에서 부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
                self.processed_files_tracker = ProcessedFilesTracker()
                logger.debug("_handle_scan_completed에서 ProcessedFilesTracker 인스턴스 새로 생성")
                
            # 스캔 결과 저장
            self.file_list = file_list
            self.file_info_dict = file_info_dict
            
            # 스킵된 파일 정보 저장
            self.skipped_files = self.scanner.get_skipped_files()
            
            # Auto-detect sequences
            self.sequence_dict = self.scanner.get_sequence_dict()
            
            # Update sequence combo
            if self.sequence_dict:
                # Get unique sequence names
                sequence_names = list(self.sequence_dict.keys())
                
                # Clear and repopulate sequence combo
                self.sequence_combo.clear()
                self.sequence_combo.addItem("자동 감지")
                
                for seq_name in sorted(sequence_names):
                    self.sequence_combo.addItem(seq_name)
            
            # Set LIG as default after populating
            lig_index = self.sequence_combo.findText("LIG")
            if lig_index >= 0:
                self.sequence_combo.setCurrentIndex(lig_index)
            
            # 테이블 UI 업데이트 준비
            self.file_table.setSortingEnabled(False)  # 정렬 일시 중지
            self.file_table.setUpdatesEnabled(False)  # 화면 업데이트 일시 중지
            
            # 진행 표시줄 설정
            total_files = len(self.file_list)
            self.progress_bar.setRange(0, total_files if total_files > 0 else 100)
            self.progress_bar.setValue(0)
            
            # Populate the table
            self.file_table.setRowCount(total_files)

            # 이미 처리된 파일 확인을 위한 처리된 파일 목록 가져오기
            processed_files = self.processed_files_tracker.get_processed_files_in_directory(self.source_directory)
            processed_files_basenames = [os.path.basename(f) for f in processed_files]
            
            # 처리된 파일과 미처리 파일 카운트
            processed_count = 0
            unprocessed_count = 0
            
            # 배치 크기로 테이블 채우기 (UI 응답성 유지)
            batch_size = 100  # 한 번에 업데이트할 행 수
            
            # 기본 텍스트 색상 설정
            dark_text_color = QColor(0, 0, 0)  # 검은색
            gray_text_color = QColor(80, 80, 80)  # 회색
            blue_text_color = QColor(0, 0, 180)  # 파란색
            green_text_color = QColor(0, 128, 0)  # 녹색
            
            for i in range(0, total_files, batch_size):
                end_idx = min(i + batch_size, total_files)
                
                for j in range(i, end_idx):
                    file_name = self.file_list[j]
                    file_path = os.path.join(self.source_directory, file_name)
                    is_processed = self.processed_files_tracker.is_file_processed(file_path) or file_name in processed_files_basenames
                    
                    # 처리 상태 카운트 업데이트
                    if is_processed:
                        processed_count += 1
                    else:
                        unprocessed_count += 1
                    
                    # 이미 처리된 파일인 경우 행 전체에 배경색 적용
                    row_background = QColor(240, 240, 240) if is_processed else QColor(255, 255, 255)
                    
                    # 체크박스 아이템
                    check_item = QTableWidgetItem()
                    check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    
                    # 기본적으로 모든 파일 선택 해제 상태로 설정, 처리되지 않은 파일만 선택
                    check_item.setCheckState(Qt.Unchecked)  # 기본적으로 모든 파일 선택 해제
                    if not is_processed:
                        check_item.setCheckState(Qt.Checked)  # 처리되지 않은 파일만 선택
                    
                    check_item.setBackground(row_background)
                    self.file_table.setItem(j, 0, check_item)
                    
                    # File name (1번 인덱스)
                    file_name_item = QTableWidgetItem(file_name)
                    if is_processed:
                        # 이미 처리된 파일은 폰트 색상 변경
                        file_name_item.setForeground(gray_text_color)
                    else:
                        # 미처리 파일은 검은색으로 설정
                        file_name_item.setForeground(dark_text_color)
                    # 배경색 적용
                    file_name_item.setBackground(row_background)
                    self.file_table.setItem(j, 1, file_name_item)
                    
                    # Status (2번 인덱스)
                    if is_processed:
                        status_item = QTableWidgetItem("✓ 처리됨")
                        status_item.setForeground(green_text_color)
                    else:
                        status_item = QTableWidgetItem("대기중")
                        status_item.setForeground(blue_text_color)
                    status_item.setBackground(row_background)
                    self.file_table.setItem(j, 2, status_item)
                    
                    # Sequence and shot (3번, 4번 인덱스)
                    if self.use_sequence_cb.isChecked():
                        # Try to find sequence info
                        sequence_found = False
                        for seq_name, files in self.sequence_dict.items():
                            for seq_file, seq_shot in files:
                                if seq_file == file_name:
                                    seq_item = QTableWidgetItem(seq_name)
                                    shot_item = QTableWidgetItem(seq_shot)
                                    
                                    seq_item.setForeground(gray_text_color if is_processed else dark_text_color)
                                    shot_item.setForeground(gray_text_color if is_processed else dark_text_color)
                                    seq_item.setBackground(row_background)
                                    shot_item.setBackground(row_background)
                                    
                                    self.file_table.setItem(j, 3, seq_item)
                                    self.file_table.setItem(j, 4, shot_item)
                                    sequence_found = True
                                    break
                            if sequence_found:
                                break
                    
                    # Message (5번 인덱스)
                    if is_processed:
                        message_item = QTableWidgetItem("이미 처리된 파일입니다")
                    else:
                        message_item = QTableWidgetItem("")
                    message_item.setForeground(gray_text_color if is_processed else dark_text_color)
                    message_item.setBackground(row_background)
                    self.file_table.setItem(j, 5, message_item)
                
                # 부분 업데이트 후 UI 반응성 유지를 위해 이벤트 처리
                self.progress_bar.setValue(end_idx)
                QApplication.processEvents()
            
            # UI 설정 복원
            self.file_table.setUpdatesEnabled(True)
            
            # 처리 상태에 따라 정렬할 수 있도록 설정
            self.file_table.setSortingEnabled(True)
            
            # 행 높이 조정
            self.file_table.resizeRowsToContents()
            
            # Enable buttons
            self.process_btn.setEnabled(True)
            
            # 진행 표시줄 초기화
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")
            
            # 파일 스캔 결과 표시
            self._update_file_info_label()
            
            if total_files > 0:
                status_message = f"총 {total_files}개 파일 발견 (처리됨: {processed_count}, 미처리: {unprocessed_count}, 스킵됨: {len(self.skipped_files)}개)"
                QMessageBox.information(self, "스캔 완료", status_message)
            
        except Exception as e:
            # 에러 발생 시 UI 복원
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("파일 스캔")
            
            logger.error(f"Error updating table: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"테이블 업데이트 중 오류가 발생했습니다: {str(e)}")
    
    def process_files(self):
        """Process selected files."""
        try:
            # 처리된 파일 트래커 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("process_files에서 부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
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
                
            logger.info(f"Processing {len(selected_files)} selected files of {len(self.file_list)} total files")
            
            # Set up output directory
            if not self.output_directory:
                # If no output directory is specified, use source directory
                self.output_directory = self.source_directory
                
            # 파일 경로 목록 생성
            file_paths = [os.path.join(self.source_directory, file_name) for file_name in selected_files]
            
            # 사용자가 선택한 시퀀스 (시퀀스 사용이 체크된 경우에만)
            selected_sequence = None
            if self.use_sequence_cb.isChecked():
                selected_text = self.sequence_combo.currentText()
                if selected_text != "자동 감지":
                    selected_sequence = selected_text
            
            # 메타데이터 추출기 생성
            metadata_extractor = MetadataExtractor()
                
            # Create ProcessingThread
            self.processing_thread = ProcessingThread(
                file_paths=file_paths,
                metadata_extractor=metadata_extractor,
                sequence_dict=self.sequence_dict, 
                selected_sequence=selected_sequence,
                output_directory=self.output_directory,
                processed_files_tracker=self.processed_files_tracker  # 처리된 파일 추적기 전달
            )
            
            # Connect signals
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.file_processed.connect(self.update_file_status)
            self.processing_thread.processing_completed.connect(self.processing_completed)
            self.processing_thread.processing_error.connect(self.processing_error)
            
            # Update UI
            self.progress_bar.setVisible(True)
            self.process_btn.setText("취소")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.cancel_processing)
            self.scan_btn.setEnabled(False)
            
            # Clear file statuses
            for i in range(self.file_table.rowCount()):
                file_name = self.file_table.item(i, 1).text()  # 파일명은 이제 1번 인덱스
                if file_name in selected_files:
                    self.file_table.setItem(i, 2, QTableWidgetItem("대기중"))  # 상태는 이제 2번 인덱스
                    self.file_table.setItem(i, 5, QTableWidgetItem(""))  # 메세지는 이제 5번 인덱스
            
            # Start processing
            logger.info("Starting file processing")
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
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """Update the progress bar.
        
        Args:
            value (int): Progress value (0-100)
        """
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str, str, str, str, str)
    def update_file_status(self, file_name, status, sequence, shot, message):
        """파일 처리 상태 업데이트
        
        Args:
            file_name (str): 파일명
            status (str): 상태
            sequence (str): 시퀀스
            shot (str): 샷
            message (str): 메시지
        """
        try:
            # 행 찾기
            for i in range(self.file_table.rowCount()):
                if self.file_table.item(i, 1).text() == file_name:  # 파일명은 1번 인덱스
                    # 상태 업데이트 및 색상 설정
                    status_item = QTableWidgetItem(status)
                    if status == "완료":
                        status_item.setBackground(QColor(200, 255, 200))  # 연한 초록색
                        status_item.setToolTip("파일이 성공적으로 처리되었습니다")
                    elif status == "실패":
                        status_item.setBackground(QColor(255, 200, 200))  # 연한 빨간색
                        status_item.setToolTip("파일 처리 중 오류가 발생했습니다")
                    elif status == "대기중":
                        status_item.setBackground(QColor(230, 230, 255))  # 연한 파란색
                        status_item.setToolTip("파일이 처리 대기 중입니다")
                    elif status == "처리중":
                        status_item.setBackground(QColor(255, 255, 200))  # 연한 노란색
                        status_item.setToolTip("파일을 처리하고 있습니다")
                    elif status == "이미처리됨":
                        status_item.setBackground(QColor(220, 220, 220))  # 연한 회색
                        status_item.setToolTip("이 파일은 이미 처리되었습니다")
                        
                    self.file_table.setItem(i, 2, status_item)  # 상태는 2번 인덱스
                    
                    # 시퀀스 업데이트
                    if sequence:
                        self.file_table.setItem(i, 3, QTableWidgetItem(sequence))  # 시퀀스는 3번 인덱스
                    
                    # 샷 업데이트
                    if shot:
                        self.file_table.setItem(i, 4, QTableWidgetItem(shot))  # 샷은 4번 인덱스
                    
                    # 메시지 업데이트
                    message_item = QTableWidgetItem(message)
                    message_item.setToolTip(message)  # 긴 메시지도 툴팁으로 볼 수 있게 함
                    self.file_table.setItem(i, 5, message_item)  # 메시지는 5번 인덱스
                    break
        
        except Exception as e:
            logger.error(f"Error updating file status: {e}", exc_info=True)
    
    @pyqtSlot(list)
    def processing_completed(self, processed_files):
        """Handle processing completion.
        
        Args:
            processed_files (list): List of processed files
        """
        try:
            # Reset UI
            self.progress_bar.setValue(100)
            self.process_btn.setText("처리 시작")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.process_files)
            self.scan_btn.setEnabled(True)
            
            # Show message
            success_count = len([f for f in processed_files if f.get("success", False)])
            total_count = len(self.file_list)
            
            logger.info(f"Processing completed: {success_count}/{total_count} files processed successfully")
            logger.debug(f"Processed files: {processed_files}")
            
            # 처리 완료 후 이미 처리된 파일 체크박스 선택 해제
            for i in range(self.file_table.rowCount()):
                file_name = self.file_table.item(i, 1).text()
                for proc_file in processed_files:
                    if proc_file.get("file_name") == file_name and proc_file.get("success", False):
                        # 체크박스 해제
                        check_item = self.file_table.item(i, 0)
                        if check_item:
                            check_item.setCheckState(Qt.Unchecked)
                            logger.debug(f"파일 처리 완료 후 선택 해제: {file_name}")
                            break
            
            # Convert processed files to format expected by ShotgridTab
            try:
                converted_files = []
                for file_info in processed_files:
                    if file_info.get("success", False):
                        # 파일명과 경로 정보 가져오기
                        file_name = file_info.get("file_name", "")
                        file_path = file_info.get("file_path", "")
                        processed_path = file_info.get("output_path", file_path)
                        metadata_path = file_info.get("metadata_path", "")
                        
                        # 메타데이터에서 시퀀스와 샷 정보 가져오기
                        sequence = file_info.get("sequence", "")
                        shot = file_info.get("shot", "")
                        
                        # 메타데이터가 있을 경우 추가 정보 추출
                        metadata = file_info.get("metadata", {})
                        if not sequence and "sequence" in metadata:
                            sequence = metadata.get("sequence", "")
                        if not shot and "shot" in metadata:
                            shot = metadata.get("shot", "")
                        
                        logger.debug(f"Converting file: {file_name}, seq: {sequence}, shot: {shot}")
                        
                        # Create a file info dict in the format expected by ShotgridTab
                        converted_file = {
                            "file_name": file_name,
                            "file_path": file_path,
                            "processed_path": processed_path,
                            "metadata_path": metadata_path,
                            "sequence": sequence,
                            "shot": shot,
                            "task": file_info.get("task", "comp"),  # 파일 처리 시 결정된 태스크 사용
                            "version": file_info.get("version", "v001"),  # 파일 처리 시 결정된 버전 정보 사용
                            "processed": True,
                            "metadata": metadata,
                            "batch_path": file_info.get("batch_path", "")  # 배치 폴더 경로 추가
                        }
                        converted_files.append(converted_file)
                
                # Emit signal with converted files
                if converted_files:
                    logger.info(f"Sending {len(converted_files)} processed files to Shotgrid tab")
                    for cf in converted_files:
                        logger.debug(f"Converted file: {cf['file_name']}, seq: {cf['sequence']}, shot: {cf['shot']}")
                    self.files_processed.emit(converted_files)
                else:
                    logger.warning("No successfully processed files to send to Shotgrid tab")
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"Error converting processed files: {e}\n{error_trace}")
            
            if success_count == total_count:
                QMessageBox.information(
                    self, 
                    "처리 완료", 
                    f"모든 파일 ({total_count}개)이 성공적으로 처리되었습니다."
                )
            else:
                QMessageBox.warning(
                    self, 
                    "처리 완료", 
                    f"{total_count}개 파일 중 {success_count}개가 성공적으로 처리되었습니다."
                )
            
        except Exception as e:
            logger.error(f"Error handling processing completion: {e}", exc_info=True)
    
    @pyqtSlot(str)
    def processing_error(self, error_message):
        """Handle processing error.
        
        Args:
            error_message (str): Error message
        """
        try:
            # Reset UI
            self.progress_bar.setValue(0)
            self.process_btn.setText("처리 시작")
            self.process_btn.clicked.disconnect()
            self.process_btn.clicked.connect(self.process_files)
            self.scan_btn.setEnabled(True)
            
            # Show error message
            logger.error(f"Processing error: {error_message}")
            QMessageBox.critical(self, "처리 오류", error_message)
            
        except Exception as e:
            logger.error(f"Error handling processing error: {e}", exc_info=True)

    def load_custom_sequences(self):
        """저장된 사용자 정의 시퀀스와 최근 사용 시퀀스를 로드"""
        try:
            sequences_file = os.path.expanduser("~/.shotpipe/sequences.json")
            
            # 파일이 존재하지 않으면 종료
            if not os.path.exists(sequences_file):
                logger.debug("No saved sequences file found")
                return
            
            # JSON 파일 로드
            with open(sequences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 버전 확인
            version = data.get("version", "1.0")
            
            # 버전에 따라 다른 방식으로 로드
            if version == "1.0":
                sequences = data.get("sequences", [])
                recent_sequence = data.get("recent_sequence", "")
                
                # 콤보박스에 저장된 시퀀스 추가
                for seq in sequences:
                    if seq and seq != "자동 감지" and self.sequence_combo.findText(seq) < 0:
                        self.sequence_combo.addItem(seq)
                
                # 최근 사용 시퀀스가 있으면 선택
                if recent_sequence and recent_sequence != "자동 감지":
                    index = self.sequence_combo.findText(recent_sequence)
                    if index >= 0:
                        self.sequence_combo.setCurrentIndex(index)
                
                logger.debug(f"Loaded {len(sequences)} custom sequences, recent: '{recent_sequence}'")
            else:
                logger.warning(f"Unknown sequences data version: {version}")
        
        except Exception as e:
            logger.error(f"Error loading custom sequences: {e}")

    def update_recent_sequence(self, sequence):
        """최근 사용한 시퀀스 업데이트 및 저장"""
        if not sequence or sequence == "자동 감지":
            return
        
        # 시퀀스가 이미 콤보박스에 있는지 확인
        if sequence not in [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count())]:
            # 없으면 추가
            self.sequence_combo.addItem(sequence)
        
        # 해당 시퀀스로 콤보박스 선택 변경
        index = self.sequence_combo.findText(sequence)
        if index >= 0:
            self.sequence_combo.setCurrentIndex(index)
        
        # 시퀀스 저장
        self.save_custom_sequences()
        logger.debug(f"Updated recent sequence to: {sequence}")

    def save_custom_sequences(self):
        """사용자 정의 시퀀스와 최근 사용 시퀀스를 JSON 파일에 저장"""
        try:
            # 시퀀스 디렉토리 확인 및 생성
            os.makedirs(os.path.expanduser("~/.shotpipe"), exist_ok=True)
            
            # 현재 콤보박스에서 모든 시퀀스 추출 (자동 감지 제외)
            sequences = [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count()) 
                         if self.sequence_combo.itemText(i) != "자동 감지"]
            
            # 현재 선택된 시퀀스 (자동 감지가 아닌 경우)
            current_sequence = self.sequence_combo.currentText()
            if current_sequence == "자동 감지":
                current_sequence = ""
            
            # 저장할 데이터 구성
            data = {
                "version": "1.0",
                "sequences": sequences,
                "recent_sequence": current_sequence
            }
            
            # JSON 파일에 저장
            with open(os.path.expanduser("~/.shotpipe/sequences.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved {len(sequences)} custom sequences and recent sequence '{current_sequence}'")
        except Exception as e:
            logger.error(f"Error saving custom sequences: {e}")

    def add_custom_sequence(self):
        """Add custom sequence from input field to combo box and save."""
        sequence_name = self.sequence_combo.currentText().strip()
        
        # 입력 검증
        if not sequence_name:
            return
            
        if sequence_name == "자동 감지":
            QMessageBox.warning(self, "시퀀스 추가 불가", 
                              "'자동 감지'는 예약된 이름으로 사용할 수 없습니다.", 
                              QMessageBox.Ok)
            return
            
        # 시퀀스 이름 형식 검증 (특수문자 제한)
        invalid_chars = r'[\\/*?:"<>|]'
        if re.search(invalid_chars, sequence_name):
            QMessageBox.warning(self, "잘못된 형식", 
                              "시퀀스 이름에 다음과 같은 특수문자를 사용할 수 없습니다: \\ / * ? : \" < > |", 
                              QMessageBox.Ok)
            return
        
        # 중복 확인
        if self.sequence_combo.findText(sequence_name) >= 0:
            # 이미 존재하는 경우 사용자에게 알림
            reply = QMessageBox.question(self, "중복된 시퀀스", 
                                     f"'{sequence_name}'은(는) 이미 존재합니다. 선택하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.sequence_combo.setCurrentText(sequence_name)
                self.update_recent_sequence(sequence_name)
            return

        # 새 시퀀스 추가
        self.sequence_combo.addItem(sequence_name)
        self.sequence_combo.setCurrentText(sequence_name)
        self.save_custom_sequences()
        
        logger.info(f"Added custom sequence: {sequence_name}")
        
        # 사용자에게 추가 완료 알림
        QMessageBox.information(self, "시퀀스 추가", 
                             f"'{sequence_name}' 시퀀스가 추가되었습니다.", 
                             QMessageBox.Ok)

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
            self.update_sequence_combo_from_directory(self.source_directory)
        else:
            # 첫 번째 항목 선택 (자동 감지)
            self.sequence_combo.setCurrentIndex(0)

    def on_sequence_changed(self, text):
        """시퀀스 콤보박스의 값이 변경되면 호출"""
        if text and text != "자동 감지":
            # 현재 시퀀스 저장
            self.update_recent_sequence(text)
            
            # 사용자가 새 시퀀스를 입력한 경우 콤보박스에 추가
            if text not in [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count())]:
                self.sequence_combo.addItem(text)
                self.sequence_combo.setCurrentText(text)
                # 커스텀 시퀀스 저장
                self.save_custom_sequences()
                logger.debug(f"Added new sequence: {text}")

    def select_all_files(self, select):
        """모든 파일 선택/해제"""
        for row in range(self.file_table.rowCount()):
            check_item = self.file_table.item(row, 0)
            if check_item:
                check_item.setCheckState(Qt.Checked if select else Qt.Unchecked)

    def get_selected_files(self):
        """선택된 파일 목록 반환"""
        selected_files = []
        for i in range(self.file_table.rowCount()):
            check_item = self.file_table.item(i, 0)
            if check_item and check_item.checkState() == Qt.Checked:
                file_name = self.file_table.item(i, 1).text()  # 파일명 컬럼은 1번 인덱스
                selected_files.append(file_name)
        return selected_files

    def browse_source_directory(self):
        """Browse for source directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "소스 디렉토리 선택", self.source_edit.text()
        )
        if directory:
            self.source_edit.setText(directory)
            self.source_directory = directory
            # 소스 디렉토리가 선택되면 시퀀스 콤보박스에 디렉토리명 추가 및 선택
            self.update_sequence_combo_from_directory(directory)
            # 디렉토리에서 파일 스캔
            self.scan_files()
            
    def update_sequence_combo_from_directory(self, directory):
        """디렉토리명을 시퀀스 콤보박스에 추가하고 선택합니다."""
        if not directory:
            return
            
        # 디렉토리명 추출
        dir_name = os.path.basename(directory)
        if not dir_name:  # 경로가 '/'로 끝나는 경우
            dir_name = os.path.basename(os.path.dirname(directory))
            
        # 콤보박스에 해당 항목이 있는지 확인
        index = self.sequence_combo.findText(dir_name)
        
        # 없으면 추가
        if index == -1:
            self.sequence_combo.addItem(dir_name)
            index = self.sequence_combo.findText(dir_name)
            
        # 디렉토리명 시퀀스 선택
        self.sequence_combo.setCurrentIndex(index)
        logger.info(f"디렉토리 '{dir_name}'을 시퀀스로 설정했습니다.")

    def select_unprocessed_files(self):
        """미처리된 파일만 선택"""
        for row in range(self.file_table.rowCount()):
            status_item = self.file_table.item(row, 2)  # 상태 컬럼
            check_item = self.file_table.item(row, 0)  # 체크박스 컬럼
            
            if check_item and status_item:
                # "대기중" 상태인 파일만 선택
                if status_item.text() == "대기중":
                    check_item.setCheckState(Qt.Checked)
                else:
                    check_item.setCheckState(Qt.Unchecked)

    def start_new_batch(self):
        """새 배치 생성"""
        try:
            # 처리된 파일 트래커 접근 방식 수정
            if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
                self.processed_files_tracker = self.parent.app.processed_files_tracker
                logger.debug("start_new_batch에서 부모 앱의 ProcessedFilesTracker 인스턴스 사용")
            elif self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
                self.processed_files_tracker = ProcessedFilesTracker()
                logger.debug("start_new_batch에서 ProcessedFilesTracker 인스턴스 새로 생성")
            
            if not self.output_directory:
                QMessageBox.warning(self, "경고", "출력 디렉토리가 설정되지 않았습니다.")
                return
                
            # 새 배치 생성
            new_batch_dir = self.processed_files_tracker.create_new_batch(self.output_directory)
            
            # 사용자에게 알림
            QMessageBox.information(
                self, 
                "새 배치 생성", 
                f"새 배치 폴더가 생성되었습니다:\n{new_batch_dir}"
            )
            
            logger.info(f"새 배치 폴더 생성됨: {new_batch_dir}")
            
        except Exception as e:
            logger.error(f"새 배치 생성 오류: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"새 배치 생성 중 오류가 발생했습니다: {str(e)}")

    def load_last_directory(self):
        """마지막으로 사용한 디렉토리 로드"""
        try:
            # ~/.shotpipe/last_directory.txt 파일에서 마지막 디렉토리 읽기
            last_dir_file = os.path.join(os.path.expanduser("~/.shotpipe"), "last_directory.txt")
            
            if os.path.exists(last_dir_file):
                with open(last_dir_file, 'r') as f:
                    last_dir = f.read().strip()
                
                if last_dir and os.path.isdir(last_dir):
                    self.source_directory = last_dir
                    self.output_directory = last_dir
                    self.source_edit.setText(last_dir)
                    self.output_edit.setText(last_dir)
                    
                    # 디렉토리 설정 후 자동 스캔 진행
                    QTimer.singleShot(500, self.scan_files)
                    
                    logger.info(f"마지막으로 사용한 디렉토리 로드됨: {last_dir}")
                    
        except Exception as e:
            logger.error(f"마지막 디렉토리 로드 중 오류: {e}")
    
    def save_last_directory(self):
        """현재 디렉토리를 마지막으로 사용한 디렉토리로 저장"""
        try:
            if not self.source_directory:
                return
                
            last_dir_file = os.path.join(os.path.expanduser("~/.shotpipe"), "last_directory.txt")
            os.makedirs(os.path.dirname(last_dir_file), exist_ok=True)
            
            with open(last_dir_file, 'w') as f:
                f.write(self.source_directory)
                
            logger.debug(f"현재 디렉토리 저장됨: {self.source_directory}")
            
        except Exception as e:
            logger.error(f"디렉토리 저장 중 오류: {e}")

    def add_sequence_if_not_exists(self, sequence_name):
        """시퀀스 콤보박스에 시퀀스가 없으면 추가"""
        if not sequence_name:
            return
            
        # 시퀀스 콤보박스에 이미 있는지 확인
        index = self.sequence_combo.findText(sequence_name)
        if index < 0:
            # 없으면 추가
            self.sequence_combo.addItem(sequence_name)
            logger.debug(f"시퀀스 추가됨: {sequence_name}")
            
            # 새로 추가된 시퀀스 선택
            index = self.sequence_combo.findText(sequence_name)
            if index >= 0:
                self.sequence_combo.setCurrentIndex(index)

    def filter_files(self):
        """현재 검색어와 필터 설정에 따라 파일 테이블을 필터링합니다."""
        search_text = self.search_edit.text().lower()
        filter_option = self.filter_combo.currentData()
        
        # 테이블의 모든 행을 확인하여 필터 조건 적용
        for row in range(self.file_table.rowCount()):
            file_name_item = self.file_table.item(row, 1)  # 파일명 열
            status_item = self.file_table.item(row, 2)     # 상태 열
            
            if not file_name_item or not status_item:
                continue
                
            file_name = file_name_item.text().lower()
            status = status_item.text()
            
            # 1. 검색어 필터
            matches_search = True if not search_text else search_text in file_name
            
            # 2. 상태 필터
            matches_status = True
            if filter_option == "processed":
                matches_status = "처리됨" in status
            elif filter_option == "unprocessed":
                matches_status = "대기중" in status
            
            # 두 조건 모두 만족하면 행 표시, 아니면 숨김
            self.file_table.setRowHidden(row, not (matches_search and matches_status))
            
        # 필터링 후 카운트 정보 업데이트
        visible_count = sum(1 for row in range(self.file_table.rowCount()) 
                           if not self.file_table.isRowHidden(row))
        logger.debug(f"필터링 결과: {visible_count}개 파일 표시됨")

    def export_history(self):
        """이력 데이터를 CSV 파일로 내보내기"""
        # 처리된 파일 트래커 접근 방식 수정
        if hasattr(self.parent, 'app') and hasattr(self.parent.app, 'processed_files_tracker'):
            self.processed_files_tracker = self.parent.app.processed_files_tracker
        elif self.processed_files_tracker is None:
            from ..utils.processed_files_tracker import ProcessedFilesTracker
            self.processed_files_tracker = ProcessedFilesTracker()
            logger.debug("export_history에서 ProcessedFilesTracker 인스턴스 새로 생성")
            
        # 저장할 파일 위치 선택
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "이력 내보내기",
            os.path.expanduser("~") + "/shotpipe_history.csv",
            "CSV 파일 (*.csv)"
        )
        
        if not file_path:
            return
            
        # 처리된 파일 트래커에서 내보내기 함수 호출
        export_path = self.processed_files_tracker.export_history(file_path)
        
        if export_path:
            QMessageBox.information(
                self,
                "내보내기 완료",
                f"이력 데이터가 성공적으로 내보내졌습니다:\n{export_path}"
            )
        else:
            QMessageBox.warning(
                self,
                "내보내기 실패",
                "이력 데이터를 내보내는 중 오류가 발생했습니다."
            )
    
    def show_history_stats(self):
        """이력 통계 표시"""
        try:
            # 처리된 파일 트래커 인스턴스 접근
            if self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
                self.processed_files_tracker = ProcessedFilesTracker()
            
            # 이력 통계 가져오기
            stats = self.processed_files_tracker.get_history_stats()
            
            # 통계 텍스트 구성
            stats_text = f"총 처리된 파일 수: {stats['total_files']}개\n\n"
            
            # 상태별 통계 (새로 추가됨)
            stats_text += "처리 상태별 통계:\n"
            if stats['status']:
                for status, count in sorted(stats['status'].items()):
                    stats_text += f"  {status}: {count}개\n"
            else:
                stats_text += "  (데이터 없음)\n"
            
            # 시퀀스별 통계
            stats_text += "\n시퀀스별 통계:\n"
            if stats['sequences']:
                for seq, count in sorted(stats['sequences'].items(), key=lambda x: x[1], reverse=True):
                    stats_text += f"  {seq}: {count}개\n"
            else:
                stats_text += "  (데이터 없음)\n"
            
            stats_text += "\n배치별 통계:\n"
            if stats['batches']:
                for batch, count in sorted(stats['batches'].items(), key=lambda x: x[0]):
                    stats_text += f"  {batch}: {count}개\n"
            else:
                stats_text += "  (데이터 없음)\n"
            
            # 대화상자 표시
            QMessageBox.information(self, "처리 이력 통계", stats_text)
            
        except Exception as e:
            logger.error(f"이력 통계 표시 중 오류 발생: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"이력 통계 표시 중 오류가 발생했습니다: {str(e)}")
            
    def reset_history(self):
        """Reset all processed files history."""
        try:
            # 확인 대화상자 표시
            reply = QMessageBox.question(
                self, 
                "이력 초기화 확인", 
                "모든 처리된 파일 이력을 초기화하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 처리된 파일 트래커 인스턴스 접근
            if self.processed_files_tracker is None:
                from ..utils.processed_files_tracker import ProcessedFilesTracker
                self.processed_files_tracker = ProcessedFilesTracker()
            
            # 이력 초기화
            history_file_path = self.processed_files_tracker.history_file
            result = self.processed_files_tracker.reset_history()
            
            if result:
                # 백업 파일 생성 (명시적인 백업을 위해)
                import shutil
                from datetime import datetime
                backup_file = f"{history_file_path}.backup-{int(datetime.now().timestamp())}"
                try:
                    if os.path.exists(history_file_path):
                        shutil.copy2(history_file_path, backup_file)
                        logger.info(f"이력 파일 백업 생성: {backup_file}")
                except Exception as e:
                    logger.warning(f"이력 파일 백업 생성 실패: {e}")
                
                QMessageBox.information(
                    self,
                    "이력 초기화 완료",
                    f"모든 처리된 파일 이력이 성공적으로 초기화되었습니다.\n"
                    f"이제 모든 파일을 새롭게 처리할 수 있습니다."
                )
                
                # 사용자 편의를 위해 파일 다시 스캔
                if self.source_directory and os.path.isdir(self.source_directory):
                    self.scan_files()
                else:
                    logger.info("이력 초기화 후 파일 다시 스캔 실패: 소스 디렉토리가 설정되지 않음")
            else:
                QMessageBox.warning(
                    self,
                    "이력 초기화 실패",
                    "이력 초기화 중 오류가 발생했습니다."
                )
        except Exception as e:
            logger.error(f"이력 초기화 중 오류 발생: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"이력 초기화 중 오류가 발생했습니다: {str(e)}")

    def populate_file_table(self, files):
        """Populate the file table with files."""
        self.file_list = files
        self.skipped_files = []  # 초기화
        self._update_file_display()

    def set_skipped_files(self, skipped_files):
        """스킵된 파일 정보를 설정합니다."""
        self.skipped_files = skipped_files
        self._update_file_info_label()
        self._update_file_display()

    def _update_file_info_label(self):
        """파일 정보를 업데이트합니다."""
        valid_count = len(self.file_list) if hasattr(self, 'file_list') else 0
        skipped_count = len(self.skipped_files) if hasattr(self, 'skipped_files') else 0
        
        # 확장자별 통계
        valid_extensions = {}
        if hasattr(self, 'file_list'):
            for file in self.file_list:
                # Handle both string filenames and dictionary file objects
                if isinstance(file, dict):
                    # File is a dictionary with metadata
                    ext = file.get("file_extension", "")
                else:
                    # File is a string (filename)
                    _, ext = os.path.splitext(file)
                    ext = ext.lower()
                    
                if ext not in valid_extensions:
                    valid_extensions[ext] = 0
                valid_extensions[ext] += 1
        
        # 스킵 이유별 통계
        skip_reasons = {}
        if hasattr(self, 'skipped_files'):
            for file in self.skipped_files:
                reason = file.get("skip_reason", "unknown")
                if reason not in skip_reasons:
                    skip_reasons[reason] = 0
                skip_reasons[reason] += 1
        
        # 정보 텍스트 구성
        info_text = f"파일 스캔 결과: 유효 {valid_count}개, 스킵됨 {skipped_count}개"
        
        if valid_extensions:
            ext_text = ", ".join([f"{ext}({count})" for ext, count in valid_extensions.items()])
            info_text += f" | 유효 확장자: {ext_text}"
        
        if skip_reasons:
            reason_text = ", ".join([f"{self._get_skip_reason_display(reason)}({count})" for reason, count in skip_reasons.items()])
            info_text += f" | 스킵 이유: {reason_text}"
        
        self.file_info_label.setText(info_text)

    def _get_skip_reason_display(self, reason):
        """스킵 이유 코드를 사용자 친화적인 텍스트로 변환합니다."""
        reason_map = {
            "already_processed": "이미 처리됨",
            "unsupported_extension": "지원되지 않는 형식",
            "unknown": "알 수 없음"
        }
        return reason_map.get(reason, reason)

    def _update_file_display(self):
        """현재 선택된 탭에 따라 파일 목록을 업데이트합니다."""
        self.file_table.setRowCount(0)  # 테이블 초기화
        
        if self.all_files_radio.isChecked():
            # 모든 파일 표시 (유효 + 스킵 파일)
            display_files = []
            
            # 유효 파일 추가
            if hasattr(self, 'file_list'):
                for file in self.file_list:
                    # Handle both string filenames and dictionary file objects
                    if isinstance(file, dict):
                        # File is a dictionary with metadata
                        file_info = file.copy()
                    else:
                        # File is a string (filename)
                        file_info = {
                            "file_name": file,
                            "file_path": os.path.join(self.source_directory, file) if self.source_directory else file,
                            "file_extension": os.path.splitext(file)[1].lower()
                        }
                    
                    file_info["is_valid"] = True
                    display_files.append(file_info)
            
            # 스킵된 파일 추가
            if hasattr(self, 'skipped_files'):
                for file in self.skipped_files:
                    file_info = file.copy()
                    file_info["is_valid"] = False
                    display_files.append(file_info)
        
        elif self.valid_files_radio.isChecked():
            # 유효 파일만 표시
            display_files = []
            if hasattr(self, 'file_list'):
                for file in self.file_list:
                    # Handle both string filenames and dictionary file objects
                    if isinstance(file, dict):
                        # File is a dictionary with metadata
                        file_info = file.copy()
                    else:
                        # File is a string (filename)
                        file_info = {
                            "file_name": file,
                            "file_path": os.path.join(self.source_directory, file) if self.source_directory else file,
                            "file_extension": os.path.splitext(file)[1].lower()
                        }
                    
                    file_info["is_valid"] = True
                    display_files.append(file_info)
        
        elif self.skipped_files_radio.isChecked():
            # 스킵된 파일만 표시
            display_files = []
            if hasattr(self, 'skipped_files'):
                for file in self.skipped_files:
                    file_info = file.copy()
                    file_info["is_valid"] = False
                    display_files.append(file_info)
        
        # 테이블에 파일 정보 추가
        self.file_table.setRowCount(len(display_files))
        for row, file_info in enumerate(display_files):
            # 체크박스 설정
            is_valid = file_info.get("is_valid", True)
            
            # 1. 체크박스 칼럼
            checkbox = QCheckBox()
            checkbox.setEnabled(is_valid)  # 유효한 파일만 체크 가능
            
            # 기본적으로 체크박스 선택 해제, 처리되지 않은 유효 파일만 선택
            is_processed = file_info.get("processed", False)
            if is_valid and not is_processed:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
                
            self.file_table.setCellWidget(row, 0, checkbox)
            
            # 2. 파일명
            self.file_table.setItem(row, 1, QTableWidgetItem(file_info.get("file_name", "")))
            
            # 3. 상태
            status_item = QTableWidgetItem()
            if is_valid:
                status_item.setText("유효")
                status_item.setBackground(QColor(240, 255, 240))  # 연한 녹색
            else:
                status_item.setText("스킵됨")
                status_item.setBackground(QColor(255, 240, 240))  # 연한 적색
            self.file_table.setItem(row, 2, status_item)
            
            # 4. 시퀀스
            sequence = file_info.get("sequence", "") if is_valid else ""
            self.file_table.setItem(row, 3, QTableWidgetItem(sequence))
            
            # 5. 샷
            shot = file_info.get("shot", "") if is_valid else ""
            self.file_table.setItem(row, 4, QTableWidgetItem(shot))
            
            # 6. 메세지
            message = file_info.get("message", "") if is_valid else ""
            self.file_table.setItem(row, 5, QTableWidgetItem(message))
            
            # 7. 스킵 이유
            skip_reason = ""
            if not is_valid:
                raw_reason = file_info.get("skip_reason", "unknown")
                skip_reason = self._get_skip_reason_display(raw_reason)
            self.file_table.setItem(row, 6, QTableWidgetItem(skip_reason))
        
        # 여기에 행 색상 스타일링 등 추가 가능
        self._update_file_info_label()

    def scan_directory(self, directory=None, recursive=True, update_ui=True):
        """디렉토리에서 지원하는 파일 스캔"""
        try:
            if not directory:
                directory = self.source_directory
                
            if not directory or not os.path.isdir(directory):
                logger.error(f"스캔할 디렉토리가 없음: {directory}")
                if update_ui:
                    self.update_status("유효한 디렉토리를 선택하세요")
                return []
                
            # 처리된 파일 제외 옵션 가져오기
            exclude_processed = self.exclude_processed_cb.isChecked()
            
            # 트래커 유효성 확인 및 재초기화
            if self.processed_files_tracker is None:
                self.processed_files_tracker = ProcessedFilesTracker()
                self.scanner.processed_files_tracker = self.processed_files_tracker
                logger.info("ProcessedFilesTracker 재초기화됨")
            
            # 하위 디렉토리 스캔 옵션 가져오기
            recursive = self.recursive_cb.isChecked()
            
            # 스캔 시작
            logger.info(f"디렉토리 스캔 시작: {directory} (recursive={recursive}, exclude_processed={exclude_processed})")
            if update_ui:
                self.update_status(f"스캔 중: {directory}...")
                
            # 파일 스캔
            file_infos = self.scanner.scan_directory(directory, recursive, exclude_processed)
            
            # 스캔 결과 처리
            if not file_infos:
                if update_ui:
                    self.update_status("지원되는 미디어 파일을 찾을 수 없습니다")
                logger.info(f"디렉토리에서 지원되는 미디어 파일을 찾을 수 없음: {directory}")
                return []
            
            # 스킵된 파일 가져오기
            self.skipped_files = self.scanner.get_skipped_files()
            
            # 파일 목록 및 정보 사전 업데이트
            self.file_list = []
            self.file_info_dict = {}
            
            for file_info in file_infos:
                file_name = file_info["file_name"]
                self.file_list.append(file_name)
                self.file_info_dict[file_name] = file_info
            
            # 시퀀스 사전 업데이트
            self.sequence_dict = self.scanner.get_sequence_dict()
            
            # 사용 가능한 시퀀스 목록 업데이트
            if self.sequence_dict:
                for seq_name in self.sequence_dict.keys():
                    if seq_name and seq_name not in [self.sequence_combo.itemText(i) for i in range(self.sequence_combo.count())]:
                        self.sequence_combo.addItem(seq_name)
            
            if update_ui:
                processed_summary = self.scanner.get_processed_files_summary()
                processed_count = processed_summary["count"]
                
                # 테이블 업데이트
                self._update_file_display()
                
                # 상태 업데이트
                if processed_count > 0:
                    self.update_status(f"{len(file_infos)}개 파일 스캔 완료 ({processed_count}개 이미 처리된 파일 스킵됨)")
                else:
                    self.update_status(f"{len(file_infos)}개 파일 스캔 완료")
                
            return file_infos
                
        except Exception as e:
            if update_ui:
                self.update_status(f"스캔 오류: {e}", error=True)
            logger.error(f"디렉토리 스캔 중 오류 발생: {e}", exc_info=True)
            return []