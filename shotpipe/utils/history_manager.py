"""
Upload history management module for ShotPipe.
"""
import os
import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UploadHistoryManager:
    """Manages the history of uploaded files to prevent duplicates."""
    
    def __init__(self, history_file=None):
        """Initialize the history manager."""
        if history_file is None:
            self.history_file = os.path.join(os.path.expanduser("~/.shotpipe"), "uploaded_files.json")
        else:
            self.history_file = history_file
            
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        self.history = self._load_history()
    
    def _load_history(self):
        """Load history from the JSON file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"uploads": {}}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading upload history: {e}")
            return {"uploads": {}}
            
    def _save_history(self):
        """Save the current history to the JSON file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4, default=str)
        except IOError as e:
            logger.error(f"Error saving upload history: {e}")
    
    def add_upload_entry(self, file_info, sg_version_id):
        """Add an entry for a successfully uploaded file."""
        processed_path = file_info.get("processed_path")
        if not processed_path:
            logger.warning("Cannot add history entry: missing processed_path")
            return
        
        file_hash = self._calculate_file_hash(processed_path)
        if not file_hash:
            return
            
        entry_key = f"{file_info.get('project', 'unknown')}_{file_info.get('sequence', 'unknown')}_{file_info.get('shot', 'unknown')}_{file_info.get('task', 'unknown')}_{file_info.get('version', 'unknown')}"
        
        entry = {
            "processed_filename": os.path.basename(processed_path),
            "original_path": file_info.get("file_path"),
            "size": os.path.getsize(processed_path),
            "hash": file_hash,
            "upload_time": datetime.now().isoformat(),
            "shotgrid_version_id": sg_version_id
        }
        
        # Add or update the entry
        self.history["uploads"][entry_key] = entry
        self._save_history()
        logger.info(f"Added upload entry for {entry['processed_filename']}")
        
    def is_file_uploaded(self, file_info):
        """Check if a file has already been uploaded."""
        processed_path = file_info.get("processed_path")
        if not processed_path or not os.path.exists(processed_path):
            return False  # Cannot check if file doesn't exist
            
        entry_key = f"{file_info.get('project', 'unknown')}_{file_info.get('sequence', 'unknown')}_{file_info.get('shot', 'unknown')}_{file_info.get('task', 'unknown')}_{file_info.get('version', 'unknown')}"
        
        existing_entry = self.history["uploads"].get(entry_key)
        
        if existing_entry:
            # Check if the file content matches (using hash)
            current_hash = self._calculate_file_hash(processed_path)
            if current_hash and current_hash == existing_entry.get("hash"):
                logger.info(f"File already uploaded (match by key and hash): {os.path.basename(processed_path)}")
                return True
        
        # Fallback: Check by file hash only (in case naming changed)
        current_hash = self._calculate_file_hash(processed_path)
        if current_hash:
            for key, entry in self.history["uploads"].items():
                if entry.get("hash") == current_hash:
                    logger.info(f"File already uploaded (match by hash): {os.path.basename(processed_path)} (original key: {key})")
                    return True
                    
        return False
        
    def _calculate_file_hash(self, file_path):
        """Calculate the SHA-256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except IOError as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None 