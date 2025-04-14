"""
Entity manager module for ShotPipe.
Handles management of Shotgrid entities (projects, sequences, shots, tasks).
"""
import logging
from .api_connector import ShotgridConnector

logger = logging.getLogger(__name__)

class EntityManager:
    """Manages Shotgrid entities (projects, sequences, shots, tasks)."""
    
    def __init__(self, connector=None):
        """
        Initialize the entity manager.
        
        Args:
            connector (ShotgridConnector, optional): Shotgrid connector instance
        """
        self.connector = connector or ShotgridConnector()
        
    def get_projects(self):
        """
        Get all active projects from Shotgrid.
        
        Returns:
            list: List of projects
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return []
            
        try:
            sg = self.connector.get_connection()
            projects = sg.find(
                "Project",
                [["sg_status", "is", "Active"]],
                ["id", "name", "sg_description"]
            )
            return projects
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    def find_project(self, project_name):
        """
        Find a project by name.
        
        Args:
            project_name (str): Project name
            
        Returns:
            dict: Project entity or None if not found
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        try:
            sg = self.connector.get_connection()
            project = sg.find_one(
                "Project",
                [["name", "is", project_name]],
                ["id", "name", "sg_description"]
            )
            return project
        except Exception as e:
            logger.error(f"Error finding project: {e}")
            return None
    
    def create_project(self, project_name, description=""):
        """
        Create a new project.
        
        Args:
            project_name (str): Project name
            description (str, optional): Project description
            
        Returns:
            dict: Created project entity or None if failed
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        try:
            sg = self.connector.get_connection()
            
            # Check if project already exists
            existing_project = self.find_project(project_name)
            if existing_project:
                logger.info(f"Project '{project_name}' already exists")
                return existing_project
                
            # Create new project
            project_data = {
                "name": project_name,
                "sg_description": description
            }
            
            project = sg.create("Project", project_data)
            logger.info(f"Created project: {project_name}")
            return project
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    def find_sequence(self, project, sequence_code):
        """
        Find a sequence by code in a project.
        
        Args:
            project (dict): Project entity
            sequence_code (str): Sequence code
            
        Returns:
            dict: Sequence entity or None if not found
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project:
            logger.error("Project not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            sequence = sg.find_one(
                "Sequence",
                [
                    ["project", "is", project],
                    ["code", "is", sequence_code]
                ],
                ["id", "code", "description"]
            )
            return sequence
        except Exception as e:
            logger.error(f"Error finding sequence: {e}")
            return None
    
    def create_sequence(self, project, sequence_code, description=""):
        """
        Create a new sequence in a project.
        
        Args:
            project (dict): Project entity
            sequence_code (str): Sequence code
            description (str, optional): Sequence description
            
        Returns:
            dict: Created sequence entity or None if failed
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project:
            logger.error("Project not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            
            # Check if sequence already exists
            existing_sequence = self.find_sequence(project, sequence_code)
            if existing_sequence:
                logger.info(f"Sequence '{sequence_code}' already exists in project '{project['name']}'")
                return existing_sequence
                
            # Create new sequence
            sequence_data = {
                "project": project,
                "code": sequence_code,
                "description": description
            }
            
            sequence = sg.create("Sequence", sequence_data)
            logger.info(f"Created sequence: {sequence_code} in project {project['name']}")
            return sequence
        except Exception as e:
            logger.error(f"Error creating sequence: {e}")
            return None
    
    def find_shot(self, project, sequence, shot_code):
        """
        Find a shot by code in a sequence.
        
        Args:
            project (dict): Project entity
            sequence (dict): Sequence entity
            shot_code (str): Shot code
            
        Returns:
            dict: Shot entity or None if not found
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project or not sequence:
            logger.error("Project or sequence not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            shot = sg.find_one(
                "Shot",
                [
                    ["project", "is", project],
                    ["sg_sequence", "is", sequence],
                    ["code", "is", shot_code]
                ],
                ["id", "code", "description"]
            )
            return shot
        except Exception as e:
            logger.error(f"Error finding shot: {e}")
            return None
    
    def create_shot(self, project, sequence, shot_code, description=""):
        """
        Create a new shot in a sequence.
        
        Args:
            project (dict): Project entity
            sequence (dict): Sequence entity
            shot_code (str): Shot code
            description (str, optional): Shot description
            
        Returns:
            dict: Created shot entity or None if failed
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project or not sequence:
            logger.error("Project or sequence not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            
            # Check if shot already exists
            existing_shot = self.find_shot(project, sequence, shot_code)
            if existing_shot:
                logger.info(f"Shot '{shot_code}' already exists in sequence '{sequence['code']}'")
                return existing_shot
                
            # Create new shot
            shot_data = {
                "project": project,
                "sg_sequence": sequence,
                "code": shot_code,
                "description": description
            }
            
            shot = sg.create("Shot", shot_data)
            logger.info(f"Created shot: {shot_code} in sequence {sequence['code']}")
            return shot
        except Exception as e:
            logger.error(f"Error creating shot: {e}")
            return None
    
    def find_task(self, project, entity, task_name):
        """
        Find a task by name for an entity.
        
        Args:
            project (dict): Project entity
            entity (dict): Entity (Shot, Asset, etc.)
            task_name (str): Task name
            
        Returns:
            dict: Task entity or None if not found
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project or not entity:
            logger.error("Project or entity not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            
            # Determine entity type
            entity_type = entity["type"]
            
            task = sg.find_one(
                "Task",
                [
                    ["project", "is", project],
                    ["entity", "is", {"type": entity_type, "id": entity["id"]}],
                    ["content", "is", task_name]
                ],
                ["id", "content", "sg_status_list"]
            )
            return task
        except Exception as e:
            logger.error(f"Error finding task: {e}")
            return None
    
    def create_task(self, project, entity, task_name, status="wtg"):
        """
        Create a new task for an entity.
        
        Args:
            project (dict): Project entity
            entity (dict): Entity (Shot, Asset, etc.)
            task_name (str): Task name
            status (str, optional): Task status
            
        Returns:
            dict: Created task entity or None if failed
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        if not project or not entity:
            logger.error("Project or entity not provided")
            return None
            
        try:
            sg = self.connector.get_connection()
            
            # Check if task already exists
            existing_task = self.find_task(project, entity, task_name)
            if existing_task:
                logger.info(f"Task '{task_name}' already exists for entity '{entity['code']}'")
                return existing_task
                
            # Create new task
            entity_type = entity["type"]
            task_data = {
                "project": project,
                "entity": {"type": entity_type, "id": entity["id"]},
                "content": task_name,
                "sg_status_list": status
            }
            
            task = sg.create("Task", task_data)
            logger.info(f"Created task: {task_name} for {entity_type} {entity['code']}")
            return task
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
    
    def find_user(self, email):
        """
        Find a user by email.
        
        Args:
            email (str): User email
            
        Returns:
            dict: User entity or None if not found
        """
        if not self.connector.is_connected():
            logger.error("Not connected to Shotgrid")
            return None
            
        try:
            sg = self.connector.get_connection()
            user = sg.find_one(
                "HumanUser",
                [["email", "is", email]],
                ["id", "name", "email"]
            )
            return user
        except Exception as e:
            logger.error(f"Error finding user: {e}")
            return None
    
    def ensure_entities(self, project_name, sequence_code, shot_code, task_name, user_email=None, status="wip"):
        """
        Ensure that all required entities exist, creating them if necessary.
        
        Args:
            project_name (str): Project name
            sequence_code (str): Sequence code
            shot_code (str): Shot code
            task_name (str): Task name
            user_email (str, optional): User email for task assignment
            status (str, optional): Task status (default: wip)
            
        Returns:
            tuple: (project, sequence, shot, task) entities
        """
        # Ensure project exists
        project = self.find_project(project_name)
        if not project:
            project = self.create_project(project_name)
            if not project:
                return None, None, None, None
                
        # Find user if email provided
        user = None
        if user_email:
            user = self.find_user(user_email)
            if not user:
                logger.warning(f"User with email {user_email} not found")
                
        # Ensure sequence exists
        sequence = self.find_sequence(project, sequence_code)
        if not sequence:
            sequence = self.create_sequence(project, sequence_code)
            if not sequence:
                return project, None, None, None
                
        # Ensure shot exists
        shot = self.find_shot(project, sequence, shot_code)
        if not shot:
            shot = self.create_shot(project, sequence, shot_code)
            if not shot:
                return project, sequence, None, None
                
        # Ensure task exists
        task = self.find_task(project, shot, task_name)
        if not task:
            # Create task with specified status
            task = self.create_task(project, shot, task_name, status=status)
            
            # Assign user to task if available
            if task and user:
                try:
                    sg = self.connector.get_connection()
                    sg.update("Task", task["id"], {"task_assignees": [user]})
                    logger.info(f"Assigned user {user['name']} to task {task_name}")
                except Exception as e:
                    logger.error(f"Error assigning user to task: {e}")
                
        return project, sequence, shot, task