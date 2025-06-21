"""
Link Manager for Shotgrid entity relationships and file links.
Provides functionality to retrieve, manage, and utilize Shotgrid link information.
"""
import logging
from typing import List, Dict, Optional, Any
from ..api_connector import ShotgridConnector
from ..entity_manager import EntityManager

logger = logging.getLogger(__name__)

class LinkManager:
    """Manages Shotgrid entity links and relationships."""
    
    def __init__(self, connector: ShotgridConnector = None, entity_manager: EntityManager = None):
        """
        Initialize the link manager.
        
        Args:
            connector: Shotgrid API connector
            entity_manager: Entity manager instance
        """
        self.connector = connector or ShotgridConnector()
        self.entity_manager = entity_manager or EntityManager(self.connector)
        
    def get_existing_versions(self, project_name: str, entity_type: str = "Shot", 
                            entity_code: str = None, task_name: str = None) -> List[Dict]:
        """
        Get existing versions for a specific entity and task.
        
        Args:
            project_name: Project name
            entity_type: Entity type (Shot, Asset, etc.)
            entity_code: Entity code (shot code, asset code)
            task_name: Task name
            
        Returns:
            List of version dictionaries with link information
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.connector.get_connection()
            
            # Find project
            project = self.entity_manager.find_project(project_name)
            if not project:
                logger.warning(f"Project '{project_name}' not found")
                return []
            
            # Build filters
            filters = [["project", "is", project]]
            
            if entity_code:
                # Find entity first
                if entity_type == "Shot":
                    entity = sg.find_one("Shot", 
                                        [["project", "is", project], ["code", "is", entity_code]],
                                        ["id", "code"])
                elif entity_type == "Asset":
                    entity = sg.find_one("Asset",
                                        [["project", "is", project], ["code", "is", entity_code]],
                                        ["id", "code"])
                else:
                    logger.warning(f"Unsupported entity type: {entity_type}")
                    return []
                
                if entity:
                    filters.append(["entity", "is", entity])
                else:
                    logger.warning(f"{entity_type} '{entity_code}' not found")
                    return []
            
            if task_name:
                # Find task
                if entity_code:
                    task = self.entity_manager.find_task(project, entity, task_name)
                    if task:
                        filters.append(["sg_task", "is", task])
                    else:
                        logger.warning(f"Task '{task_name}' not found")
                        return []
            
            # Query versions
            fields = [
                "id", "code", "entity", "sg_task", "created_at", "created_by",
                "description", "sg_path_to_movie", "sg_path_to_frames", 
                "sg_uploaded_movie", "image", "filmstrip_image"
            ]
            
            versions = sg.find("Version", filters, fields, order=[{"field_name": "created_at", "direction": "desc"}])
            
            # Add link information to each version
            for version in versions:
                version["shotgrid_url"] = self._build_shotgrid_url(version)
                version["entity_link"] = self._get_entity_link_info(version.get("entity"))
                version["task_link"] = self._get_task_link_info(version.get("sg_task"))
            
            logger.info(f"Found {len(versions)} versions for {entity_type} '{entity_code}', task '{task_name}'")
            return versions
            
        except Exception as e:
            logger.error(f"Error getting existing versions: {e}")
            return []
    
    def get_related_assets(self, project_name: str, shot_code: str) -> List[Dict]:
        """
        Get assets related to a specific shot.
        
        Args:
            project_name: Project name
            shot_code: Shot code
            
        Returns:
            List of related asset dictionaries
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.connector.get_connection()
            
            # Find project and shot
            project = self.entity_manager.find_project(project_name)
            if not project:
                return []
                
            shot = sg.find_one("Shot", 
                             [["project", "is", project], ["code", "is", shot_code]],
                             ["id", "code", "assets"])
            
            if not shot or not shot.get("assets"):
                logger.info(f"No related assets found for shot '{shot_code}'")
                return []
            
            # Get asset details
            asset_ids = [asset["id"] for asset in shot["assets"]]
            assets = sg.find("Asset",
                           [["id", "in", asset_ids]],
                           ["id", "code", "sg_asset_type", "description", "image"])
            
            # Add link information
            for asset in assets:
                asset["shotgrid_url"] = self._build_shotgrid_url(asset)
                asset["versions"] = self._get_asset_versions(asset)
            
            logger.info(f"Found {len(assets)} related assets for shot '{shot_code}'")
            return assets
            
        except Exception as e:
            logger.error(f"Error getting related assets: {e}")
            return []
    
    def get_file_links(self, version_id: int) -> Dict[str, Any]:
        """
        Get file link information for a specific version.
        
        Args:
            version_id: Version ID
            
        Returns:
            Dictionary with file link information
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return {}
            
        try:
            sg = self.connector.get_connection()
            
            # Get version with file information
            version = sg.find_one("Version", [["id", "is", version_id]], [
                "id", "code", "sg_path_to_movie", "sg_path_to_frames",
                "sg_uploaded_movie", "image", "filmstrip_image"
            ])
            
            if not version:
                logger.warning(f"Version {version_id} not found")
                return {}
            
            # Get published files related to this version
            published_files = sg.find("PublishedFile",
                                    [["version", "is", version]],
                                    ["id", "code", "path", "published_file_type"])
            
            link_info = {
                "version": version,
                "shotgrid_url": self._build_shotgrid_url(version),
                "movie_path": version.get("sg_path_to_movie"),
                "frames_path": version.get("sg_path_to_frames"),
                "uploaded_movie": version.get("sg_uploaded_movie"),
                "thumbnail": version.get("image"),
                "filmstrip": version.get("filmstrip_image"),
                "published_files": published_files
            }
            
            return link_info
            
        except Exception as e:
            logger.error(f"Error getting file links: {e}")
            return {}
    
    def search_similar_files(self, file_name: str, project_name: str, 
                           sequence_code: str = None) -> List[Dict]:
        """
        Search for similar files in Shotgrid based on file name patterns.
        
        Args:
            file_name: File name to search for
            project_name: Project name
            sequence_code: Optional sequence code to limit search
            
        Returns:
            List of similar file dictionaries
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.connector.get_connection()
            
            # Find project
            project = self.entity_manager.find_project(project_name)
            if not project:
                return []
            
            # Extract base name for pattern matching
            base_name = self._extract_base_name(file_name)
            
            # Search in versions
            filters = [
                ["project", "is", project],
                ["code", "contains", base_name]
            ]
            
            if sequence_code:
                # Add sequence filter if specified
                sequence = sg.find_one("Sequence",
                                     [["project", "is", project], ["code", "is", sequence_code]],
                                     ["id", "code"])
                if sequence:
                    filters.append(["entity.Shot.sg_sequence", "is", sequence])
            
            similar_versions = sg.find("Version", filters, [
                "id", "code", "entity", "sg_task", "created_at",
                "description", "sg_uploaded_movie", "image"
            ])
            
            # Add link information
            for version in similar_versions:
                version["shotgrid_url"] = self._build_shotgrid_url(version)
                version["similarity_score"] = self._calculate_similarity(file_name, version["code"])
            
            # Sort by similarity score
            similar_versions.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            logger.info(f"Found {len(similar_versions)} similar files for '{file_name}'")
            return similar_versions
            
        except Exception as e:
            logger.error(f"Error searching similar files: {e}")
            return []
    
    def _build_shotgrid_url(self, entity: Dict) -> str:
        """Build Shotgrid URL for an entity."""
        if not entity or not self.connector.server_url:
            return ""
            
        entity_type = entity.get("type", "Version")
        entity_id = entity.get("id")
        
        if not entity_id:
            return ""
        
        # Remove 'https://' and '/api3/json' from server URL to get base URL
        base_url = self.connector.server_url.replace("/api3/json", "").rstrip("/")
        return f"{base_url}/detail/{entity_type}/{entity_id}"
    
    def _get_entity_link_info(self, entity: Dict) -> Optional[Dict]:
        """Get link information for an entity."""
        if not entity:
            return None
            
        return {
            "type": entity.get("type"),
            "id": entity.get("id"),
            "name": entity.get("name") or entity.get("code"),
            "url": self._build_shotgrid_url(entity)
        }
    
    def _get_task_link_info(self, task: Dict) -> Optional[Dict]:
        """Get link information for a task."""
        if not task:
            return None
            
        return {
            "id": task.get("id"),
            "name": task.get("content"),
            "url": self._build_shotgrid_url(task)
        }
    
    def _get_asset_versions(self, asset: Dict) -> List[Dict]:
        """Get recent versions for an asset."""
        try:
            sg = self.connector.get_connection()
            versions = sg.find("Version",
                             [["entity", "is", asset]],
                             ["id", "code", "created_at"],
                             order=[{"field_name": "created_at", "direction": "desc"}],
                             limit=5)
            return versions
        except Exception as e:
            logger.error(f"Error getting asset versions: {e}")
            return []
    
    def _extract_base_name(self, file_name: str) -> str:
        """Extract base name from file name for pattern matching."""
        # Remove extension
        base = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
        
        # Remove version numbers (v001, v002, etc.)
        import re
        base = re.sub(r'_v\d{3,4}$', '', base)
        
        # Take first part before shot number
        parts = base.split("_")
        if len(parts) > 1:
            return parts[0]
        
        return base
    
    def _calculate_similarity(self, file1: str, file2: str) -> float:
        """Calculate similarity score between two file names."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, file1.lower(), file2.lower()).ratio()
