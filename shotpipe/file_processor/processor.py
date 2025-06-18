"""
Main file processor module for ShotPipe.
Orchestrates the file processing workflow.
"""
import os
import json
import csv
import shutil
from pathlib import Path
import logging
from .scanner import FileScanner
from .metadata import MetadataExtractor
from .naming import NamingManager
from .task_assigner import TaskAssigner
from ..config import config
from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import re
import time
try:
    from ..utils.processed_files_tracker import ProcessedFilesTracker
except ImportError:
    # 절대 경로로 시도
    from shotpipe.utils.processed_files_tracker import ProcessedFilesTracker

logger = logging.getLogger(__name__)

class FileProcessor:
    """Main file processor orchestrating the entire file processing workflow."""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.metadata_extractor = MetadataExtractor()
        self.naming_manager = NamingManager()
        self.task_assigner = TaskAssigner()
    
    def process_directory(self, source_dir, output_dir=None, recursive=True, copy_files=True, exclude_processed=True):
        """
        Process all supported files in a directory.
        
        Args:
            source_dir (str): Source directory path
            output_dir (str, optional): Output directory for processed files
            recursive (bool): Whether to scan subdirectories
            copy_files (bool): Whether to copy processed files to output_dir
            exclude_processed (bool): Whether to exclude files that appear to be already processed
        
        Returns:
            list: List of processed file information
        """
        # Scan the directory for files, excluding already processed files if requested
        file_infos = self.scanner.scan_directory(source_dir, recursive, exclude_processed)
        
        if not file_infos:
            logger.info(f"No supported files found in {source_dir}")
            return []
        
        # Assign tasks to files
        file_infos = self.task_assigner.assign_tasks_batch(file_infos)
        
        # Process each file
        processed_files = []
        for file_info in file_infos:
            try:
                processed_file = self.process_file(file_info, output_dir, copy_files)
                processed_files.append(processed_file)
            except Exception as e:
                logger.error(f"Error processing file {file_info['file_path']}: {e}")
        
        return processed_files
    
    def process_file(self, file_info, output_dir=None, copy_file=True):
        """
        Process a single file.
        
        Args:
            file_info (dict): File information dictionary
            output_dir (str, optional): Output directory for processed file
            copy_file (bool): Whether to copy the processed file to output_dir
        
        Returns:
            dict: Updated file information after processing
        """
        try:
            if not isinstance(file_info, dict):
                logger.error(f"Invalid file_info provided: {type(file_info)}. Expected dictionary.")
                return None
                
            logger.debug(f"Processing file: {file_info.get('file_path', 'Unknown')}")
            
            # Extract metadata
            try:
                metadata = self.metadata_extractor.extract_metadata(file_info["file_path"])
                file_info["metadata"] = metadata
                logger.debug(f"Metadata extracted successfully for {file_info['file_path']}")
            except Exception as e:
                logger.error(f"Error extracting metadata for {file_info['file_path']}: {e}")
                file_info["metadata"] = {}
            
            # Apply naming convention
            logger.debug(f"Applying naming convention for {file_info['file_path']}")
            try:
                file_info = self.naming_manager.apply_naming_convention(file_info, output_dir)
                logger.debug(f"Naming convention applied: {file_info.get('processed_path', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error applying naming convention: {e}")
                # Set default processed path if none exists
                if 'processed_path' not in file_info:
                    file_name = os.path.basename(file_info['file_path'])
                    file_info['processed_path'] = os.path.join(output_dir or os.path.dirname(file_info['file_path']), file_name)
            
            # Check if source and destination are the same file
            if file_info["file_path"] == file_info["processed_path"]:
                logger.debug(f"Source and destination are the same: {file_info['file_path']}")
                file_info["processed"] = True
            # Copy the file if requested
            elif copy_file:
                logger.debug(f"Copying file from {file_info['file_path']} to {file_info['processed_path']}")
                if self._copy_file(file_info["file_path"], file_info["processed_path"]):
                    file_info["processed"] = True
                else:
                    file_info["processed"] = False
            
            # Save metadata alongside the processed file
            if file_info.get("processed", False) or not copy_file:
                try:
                    metadata_path = Path(file_info["processed_path"]).with_suffix(".metadata.json")
                    self.metadata_extractor.save_metadata(metadata, metadata_path)
                    file_info["metadata_path"] = str(metadata_path)
                    logger.debug(f"Metadata saved to {metadata_path}")
                    
                    # Add user and status information
                    file_info["user_email"] = "hsjang@lennon.co.kr"  # Default user
                    file_info["status"] = "wip"  # Default status
                except Exception as e:
                    logger.error(f"Error saving metadata file: {e}")
            
            logger.info(f"Processed file: {file_info['file_name']} -> {Path(file_info['processed_path']).name}")
            return file_info
            
        except Exception as e:
            logger.error(f"Unexpected error processing file {file_info.get('file_path', 'Unknown')}: {str(e)}", exc_info=True)
            return file_info if isinstance(file_info, dict) else {}
    
    def _copy_file(self, source_path, dest_path):
        """
        Copy a file from source to destination.
        
        Args:
            source_path (str): Source file path
            dest_path (str): Destination file path
        
        Returns:
            bool: Success status
        """
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied file: {source_path} -> {dest_path}")
            
            # 리네이밍된 결과 로그 출력 (원본 경로 -> 대상 경로)
            relative_src = os.path.relpath(source_path)
            relative_dst = os.path.relpath(dest_path)
            logger.info(f"파일 리네이밍: {relative_src} -> {relative_dst}")
            
            return True
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return False
    
    def save_processed_files(self, file_infos, output_path=None, format="json"):
        """
        Save processed file information to a file.
        
        Args:
            file_infos (list): List of file information dictionaries
            output_path (str, optional): Output file path
            format (str): Output format ("json" or "csv")
        
        Returns:
            str: Path to the saved file
        """
        if not output_path:
            output_path = config.get("general", "save_processed_to")
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            if format.lower() == "json":
                with open(output_path, "w") as f:
                    json.dump(file_infos, f, indent=4, default=str)
            elif format.lower() == "csv":
                # For CSV, we need to flatten the structure
                with open(output_path, "w", newline="") as f:
                    # Determine all unique keys
                    fieldnames = set()
                    for file_info in file_infos:
                        fieldnames.update(file_info.keys())
                    
                    # Remove metadata field as it's too complex for CSV
                    if "metadata" in fieldnames:
                        fieldnames.remove("metadata")
                    
                    # Sort fieldnames for better readability
                    fieldnames = sorted(list(fieldnames))
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for file_info in file_infos:
                        # Create a copy without metadata
                        row = {k: v for k, v in file_info.items() if k != "metadata"}
                        writer.writerow(row)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Saved processed file information to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving processed file information: {e}")
            return None

