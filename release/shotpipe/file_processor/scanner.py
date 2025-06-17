"""
File scanner module for ShotPipe.
Provides functionality for scanning directories and identifying media files.
"""
import os
from pathlib import Path
import logging
from ..config import config
import re
import json
import time
from ..utils.processed_files_tracker import ProcessedFilesTracker  # ProcessedFilesTracker 임포트 추가

logger = logging.getLogger(__name__)

class FileScanner:
    """Scans directories for media files and collects file information."""
    
    def __init__(self):
        self.supported_image_extensions = config.get("file_processing", "supported_image_extensions")
        self.supported_video_extensions = config.get("file_processing", "supported_video_extensions")
        self.supported_extensions = self.supported_image_extensions + self.supported_video_extensions
        self._scanned_files = []  # 스캔된 파일 목록 저장용 속성 추가
        self._skipped_files = []  # 스킵된 파일 목록 추적용 속성 추가
        self.processed_files_tracker = None  # ProcessedFilesTracker 인스턴스 추가
    
    def scan_directory(self, directory_path, recursive=True, exclude_processed=True):
        """
        Scan a directory for media files.
        
        Args:
            directory_path (str): Path to the directory to scan
            recursive (bool): Whether to scan subdirectories
            exclude_processed (bool): Whether to exclude files that appear to be already processed
        
        Returns:
            list: List of dictionaries containing file information
        """
        start_time = time.time()
        
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory not found or not a directory: {directory_path}")
            return []
        
        logger.info(f"Scanning directory: {directory_path} (recursive={recursive}, exclude_processed={exclude_processed})")
        
        files = []
        self._skipped_files = []  # 스킵된 파일 목록 초기화
        
        # Initialize ProcessedFilesTracker if needed
        if exclude_processed and self.processed_files_tracker is None:
            self.processed_files_tracker = ProcessedFilesTracker()
            logger.info("초기화된 처리된 파일 추적기 사용")
        
        # Define walk function based on recursion setting
        if recursive:
            logger.debug(f"Using recursive search (rglob) for {directory_path}")
            items = directory_path.rglob("*")
        else:
            logger.debug(f"Using non-recursive search (glob) for {directory_path}")
            items = directory_path.glob("*")
        
        # 처리 통계 변수
        total_checked = 0
        processed_skipped = 0
        supported_found = 0
        unsupported_skipped = 0
        
        # Filter and process files
        for item in items:
            if item.is_file():
                total_checked += 1
                
                # 지원되는 확장자인지 확인
                if item.suffix.lower() in self.supported_extensions:
                    supported_found += 1
                    
                    # Skip files that match the processed file pattern if exclude_processed is True
                    if exclude_processed:
                        is_processed = False
                        
                        # 우선 ProcessedFilesTracker로 확인 (가장 정확한 방법)
                        if self.processed_files_tracker and self.processed_files_tracker.is_file_processed(str(item)):
                            is_processed = True
                            logger.debug(f"ProcessedFilesTracker에서 처리된 파일로 확인됨: {item.name}")
                        # 패턴 매칭과 기타 방법으로 백업 검사
                        elif self._is_processed_file(item):
                            is_processed = True
                            logger.debug(f"패턴 매칭으로 처리된 파일로 확인됨: {item.name}")
                            
                        if is_processed:
                            processed_skipped += 1
                            logger.debug(f"Skipping already processed file: {item.name}")
                            # 스킵된 파일 정보 저장
                            self._skipped_files.append({
                                "file_path": str(item.absolute()),
                                "file_name": item.name,
                                "file_extension": item.suffix.lower(),
                                "file_size": item.stat().st_size,
                                "file_type": self._determine_file_type(item),
                                "skip_reason": "already_processed"
                            })
                            continue
                    
                    file_info = self._create_file_info(item)
                    files.append(file_info)
                else:
                    unsupported_skipped += 1
                    # 지원되지 않는 파일 유형 추적
                    self._skipped_files.append({
                        "file_path": str(item.absolute()),
                        "file_name": item.name,
                        "file_extension": item.suffix.lower(),
                        "file_size": item.stat().st_size,
                        "file_type": "unsupported",
                        "skip_reason": "unsupported_extension"
                    })
                    if total_checked < 10 or total_checked % 100 == 0:  # 로그 과다 방지
                        logger.debug(f"Skipping unsupported file type: {item.name} (확장자: {item.suffix})")
        
        # 스캔된 파일 목록 저장
        self._scanned_files = files
        
        # 처리 통계 로깅
        logger.info(f"Directory scan completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Files checked: {total_checked}, Supported: {supported_found}, Processed skipped: {processed_skipped}, Unsupported: {unsupported_skipped}")
        
        return files
    
    def _create_file_info(self, file_path):
        """
        Create a file information dictionary for a file.
        
        Args:
            file_path (Path): Path to the file
        
        Returns:
            dict: Dictionary containing file information
        """
        file_type = self._determine_file_type(file_path)
        
        return {
            "file_path": str(file_path.absolute()),
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
            "file_type": file_type,
            "modified_time": file_path.stat().st_mtime,
            "processed": False,
            "processed_path": None,
            "task": None,  # Will be assigned by task_assigner
            "sequence": None,  # Will be assigned during processing
            "shot": "c001",  # Default shot number
            "version": "v0001",  # Default version
        }
    
    def _is_processed_file(self, file_path, output_dir=None):
        """
        Check if a file is already processed.
        
        Args:
            file_path (str): Path to the file
            output_dir (str, optional): Output directory where processed files are stored
            
        Returns:
            bool: True if file is processed, False otherwise
        """
        logger.debug(f"Checking if file is processed: {file_path}")
        
        # Convert Path object to string if needed
        if hasattr(file_path, 'name'):
            filename = file_path.name
            file_path_str = str(file_path)
        else:
            filename = os.path.basename(file_path)
            file_path_str = file_path
        
        # Check naming pattern for processed files
        if self._matches_processed_file_pattern(filename):
            return True
                
        # Check if metadata file exists for this file
        if self._has_metadata_file(file_path_str):
            return True
            
        # Check if file exists in output directory with same name
        if self._exists_in_output_directory(filename, output_dir):
            return True
        
        # Check if the file is in sequence_files.json
        if self._is_in_sequence_files_json(file_path_str, filename):
            return True
        
        logger.debug(f"File not detected as processed: {file_path_str}")
        return False

    def _matches_processed_file_pattern(self, filename):
        """
        Check if filename matches any of the processed file patterns.
        
        Args:
            filename (str): Name of the file to check
            
        Returns:
            bool: True if filename matches any pattern, False otherwise
        """
        # 패턴을 더 제한적으로 수정
        processed_patterns = [
            r'^[sS]\d+_c\d+_.*\.\w+$',             # S01_c001 패턴으로 시작하는 파일
            r'^.*_s\d+_c\d+_.*_v\d+\.\w+$',         # 정확한 시퀀스, 샷, 버전 포함 패턴
            r'^.*_sq\d+_sh\d+_v\d+\.\w+$',          # 명시적 sq/sh 패턴과 버전
            r'^LIG_c\d+_.*_v\d+\.\w+$',             # LIG 시퀀스 패턴과 버전
            r'^KIAP_c\d+_.*_v\d+\.\w+$'             # KIAP 시퀀스 패턴과 버전
        ]
        
        for pattern in processed_patterns:
            if re.match(pattern, filename):
                logger.debug(f"File matches processed naming pattern: {pattern}")
                return True
        
        return False

    def _has_metadata_file(self, file_path_str):
        """
        Check if metadata file exists for the given file.
        
        Args:
            file_path_str (str): String path to the file
            
        Returns:
            bool: True if metadata file exists, False otherwise
        """
        metadata_patterns = [
            os.path.splitext(file_path_str)[0] + ".metadata.json",
            os.path.splitext(file_path_str)[0] + ".json"
        ]
        
        for metadata_path in metadata_patterns:
            if os.path.exists(metadata_path):
                logger.debug(f"Metadata file exists: {metadata_path}")
                return True
                
        return False

    def _exists_in_output_directory(self, filename, output_dir):
        """
        Check if file exists in the output directory.
        
        Args:
            filename (str): Name of the file to check
            output_dir (str, optional): Output directory path
            
        Returns:
            bool: True if file exists in output directory, False otherwise
        """
        if output_dir and os.path.isdir(output_dir):
            output_file = os.path.join(output_dir, filename)
            if os.path.exists(output_file):
                logger.debug(f"File exists in output directory: {output_file}")
                return True
        
        return False

    def _is_in_sequence_files_json(self, file_path_str, filename):
        """
        Check if file is recorded in sequence_files.json.
        
        Args:
            file_path_str (str): String path to the file
            filename (str): Name of the file
            
        Returns:
            bool: True if file is in sequence_files.json, False otherwise
        """
        workspace_dir = os.path.expanduser("~/.shotpipe")
        sequence_files_path = os.path.join(workspace_dir, "sequence_files.json")
        
        if not os.path.exists(sequence_files_path):
            return False
            
        try:
            with open(sequence_files_path, 'r', encoding='utf-8') as f:
                sequence_files = json.load(f)
                
            # Check for exact path match
            if file_path_str in sequence_files.get('files', []):
                logger.debug(f"File found in sequence_files.json: {file_path_str}")
                return True
                
            # Check for filename match (just in case paths changed)
            for processed_file in sequence_files.get('files', []):
                if os.path.basename(processed_file) == filename:
                    logger.debug(f"Filename found in sequence_files.json: {filename}")
                    return True
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read sequence_files.json: {e}")
            
        return False
    
    def _determine_file_type(self, file_path):
        """
        Determine the general file type (image or video) based on extension.
        
        Args:
            file_path (Path): Path to the file
        
        Returns:
            str: "image" or "video"
        """
        extension = file_path.suffix.lower()
        
        if extension in self.supported_image_extensions:
            return "image"
        elif extension in self.supported_video_extensions:
            return "video"
        else:
            return "unknown"
    
    def get_sequence_dict(self):
        """
        Extract sequences from scanned file names. Only recognizes LIG and KIAP as valid sequences.
        
        Returns:
            dict: Dictionary of sequences (key: sequence name, value: list of (file, shot) tuples)
        """
        try:
            logger.info("Extracting sequences from file names (LIG/KIAP only)")
            
            sequences = {
                "LIG": [],
                "KIAP": []
            }
            
            # Only recognize LIG and KIAP sequences
            for file_name in self.get_scanned_filenames():
                # Check if file is in a LIG folder
                if "/LIG/" in file_name or "\\LIG\\" in file_name:
                    seq = "LIG"
                    shot = "c001"
                    shot_match = re.search(r'[cC](\d+)', file_name)
                    if shot_match:
                        shot = f"c{int(shot_match.group(1)):03d}"
                    sequences["LIG"].append((file_name, shot))
                
                # Check if file is in a KIAP folder
                elif "/KIAP/" in file_name or "\\KIAP\\" in file_name:
                    seq = "KIAP"
                    shot = "c001"
                    shot_match = re.search(r'[cC](\d+)', file_name)
                    if shot_match:
                        shot = f"c{int(shot_match.group(1)):03d}"
                    sequences["KIAP"].append((file_name, shot))
                
                # Explicit LIG pattern in filename
                elif re.search(r'(?i)\bLIG\b', file_name):
                    seq = "LIG"
                    shot = "c001"
                    shot_match = re.search(r'[cC](\d+)', file_name)
                    if shot_match:
                        shot = f"c{int(shot_match.group(1)):03d}"
                    sequences["LIG"].append((file_name, shot))
                
                # Explicit KIAP pattern in filename
                elif re.search(r'(?i)\bKIAP\b', file_name):
                    seq = "KIAP"
                    shot = "c001"
                    shot_match = re.search(r'[cC](\d+)', file_name)
                    if shot_match:
                        shot = f"c{int(shot_match.group(1)):03d}"
                    sequences["KIAP"].append((file_name, shot))
                
                # Default to LIG if nothing is matched
                else:
                    sequences["LIG"].append((file_name, "c001"))
            
            # Remove empty sequences
            for seq_name in list(sequences.keys()):
                if len(sequences[seq_name]) < 1:
                    del sequences[seq_name]
            
            logger.info(f"Found {len(sequences)} sequences")
            logger.debug(f"Sequences found: {list(sequences.keys())}")
            
            return sequences
            
        except Exception as e:
            logger.error(f"Error extracting sequences: {e}", exc_info=True)
            # Return a default LIG sequence in case of error
            return {"LIG": [(file_name, "c001") for file_name in self.get_scanned_filenames()]}
    
    def get_skipped_files(self):
        """
        Returns the list of files that were skipped during scanning.
        
        Returns:
            list: List of skipped file information (each file includes file path, name, extension, and skip reason)
        """
        return self._skipped_files
    
    def get_skipped_files_count(self):
        """
        Returns the number of files that were skipped during scanning.
        
        Returns:
            int: Number of skipped files
        """
        return len(self._skipped_files)
    
    def get_skipped_files_by_reason(self, reason=None):
        """
        Filters and returns skipped files by a specific reason.
        
        Args:
            reason (str, optional): Reason to filter by. E.g., "already_processed", "unsupported_extension"
            
        Returns:
            list: Filtered list of skipped files
        """
        if reason is None:
            return self._skipped_files
        
        return [file for file in self._skipped_files if file.get("skip_reason") == reason]
    
    def get_processed_files_summary(self):
        """
        Returns a summary of files that were detected as already processed.
        
        Returns:
            dict: Summary information of processed files including:
                - count: Total number of processed files
                - extensions: Statistics by file extension
                - total_size: Total size of processed files
                - file_list: List of processed file names
        """
        processed_files = self.get_skipped_files_by_reason("already_processed")
        
        # Extension statistics
        extensions = {}
        for file in processed_files:
            ext = file["file_extension"]
            if ext not in extensions:
                extensions[ext] = 0
            extensions[ext] += 1
        
        # Total size of processed files
        total_size = sum(file["file_size"] for file in processed_files)
        
        return {
            "count": len(processed_files),
            "extensions": extensions,
            "total_size": total_size,
            "file_list": [file["file_name"] for file in processed_files]
        }

    def get_scanned_filenames(self):
        """
        Get the filenames of all scanned files.
        
        Returns:
            list: List of filenames
        """
        return [file_info["file_name"] for file_info in self._scanned_files]
