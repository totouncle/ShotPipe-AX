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
    
    def __init__(self, file_paths, metadata_extractor, sequence_dict=None, selected_sequence=None, output_directory=None):
        """
        Initialize the processing thread.
        
        Args:
            file_paths (list): List of file paths to process
            metadata_extractor (MetadataExtractor): Metadata extractor instance
            sequence_dict (dict, optional): Dictionary mapping files to sequences. Defaults to None.
            selected_sequence (str, optional): Selected sequence name. Defaults to None.
            output_directory (str, optional): Output directory for processed files. Defaults to None.
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
                    sequence, shot = self._determine_sequence_and_shot(file_name)
                    
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
            file_path (str): Path of the file to process
            sequence (str, optional): Sequence name. Defaults to None.
            shot (str, optional): Shot number. Defaults to None.
            
        Returns:
            dict: Processing result
        """
        try:
            file_name = os.path.basename(file_path)
            logger.info(f"Processing file: {file_path}")
            
            # Initialize result dictionary
            result = {
                "file_name": file_name,
                "file_path": file_path,
                "success": False,
                "message": "",
                "sequence": sequence or "",
                "shot": shot or "",
                "metadata": {},
                "output_path": file_path,  # Default to original path
                "metadata_path": "",  # 메타데이터 파일 경로
                "task": "comp"  # 기본 작업 유형 추가
            }
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                result["message"] = "파일을 찾을 수 없습니다"
                return result
            
            # Extract metadata from the file using the MetadataExtractor instance
            try:
                # Make sure we have a valid MetadataExtractor instance
                if not hasattr(self, 'metadata_extractor') or self.metadata_extractor is None:
                    logger.error("Missing metadata_extractor instance")
                    # Create a new instance as fallback
                    from .metadata import MetadataExtractor
                    self.metadata_extractor = MetadataExtractor()
                
                # Check if the method exists
                if not hasattr(self.metadata_extractor, 'extract_metadata'):
                    logger.error("Invalid metadata_extractor object (missing extract_metadata method)")
                    # Try to create a basic metadata dictionary
                    metadata = {
                        "file_path": file_path,
                        "file_name": file_name,
                        "file_extension": os.path.splitext(file_path)[1].lower(),
                        "file_size": os.path.getsize(file_path),
                        "error": "메타데이터 추출기 초기화 실패"
                    }
                else:
                    # Extract metadata using the extractor
                    metadata = self.metadata_extractor.extract_metadata(file_path)
                
                # Ensure metadata is a dictionary, even if extraction returns None
                if metadata is None:
                    metadata = {}
                    logger.warning(f"No metadata extracted for {file_name}, using empty dictionary")
                
                result["metadata"] = metadata
                
                # Add sequence and shot information to metadata
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
                
                # Determine output path
                if self.output_directory:
                    # 네이밍 매니저에서 설정한 processed_path 사용
                    output_path = renamed_info["processed_path"]
                    result["output_path"] = output_path
                    
                    # 출력 디렉토리 생성
                    output_dir = os.path.dirname(output_path)
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Copy file to output directory with the new name
                    try:
                        shutil.copy2(file_path, output_path)
                        logger.info(f"Copied and renamed file to: {output_path}")
                        
                        # 리네이밍된 결과 로그 출력 (원본 경로 -> 대상 경로)
                        relative_src = os.path.relpath(file_path)
                        relative_dst = os.path.relpath(output_path)
                        logger.info(f"파일 리네이밍: {relative_src} -> {relative_dst}")
                    except Exception as copy_err:
                        logger.error(f"Error copying file to output directory: {copy_err}")
                        result["message"] += f"파일 복사 실패: {str(copy_err)}. "
                    
                    # Use output path for metadata
                    metadata_path = f"{os.path.splitext(output_path)[0]}.metadata.json"
                else:
                    # Keep file in original location
                    output_dir = os.path.dirname(file_path)
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Use original path for metadata
                    metadata_path = f"{os.path.splitext(file_path)[0]}.metadata.json"
                
                result["metadata_path"] = metadata_path  # 메타데이터 경로 저장
                
                # Check if save_metadata method exists
                if not hasattr(self.metadata_extractor, 'save_metadata'):
                    logger.error("Invalid metadata_extractor object (missing save_metadata method)")
                    # Try to save metadata directly
                    try:
                        with open(metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=4, ensure_ascii=False)
                        result["success"] = True
                        result["message"] = "메타데이터 직접 저장됨"
                        logger.info(f"Metadata directly saved to {metadata_path}")
                    except Exception as e:
                        logger.error(f"Failed to directly save metadata: {e}")
                        result["message"] = f"메타데이터 저장 실패: {str(e)}"
                        # Still mark as successful if we got this far
                        result["success"] = True
                else:
                    # Save using the extractor method
                    if self.metadata_extractor.save_metadata(metadata, metadata_path):
                        logger.info(f"Metadata saved to {metadata_path}")
                        result["success"] = True
                        result["message"] = "처리 완료"
                    else:
                        logger.error(f"Failed to save metadata to {metadata_path}")
                        result["message"] = "메타데이터 저장 실패"
                        # Still mark as successful if we got this far
                        result["success"] = True
                
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
    
    def _determine_sequence_and_shot(self, file_name):
        """Determine sequence and shot for a file.
        
        Args:
            file_name (str): Name of the file
            
        Returns:
            tuple: (sequence, shot)
        """
        # If we have a selected sequence and it exists in the dictionary
        if self.selected_sequence and self.selected_sequence in self.sequence_dict:
            # Try to find the file in this sequence
            for seq_file, seq_shot in self.sequence_dict[self.selected_sequence]:
                if seq_file == file_name:
                    return self.selected_sequence, seq_shot
        
        # If we have sequence dictionary, try to find the file in any sequence
        if self.sequence_dict:
            for seq_name, files in self.sequence_dict.items():
                for seq_file, seq_shot in files:
                    if seq_file == file_name:
                        return seq_name, seq_shot
        
        # If we couldn't find sequence info, try to extract it from the file name
        sequence = ""
        sequence_match = re.search(r'([sS][0-9]+)', file_name)
        if sequence_match:
            sequence = sequence_match.group(1).upper()
        else:
            # Try other common sequence patterns
            seq_patterns = [
                r'(seq[0-9]+)',  # seq01
                r'(sequence[0-9]+)',  # sequence01
                r'(sq[0-9]+)',   # sq01
                r'_(s[0-9]+)_',   # _s01_
                r'(MP[0-9])',    # MP4
                r'(U[0-9]+)'     # U7166812697
            ]
            
            for pattern in seq_patterns:
                match = re.search(pattern, file_name, re.IGNORECASE)
                if match:
                    sequence = match.group(1).upper()
                    break
            
        shot_number = self._extract_shot_number(file_name)
        if shot_number:
            # Format is already handled in _extract_shot_number
            return sequence, shot_number
        
        # 파일 내용에 LIG, KIAP이 포함되어 있는지 확인
        if "LIG" in file_name:
            return "LIG", "c001"
        elif "KIAP" in file_name:
            return "KIAP", "c001"
                
        # PRD에 따라 특별히 처리해야 하는 파일명 패턴
        # 파일 이름이 IMG로 시작하는 경우 기본 시퀀스와 샷 할당
        if file_name.startswith("IMG"):
            return "LIG", "c001"  # PRD 요구사항에 따라 LIG 프로젝트로 설정
            
        # 파일 경로와 확장자에서 기본 시퀀스 유추
        ext = os.path.splitext(file_name)[1].lower()
        if ext in ['.mp4', '.mov', '.avi']:
            return "LIG", "c001"  # 영상 파일은 LIG 프로젝트로 기본 설정
        elif ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
            return "LIG", "c001"  # 이미지 파일은 LIG 프로젝트로 기본 설정
            
        # If all else fails, return default sequence and shot
        return "LIG", "c001"  # 기본값도 LIG 프로젝트로 설정
    
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