class ProcessingThread(QThread):
    """Thread for processing files in the background.
    
    This class handles the processing of files in a separate thread to keep the UI responsive
    and provides progress updates via signals.
    """
    # Signals
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(str, str, str, str, str, float)  # 파일명, 상태, 시퀀스, 샷, 메시지, 경과 시간
    processing_completed = pyqtSignal(list)
    processing_error = pyqtSignal(str)
    
    def __init__(self, file_infos, metadata_extractor, sequence_dict=None, selected_sequence=None, output_directory=None, processed_files_tracker=None):
        """
        Initialize the processing thread.
        
        Args:
            file_infos (list): List of file information dictionaries to process
            metadata_extractor (MetadataExtractor): Metadata extractor instance
            sequence_dict (dict, optional): Dictionary mapping files to sequences. Defaults to None.
            selected_sequence (str, optional): Selected sequence name. Defaults to None.
            output_directory (str, optional): Output directory for processed files. Defaults to None.
            processed_files_tracker (ProcessedFilesTracker, optional): Tracker for processed files. Defaults to None.
        """
        super().__init__()
        logger.debug("ProcessingThread.__init__: Initializing thread.")
        self.file_infos = file_infos  # 파라미터 이름 변경
        self.metadata_extractor = metadata_extractor
        self.naming_manager = NamingManager()
        self.task_assigner = TaskAssigner()
        self.sequence_dict = sequence_dict or {}
        self.selected_sequence = selected_sequence
        self.output_directory = output_directory
        self._is_cancelled = False
        self.processed_files = []
        self.processed_files_tracker = processed_files_tracker
        if not self.file_infos:
            logger.warning("ProcessingThread.__init__: file_infos is empty.")
        else:
            logger.debug(f"ProcessingThread.__init__: Thread initialized with {len(self.file_infos)} files.")
        
    def run(self):
        """Run the file processing task."""
        logger.info("🚀 파일 처리 작업 시작")
        try:
            total_files = len(self.file_infos)
            if total_files == 0:
                logger.warning("⚠️ 처리할 파일이 없습니다")
                self.processing_completed.emit([])
                return

            processed_files_list = []
            logger.info(f"📋 총 {total_files}개 파일 처리 시작")
            
            for i, file_info in enumerate(self.file_infos):
                if self._is_cancelled:
                    logger.info("⏹️ 파일 처리가 취소되었습니다")
                    break
                
                current_file = file_info.get('file_name', f'파일 {i+1}')
                logger.info(f"📁 [{i+1}/{total_files}] {current_file} 처리 중...")
                
                try:
                    start_time = time.time()
                    
                    # 사용자가 테이블에서 설정한 시퀀스와 샷 정보 우선 사용
                    sequence = file_info.get('sequence', '')
                    shot = file_info.get('shot', '')
                    
                    # 시퀀스나 샷이 비어있으면 자동 결정
                    if not sequence or not shot:
                        auto_sequence, auto_shot = self._determine_sequence_and_shot(file_info['file_name'], file_info['file_path'])
                        if not sequence:
                            sequence = auto_sequence
                        if not shot:
                            shot = auto_shot
                    
                    # 선택된 시퀀스가 있으면 우선 적용 (전체 배치 처리용)
                    if self.selected_sequence:
                        sequence = self.selected_sequence
                        
                    processed_info = self._process_file(file_info, sequence=sequence, shot=shot)
                    processed_files_list.append(processed_info)
                    
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    
                    status = "성공" if processed_info.get("success") else "실패"
                    message = processed_info.get("message", "")
                    
                    # 시그널 emit 전에 타입 확인 및 변환
                    sequence_str = str(sequence) if sequence else ""
                    shot_str = str(shot) if shot else ""
                    self.file_processed.emit(file_info['file_name'], status, sequence_str, shot_str, message, elapsed_time)
                    
                    if status == "완료":
                        logger.info(f"✅ {file_info['file_name']} 처리 완료 ({elapsed_time:.1f}초)")
                    else:
                        logger.warning(f"⚠️ {file_info['file_name']} 처리 중 문제 발생: {message}")
                
                except Exception as e:
                    file_name = file_info.get('file_name', 'Unknown') if isinstance(file_info, dict) else file_info
                    logger.error(f"❌ {file_name} 처리 실패: {e}")
                    error_info = {
                        "file_name": file_name,
                        "file_path": file_info.get('file_path', 'Unknown') if isinstance(file_info, dict) else file_info,
                        "success": False,
                        "message": str(e)
                    }
                    processed_files_list.append(error_info)
                    self.file_processed.emit(file_name, "실패", "", "", str(e), 0)

                # Update progress (파일 번호로 전송)
                self.progress_updated.emit(i + 1)
                progress_percent = int((i + 1) / total_files * 100)
                logger.info(f"⏳ 진행률: {progress_percent}% ({i+1}/{total_files})")
            
            logger.info(f"🎉 모든 파일 처리 완료! 총 {len(processed_files_list)}개 파일 처리됨")
            self.processing_completed.emit(processed_files_list)
        except Exception as e:
            logger.critical(f"💥 처리 스레드에서 예상치 못한 오류 발생: {e}", exc_info=True)
            self.processing_error.emit(str(e))
    
    def _process_file(self, file_info, sequence=None, shot=None):
        """Process a single file with assigned sequence and shot."""
        try:
            file_path = file_info['file_path']
            file_name = file_info['file_name']
            
            logger.info(f"Processing file: {file_name}")
            
            # 메타데이터 추출
            try:
                metadata = self.metadata_extractor.extract_metadata(file_path)
                if not metadata:
                    raise ValueError("메타데이터를 추출할 수 없습니다.")
                file_info["metadata"] = metadata
                logger.debug(f"Metadata extracted for {file_name}")
            except Exception as e:
                logger.error(f"메타데이터 추출 실패: {file_name} - {e}", exc_info=True)
                return {
                    "file_name": file_name,
                    "file_path": file_path,
                    "success": False,
                    "message": f"메타데이터 추출 실패: {e}"
                }

            # 태스크 할당
            try:
                # Assign sequence and shot to file_info before calling assign_task
                file_info['sequence'] = sequence
                file_info['shot'] = shot
                file_info = self.task_assigner.assign_task(file_info)
                logger.debug(f"Task assigned for {file_name}: {file_info.get('task')}")
            except Exception as e:
                logger.error(f"태스크 할당 실패: {file_name} - {e}", exc_info=True)
                return {
                    "file_name": file_name,
                    "file_path": file_path,
                    "success": False,
                    "message": f"태스크 할당 실패: {e}"
                }

            # 네이밍 규칙 적용
            try:
                file_info = self.naming_manager.apply_naming_convention(file_info, self.output_directory)
                logger.debug(f"Naming convention applied for {file_name}: {file_info.get('processed_path')}")
            except Exception as e:
                logger.error(f"네이밍 규칙 적용 실패: {file_name} - {e}", exc_info=True)
                return {
                    "file_name": file_name,
                    "file_path": file_path,
                    "success": False,
                    "message": f"네이밍 규칙 적용 실패: {e}"
                }
            
            # 파일 복사
            try:
                output_path = Path(file_info["processed_path"])
                
                # 출력 디렉토리가 존재하지 않으면 생성
                output_dir = output_path.parent
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"출력 디렉토리 확인/생성: {output_dir}")
                
                shutil.copy2(file_path, output_path)
                logger.info(f"파일 복사 완료: {file_path} -> {output_path}")
            except Exception as e:
                logger.error(f"파일 복사 실패: {file_path} -> {file_info.get('processed_path')} - {e}", exc_info=True)
                return {
                    "file_name": file_name,
                    "file_path": file_path,
                    "success": False,
                    "message": f"파일 복사 실패: {e}"
                }
            
            # 메타데이터 파일 저장
            try:
                metadata_path = output_path.with_suffix(".metadata.json")
                self.metadata_extractor.save_metadata(file_info["metadata"], str(metadata_path))
                file_info["metadata_path"] = str(metadata_path)
                logger.info(f"메타데이터 저장 완료: {metadata_path}")
            except Exception as e:
                logger.error(f"메타데이터 저장 실패: {metadata_path} - {e}", exc_info=True)
                # 메타데이터 저장이 실패해도 일단은 성공으로 간주할 수 있음 (선택사항)
                pass

            # 처리된 파일 히스토리 추가
            if self.processed_files_tracker:
                self.processed_files_tracker.add_processed_file(file_path, file_info)
            
            file_info["success"] = True
            file_info["message"] = "처리 완료"
            return file_info
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"An unexpected error occurred while processing {file_info.get('file_name', 'N/A')}: {e}\n{error_trace}")
            return {
                "file_name": file_info.get('file_name', 'N/A'),
                "file_path": file_info.get('file_path', 'N/A'),
                "success": False,
                "message": str(e)
            }
    
    def _determine_sequence_and_shot(self, file_name, file_path=None):
        """Determine sequence and shot from file name or path."""
        # 로깅 추가
        logger.debug(f"시퀀스 결정 시작: {file_name}, selected_sequence: {self.selected_sequence}")
        
        # 선택된 시퀀스가 있고 '자동 감지'가 아니면 사용
        if self.selected_sequence and self.selected_sequence != "자동 감지":
            logger.info(f"사용자가 선택한 시퀀스 사용: {self.selected_sequence}")
            return self.selected_sequence, "c001"
        
        # 파일 경로에서 디렉토리 이름 추출 (파일 경로가 있는 경우)
        if file_path:
            # 파일이 있는 디렉토리 이름 추출
            dir_name = os.path.basename(os.path.dirname(file_path))
            if dir_name:
                logger.info(f"디렉토리 이름을 시퀀스로 사용: {dir_name}")
                return dir_name, "c001"
        
        # 1. 파일 이름에서 시퀀스 및 샷 추출 시도
        for pattern, extractor in [
            # 패턴: s01_c001_name.ext
            (r'^([sS]\d+)_[cC](\d+)_', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
            
            # 패턴: seq_shot.ext (예: A_001.jpg)
            (r'^([A-Za-z]+)_(\d+)\.', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
            
            # 패턴: seq.shot.ext (예: A.001.jpg)
            (r'^([A-Za-z]+)\.(\d+)\.', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
            
            # 패턴: name_s01_c001.ext
            (r'_([sS]\d+)_[cC](\d+)', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
            
            # 패턴: LIG_c001_name.ext 또는 KIAP_c001_name.ext
            (r'^(LIG|KIAP)_[cC](\d+)', lambda m: (m.group(1).upper(), f"c{int(m.group(2)):03d}")),
        ]:
            match = re.search(pattern, file_name)
            if match:
                seq, shot = extractor(match)
                logger.debug(f"파일 이름에서 시퀀스/샷 추출: {seq}/{shot}")
                return seq, shot
        
        # 3. 시퀀스 사전에서 정보 찾기
        if self.sequence_dict:
            for seq_name, files in self.sequence_dict.items():
                for seq_file, seq_shot in files:
                    if seq_file == file_name:
                        logger.debug(f"시퀀스 사전에서 정보 찾음: {seq_name}/{seq_shot}")
                        return seq_name, seq_shot
        
        # 4. 파일 이름에서 LIG 또는 KIAP 문자열 추출
        if "LIG" in file_name.upper():
            logger.debug("파일 이름에서 LIG 추출")
            return "LIG", "c001"
        elif "KIAP" in file_name.upper():
            logger.debug("파일 이름에서 KIAP 추출")
            return "KIAP", "c001"
            
        # 5. 최종 기본값 사용
        logger.info("기본 시퀀스 's01' 사용")
        return "s01", "c001"
    
    def _extract_shot_number(self, file_name):
        """Extract shot number from file name.
        
        Args:
            file_name (str): Name of the file
            
        Returns:
            str: Shot number or empty string if not found
        """
        # Common patterns for shot number extraction
        patterns = [
            r'[_\.]c([0-9]+)[_\.]',  # Format: name_c001_task or name.c001.ext
            r'[_\.]([0-9]{3,4})[_\.]',  # Format: name_001_task or name.001.ext
            r'_shot([0-9]+)[_\.]',  # Format: name_shot001_task
            r'[_\.]sc([0-9]+)[_\.]',  # Format: name_sc001_task
            r'[_\.]sh([0-9]+)[_\.]',  # Format: name_sh001_task
            r'[_\.]s([0-9]+)[_\.]',  # Format: name_s001_task
            r'shot([0-9]+)',  # Format: shot001
            r'[_\.]cut([0-9]+)[_\.]',  # Format: name_cut001_task
        ]
        
        # Add underscore prefix and suffix to help with pattern matching
        padded_name = f"_{file_name}_"
        
        for pattern in patterns:
            match = re.search(pattern, padded_name)
            if match:
                shot_num = int(match.group(1))
                return f"c{shot_num:03d}"
        
        return ""

    def cancel_processing(self):
        """Cancel the processing."""
        logger.info("Processing cancellation requested")
        self._is_cancelled = True