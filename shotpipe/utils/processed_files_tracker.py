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

# QMessageBox를 임포트합니다.
from PyQt5.QtWidgets import QMessageBox

# Import the new hash utility
from .hash_utils import get_file_hash

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
        
        # Build a reverse lookup dictionary for hashes for faster checks
        self._hash_lookup = {
            details['hash']: path
            for path, details in self.history.get("processed_files", {}).items()
            if 'hash' in details
        }
    
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
        
        # 현재 날짜 가져오기 (더 읽기 쉬운 형식)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
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
    
    def add_processed_file(self, file_path, processed_info):
        """처리된 파일 정보 추가. 키는 원본 파일 경로입니다."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Cannot add to history, source file does not exist: {file_path}")
                return

            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            file_hash = get_file_hash(file_path)

            if not file_hash:
                logger.error(f"Could not add to history, failed to calculate hash for {file_path}")
                return

            entry = {
                "mtime": file_mtime,
                "size": file_size,
                "hash": file_hash,
                "processed_info": processed_info # All other data goes here
            }
            
            self.history["processed_files"][file_path] = entry
            self._hash_lookup[file_hash] = file_path # Update lookup table
            self._save_history()
            logger.info(f"Added/updated processing history for: {os.path.basename(file_path)}")

        except Exception as e:
            logger.error(f"Failed to add processed file to history: {e}", exc_info=True)

    def is_file_processed(self, file_path):
        """
        파일이 이미 처리되었는지 하이브리드 방식으로 확인합니다.
        
        1. 경로, 수정시간, 파일 크기를 먼저 비교 (가장 빠름)
        2. 1번이 실패하면 파일 해시를 비교 (정확함)
        
        Returns:
            str: 처리된 경우 스킵 사유, 아닌 경우 None
        """
        if not os.path.exists(file_path):
            return "File does not exist"

        try:
            # 1단계: 빠른 검사 (경로, 수정 시간, 크기)
            if file_path in self.history["processed_files"]:
                history_entry = self.history["processed_files"][file_path]
                
                current_size = os.path.getsize(file_path)
                current_mtime = os.path.getmtime(file_path)

                if history_entry.get("size") == current_size and \
                   history_entry.get("mtime") == current_mtime:
                    logger.debug(f"'{os.path.basename(file_path)}' was already processed (path and mtime match).")
                    return "이미 처리됨 (경로, 시간 일치)"

            # 2단계: 정밀 검사 (파일 해시)
            current_hash = get_file_hash(file_path)
            if not current_hash:
                logger.warning(f"Could not calculate hash for {file_path}, cannot check history via hash.")
                return None # 해시 계산 실패 시, 처리되지 않은 것으로 간주

            if current_hash in self._hash_lookup:
                original_path_from_hash = self._hash_lookup[current_hash]
                logger.debug(f"'{os.path.basename(file_path)}' was already processed (hash match with '{original_path_from_hash}').")
                return f"이미 처리됨 (내용 동일: {os.path.basename(original_path_from_hash)})"

            return None # 처리되지 않은 파일

        except Exception as e:
            logger.error(f"Error checking if file was processed: {e}", exc_info=True)
            return None # 오류 발생 시, 안전하게 처리되지 않은 것으로 간주
    
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
            # 더 명확하고 읽기 쉬운 파일명 생성
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            export_path = os.path.join(os.path.dirname(self.history_file), f"shotpipe_history_{timestamp}.csv")
            
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
        """모든 처리 이력을 초기화합니다."""
        try:
            # 1. 메모리 내 이력 초기화
            self.history = {
                "processed_files": {},
                "batch_info": {
                    "last_batch": 0,
                    "current_batch": "batch01"
                }
            }
            
            # 2. 해시 룩업 테이블 초기화
            self._hash_lookup = {}
            
            # 3. 파일에 변경사항 저장 (초기화된 내용으로 덮어쓰기)
            self._save_history()
            
            # 4. (선택사항) 물리적인 json 파일 삭제
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                logger.info(f"이력 파일 삭제됨: {self.history_file}")

            logger.info("모든 처리 이력이 성공적으로 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"처리 이력 초기화 중 오류 발생: {e}", exc_info=True)

    def show_stats_popup(self):
        """처리 이력 통계를 MessageBox로 표시합니다."""
        try:
            stats = self.get_history_stats()
            if not stats:
                QMessageBox.information(None, "이력 통계", "처리 이력이 없습니다.")
                return

            stats_str = "처리 이력 통계:\n\n"
            for key, value in stats.items():
                # 보기 좋게 키 이름을 변환합니다.
                display_key = key.replace("_", " ").title()
                stats_str += f"- {display_key}: {value}\n"
            
            QMessageBox.information(None, "이력 통계", stats_str)

        except Exception as e:
            logger.error(f"통계 표시 중 오류 발생: {e}", exc_info=True)
            QMessageBox.warning(None, "오류", f"통계를 표시하는 중 오류가 발생했습니다: {str(e)}")

    def export_history_to_csv(self, output_path):
        """이력을 CSV 파일로 내보냅니다."""
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