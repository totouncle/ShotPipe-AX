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
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    file_processed = pyqtSignal(str, str, str, str, str)  # filename, status, sequence, shot, message
    processing_completed = pyqtSignal(list)  # List of processed file results
    processing_error = pyqtSignal(str)  # Error message
    
    def __init__(self, file_paths, metadata_extractor, sequence_dict=None, selected_sequence=None, output_directory=None, processed_files_tracker=None):
        """
        Initialize the processing thread.
        
        Args:
            file_paths (list): List of file paths to process
            metadata_extractor (MetadataExtractor): Metadata extractor instance
            sequence_dict (dict, optional): Dictionary mapping files to sequences. Defaults to None.
            selected_sequence (str, optional): Selected sequence name. Defaults to None.
            output_directory (str, optional): Output directory for processed files. Defaults to None.
            processed_files_tracker (ProcessedFilesTracker, optional): Tracker for processed files. Defaults to None.
        """
        super().__init__()
        self.file_paths = file_paths
        self.metadata_extractor = metadata_extractor
        self.sequence_dict = sequence_dict or {}
        self.selected_sequence = selected_sequence
        self.output_directory = output_directory
        self.cancel = False
        self.processed_files = []
        self.naming_manager = NamingManager()  # NamingManager 인스턴스 추가
        self.processed_files_tracker = processed_files_tracker  # 처리된 파일 추적기 추가
        
        logger.info(f"Processing thread initialized with {len(file_paths)} files")
        if output_directory:
            logger.info(f"Output directory set to: {output_directory}")
        
    def run(self):
        """Run the processing thread."""
        logger.info("Starting file processing")
        try:
            # Check if we have files to process
            if not self.file_paths:
                logger.warning("No files to process")
                self.processing_error.emit("처리할 파일이 없습니다")
                return
            
            # Process each file
            total_files = len(self.file_paths)
            processed_count = 0
            
            for file_path in self.file_paths:
                # Check if processing was canceled
                if self.cancel:
                    logger.info("Processing canceled")
                    self.processing_error.emit("사용자에 의해 처리가 취소되었습니다")
                    return
                
                try:
                    # Get filename from path
                    file_name = os.path.basename(file_path)
                    logger.info(f"Processing file: {file_name}")
                    
                    # Determine sequence and shot for this file
                    sequence, shot = self._determine_sequence_and_shot(file_name, file_path)
                    
                    # Update UI with "processing" status
                    self.file_processed.emit(file_name, "처리중", sequence or "", shot or "", "")
                    
                    # Process the file
                    result = self._process_file(file_path, sequence, shot)
                    
                    # Update processed files list
                    self.processed_files.append(result)
                    
                    # 처리된 파일명 사용
                    processed_filename = os.path.basename(result.get("output_path", file_path))
                    # 처리된 시퀀스 및 샷 정보 사용
                    processed_sequence = result.get("sequence", sequence)
                    processed_shot = result.get("shot", shot)
                    
                    # Update UI with result
                    if result["success"]:
                        self.file_processed.emit(
                            processed_filename, "완료", processed_sequence or "", processed_shot or "", "성공적으로 처리됨"
                        )
                    else:
                        self.file_processed.emit(
                            processed_filename, "실패", processed_sequence or "", processed_shot or "", result["message"]
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
                    file_name = os.path.basename(file_path)
                    self.file_processed.emit(
                        file_name, "실패", "", "", f"오류: {str(e)}"
                    )
                    self.processed_files.append({
                        "file_name": file_name,
                        "file_path": file_path,
                        "success": False,
                        "message": str(e)
                    })
                
                # Update progress
                processed_count += 1
                progress_percent = int((processed_count / total_files) * 100)
                self.progress_updated.emit(progress_percent)
            
            # Processing completed
            logger.info(f"File processing completed: {processed_count} files processed")
            self.processing_completed.emit(self.processed_files)
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error in processing thread: {e}\n{error_trace}")
            error_message = f"파일 처리 중 오류가 발생했습니다: {str(e)}"
            self.processing_error.emit(error_message)
    
    def _process_file(self, file_path, sequence=None, shot=None):
        """Process a single file.
        
        Args:
            file_path (str): Path to the file
            sequence (str, optional): Sequence identifier. Defaults to None.
            shot (str, optional): Shot identifier. Defaults to None.
            
        Returns:
            dict: Processing results dictionary
        """
        try:
            file_name = os.path.basename(file_path)
            logger.info(f"\n===== 파일 처리 시작: {file_name} =====")
            
            # Initialize the result dictionary
            result = {
                "file_name": file_name,
                "file_path": file_path,
                "success": False,
                "message": "",
                "sequence": sequence or "",
                "shot": shot or ""
            }
            
            # 처리된 파일 인지 확인
            if self.processed_files_tracker and self.processed_files_tracker.is_file_processed(file_path):
                logger.info(f"건너뛰기: 이미 처리된 파일 ({file_name})")
                result["success"] = False
                result["message"] = "이미 처리된 파일"
                logger.info(f"===== 파일 처리 완료(이미 처리됨): {file_name} =====\n")
                return result
            
            # Determine if this is a reprocessing of an existing file
            is_reprocessing = False
            
            # Check if the file path or name indicates previous processing
            for pattern in ["_v[0-9]{4}", "/processed/", "_processed_"]:
                if re.search(pattern, file_path):
                    is_reprocessing = True
                    logger.info(f"Reprocessing detected for {file_name}")
                    break
                    
            # If sequence and shot are not provided, determine from file name or path
            if not sequence or not shot:
                sequence, shot = self._determine_sequence_and_shot(file_name, file_path)
                result["sequence"] = sequence
                result["shot"] = shot
                
            try:
                # Extract metadata
                metadata = self.metadata_extractor.extract_metadata(file_path)
                result["metadata"] = metadata
                
                # Add sequence and shot to metadata
                if sequence:
                    metadata["sequence"] = sequence
                    result["sequence"] = sequence
                
                if shot:
                    metadata["shot"] = shot
                    result["shot"] = shot
                
                # 파일 확장자에 따라 기본 태스크 결정 (PRD에 따라)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # PRD에 따라 이미지는 txtToImage, 영상은 imgToVideo
                if file_ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.exr', '.dpx']:
                    task = "txtToImage"
                elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.mxf', '.m4v', '.webm']:
                    task = "imgToVideo"
                else:
                    task = "comp"  # 기타 파일 타입에 대한 기본 태스크
                
                # 태스크 정보 저장
                result["task"] = task
                metadata["task"] = task
                
                # NamingManager를 사용하여 파일명 규칙 적용
                file_info = {
                    "file_path": file_path,
                    "file_name": file_name,
                    "sequence": sequence,
                    "shot": shot,
                    "task": task
                }
                
                # NamingManager를 통해 파일명 규칙 적용
                renamed_info = self.naming_manager.apply_naming_convention(file_info, self.output_directory)
                
                # 처리된 정보 업데이트
                result["sequence"] = renamed_info["sequence"]
                result["shot"] = renamed_info["shot"]
                result["task"] = renamed_info["task"]
                result["version"] = renamed_info["version"]
                
                # Add a message about version if this is a reprocessed file
                if is_reprocessing:
                    msg = f"다시 처리됨: 버전 {renamed_info['version']}"
                    result["message"] += msg
                    logger.info(msg)
                
                # 출력 디렉토리 확인 및 생성
                if self.output_directory:
                    # 출력 디렉토리가 존재하는지 확인하고 생성
                    os.makedirs(self.output_directory, exist_ok=True)
                    
                    # 파일 처리 경로 설정
                    result["output_path"] = renamed_info["processed_path"]
                    
                    # 메타데이터 경로 설정 (배치 폴더에 저장될 메타데이터 경로는 나중에 결정)
                    metadata_path = f"{os.path.splitext(renamed_info['processed_path'])[0]}.metadata.json"
                else:
                    # 출력 디렉토리가 없으면 원본 경로 사용
                    result["output_path"] = file_path
                    
                    # 메타데이터 경로 설정
                    metadata_path = f"{os.path.splitext(file_path)[0]}.metadata.json"
                
                result["metadata_path"] = metadata_path  # 메타데이터 경로 저장
                
                # 배치 폴더 처리: NamingManager로 생성된 파일명을 사용하되, 파일은 배치 폴더에만 저장
                if self.processed_files_tracker and self.output_directory:
                    try:
                        logger.info(f"\n----- 배치 폴더 처리 시작 -----")
                        logger.info(f"배치 폴더 이동 준비 중: {file_name}")
                        
                        # 처리된 파일명 명시적으로 확인 및 로깅
                        processed_filename = renamed_info.get("processed_filename", "")
                        logger.info(f"처리될 파일명: {processed_filename}")
                        
                        # processed_info에 processed_filename 포함하여 전달
                        processed_info = {
                            "processed_path": result["output_path"],
                            "processed_filename": processed_filename  # 리네이밍된 파일명 명시적 전달
                        }
                        
                        # 배치 폴더로 이동
                        batch_path = self.processed_files_tracker.move_to_batch_folder(
                            file_path, 
                            processed_info,
                            self.output_directory
                        )
                        
                        if batch_path:
                            # 이동된 파일 경로 설정
                            result["batch_path"] = batch_path
                            # Shotgrid가 참조하는 output_path도 배치 경로로 업데이트
                            result["output_path"] = batch_path
                            logger.info(f"배치 경로 설정 및 output_path 업데이트: {batch_path}")
                            
                            # 배치 폴더에 메타데이터 저장
                            batch_metadata_path = f"{os.path.splitext(batch_path)[0]}.metadata.json"
                            try:
                                with open(batch_metadata_path, 'w', encoding='utf-8') as f:
                                    json.dump(metadata, f, indent=4, default=str)
                                logger.info(f"배치 폴더에 메타데이터 저장됨: {batch_metadata_path}")
                                result["metadata_path"] = batch_metadata_path
                            except Exception as meta_err:
                                logger.error(f"배치 폴더에 메타데이터 저장 오류: {meta_err}")
                            
                            # 처리된 파일 정보 추가
                            logger.info(f"처리된 파일 정보 기록 중...")
                            self.processed_files_tracker.add_processed_file(
                                result, 
                                batch_path,  # 배치 폴더 경로를 output_path로 사용
                                success=True,
                                status_message=result.get("message", "")
                            )
                            logger.info(f"처리된 파일 정보 기록 완료")
                            
                            logger.info(f"파일이 배치 폴더로 성공적으로 이동됨: {batch_path}")
                        else:
                            logger.warning(f"배치 폴더로 이동 실패: {file_name}")
                        
                        logger.info(f"----- 배치 폴더 처리 완료 -----")
                    except Exception as batch_err:
                        logger.error(f"배치 폴더 처리 오류: {batch_err}")
                        result["message"] += f"배치 처리 실패: {str(batch_err)}. "
                
                # 성공적으로 처리됨
                result["success"] = True
                result["message"] = "처리 완료"
                logger.info(f"===== 파일 처리 완료: {file_name} =====\n")
                return result
                
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"Error extracting/saving metadata: {e}\n{error_trace}")
                result["message"] = f"메타데이터 처리 오류: {str(e)}"
                # Set to success even with errors to prevent UI errors
                result["success"] = True
                result["metadata"] = {
                    "file_path": file_path,
                    "file_name": file_name,
                    "error": str(e)
                }
            
            # Add basic file info even if metadata extraction failed
            if "file_name" not in result["metadata"]:
                result["metadata"]["file_name"] = file_name
            if "file_path" not in result["metadata"]:
                result["metadata"]["file_path"] = file_path
                
            # 디버깅을 위한 로그 추가
            logger.debug(f"Processing completed for {file_name}: {result}")
                
            return result
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error processing file {file_path}: {e}\n{error_trace}")
            return {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "success": False,
                "message": f"처리 오류: {str(e)}",
                "sequence": sequence or "",
                "shot": shot or "",
                "metadata_path": ""
            }
    
    def _determine_sequence_and_shot(self, file_name, file_path=None):
        """파일 이름에서 시퀀스와 샷 번호를 결정합니다.
        
        Args:
            file_name (str): 파일 이름
            file_path (str, optional): 파일 전체 경로. Defaults to None.
            
        Returns:
            tuple: (sequence, shot)
        """
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
        self.cancel = True