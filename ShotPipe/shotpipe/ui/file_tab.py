"""
File processing tab module for ShotPipe UI.
"""
import os
import sys
import logging
import traceback
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QProgressBar, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QMenu, QAction, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QColor
from ..file_processor.processor import ProcessingThread
from ..file_processor.scanner import FileScanner
from ..config import config

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
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        try:
            # Main layout
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # Source directory selection
            dir_layout = QHBoxLayout()
            dir_label = QLabel("소스 디렉토리:")
            self.dir_path_label = QLabel("선택된 디렉토리 없음")
            self.dir_path_label.setStyleSheet("font-weight: bold;")
            self.select_dir_btn = QPushButton("디렉토리 선택...")
            self.select_dir_btn.clicked.connect(self.select_source_directory)
            
            dir_layout.addWidget(dir_label)
            dir_layout.addWidget(self.dir_path_label, 1)
            dir_layout.addWidget(self.select_dir_btn)
            
            main_layout.addLayout(dir_layout)
            
            # Output directory selection
            output_layout = QHBoxLayout()
            output_label = QLabel("출력 폴더:")
            self.output_path_label = QLabel("소스 디렉토리와 동일")
            self.output_path_label.setStyleSheet("font-style: italic;")
            
            self.select_output_btn = QPushButton("출력 폴더 선택...")
            self.select_output_btn.clicked.connect(self.select_output_directory)
            
            # Create processed files folder checkbox
            self.create_processed_folder_cb = QCheckBox("처리된 파일용 폴더 생성")
            self.create_processed_folder_cb.setChecked(True)
            self.create_processed_folder_cb.setToolTip("처리된 파일을 'processed' 하위 폴더로 이동합니다.")
            
            output_layout.addWidget(output_label)
            output_layout.addWidget(self.output_path_label, 1)
            output_layout.addWidget(self.select_output_btn)
            output_layout.addWidget(self.create_processed_folder_cb)
            
            main_layout.addLayout(output_layout)
            
            # File processing options group
            options_group = QGroupBox("처리 옵션")
            options_inner_layout = QVBoxLayout()
            
            # File options
            file_options_layout = QHBoxLayout()
            
            # 이미 처리된 파일 제외 옵션
            self.exclude_processed_cb = QCheckBox("이미 처리된 파일 제외")
            self.exclude_processed_cb.setChecked(True)  # Default to checked
            self.exclude_processed_cb.setToolTip("이미 메타데이터 파일이 있거나 처리된 형식으로 명명된 파일을 제외합니다.")
            file_options_layout.addWidget(self.exclude_processed_cb)
            
            # Recursive option
            self.recursive_cb = QCheckBox("하위 폴더 포함")
            self.recursive_cb.setChecked(False)  # Default to unchecked
            file_options_layout.addWidget(self.recursive_cb)
            
            file_options_layout.addStretch()
            options_inner_layout.addLayout(file_options_layout)
            
            # Sequence settings
            sequence_layout = QHBoxLayout()
            
            self.use_sequence_cb = QCheckBox("시퀀스 사용")
            self.use_sequence_cb.setChecked(True)  # Enable by default
            self.use_sequence_cb.toggled.connect(self.toggle_sequence_combo)
            
            sequence_label = QLabel("시퀀스:")
            
            self.sequence_combo = QComboBox()
            self.sequence_combo.setEditable(True)
            self.sequence_combo.setMinimumWidth(200)
            
            # Add default sequences at initialization
            self.sequence_combo.addItem("자동 감지")  # Auto Detect
            default_sequences = ["LIG", "KIAP", "LIG_KIAP"]
            for seq in default_sequences:
                self.sequence_combo.addItem(seq)
                
            # Set LIG as the default sequence
            lig_index = self.sequence_combo.findText("LIG")
            if lig_index >= 0:
                self.sequence_combo.setCurrentIndex(lig_index)
            
            # Add tooltip to explain sequence combo usage
            self.sequence_combo.setToolTip("시퀀스 선택 또는 새 시퀀스 입력 가능")
            
            sequence_layout.addWidget(self.use_sequence_cb)
            sequence_layout.addWidget(sequence_label)
            sequence_layout.addWidget(self.sequence_combo)
            sequence_layout.addStretch()
            
            options_inner_layout.addLayout(sequence_layout)
            options_group.setLayout(options_inner_layout)
            main_layout.addWidget(options_group)
            
            # Files table
            main_layout.addWidget(QLabel("파일 목록:"))
            
            self.file_table = QTableWidget(0, 5)
            self.file_table.setHorizontalHeaderLabels(["파일명", "상태", "시퀀스", "샷", "메세지"])
            self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
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
            
            btn_layout.addWidget(self.scan_btn)
            btn_layout.addWidget(self.process_btn)
            btn_layout.addStretch()
            
            main_layout.addLayout(btn_layout)
            
            # Set the main layout
            self.setLayout(main_layout)
        
        except Exception as e:
            logger.critical(f"Failed to initialize file tab UI: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"UI 초기화 중 오류가 발생했습니다: {str(e)}")
    
    def select_source_directory(self):
        """Select a source directory."""
        try:
            # Open file dialog
            directory = QFileDialog.getExistingDirectory(
                self, 
                "소스 디렉토리 선택",
                os.path.expanduser("~"),
                QFileDialog.ShowDirsOnly
            )
            
            # If user cancels, directory will be empty
            if not directory:
                return
            
            self.source_directory = directory
            self.dir_path_label.setText(directory)
            self.reset_ui()
            
            # Automatically scan files
            self.scan_files()
            
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
            self.output_path_label.setText(directory)
            
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
    
    def toggle_sequence_combo(self, state):
        """
        Toggle the sequence combo box based on checkbox state.
        
        Args:
            state (bool): Checkbox state
            
        This method enables/disables the combo box and populates it with
        available sequences based on the checkbox state.
        """
        # Enable or disable the sequence combo box
        self.sequence_combo.setEnabled(state)
        
        # Always make sure the combo box has the auto-detect option
        self.sequence_combo.clear()
        self.sequence_combo.addItem("자동 감지")  # Auto Detect
        
        # Add default sequences
        default_sequences = ["LIG", "KIAP", "LIG_KIAP"]
        for seq in default_sequences:
            self.sequence_combo.addItem(seq)
        
        # If checkbox is checked, add available sequences from sequence_dict
        if state and self.sequence_dict:
            unique_sequences = set()
            for seq_name, files in self.sequence_dict.items():
                if seq_name and seq_name not in default_sequences:
                    unique_sequences.add(seq_name)
            
            # Add any unique sequences not already in default options
            for seq in sorted(unique_sequences):
                if seq not in default_sequences and seq != "자동 감지":
                    self.sequence_combo.addItem(seq)
        
        # Make the combo box editable to allow custom sequence input
        self.sequence_combo.setEditable(True)
        
        # Select LIG by default instead of auto-detect
        lig_index = self.sequence_combo.findText("LIG")
        if lig_index >= 0:
            self.sequence_combo.setCurrentIndex(lig_index)
        else:
            self.sequence_combo.setCurrentIndex(0)  # Fallback to first item if LIG not found
    
    def scan_files(self):
        """Scan files in the source directory."""
        try:
            # Verify that source directory is set
            if not self.source_directory or not os.path.isdir(self.source_directory):
                QMessageBox.warning(self, "경고", "유효한 소스 디렉토리를 선택해주세요.")
                return
            
            # Reset UI
            self.reset_ui()
            
            logger.info(f"Scanning files in {self.source_directory}")
            
            # Get all files in the directory
            try:
                # 이미 처리된 파일을 제외하는 옵션과 하위 폴더 포함 옵션 적용
                file_infos = self.scanner.scan_directory(
                    self.source_directory, 
                    recursive=self.recursive_cb.isChecked(), 
                    exclude_processed=self.exclude_processed_cb.isChecked()
                )
                
                # Extract just the file names for display
                self.file_list = [file_info.get('file_name') for file_info in file_infos]
                # Store the full file info for later use
                self.file_info_dict = {file_info.get('file_name'): file_info for file_info in file_infos}
            except Exception as scan_err:
                logger.error(f"Error scanning directory: {scan_err}", exc_info=True)
                QMessageBox.critical(self, "오류", f"디렉토리 스캔 중 오류가 발생했습니다: {str(scan_err)}")
                return
            
            # Always add the "자동 감지" option to combo box
            self.sequence_combo.clear()
            self.sequence_combo.addItem("자동 감지")
            
            # Extract sequences
            self.sequence_dict = self.extract_sequences(self.file_list)
            
            # Add sequences to combo box if any were found
            if self.sequence_dict:
                for sequence in sorted(self.sequence_dict.keys()):
                    self.sequence_combo.addItem(sequence)
            
            # Set LIG as default after populating
            lig_index = self.sequence_combo.findText("LIG")
            if lig_index >= 0:
                self.sequence_combo.setCurrentIndex(lig_index)
            
            # Populate the table
            self.file_table.setRowCount(len(self.file_list))
            
            for i, file_name in enumerate(self.file_list):
                # File name
                self.file_table.setItem(i, 0, QTableWidgetItem(file_name))
                
                # Status (empty initially)
                self.file_table.setItem(i, 1, QTableWidgetItem("대기중"))
                
                # Sequence and shot (empty initially)
                if self.use_sequence_cb.isChecked():
                    # Try to find sequence info
                    sequence_found = False
                    for seq_name, files in self.sequence_dict.items():
                        for seq_file, seq_shot in files:
                            if seq_file == file_name:
                                self.file_table.setItem(i, 2, QTableWidgetItem(seq_name))
                                self.file_table.setItem(i, 3, QTableWidgetItem(seq_shot))
                                sequence_found = True
                                break
                        if sequence_found:
                            break
                
                # Message (empty initially)
                self.file_table.setItem(i, 4, QTableWidgetItem(""))
            
            # Enable process button if files were found
            if self.file_list:
                self.process_btn.setEnabled(True)
                logger.info(f"Found {len(self.file_list)} files")
            else:
                QMessageBox.information(self, "정보", "선택한 디렉토리에 파일이 없습니다.")
                logger.warning("No files found in the selected directory")
                
        except Exception as e:
            logger.error(f"Error scanning files: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"파일 스캔 중 오류가 발생했습니다: {str(e)}")
    
    def extract_sequences(self, file_list):
        """Extract sequences from file names.
        
        Args:
            file_list (list): List of file names
            
        Returns:
            dict: Dictionary of sequences (key: sequence name, value: list of (file, shot) tuples)
        """
        try:
            logger.info("Extracting sequences from file names")
            
            sequences = {}
            
            # Common patterns for sequence detection (expanded)
            patterns = [
                # Format: s01_c001_name.ext
                (r'^([sS]\d+)_[cC](\d+)_', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: seq_shot.ext (e.g., A_001.jpg)
                (r'^([A-Za-z]+)_(\d+)\.', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: seq.shot.ext (e.g., A.001.jpg)
                (r'^([A-Za-z]+)\.(\d+)\.', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: seqshot.ext (e.g., A001.jpg)
                (r'^([A-Za-z]+)(\d+)\.', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: name_s01_c001_task.ext
                (r'_([sS]\d+)_[cC](\d+)_', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: LIG_c001_unknown.ext or KIAP_c001_unknown.ext
                (r'^(LIG|KIAP)_[cC](\d+)', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: LIG-KIAP_c001_unknown.ext or LIG_KIAP_c001_unknown.ext
                (r'^(LIG[-_]KIAP)_[cC](\d+)', lambda m: ("LIG_KIAP", f"c{int(m.group(2)):03d}")),
                
                # Format: LIG or KIAP anywhere in the filename with a shot number
                (r'(LIG|KIAP)[^a-zA-Z0-9].*?[cC](\d+)', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
                
                # Format: seq_shot_task.ext
                (r'^([A-Za-z0-9_-]+)_([cC]\d+)_', lambda m: (m.group(1).upper(), m.group(2).lower() if m.group(2).lower().startswith('c') else f"c{int(m.group(2)):03d}"))
            ]
            
            for file_name in file_list:
                sequence_found = False
                
                # Try each pattern
                for pattern, extractor in patterns:
                    match = re.search(pattern, file_name)
                    if match:
                        seq, shot = extractor(match)
                        if seq not in sequences:
                            sequences[seq] = []
                        sequences[seq].append((file_name, shot))
                        sequence_found = True
                        break
                
                # If no pattern matched, try to find any sequence-like pattern
                if not sequence_found:
                    # Look for common sequence indicators: S01, SEQ01, etc.
                    seq_match = re.search(r'([sS]\d+|[sS][eE][qQ]\d+|[A-Za-z]+\d+|LIG|KIAP|LIG[-_]KIAP)', file_name)
                    shot_match = re.search(r'[cC](\d+)|[sS][hH](\d+)|[sS][hH][oO][tT](\d+)', file_name)
                    
                    if seq_match:
                        seq = seq_match.group(1).upper()
                        # LIG-KIAP 패턴 정규화
                        if seq in ["LIG-KIAP", "LIG_KIAP"]:
                            seq = "LIG_KIAP"
                            
                        # 샷 번호가 없으면 기본값 설정
                        shot = "c001"
                        if shot_match:
                            shot_num = shot_match.group(1) or shot_match.group(2) or shot_match.group(3)
                            shot = f"c{int(shot_num):03d}"
                        
                        if seq not in sequences:
                            sequences[seq] = []
                        sequences[seq].append((file_name, shot))
                        sequence_found = True
                
                # If sequence is still not found but contains LIG or KIAP, add as a default
                if not sequence_found:
                    if "LIG" in file_name.upper():
                        seq = "LIG"
                        shot = "c001"
                        if seq not in sequences:
                            sequences[seq] = []
                        sequences[seq].append((file_name, shot))
                    elif "KIAP" in file_name.upper():
                        seq = "KIAP"
                        shot = "c001"
                        if seq not in sequences:
                            sequences[seq] = []
                        sequences[seq].append((file_name, shot))
            
            # Keep sequences with at least one file - we're being more permissive now
            for seq_name in list(sequences.keys()):
                if len(sequences[seq_name]) < 1:
                    del sequences[seq_name]
            
            logger.info(f"Found {len(sequences)} sequences")
            logger.debug(f"Sequences found: {list(sequences.keys())}")
            return sequences
            
        except Exception as e:
            logger.error(f"Error extracting sequences: {e}", exc_info=True)
            return {}
    
    def process_files(self):
        """Process files in the source directory."""
        try:
            # Verify that source directory is set
            if not self.source_directory or not os.path.isdir(self.source_directory):
                QMessageBox.warning(self, "경고", "유효한 소스 디렉토리를 선택해주세요.")
                return
            
            # Check if we have files
            if not self.file_list:
                QMessageBox.warning(self, "경고", "처리할 파일이 없습니다.")
                return
            
            # Determine output directory
            output_dir = self.output_directory if self.output_directory else self.source_directory
            
            # If create processed folder is checked, create a processed subfolder
            if self.create_processed_folder_cb.isChecked():
                if self.output_directory:
                    # Use specified output directory with processed subfolder
                    processed_dir = os.path.join(self.output_directory, "processed")
                else:
                    # Use source directory with processed subfolder
                    processed_dir = os.path.join(self.source_directory, "processed")
                    
                # Create the directory if it doesn't exist
                os.makedirs(processed_dir, exist_ok=True)
                output_dir = processed_dir
            
            # Determine which sequence to use
            selected_sequence = None
            if self.use_sequence_cb.isChecked():
                selected_text = self.sequence_combo.currentText()
                if selected_text != "자동 감지":
                    selected_sequence = selected_text
                    # If it's a new user-entered sequence not in the sequence_dict
                    if selected_sequence not in self.sequence_dict:
                        # Create a new entry with default shot number c001
                        self.sequence_dict[selected_sequence] = [
                            (file_name, "c001") for file_name in self.file_list
                        ]
                        logger.info(f"Created new sequence mapping for user-entered sequence: {selected_sequence}")
            
            # Create a metadata extractor instance
            from ..file_processor.metadata import MetadataExtractor
            metadata_extractor = MetadataExtractor()
            
            # Get full file paths for each file in the list
            file_paths = [os.path.join(self.source_directory, file_name) for file_name in self.file_list]
            
            # Log for debugging
            logger.info(f"Creating processing thread with {len(file_paths)} files")
            logger.info(f"Selected sequence: {selected_sequence}")
            logger.info(f"Output directory: {output_dir}")
            logger.info(f"Number of sequences in dictionary: {len(self.sequence_dict)}")
            
            # Create processing thread with metadata extractor instance and output directory
            self.processing_thread = ProcessingThread(
                file_paths,
                metadata_extractor,
                self.sequence_dict,
                selected_sequence,
                output_dir  # 출력 디렉토리 전달
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
                self.file_table.setItem(i, 1, QTableWidgetItem("대기중"))
                self.file_table.setItem(i, 4, QTableWidgetItem(""))
            
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
        """Update the status of a processed file.
        
        Args:
            file_name (str): The file name
            status (str): The status of the file
            sequence (str): The sequence name
            shot (str): The shot number
            message (str): Additional message
        """
        try:
            # Find the row for this file
            for i in range(self.file_table.rowCount()):
                if self.file_table.item(i, 0).text() == file_name:
                    # Update status
                    status_item = QTableWidgetItem(status)
                    if status == "완료":
                        status_item.setBackground(Qt.green)
                    elif status == "실패":
                        status_item.setBackground(Qt.red)
                    self.file_table.setItem(i, 1, status_item)
                    
                    # Update sequence if provided
                    if sequence:
                        self.file_table.setItem(i, 2, QTableWidgetItem(sequence))
                    
                    # Update shot if provided
                    if shot:
                        self.file_table.setItem(i, 3, QTableWidgetItem(shot))
                    
                    # Update message
                    self.file_table.setItem(i, 4, QTableWidgetItem(message))
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
                            "metadata": metadata
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