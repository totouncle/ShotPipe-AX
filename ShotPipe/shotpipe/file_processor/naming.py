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
        sequence = file_info.get("sequence") or "LIG"  # Default sequence
        
        # PRD 요구사항: 시퀀스는 's01', 's02' 형식으로 표현
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
        
        # 출력 디렉토리 결정
        if output_dir:
            target_dir = os.path.join(output_dir, sequence, shot)
            os.makedirs(target_dir, exist_ok=True)
        else:
            target_dir = original_path.parent
            
        # 다음 버전 번호 가져오기
        version = self.get_next_version(target_dir, sequence, shot, task)
        
        # 네이밍 규칙에 따라 새 파일명 생성: [시퀀스]_c001_[task]_v0001
        base_filename = f"{sequence}_{shot}_{task}_{version}"
        new_filename = f"{base_filename}{original_path.suffix}"
        
        # 해당 이름의 파일이 이미 존재하는지 확인
        output_path = Path(target_dir) / new_filename
            
        # 출력 파일이 이미 존재하고 원본과 다른 경우 버전 증가
        if output_path.exists() and str(output_path.absolute()) != str(original_path.absolute()):
            version = self.get_next_version(target_dir, sequence, shot, task)
            new_filename = f"{sequence}_{shot}_{task}_{version}{original_path.suffix}"
            output_path = Path(target_dir) / new_filename
        
        # 파일 정보 업데이트
        file_info["processed_path"] = str(output_path.absolute())
        file_info["sequence"] = sequence
        file_info["shot"] = shot
        file_info["task"] = task
        file_info["version"] = version
        
        logger.info(f"Applied naming convention: {original_path.name} -> {new_filename}")
        return file_info
    
    def _normalize_sequence(self, sequence):
        """
        PRD 요구사항에 맞게 시퀀스 형식을 정규화합니다.
        
        Args:
            sequence (str): 원본 시퀀스 문자열
            
        Returns:
            str: 정규화된 시퀀스 ('s01', 's02' 형식)
        """
        # 빈 시퀀스인 경우 기본값
        if not sequence:
            return "s01"
        
        # 이미 's' 또는 'S'로 시작하고 숫자가 있는 형식이면 표준화
        s_pattern = re.match(r'^[sS](\d+)', sequence)
        if s_pattern:
            seq_num = int(s_pattern.group(1))
            return f"s{seq_num:02d}"
        
        # 숫자만 있는 경우 's' 접두사 추가
        if sequence.isdigit():
            return f"s{int(sequence):02d}"
        
        # 'seq' 또는 'sequence' 형식
        seq_pattern = re.match(r'^(?:seq|sequence)[_\s]*(\d+)', sequence.lower())
        if seq_pattern:
            seq_num = int(seq_pattern.group(1))
            return f"s{seq_num:02d}"
            
        # 특수 시퀀스 처리
        if sequence.upper() == "LIG":
            return "s01"
        if sequence.upper() == "KIAP":
            return "s02"
        if sequence.upper() == "LIG_KIAP":
            return "s03"
        
        # 다른 모든 경우 첫 문자를 01로 변환 (기본적으로 모든 시퀀스를 s01로 변환)
        return "s01"
    
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
