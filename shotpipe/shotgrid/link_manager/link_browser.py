"""
Link Browser for browsing and searching Shotgrid entities and their relationships.
Provides UI-friendly methods to browse existing content.
"""
import logging
from typing import List, Dict, Optional, Any, Tuple
from .link_manager import LinkManager

logger = logging.getLogger(__name__)

class LinkBrowser:
    """Browser for Shotgrid entities and links."""
    
    def __init__(self, link_manager: LinkManager = None):
        """
        Initialize the link browser.
        
        Args:
            link_manager: LinkManager instance
        """
        self.link_manager = link_manager or LinkManager()
        
    def browse_project_structure(self, project_name: str) -> Dict[str, Any]:
        """
        Browse the complete project structure with sequences, shots, and tasks.
        
        Args:
            project_name: Project name
            
        Returns:
            Hierarchical structure dictionary
        """
        if not self.link_manager.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return {}
            
        try:
            sg = self.link_manager.connector.get_connection()
            
            # Find project
            project = self.link_manager.entity_manager.find_project(project_name)
            if not project:
                logger.warning(f"Project '{project_name}' not found")
                return {}
            
            # Get sequences
            sequences = sg.find("Sequence",
                              [["project", "is", project]],
                              ["id", "code", "description"],
                              order=[{"field_name": "code", "direction": "asc"}])
            
            structure = {
                "project": {
                    "id": project["id"],
                    "name": project["name"],
                    "url": self.link_manager._build_shotgrid_url(project)
                },
                "sequences": {}
            }
            
            for sequence in sequences:
                # Get shots for this sequence
                shots = sg.find("Shot",
                              [["project", "is", project], ["sg_sequence", "is", sequence]],
                              ["id", "code", "description", "sg_status_list"],
                              order=[{"field_name": "code", "direction": "asc"}])
                
                sequence_data = {
                    "info": {
                        "id": sequence["id"],
                        "code": sequence["code"],
                        "description": sequence.get("description", ""),
                        "url": self.link_manager._build_shotgrid_url(sequence)
                    },
                    "shots": {}
                }
                
                for shot in shots:
                    # Get tasks for this shot
                    tasks = sg.find("Task",
                                  [["project", "is", project], ["entity", "is", shot]],
                                  ["id", "content", "sg_status_list", "task_assignees"],
                                  order=[{"field_name": "content", "direction": "asc"}])
                    
                    # Get version count for this shot
                    version_count = len(sg.find("Version", [["entity", "is", shot]], ["id"]))
                    
                    shot_data = {
                        "info": {
                            "id": shot["id"],
                            "code": shot["code"],
                            "description": shot.get("description", ""),
                            "status": shot.get("sg_status_list", ""),
                            "url": self.link_manager._build_shotgrid_url(shot),
                            "version_count": version_count
                        },
                        "tasks": {}
                    }
                    
                    for task in tasks:
                        # Get version count for this task
                        task_version_count = len(sg.find("Version", 
                                                       [["sg_task", "is", task]], ["id"]))
                        
                        task_data = {
                            "id": task["id"],
                            "name": task["content"],
                            "status": task.get("sg_status_list", ""),
                            "assignees": [user.get("name", "") for user in task.get("task_assignees", [])],
                            "url": self.link_manager._build_shotgrid_url(task),
                            "version_count": task_version_count
                        }
                        
                        shot_data["tasks"][task["content"]] = task_data
                    
                    sequence_data["shots"][shot["code"]] = shot_data
                
                structure["sequences"][sequence["code"]] = sequence_data
            
            logger.info(f"Built project structure for '{project_name}': {len(sequences)} sequences")
            return structure
            
        except Exception as e:
            logger.error(f"Error browsing project structure: {e}")
            return {}
    
    def search_entities(self, project_name: str, search_term: str, 
                       entity_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for entities by name/code across different entity types.
        
        Args:
            project_name: Project name
            search_term: Search term
            entity_types: List of entity types to search (default: ["Shot", "Asset", "Sequence"])
            
        Returns:
            List of matching entities with link information
        """
        if not entity_types:
            entity_types = ["Shot", "Asset", "Sequence"]
            
        if not self.link_manager.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.link_manager.connector.get_connection()
            
            # Find project
            project = self.link_manager.entity_manager.find_project(project_name)
            if not project:
                return []
            
            results = []
            
            for entity_type in entity_types:
                # Build search filters
                filters = [
                    ["project", "is", project],
                    {
                        "filter_operator": "any",
                        "filters": [
                            ["code", "contains", search_term],
                            ["description", "contains", search_term]
                        ]
                    }
                ]
                
                # Define fields based on entity type
                fields = ["id", "code", "description"]
                if entity_type == "Shot":
                    fields.extend(["sg_sequence", "sg_status_list"])
                elif entity_type == "Asset":
                    fields.extend(["sg_asset_type", "sg_status_list"])
                elif entity_type == "Sequence":
                    fields.extend(["shots"])
                
                entities = sg.find(entity_type, filters, fields)
                
                for entity in entities:
                    # Get version count
                    version_count = len(sg.find("Version", [["entity", "is", entity]], ["id"]))
                    
                    entity_info = {
                        "type": entity_type,
                        "id": entity["id"],
                        "code": entity["code"],
                        "description": entity.get("description", ""),
                        "status": entity.get("sg_status_list", ""),
                        "url": self.link_manager._build_shotgrid_url(entity),
                        "version_count": version_count
                    }
                    
                    # Add type-specific information
                    if entity_type == "Shot" and entity.get("sg_sequence"):
                        entity_info["sequence"] = entity["sg_sequence"].get("name", "")
                    elif entity_type == "Asset" and entity.get("sg_asset_type"):
                        entity_info["asset_type"] = entity["sg_asset_type"]
                    elif entity_type == "Sequence" and entity.get("shots"):
                        entity_info["shot_count"] = len(entity["shots"])
                    
                    results.append(entity_info)
            
            # Sort results by relevance (exact matches first, then partial matches)
            results.sort(key=lambda x: (
                0 if search_term.lower() == x["code"].lower() else 1,
                0 if search_term.lower() in x["code"].lower() else 1,
                x["code"]
            ))
            
            logger.info(f"Found {len(results)} entities matching '{search_term}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching entities: {e}")
            return []
    
    def get_recent_activity(self, project_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent activity (versions, tasks updates, etc.) in the project.
        
        Args:
            project_name: Project name
            limit: Maximum number of results
            
        Returns:
            List of recent activity items
        """
        if not self.link_manager.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.link_manager.connector.get_connection()
            
            # Find project
            project = self.link_manager.entity_manager.find_project(project_name)
            if not project:
                return []
            
            # Get recent versions
            recent_versions = sg.find("Version",
                                    [["project", "is", project]],
                                    ["id", "code", "entity", "sg_task", "created_at", 
                                     "created_by", "description", "image"],
                                    order=[{"field_name": "created_at", "direction": "desc"}],
                                    limit=limit)
            
            activity_items = []
            
            for version in recent_versions:
                entity_info = ""
                if version.get("entity"):
                    entity_info = f"{version['entity']['type']} {version['entity']['name']}"
                
                task_info = ""
                if version.get("sg_task"):
                    task_info = version["sg_task"]["name"]
                
                creator_info = ""
                if version.get("created_by"):
                    creator_info = version["created_by"]["name"]
                
                activity_item = {
                    "type": "version_created",
                    "title": f"Version: {version['code']}",
                    "description": version.get("description", ""),
                    "entity": entity_info,
                    "task": task_info,
                    "created_by": creator_info,
                    "created_at": version["created_at"],
                    "url": self.link_manager._build_shotgrid_url(version),
                    "thumbnail": version.get("image")
                }
                
                activity_items.append(activity_item)
            
            logger.info(f"Retrieved {len(activity_items)} recent activity items")
            return activity_items
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def get_entity_relationships(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """
        Get all relationships for a specific entity.
        
        Args:
            entity_type: Type of entity (Shot, Asset, etc.)
            entity_id: Entity ID
            
        Returns:
            Dictionary with relationship information
        """
        if not self.link_manager.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return {}
            
        try:
            sg = self.link_manager.connector.get_connection()
            
            # Get the entity
            entity = sg.find_one(entity_type, [["id", "is", entity_id]], 
                               ["id", "code", "name", "description"])
            
            if not entity:
                logger.warning(f"{entity_type} {entity_id} not found")
                return {}
            
            relationships = {
                "entity": {
                    "type": entity_type,
                    "id": entity_id,
                    "code": entity.get("code", ""),
                    "name": entity.get("name", ""),
                    "description": entity.get("description", ""),
                    "url": self.link_manager._build_shotgrid_url(entity)
                },
                "versions": [],
                "tasks": [],
                "notes": [],
                "published_files": []
            }
            
            # Get versions
            versions = sg.find("Version",
                             [["entity", "is", entity]],
                             ["id", "code", "sg_task", "created_at", "created_by", "description"],
                             order=[{"field_name": "created_at", "direction": "desc"}])
            
            for version in versions:
                version_info = {
                    "id": version["id"],
                    "code": version["code"],
                    "task": version.get("sg_task", {}).get("name", "") if version.get("sg_task") else "",
                    "created_at": version["created_at"],
                    "created_by": version.get("created_by", {}).get("name", "") if version.get("created_by") else "",
                    "description": version.get("description", ""),
                    "url": self.link_manager._build_shotgrid_url(version)
                }
                relationships["versions"].append(version_info)
            
            # Get tasks
            tasks = sg.find("Task",
                          [["entity", "is", entity]],
                          ["id", "content", "sg_status_list", "task_assignees"],
                          order=[{"field_name": "content", "direction": "asc"}])
            
            for task in tasks:
                task_info = {
                    "id": task["id"],
                    "name": task["content"],
                    "status": task.get("sg_status_list", ""),
                    "assignees": [user.get("name", "") for user in task.get("task_assignees", [])],
                    "url": self.link_manager._build_shotgrid_url(task)
                }
                relationships["tasks"].append(task_info)
            
            # Get notes
            notes = sg.find("Note",
                          [["note_links", "is", entity]],
                          ["id", "subject", "content", "created_by", "created_at"],
                          order=[{"field_name": "created_at", "direction": "desc"}],
                          limit=10)
            
            for note in notes:
                note_info = {
                    "id": note["id"],
                    "subject": note.get("subject", ""),
                    "content": note.get("content", ""),
                    "created_by": note.get("created_by", {}).get("name", "") if note.get("created_by") else "",
                    "created_at": note["created_at"],
                    "url": self.link_manager._build_shotgrid_url(note)
                }
                relationships["notes"].append(note_info)
            
            # Get published files
            published_files = sg.find("PublishedFile",
                                     [["entity", "is", entity]],
                                     ["id", "code", "path", "published_file_type", "created_at"],
                                     order=[{"field_name": "created_at", "direction": "desc"}])
            
            for pub_file in published_files:
                file_info = {
                    "id": pub_file["id"],
                    "code": pub_file["code"],
                    "path": pub_file.get("path", {}).get("local_path", "") if pub_file.get("path") else "",
                    "file_type": pub_file.get("published_file_type", {}).get("name", "") if pub_file.get("published_file_type") else "",
                    "created_at": pub_file["created_at"],
                    "url": self.link_manager._build_shotgrid_url(pub_file)
                }
                relationships["published_files"].append(file_info)
            
            logger.info(f"Retrieved relationships for {entity_type} {entity_id}")
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting entity relationships: {e}")
            return {}
    
    def find_linked_entities(self, project_name: str, search_pattern: str) -> List[Tuple[str, Dict]]:
        """
        Find entities that might be linked to a file based on naming patterns.
        
        Args:
            project_name: Project name
            search_pattern: Pattern to search for (file name, sequence, etc.)
            
        Returns:
            List of tuples (relationship_type, entity_info)
        """
        if not self.link_manager.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            # Extract potential sequence and shot codes from pattern
            import re
            
            # Pattern: sequence_shot_task_version
            match = re.match(r'([A-Za-z]+\d*)_([A-Za-z]*\d+)_([A-Za-z]+)_v(\d+)', search_pattern)
            
            results = []
            
            if match:
                seq_code, shot_code, task_name, version = match.groups()
                
                # Search for exact matches
                entities = self.search_entities(project_name, shot_code, ["Shot"])
                for entity in entities:
                    if entity["code"] == shot_code:
                        results.append(("exact_shot_match", entity))
                
                entities = self.search_entities(project_name, seq_code, ["Sequence"])
                for entity in entities:
                    if entity["code"] == seq_code:
                        results.append(("exact_sequence_match", entity))
            
            # Search for partial matches
            similar_files = self.link_manager.search_similar_files(search_pattern, project_name)
            for similar_file in similar_files[:5]:  # Limit to top 5 similar files
                entity_info = {
                    "type": "Version",
                    "id": similar_file["id"],
                    "code": similar_file["code"],
                    "url": similar_file["shotgrid_url"],
                    "similarity": similar_file.get("similarity_score", 0)
                }
                results.append(("similar_version", entity_info))
            
            logger.info(f"Found {len(results)} linked entities for pattern '{search_pattern}'")
            return results
            
        except Exception as e:
            logger.error(f"Error finding linked entities: {e}")
            return []
