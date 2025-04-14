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

logger = logging.getLogger(__name__)

class FileScanner:
    """Scans directories for media files and collects file information."""
    
    def __init__(self):
        self.supported_image_extensions = config.get("file_processing", "supported_image_extensions")
        self.supported_video_extensions = config.get("file_processing", "supported_video_extensions")
        self.supported_extensions = self.supported_image_extensions + self.supported_video_extensions
    
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
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory not found or not a directory: {directory_path}")
            return []
        
        logger.info(f"Scanning directory: {directory_path}")
        
        files = []
        processed_pattern = r"s\d+_c\d+_.*_v\d+"  # Pattern for processed files
        
        # Define walk function based on recursion setting
        if recursive:
            items = directory_path.rglob("*")
        else:
            items = directory_path.glob("*")
        
        # Filter and process files
        for item in items:
            if item.is_file() and item.suffix.lower() in self.supported_extensions:
                # Skip files that match the processed file pattern if exclude_processed is True
                if exclude_processed and self._is_processed_file(item):
                    logger.debug(f"Skipping already processed file: {item.name}")
                    continue
                
                file_info = self._create_file_info(item)
                files.append(file_info)
        
        logger.info(f"Found {len(files)} media files in {directory_path}")
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
        processed_patterns = [
            r'.*_s\d+_c\d+.*\.\w+$',               # Standard pattern with sequence and shot
            r'.*_\d{2,4}[_-]c?\d{2,4}\.\w+$',      # Alternative numeric pattern
            r'.*_sq\d+_sh\d+\.\w+$',               # Explicit sq/sh pattern
            r'.*_[Ss][Ee][Qq]\d+_[Ss][Hh][Oo][Tt]\d+.*\.\w+$',  # SEQ/SHOT spelled out
            r'.*_v\d+\.\w+$',                       # Any file with a version number
            r'.*_LIG_c\d+.*\.\w+$',                # LIG sequence pattern
            r'.*_KIAP_c\d+.*\.\w+$'                # KIAP sequence pattern
        ]
        
        for pattern in processed_patterns:
            if re.match(pattern, filename):
                logger.debug(f"File matches processed naming pattern: {pattern}")
                return True
                
        # Check if metadata file exists for this file
        metadata_patterns = [
            os.path.splitext(file_path_str)[0] + ".metadata.json",
            os.path.splitext(file_path_str)[0] + ".json"
        ]
        
        for metadata_path in metadata_patterns:
            if os.path.exists(metadata_path):
                logger.debug(f"Metadata file exists: {metadata_path}")
                return True
            
        # Check if file exists in output directory with same name
        if output_dir and os.path.isdir(output_dir):
            output_file = os.path.join(output_dir, filename)
            if os.path.exists(output_file):
                logger.debug(f"File exists in output directory: {output_file}")
                return True
        
        # Check if the file is in sequence_files.json
        workspace_dir = os.path.expanduser("~/.shotpipe")
        sequence_files_path = os.path.join(workspace_dir, "sequence_files.json")
        
        if os.path.exists(sequence_files_path):
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
        
        logger.debug(f"File not detected as processed: {file_path_str}")
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
