"""
Task assigner module for ShotPipe.
Assigns tasks to files based on their type and user configuration.
"""
import logging
import os
from pathlib import Path
from ..config import config

logger = logging.getLogger(__name__)

class TaskAssigner:
    """Assigns appropriate tasks to files based on their type and metadata."""
    
    def __init__(self):
        # PRD에 맞게 기본 태스크 매핑 설정
        self.task_mapping = {
            "image": "txtToImage",
            "video": "imgToVideo"
        }
        
        # 설정 파일에서 매핑 로드 (있으면)
        config_mapping = config.get("file_processing", "task_mapping")
        if config_mapping:
            self.task_mapping.update(config_mapping)
    
    def assign_task(self, file_info):
        """
        Assign a task to a file based on its type.
        
        Args:
            file_info (dict): File information dictionary
        
        Returns:
            dict: Updated file information with task assigned
        """
        # 파일 타입 및 확장자 확인
        file_path = file_info.get("file_path", "")
        file_ext = Path(file_path).suffix.lower() if file_path else ""
        
        # 확장자 기반 파일 타입 결정
        if file_ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.exr', '.dpx']:
            file_type = "image"
        elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.mxf', '.m4v', '.webm']:
            file_type = "video"
        else:
            file_type = "unknown"
        
        # 파일 정보에 파일 타입 설정
        file_info["file_type"] = file_type
        
        # PRD에 따라 파일 타입에 맞는 태스크 할당
        if file_type == "image":
            task = "txtToImage"  # PRD 요구사항
        elif file_type == "video":
            task = "imgToVideo"  # PRD 요구사항
        else:
            # 알 수 없는 타입은 기본값 comp 사용
            task = "comp"
            logger.warning(f"No task mapping found for file type: {file_type}, using 'comp'")
        
        # 파일 정보 업데이트
        file_info["task"] = task
        
        logger.debug(f"Assigned task {task} to {file_info.get('file_name', 'unknown file')}")
        return file_info
    
    def assign_tasks_batch(self, file_infos):
        """
        Assign tasks to a batch of files.
        
        Args:
            file_infos (list): List of file information dictionaries
        
        Returns:
            list: Updated file information list with tasks assigned
        """
        return [self.assign_task(file_info) for file_info in file_infos]
    
    def update_task_mapping(self, file_type, task):
        """
        Update the task mapping for a file type.
        
        Args:
            file_type (str): File type (e.g., "image", "video")
            task (str): Task to assign to this file type
        """
        self.task_mapping[file_type] = task
        
        # Update the configuration
        config.set("file_processing", "task_mapping", self.task_mapping)
        logger.info(f"Updated task mapping: {file_type} -> {task}")
