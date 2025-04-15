"""
Shotgrid uploader module for ShotPipe.
Handles uploading files to Shotgrid.
"""
import os
import time
import json
import threading
import logging
from pathlib import Path
from .api_connector import ShotgridConnector
from .entity_manager import EntityManager
from ..config import config

logger = logging.getLogger(__name__)

class Uploader:
    """Handles uploading files to Shotgrid."""
    
    def __init__(self, connector=None, entity_manager=None):
        """
        Initialize the uploader.
        
        Args:
            connector (ShotgridConnector, optional): Shotgrid connector instance
            entity_manager (EntityManager, optional): Entity manager instance
        """
        self.connector = connector or ShotgridConnector()
        self.entity_manager = entity_manager or EntityManager(self.connector)
        self.chunk_size = config.get("shotgrid", "upload_chunk_size") or 10485760  # 10MB default
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def upload_file(self, file_info, project_name=None, sequence_code=None, shot_code=None, task_name=None, user_email=None, status="wip"):
        """
        Upload a file to Shotgrid.
        
        Args:
            file_info (dict): File information dictionary
            project_name (str, optional): Project name (overridden by hardcoded value)
            sequence_code (str, optional): Sequence code, extracted from file if not provided
            shot_code (str, optional): Shot code, extracted from file if not provided
            task_name (str, optional): Task name, extracted from file if not provided
            user_email (str, optional): User email for task assignment
            status (str, optional): Task status (default: wip)
            
        Returns:
            dict: Upload result information
        """
        # 하드코딩된 프로젝트 이름 사용
        project_name = "AXRD-296"
        
        # 로그 추가 - 업로드 시작
        file_path = file_info.get("processed_path") or file_info.get("file_path")
        file_name = os.path.basename(file_path) if file_path else "알 수 없는 파일"
        logger.info(f"\n\n▶▶▶ Shotgrid 업로드 시작: {file_name} ▶▶▶")
        logger.info(f"프로젝트: {project_name}")
        
        if not self.connector.is_connected():
            error_msg = "Not connected to Shotgrid"
            logger.error(error_msg)
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 연결 없음 ◀◀◀")
            return {"success": False, "error": error_msg}
            
        # Verify file exists
        if not file_path or not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 파일 없음 ◀◀◀")
            return {"success": False, "error": error_msg}
        
        # 파일 크기 로깅
        file_size = os.path.getsize(file_path)
        logger.info(f"파일 크기: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        
        # Extract codes from file_info if not provided
        sequence_code = sequence_code or file_info.get("sequence")
        shot_code = shot_code or file_info.get("shot")
        task_name = task_name or file_info.get("task")
        
        logger.info(f"시퀀스: {sequence_code}, 샷: {shot_code}, 태스크: {task_name}")
        
        if not sequence_code or not shot_code or not task_name:
            error_msg = "Missing required sequence, shot, or task information"
            logger.error(error_msg)
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 필수 정보 누락 ◀◀◀")
            return {"success": False, "error": error_msg}
            
        # Ensure entities exist
        logger.info(f"Shotgrid 엔티티 확인 중...")
        project, sequence, shot, task = self.entity_manager.ensure_entities(
            project_name, sequence_code, shot_code, task_name, user_email, status
        )
        
        if not project or not sequence or not shot or not task:
            error_msg = "Failed to ensure required entities exist"
            logger.error(error_msg)
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 엔티티 확인 실패 ◀◀◀")
            return {"success": False, "error": error_msg}
        
        logger.info(f"엔티티 확인 완료 - 프로젝트ID: {project['id']}, 시퀀스ID: {sequence['id']}, 샷ID: {shot['id']}, 태스크ID: {task['id']}")
        
        # Create version entity
        logger.info(f"Shotgrid 버전 생성 중...")
        version_data = self._create_version(project, shot, task, file_info)
        if not version_data.get("success"):
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 버전 생성 실패 ◀◀◀")
            return version_data
        
        version = version_data["version"]
        logger.info(f"버전 생성 완료 - 버전ID: {version['id']}")
        
        # Upload the file
        logger.info(f"파일 업로드 중...")
        upload_data = self._upload_file_to_version(version, file_path)
        if not upload_data.get("success"):
            logger.error(f"▶▶▶ Shotgrid 업로드 실패: 파일 업로드 실패 ◀◀◀")
            return upload_data
        
        logger.info(f"파일 업로드 완료: {Path(file_path).name}")
        logger.info(f"▶▶▶ Shotgrid 업로드 완료 ◀◀◀\n")
        
        # Return combined result
        return {
            "success": True,
            "version": version,
            "file_path": file_path,
            "project": project,
            "sequence": sequence,
            "shot": shot,
            "task": task
        }
    
    def _create_version(self, project, shot, task, file_info):
        """
        Create a Version entity in Shotgrid.
        
        Args:
            project (dict): Project entity
            shot (dict): Shot entity
            task (dict): Task entity
            file_info (dict): File information dictionary
            
        Returns:
            dict: Result with success status and version entity
        """
        try:
            sg = self.connector.get_connection()
            
            # Extract version name from file_info
            version_name = file_info.get("version", "v0001")
            # We'll include the version name in the description instead of using version_number field
            # since Shotgrid API doesn't accept this field directly
            
            file_path = file_info.get("processed_path") or file_info.get("file_path")
            
            # 원본 파일명 대신 처리된 파일명 사용
            file_name = os.path.basename(file_path)
            
            # 처리된 파일명에서 코드 추출 (시퀀스_샷_태스크_버전)
            base_name = os.path.splitext(file_name)[0]
            
            # Find user if specified in file_info
            user = None
            user_email = file_info.get("user_email") 
            if user_email:
                user = self.entity_manager.find_user(user_email)
            
            # Create version data
            version_data = {
                "project": project,
                "code": file_name,  # 원본 파일명 대신 처리된 파일명 사용
                "description": f"Uploaded by ShotPipe - {version_name}",
                "sg_status_list": "wip",  # 수정됨: 'rev'에서 'wip'으로 변경
                "entity": {"type": "Shot", "id": shot["id"]},
                "sg_task": task,
                "user": user,
                # "version_number" field doesn't exist in Shotgrid API
                "sg_path_to_movie": file_path  # Local file path reference
            }
            
            # Add metadata if available
            if file_info.get("metadata"):
                # Convert metadata to string if it's complex
                metadata_str = json.dumps(file_info["metadata"], default=str)
                version_data["description"] += f"\n\nMetadata: {metadata_str[:500]}..."
            
            # Create the version
            version = sg.create("Version", version_data)
            logger.info(f"Created version: {file_name}")
            
            return {"success": True, "version": version}
        except Exception as e:
            error_msg = f"Error creating version: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _upload_file_to_version(self, version, file_path):
        """
        Upload a file to a Version entity.
        
        Args:
            version (dict): Version entity
            file_path (str): Path to the file
            
        Returns:
            dict: Result with success status
        """
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            sg = self.connector.get_connection()
            file_name = Path(file_path).name
            file_size = os.path.getsize(file_path)
            
            # 파일 타입에 상관없이 동일한 필드 사용
            field_name = "sg_uploaded_movie"
            logger.info(f"업로드 준비: {file_name} ({file_size} bytes, {file_size/1024/1024:.2f} MB)")
            logger.info(f"대상 필드: {field_name}, 버전ID: {version['id']}")
            
            # 모든 미디어 타입에 대해 통합된 필드 목록 사용
            field_alternatives = [
                "sg_uploaded_movie",
                "sg_movie",
                "sg_uploaded_file",
                "sg_path_to_movie",
                "sg_uploaded_image",
                "sg_image",
                "image",
                "thumb",
                "thumbnail",
                "attachments", 
                "attachment_links"
            ]
            
            # Upload with retry logic and alternative fields
            success = False
            last_error = None
            
            for field in field_alternatives:
                for attempt in range(self.max_retries):
                    try:
                        logger.info(f"업로드 시도 {attempt+1}/{self.max_retries} - 필드: '{field}'")
                        
                        # 기본 업로드 시도
                        sg.upload(
                            "Version", 
                            version["id"], 
                            file_path, 
                            field
                        )
                        logger.info(f">>> 업로드 성공: {file_name} (필드: {field}) <<<")
                        success = True
                        return {"success": True, "field": field}
                    except Exception as e:
                        last_error = e
                        if attempt < self.max_retries - 1:
                            logger.warning(f"업로드 시도 {attempt+1} 실패 (필드: '{field}'), 재시도 중: {e}")
                            time.sleep(self.retry_delay)
                        else:
                            logger.warning(f"모든 시도 실패 (필드: '{field}'), 다음 필드 시도 중: {e}")
                
                if success:
                    break
            
            # 업로드 실패 시 대안 메소드 시도
            if not success:
                try:
                    # 모든 파일 타입에 대해 영화 버전 업로드 시도
                    logger.info("Trying to create movie version directly")
                    result = sg.upload_movie_version(file_path, version["id"])
                    logger.info(f"Movie version upload successful: {result}")
                    return {"success": True, "method": "movie_version"}
                except Exception as e:
                    last_error = e
                    logger.warning(f"Movie version upload failed: {e}")
                    
                    # 대안 2: 일반 첨부로 시도
                    try:
                        logger.info("Trying to upload as attachment")
                        sg.upload(
                            "Version", 
                            version["id"], 
                            file_path
                        )
                        logger.info(f"Attachment upload successful")
                        return {"success": True, "method": "attachment"}
                    except Exception as attach_error:
                        logger.warning(f"Attachment upload failed: {attach_error}")
            
            if not success:
                raise last_error or Exception("모든 업로드 시도가 실패했습니다")
            
        except Exception as e:
            error_msg = f"Error uploading file: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def upload_files_batch(self, file_infos, project_name=None, callback=None):
        """
        Upload multiple files to Shotgrid.
        
        Args:
            file_infos (list): List of file information dictionaries
            project_name (str, optional): Project name (overridden by hardcoded value)
            callback (function, optional): Progress callback function
            
        Returns:
            dict: Results with success count, failure count, and details
        """
        # 하드코딩된 프로젝트 이름 사용
        project_name = "AXRD-296"
        
        # 배치 업로드 시작 로그
        logger.info(f"\n\n===== Shotgrid 배치 업로드 시작: {len(file_infos)}개 파일 =====")
        
        results = {
            "total": len(file_infos),
            "success": 0,
            "failure": 0,
            "details": []
        }
        
        for i, file_info in enumerate(file_infos):
            try:
                file_name = file_info.get("file_name") or os.path.basename(file_info.get("file_path", ""))
                logger.info(f"\n----- 파일 {i+1}/{len(file_infos)} 업로드: {file_name} -----")
                
                # Upload file
                upload_result = self.upload_file(file_info, project_name)
                
                # Add to results
                results["details"].append({
                    "file": file_name,
                    "result": upload_result
                })
                
                if upload_result.get("success"):
                    results["success"] += 1
                    logger.info(f"파일 {i+1}/{len(file_infos)} 업로드 성공: {file_name}")
                else:
                    results["failure"] += 1
                    logger.error(f"파일 {i+1}/{len(file_infos)} 업로드 실패: {file_name}")
                    
                # Call progress callback if provided
                if callback:
                    callback(i + 1, len(file_infos), upload_result)
                
            except Exception as e:
                logger.error(f"Error uploading file {file_info.get('file_name')}: {e}")
                results["failure"] += 1
                results["details"].append({
                    "file": file_info.get("file_name"),
                    "result": {"success": False, "error": str(e)}
                })
                
                # Call progress callback if provided
                if callback:
                    callback(i + 1, len(file_infos), {"success": False, "error": str(e)})
        
        # 배치 업로드 완료 로그
        logger.info(f"\n===== Shotgrid 배치 업로드 완료: 총 {len(file_infos)}개 중 {results['success']}개 성공, {results['failure']}개 실패 =====\n")
        
        return results
    
    def upload_files_async(self, file_infos, project_name, callback=None):
        """
        Upload multiple files to Shotgrid asynchronously.
        
        Args:
            file_infos (list): List of file information dictionaries
            project_name (str): Project name
            callback (function, optional): Progress callback function
            
        Returns:
            threading.Thread: Thread object handling the upload
        """
        def upload_worker():
            self.upload_files_batch(file_infos, project_name, callback)
            
        thread = threading.Thread(target=upload_worker)
        thread.daemon = True
        thread.start()
        
        return thread