"""
Configuration handling for ShotPipe.
Manages reading and writing of configuration settings.
"""
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """Configuration manager for ShotPipe."""
    
    DEFAULT_CONFIG = {
        "general": {
            "save_processed_to": "processed_files.json",
            "recent_projects": []
        },
        "file_processing": {
            "supported_image_extensions": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".gif", ".bmp", ".webp", ".exr", ".dpx"],
            "supported_video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".mxf", ".m4v", ".webm"],
            "task_mapping": {
                "image": "comp",
                "video": "edit"
            }
        },
        "shotgrid": {
            "server_url": os.getenv("SHOTGRID_URL", ""),
            "script_name": os.getenv("SHOTGRID_SCRIPT_NAME", ""),
            "api_key": os.getenv("SHOTGRID_API_KEY", ""),
            "upload_chunk_size": 10485760,  # 10MB
            "default_project": "AXRD-296",  # 기본 고정 프로젝트
            "auto_select_project": True,    # 앱 시작시 자동 선택
            "show_project_selector": False, # 프로젝트 선택기 숨김
        },
        "ui": {
            "theme": "system",
            "window_size": [1024, 768]
        }
    }
    
    def __init__(self, config_path=None):
        """Initialize configuration."""
        self.config_data = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to user config directory
            home_dir = Path.home()
            self.config_path = home_dir / ".shotpipe" / "config.yaml"
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.load()
        
        # 환경 변수에서 설정 우선 적용
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        if os.getenv("SHOTGRID_URL"):
            self.config_data["shotgrid"]["server_url"] = os.getenv("SHOTGRID_URL")
        
        if os.getenv("SHOTGRID_SCRIPT_NAME"):
            self.config_data["shotgrid"]["script_name"] = os.getenv("SHOTGRID_SCRIPT_NAME")
            
        if os.getenv("SHOTGRID_API_KEY"):
            self.config_data["shotgrid"]["api_key"] = os.getenv("SHOTGRID_API_KEY")
    
    def load(self):
        """Load configuration from file."""
        if not self.config_path.exists():
            self.save()  # Create default config
            return
        
        try:
            with open(self.config_path, "r") as f:
                if self.config_path.suffix == ".json":
                    loaded_config = json.load(f)
                else:  # Default to YAML
                    loaded_config = yaml.safe_load(f)
                
                # Update default config with loaded values
                self._deep_update(self.config_data, loaded_config)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                if self.config_path.suffix == ".json":
                    json.dump(self.config_data, f, indent=4)
                else:  # Default to YAML
                    yaml.dump(self.config_data, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, section, key=None):
        """Get configuration value."""
        if section not in self.config_data:
            return None
        
        if key is None:
            return self.config_data[section]
        
        return self.config_data[section].get(key)
    
    def set(self, section, key, value):
        """Set configuration value."""
        if section not in self.config_data:
            self.config_data[section] = {}
        
        self.config_data[section][key] = value
        self.save()
    
    def _deep_update(self, base_dict, update_dict):
        """Recursively update a dict."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

# Global configuration instance
config = Config()