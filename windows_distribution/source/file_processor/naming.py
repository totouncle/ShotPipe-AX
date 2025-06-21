"""
File naming module for ShotPipe.
Provides functionality for applying naming conventions to files.
"""
import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class NamingManager:
    """Manages file naming conventions and version tracking."""
    
    def __init__(self):
        # 네이밍 패턴: [시퀀스]_c001_[task]_v0001
        self.naming_pattern = r"([a-zA-Z0-9]+)_c([0-9]+)_([a-zA-Z0-9]+)_v([0-9]+)"
    
    def apply_naming_convention(self, file_info, output_dir=None):
        """
        Apply naming convention to a file.
        
        Args:
            file_info (dict): File information dictionary
            output_dir (str, optional): Output directory for the processed file
        
        Returns:
            dict: Updated file information with new path and naming information
        """
        # Extract needed information
        sequence = file_info.get("sequence") or "s01"  # 기본 시퀀스를 s01로 변경
        
        # 시퀀스 이름 정규화
        sequence = self._normalize_sequence(sequence)
        
        shot = file_info.get("shot") or "c001"  # Default shot
        
        # Ensure shot starts with 'c' and is properly formatted
        if not shot.startswith('c'):
            shot = f"c{int(shot.replace('c', '').lstrip('0') or 1):03d}"
        else:
            # 숫자 부분만 추출하여 포맷 맞추기
            shot_num = re.search(r'c(\d+)', shot)
            if shot_num:
                shot = f"c{int(shot_num.group(1)):03d}"
            else:
                shot = "c001"
        
        # 파일 확장자에 따라 기본 태스크 결정
        original_path = Path(file_info["file_path"])
        file_ext = original_path.suffix.lower()
        
        # PRD에 따라 이미지는 txtToImage, 영상은 imgToVideo
        if file_ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.exr', '.dpx']:
            default_task = "txtToImage"
        elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.mxf', '.m4v', '.webm']:
            default_task = "imgToVideo"
        else:
            default_task = "comp"  # 기타 파일 타입에 대한 기본 태스크
        
        task = file_info.get("task") or default_task
        
        # 이미 지정된 태스크가 있더라도 PRD에 따라 기본값 재설정
        if task == "comp" or task == "unknown":
            task = default_task
        
        # 출력 디렉토리 결정 - 배치 기반 구조만 사용하도록 수정
        if output_dir:
            # 시퀀스/샷 폴더 생성하지 않고 output_dir 자체를 target_dir로 사용
            target_dir = output_dir
        else:
            target_dir = original_path.parent
        
        # Check if this file is being reprocessed by examining the original filename
        is_reprocessing = False
        current_version = "v0000"  # Default version start
        
        # If file_info has a processed_path from a previous processing, extract that info
        if "processed_path" in file_info and file_info["processed_path"]:
            prev_processed_filename = os.path.basename(file_info["processed_path"])
            prev_info = self.parse_filename(prev_processed_filename)
            if prev_info:
                is_reprocessing = True
                current_version = prev_info["version"]
                logger.info(f"Reprocessing detected. Previous version: {current_version}")
        
        # Also check if the original filename follows our naming pattern
        orig_info = self.parse_filename(original_path.name)
        if orig_info and not is_reprocessing:
            is_reprocessing = True
            current_version = orig_info["version"]
            logger.info(f"Reprocessing a previously named file. Previous version: {current_version}")
        
        # 다음 버전 번호 가져오기
        if is_reprocessing:
            # Calculate next version based on the current version
            version_num = int(current_version[1:])  # Extract number part
            version = f"v{version_num + 1:04d}"  # Increment version
            logger.info(f"Incrementing version for reprocessed file: {current_version} -> {version}")
        else:
            # Get next version from disk
            version = self.get_next_version(target_dir, sequence, shot, task)
        
        # 네이밍 규칙에 따라 새 파일명 생성: [시퀀스]_c001_[task]_v0001
        base_filename = f"{sequence}_{shot}_{task}_{version}"
        new_filename = f"{base_filename}{original_path.suffix}"
        
        # 해당 이름의 파일이 이미 존재하는지 확인
        output_path = Path(target_dir) / new_filename
            
        # 출력 파일이 이미 존재하고 원본과 다른 경우 버전 증가
        # This adds an extra safety check for collision
        if output_path.exists() and str(output_path.absolute()) != str(original_path.absolute()):
            # Get version from existing file
            existing_info = self.parse_filename(output_path.name)
            if existing_info:
                existing_version = existing_info["version"]
                version_num = int(existing_version[1:])
                version = f"v{version_num + 1:04d}"
                logger.info(f"Found existing file with the same name. Incrementing version: {existing_version} -> {version}")
            else:
                # If parsing fails, use standard get_next_version
                version = self.get_next_version(target_dir, sequence, shot, task)
                
            new_filename = f"{sequence}_{shot}_{task}_{version}{original_path.suffix}"
            output_path = Path(target_dir) / new_filename
        
        # 파일 정보 업데이트 - processed_filename 필드 추가
        file_info["processed_filename"] = new_filename  # 파일명만 별도로 저장
        file_info["processed_path"] = str(output_path.absolute())
        file_info["sequence"] = sequence
        file_info["shot"] = shot
        file_info["task"] = task
        file_info["version"] = version
        
        logger.info(f"Applied naming convention: {original_path.name} -> {new_filename}")
        return file_info
    
    def _normalize_sequence(self, sequence):
        """
        특정 시퀀스만 사용하도록 정규화합니다.
        LIG와 KIAP를 우선적으로 사용하고, 사용자가 명시적으로 지정한 시퀀스만 허용합니다.
        
        Args:
            sequence (str): 원본 시퀀스 문자열
            
        Returns:
            str: 정규화된 시퀀스
        """
        # 빈 시퀀스인 경우 기본값
        if not sequence:
            return "LIG"  # 기본값을 LIG로 변경
        
        # 특수 시퀀스 처리 - 대문자로 정규화
        if sequence.upper() in ["LIG", "KIAP", "LIG_KIAP"]:
            return sequence.upper()
            
        # 기타 시퀀스는 사용자가 지정한 그대로 사용
        return sequence
    
    def parse_filename(self, filename):
        """
        Parse a filename according to the naming convention.
        
        Args:
            filename (str): Filename to parse
        
        Returns:
            dict: Dictionary with sequence, shot, task, and version, or None if not matching
        """
        match = re.match(self.naming_pattern, Path(filename).stem)
        
        if not match:
            return None
        
        return {
            "sequence": match.group(1),
            "shot": f"c{int(match.group(2)):03d}",
            "task": match.group(3),
            "version": f"v{int(match.group(4)):04d}"
        }
    
    def get_next_version(self, directory, sequence, shot, task):
        """
        Get the next available version number for a given sequence, shot, and task.
        
        Args:
            directory (str): Directory to scan for existing versions
            sequence (str): Sequence identifier
            shot (str): Shot identifier
            task (str): Task identifier
        
        Returns:
            str: Next version string (e.g., "v0002")
        """
        max_version = 0
        directory_path = Path(directory)
        
        # 이 시퀀스/샷/태스크에 대한 패턴 생성
        prefix = f"{sequence}_{shot}_{task}_v"
        
        # 일치하는 모든 파일 찾기
        try:
            for file in directory_path.glob(f"{prefix}*.*"):
                # 버전 번호 추출
                version_match = re.search(r"v([0-9]+)", file.stem)
                if version_match:
                    version_num = int(version_match.group(1))
                    max_version = max(max_version, version_num)
        except Exception as e:
            logger.error(f"Error searching for versions: {e}")
        
        # 다음 버전 문자열 생성 (v0001 형식)
        next_version = f"v{max_version + 1:04d}"
        
        logger.debug(f"Next version for {sequence}_{shot}_{task}: {next_version}")
        return next_version
