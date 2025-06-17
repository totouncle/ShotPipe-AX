"""
Shotgrid API connector module for ShotPipe.
Handles connection and authentication with Shotgrid API.
"""
import os
import logging
import sys
from dotenv import load_dotenv
from ..config import config

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 호환성 패치 적용
from .sg_compat import is_patched

# shotgun_api3 모듈 가져오기 시도
try:
    import shotgun_api3
    SHOTGRID_API_AVAILABLE = True
    logger.info(f"Successfully imported shotgun_api3 version: {getattr(shotgun_api3, '__version__', 'unknown')}")
except ImportError as e:
    SHOTGRID_API_AVAILABLE = False
    logger.error(f"shotgun_api3 not installed, Shotgrid integration will be disabled: {e}")

# 환경 변수에서 Shotgrid 연결 정보 가져오기
shotgrid_url = os.getenv('SHOTGRID_URL')
shotgrid_script_name = os.getenv('SHOTGRID_SCRIPT_NAME')
shotgrid_api_key = os.getenv('SHOTGRID_API_KEY')

if shotgrid_url and shotgrid_script_name and shotgrid_api_key:
    logger.info(f"Shotgrid credentials found in .env file: {shotgrid_url}")
else:
    logger.warning("Shotgrid credentials not found in .env file")

class ShotgridConnector:
    """Manages connection to Shotgrid API."""
    
    def __init__(self, server_url=None, script_name=None, api_key=None):
        """
        Initialize the Shotgrid connector.
        
        Args:
            server_url (str, optional): Shotgrid server URL
            script_name (str, optional): Script name for authentication
            api_key (str, optional): API key for authentication
        """
        # 환경 변수나 설정에서 연결 정보 가져오기
        self.server_url = server_url or os.getenv('SHOTGRID_URL') or config.get("shotgrid", "server_url")
        self.script_name = script_name or os.getenv('SHOTGRID_SCRIPT_NAME') or config.get("shotgrid", "script_name")
        self.api_key = api_key or os.getenv('SHOTGRID_API_KEY') or config.get("shotgrid", "api_key")
        self.sg = None
        
        if not SHOTGRID_API_AVAILABLE:
            logger.error("shotgun_api3 not available, Shotgrid integration is disabled")
            return
            
        if not is_patched:
            logger.error("shotgun_api3 patching failed, Shotgrid integration is disabled")
            return
        
        logger.info(f"Connecting with server_url: {self.server_url}, script_name: {self.script_name}")
        self.connect()
    
    def connect(self):
        """
        Connect to Shotgrid API.
        
        Returns:
            bool: Success status
        """
        if not SHOTGRID_API_AVAILABLE:
            return False
        
        if not self.server_url or not self.script_name or not self.api_key:
            logger.error("Shotgrid credentials not configured")
            return False
        
        try:
            self.sg = shotgun_api3.Shotgun(
                self.server_url,
                script_name=self.script_name,
                api_key=self.api_key
            )
            logger.info(f"Connected to Shotgrid server: {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Shotgrid: {e}")
            self.sg = None
            return False
    
    def is_connected(self):
        """
        Check if connected to Shotgrid.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.sg is not None
    
    def get_connection(self):
        """
        Get the Shotgrid connection object.
        
        Returns:
            shotgun_api3.Shotgun: Shotgrid connection object
        """
        if not self.is_connected():
            self.connect()
        return self.sg
    
    def update_credentials(self, server_url=None, script_name=None, api_key=None):
        """
        Update Shotgrid credentials and reconnect.
        
        Args:
            server_url (str, optional): Shotgrid server URL
            script_name (str, optional): Script name for authentication
            api_key (str, optional): API key for authentication
        
        Returns:
            bool: Success status
        """
        if server_url:
            self.server_url = server_url
            config.set("shotgrid", "server_url", server_url)
        
        if script_name:
            self.script_name = script_name
            config.set("shotgrid", "script_name", script_name)
        
        if api_key:
            self.api_key = api_key
            config.set("shotgrid", "api_key", api_key)
        
        # Disconnect and reconnect
        self.sg = None
        return self.connect()
    
    def test_connection(self):
        """
        Test the connection to Shotgrid.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        if not self.is_connected():
            return self.connect()
        
        try:
            # Try to fetch a simple entity to test connection
            self.sg.find_one("Project", [])
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_user_info(self):
        """
        Get current user information from Shotgrid.

        Returns:
            str: User's name or 'Unknown' if not available.
        """
        if not self.is_connected():
            return "연결 안됨"
        
        try:
            # 'current_user' is a property of the shotgun connection object
            user = self.sg.current_user
            if user and 'name' in user:
                return user['name']
            return "알 수 없는 사용자"
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return "정보 조회 실패"