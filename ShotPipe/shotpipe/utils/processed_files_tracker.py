"""
Processed files tracking module for ShotPipe.

이 모듈은 처리된 파일을 추적하고 관리하는 기능을 제공합니다.
이미 처리된 파일을 식별하여 UI에서 자동으로 선택 해제하는 데 사용됩니다.
"""
import os
import json
import hashlib
import datetime
import logging
import shutil
from pathlib import Path
import csv

logger = logging.getLogger(__name__)

class ProcessedFilesTracker:
    """처리된 파일을 추적하고 관리하는 클래스"""
    
    # 이력 버전
    HISTORY_VERSION = "1.0"
    
    def __init__(self, history_file=None):
        """트래커 초기화"""
        if history_file is None:
            self.history_file = os.path.join(os.path.expanduser("~/.shotpipe"), "processed_files.json")
        else:
            self.history_file = history_file
            
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        self.history = self._load_history()
        
        # 배치당 최대 파일 수 (설정 가능)
        self.max_files_per_batch = 100
        
        # 이력 데이터 최대 크기 (항목 수)
        self.max_history_items = 5000
        
        # 이력 데이터가 너무 많아지면 정리
        self._cleanup_history()
    
    def _load_history(self):
        """이력 파일에서 처리된 파일 정보 로드"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "processed_files": {},
                    "batch_info": {
                        "last_batch": 0,
                        "current_batch": "batch01"
                    }
                }
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"처리된 파일 이력 로드 오류: {e}")
            return {
                "processed_files": {},
                "batch_info": {
                    "last_batch": 0,
                    "current_batch": "batch01"
                }
            }
            
    def _save_history(self):
        """현재 이력을 파일에 저장"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4, default=str)
        except IOError as e:
            logger.error(f"처리된 파일 이력 저장 오류: {e}")
    
    def _calculate_file_hash(self, file_path):
        """파일의 SHA-256 해시 계산
        
        대용량 파일의 경우 전체 파일이 아닌 일부만 해시 계산
        """
        try:
            # 파일이 존재하지 않으면 None 반환
            if not os.path.exists(file_path):
                logger.warning(f"해시 계산 불가: 파일이 존재하지 않음 - {file_path}")
                return None
                
            # 파일 크기 확인
            file_size = os.path.getsize(file_path)
            
            hasher = hashlib.sha256()
            
            # 파일 크기에 따라 다른 해시 전략 사용
            with open(file_path, 'rb') as file:
                if file_size < 10 * 1024 * 1024:  # 10MB 미만은 전체 해시
                    # 작은 파일은 전체 해시 계산
                    while True:
                        chunk = file.read(8192)  # 8KB 청크 단위로 읽기
                        if not chunk:
                            break
                        hasher.update(chunk)
                else:
                    # 큰 파일은 부분 해시만 계산 (시작, 중간, 끝)
                    # 파일 시작부분 읽기 (1MB)
                    start_chunk = file.read(1024 * 1024)
                    hasher.update(start_chunk)
                    
                    # 파일 중간으로 이동
                    file.seek(file_size // 2)
                    # 중간 부분 읽기 (1MB)
                    middle_chunk = file.read(1024 * 1024)
                    hasher.update(middle_chunk)
                    
                    # 파일 끝으로 이동 (끝에서 1MB 앞)
                    file.seek(max(0, file_size - 1024 * 1024))
                    # 끝 부분 읽기
                    end_chunk = file.read(1024 * 1024)
                    hasher.update(end_chunk)
                    
                    # 파일 크기도 해시에 포함
                    hasher.update(str(file_size).encode())
                    
                    logger.debug(f"대용량 파일({file_size/1024/1024:.1f}MB)에 대해 부분 해시 계산: {os.path.basename(file_path)}")
            
            return hasher.hexdigest()
        except IOError as e:
            logger.error(f"파일 해시 계산 오류 ({file_path}): {e}")
            return None
    
    def get_or_create_batch_folder(self, output_directory):
        """배치 폴더를 생성하거나 현재 배치 폴더 경로 반환"""
        # 출력 디렉토리에 processed 폴더 구조 생성
        processed_dir = os.path.join(output_directory, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        # 현재 배치 정보 가져오기
        current_batch = self.history["batch_info"]["current_batch"]
        batch_dir = os.path.join(processed_dir, current_batch)
        
        # 현재 배치에 있는 파일 수 확인
        batch_files_count = self._count_files_in_batch(batch_dir)
        
        # 배치에 파일이 너무 많으면 새 배치 생성
        if batch_files_count >= self.max_files_per_batch:
            logger.info(f"현재 배치({current_batch})에 파일이 {batch_files_count}개로 최대치({self.max_files_per_batch})에 도달했습니다. 새 배치를 생성합니다.")
            return self.create_new_batch(output_directory)
        
        # 배치 폴더 생성
        os.makedirs(batch_dir, exist_ok=True)
        return batch_dir
    
    def _count_files_in_batch(self, batch_dir):
        """배치 디렉토리에 있는 파일 수 반환"""
        if not os.path.exists(batch_dir):
            return 0
            
        count = 0
        for root, dirs, files in os.walk(batch_dir):
            count += len(files)
        return count
    
    def create_new_batch(self, output_directory):
        """새 배치 폴더 생성"""
        # 다음 배치 번호 계산
        last_batch = self.history["batch_info"]["last_batch"]
        next_batch = last_batch + 1
        
        # 현재 날짜 가져오기
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        
        # 새 배치 이름 생성 (batch_YYYYMMDD_##)
        batch_name = f"batch_{current_date}_{next_batch:02d}"
        
        # 배치 정보 업데이트
        self.history["batch_info"]["last_batch"] = next_batch
        self.history["batch_info"]["current_batch"] = batch_name
        
        # 새 배치 폴더 생성
        processed_dir = os.path.join(output_directory, "processed")
        batch_dir = os.path.join(processed_dir, batch_name)
        os.makedirs(batch_dir, exist_ok=True)
        
        # 배치 정보 저장
        self._save_history()
        
        logger.info(f"새 배치 폴더 생성됨: {batch_name}")
        return batch_dir
    
    def add_processed_file(self, file_info, output_path, success=False, status_message=""):
        """처리된 파일 정보 추가
        
        Args:
            file_info (dict): 파일 정보 딕셔너리
            output_path (str): 처리된 파일 출력 경로
            success (bool): 처리 성공 여부
            status_message (str): 상태 메시지
        """
        original_path = file_info.get("file_path")
        if not original_path or not output_path:
            logger.warning("이력 항목 추가 불가: 파일 경로 누락")
            return
        
        # 성공하지 않은 경우 이력에 추가하지 않음
        if not success:
            logger.debug(f"처리 실패한 파일은 이력에 추가되지 않음: {original_path}")
            return
            
        # 원본 파일 해시 계산
        file_hash = self._calculate_file_hash(original_path)
        if not file_hash:
            logger.warning(f"이력 항목 추가 불가: 해시 계산 실패 ({original_path})")
            return
            
        # 파일 식별 키 생성
        file_key = file_hash
        
        # 처리 정보 생성
        processed_info = {
            "original_path": original_path,
            "original_filename": os.path.basename(original_path),
            "processed_path": output_path,
            "processed_filename": os.path.basename(output_path),
            "size": os.path.getsize(original_path),
            "hash": file_hash,
            "sequence": file_info.get("sequence", ""),
            "shot": file_info.get("shot", ""),
            "task": file_info.get("task", ""),
            "version": file_info.get("version", ""),
            "processing_time": datetime.datetime.now().isoformat(),
            "batch": self.history["batch_info"]["current_batch"],
            "success": success,
            "status": "완료" if success else "실패",
            "status_message": status_message
        }
        
        # 이력에 추가
        self.history["processed_files"][file_key] = processed_info
        self._save_history()
        logger.info(f"처리 이력 추가됨: {processed_info['original_filename']} -> {processed_info['processed_filename']}")
        return file_key
    
    def is_file_processed(self, file_path, check_name_size=True):
        """파일이 이미 처리되었는지 확인
        
        Args:
            file_path (str): 파일 경로
            check_name_size (bool): 파일명과 크기로 추가 확인 여부
            
        Returns:
            bool: 이미 처리된 파일이면 True, 아니면 False
        """
        if not file_path or not os.path.exists(file_path):
            return False
        
        # 파일 해시 계산
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return False
        
        # 해시로 직접 확인 (가장 정확한 방법)
        if file_hash in self.history["processed_files"]:
            logger.info(f"이미 처리된 파일 (해시 일치): {os.path.basename(file_path)}")
            return True
            
        # 파일명과 크기로 추가 검사 (선택적 검사)
        if check_name_size:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            
            for key, entry in self.history["processed_files"].items():
                # 기본적인 파일명과 크기 검사
                name_match = entry.get("original_filename") == file_name
                size_match = entry.get("size") == file_size
                
                # 이름과 크기가 모두 일치하면 추가 검증
                if name_match and size_match:
                    # 처리 시간과 파일 수정 시간 비교 (처리 시간이 수정 시간보다 나중이어야 함)
                    try:
                        if "processing_time" in entry:
                            proc_time = datetime.datetime.fromisoformat(entry["processing_time"])
                            proc_timestamp = proc_time.timestamp()
                            
                            # 파일이 처리 시간 이후에 수정되었다면 다른 파일로 간주
                            if file_mtime > proc_timestamp:
                                logger.debug(f"파일이 처리 후 수정됨 (다른 파일로 간주): {file_name}")
                                continue
                    except (ValueError, TypeError) as e:
                        logger.warning(f"시간 비교 오류: {e}")
                    
                    logger.info(f"이미 처리된 파일 (이름/크기 일치): {file_name}")
                    return True
                
        return False
    
    def get_processed_files_in_directory(self, directory):
        """지정된 디렉토리에 있는 모든 처리된 파일 목록 반환"""
        processed_files = []
        
        if not directory or not os.path.isdir(directory):
            return processed_files
            
        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
                
        for file_path in files:
            if self.is_file_processed(file_path):
                processed_files.append(file_path)
                
        return processed_files
    
    def move_to_batch_folder(self, original_path, processed_info, output_directory):
        """파일을 배치 폴더로 이동
        
        파일은 배치 폴더 바로 아래에 저장되며, 시퀀스나 샷 등의 하위 폴더는 생성하지 않습니다.
        """
        logger.info(f"======== 배치 폴더 이동 시작: {os.path.basename(original_path)} ========")
        
        # 배치 폴더 확인/생성
        logger.info(f"배치 폴더 확인/생성 중: {output_directory}")
        batch_dir = self.get_or_create_batch_folder(output_directory)
        logger.info(f"배치 폴더 경로: {batch_dir}")
        
        # 처리된 파일명 가져오기 (processed_filename 필드를 우선 사용)
        processed_filename = processed_info.get("processed_filename", "")
        if not processed_filename:
            # 이전 방식 (processed_path에서 파일명 추출)
            processed_filename = os.path.basename(processed_info.get("processed_path", ""))
        if not processed_filename:
            processed_filename = os.path.basename(original_path)
        logger.info(f"처리될 파일명: {processed_filename}")
        
        # 대상 경로 구성 - 배치 폴더 바로 아래에 파일 저장 (하위 폴더 없음)
        target_path = os.path.join(batch_dir, processed_filename)
        logger.info(f"이동 경로: {original_path} -> {target_path}")
        
        # 파일 크기 정보 로깅
        file_size = os.path.getsize(original_path)
        logger.info(f"파일 크기: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        
        # 파일 복사
        try:
            logger.info(f"파일 복사 시작...")
            shutil.copy2(original_path, target_path)
            logger.info(f"파일 복사 완료: {os.path.basename(original_path)} -> {target_path}")
            logger.info(f"======== 배치 폴더 이동 완료 ========")
            return target_path
        except Exception as e:
            logger.error(f"배치 폴더로 파일 이동 오류: {e}")
            logger.error(f"======== 배치 폴더 이동 실패 ========")
            return None
    
    def _cleanup_history(self):
        """이력 데이터가 너무 많아지면 오래된 항목 정리"""
        processed_files = self.history.get("processed_files", {})
        
        # 이력 항목이 최대 크기를 초과하는지 확인
        if len(processed_files) > self.max_history_items:
            logger.info(f"이력 데이터 정리 중: {len(processed_files)}개 항목 > 최대 {self.max_history_items}개")
            
            # 파일 처리 시간을 기준으로 정렬
            items = []
            for key, info in processed_files.items():
                # 처리 시간이 없으면 현재 시간으로 가정
                processing_time = info.get("processing_time", datetime.datetime.now().isoformat())
                items.append((key, info, processing_time))
            
            # 날짜순으로 정렬
            sorted_items = sorted(items, key=lambda x: x[2], reverse=True)
            
            # 최대 크기까지만 유지
            kept_items = sorted_items[:self.max_history_items]
            
            # 새 이력 딕셔너리 생성
            new_processed_files = {}
            for key, info, _ in kept_items:
                new_processed_files[key] = info
            
            # 이력 업데이트
            self.history["processed_files"] = new_processed_files
            
            # 변경사항 저장
            self._save_history()
            
            logger.info(f"이력 데이터 정리 완료: {len(new_processed_files)}개 항목 유지됨")
    
    def get_history_stats(self, filter_by_status=None):
        """이력 데이터 통계 반환
        
        Args:
            filter_by_status (str, optional): 상태별 필터링 (예: "완료", "실패")
            
        Returns:
            dict: 이력 데이터 통계
        """
        processed_files = self.history.get("processed_files", {})
        
        # 상태별 필터링
        if filter_by_status:
            processed_files = {k: v for k, v in processed_files.items() 
                              if v.get("status") == filter_by_status}
        
        stats = {
            "total_files": len(processed_files),
            "batches": {},
            "sequences": {},
            "status": {}
        }
        
        # 배치별, 시퀀스별, 상태별 통계 수집
        for key, info in processed_files.items():
            batch = info.get("batch", "unknown")
            sequence = info.get("sequence", "unknown")
            status = info.get("status", "unknown")
            
            # 배치별 카운트
            if batch not in stats["batches"]:
                stats["batches"][batch] = 0
            stats["batches"][batch] += 1
            
            # 시퀀스별 카운트
            if sequence not in stats["sequences"]:
                stats["sequences"][sequence] = 0
            stats["sequences"][sequence] += 1
            
            # 상태별 카운트
            if status not in stats["status"]:
                stats["status"][status] = 0
            stats["status"][status] += 1
        
        return stats
        
    def export_history(self, export_path=None):
        """이력 데이터를 CSV 파일로 내보내기"""
        if not export_path:
            export_path = os.path.join(os.path.dirname(self.history_file), "processed_files_export.csv")
            
        try:
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 헤더 작성
                writer.writerow(["Hash", "원본 파일명", "처리된 파일명", "시퀀스", "샷", "태스크", "버전", "처리 시간", "배치"])
                
                # 데이터 작성
                for key, info in self.history.get("processed_files", {}).items():
                    writer.writerow([
                        key,
                        info.get("original_filename", ""),
                        info.get("processed_filename", ""),
                        info.get("sequence", ""),
                        info.get("shot", ""),
                        info.get("task", ""),
                        info.get("version", ""),
                        info.get("processing_time", ""),
                        info.get("batch", "")
                    ])
                    
            logger.info(f"이력 데이터 내보내기 완료: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"이력 데이터 내보내기 실패: {e}")
            return None

    def clean_history(self, max_history_items=1000):
        """
        Clean the history data to keep only max_history_items.
        Removes the oldest entries based on processing time.
        
        Args:
            max_history_items (int): Maximum number of history items to keep
        """
        processed_files = self.history.get("processed_files", {})
        
        # If we have fewer items than the max, no need to clean
        if len(processed_files) <= max_history_items:
            return
            
        # Sort files by processing_time (oldest first)
        sorted_files = sorted(
            processed_files.items(),
            key=lambda x: datetime.datetime.fromisoformat(x[1].get("processing_time", datetime.datetime.now().isoformat()))
        )
        
        # Keep only the newest max_history_items
        files_to_keep = sorted_files[-max_history_items:]
        
        # Create new dictionary with only the kept items
        kept_items = {path: data for path, data in files_to_keep}
        
        # Update history with cleaned data
        self.history["processed_files"] = kept_items
        self.history["last_updated"] = datetime.datetime.now().isoformat()
        
        # Save the cleaned history
        self._save_history()
        
        removed_count = len(processed_files) - len(kept_items)
        logger.info(f"{removed_count}개의 오래된 이력 항목이 제거되었습니다.")

    def reset_history(self):
        """Reset the history data completely and save the empty history."""
        # Initialize empty history structure with the correct structure
        self.history = {
            "processed_files": {},
            "batch_info": {
                "last_batch": 0,
                "current_batch": "batch01"
            },
            "version": self.HISTORY_VERSION,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # Save the empty history to file
        self._save_history()
        
        logger.info("성공적으로 모든 처리된 파일 이력이 초기화되었습니다.")
        return True

    def export_history_to_csv(self, output_path):
        """Export processed files history to a CSV file.
        
        Args:
            output_path (str): The path where the CSV file will be saved
            
        Returns:
            str: The path to the saved CSV file or None if failed
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['File Hash', 'Original Path', 'Processed Path', 
                                'Processing Time', 'Batch', 'Status'])
                
                # Write data rows
                for file_hash, file_data in self.history.get('processed_files', {}).items():
                    writer.writerow([
                        file_hash,
                        file_data.get('original_path', ''),
                        file_data.get('processed_path', ''),
                        file_data.get('processing_time', ''),
                        file_data.get('batch', ''),
                        file_data.get('status', '')
                    ])
                    
            logger.info(f"Successfully exported history to CSV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export history to CSV: {e}")
            return None 