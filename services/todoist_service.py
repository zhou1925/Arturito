import os
import logging
from typing import Optional, List, Dict, Any
from todoist_api_python.api import TodoistAPI, Task, Comment
from datetime import datetime


logger = logging.getLogger(__name__)

class TodoistService:
    """ handles intereactions with todoist API """

    def __init__(self, api_key: str):
        if not api_key:
            logger.error("Todoist API key is required")
            raise ValueError("Todoist API key missing")
        try:
            self.api = TodoistAPI(api_key)
            self.api.get_projects()
            logger.info("TodoistService sucessfully connected")
        except Exception as e:
            logger.error(f"Failed to initialize Todoist API: {e}", exc_info=True)
            raise ConnectionError(f"Could not connect to Todoist API: {e}") from e
    
    def get_tasks_by_filter(self, filter_string: str) -> List[Task]:
        """ Get tasks matching a Todoist filter string: ('today', '@arturito' )"""
        logger.debug(f"fetching tasks with filter: {filter_string}")
        try:
            tasks = self.api.get_tasks(filter=filter_string)
            logger.info(f"Found {len(tasks)} tasks matching filter '{filter_string}'.")
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks with filter '{filter_string}': {e}", exc_info=True)
            return []

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Gets a single task by its ID."""
        logger.debug(f"Fetching task with ID: {task_id}")
        try:
            task = self.api.get_task(task_id=task_id)
            return task
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {e}", exc_info=True)
            return None

    def add_comment(self, task_id: str, content: str, attachment: Optional[Dict] = None) -> Optional[Comment]:
        """Adds a comment to a specific task, optionally with an attachment."""
        if not content or not content.strip():
            logger.warning(f"Attempted to add empty or whitespace-only comment to task {task_id}")
            return None
        if not task_id:
            logger.warning(f"Attempted to add a comment but ID not received")
            return None
        
        logger.debug(f"Adding comment to task {task_id}: {content[:20]}...")
        try:
            comment = self.api.add_comment(task_id=task_id, content=content, attachment=attachment)
            logger.info(f"Comment added successfully to task {task_id}.")
            return comment
        except Exception as e:
            logger.error(f"Error adding comment to task {task_id}: {e}", exc_info=True)
            return None
    
    def update_task_labels(self, task_id: str, new_labels: List[str]) -> bool:
        """
        Updates the labels/tags of a task, *replacing* all existing ones.
        Use add_task_label or remove_task_label for granular changes.
        """
        logger.debug(f"Replacing labels for task {task_id} with: {new_labels}")
        try:
            is_success = self.api.update_task(task_id=task_id, labels=new_labels)
            if is_success:
                logger.info(f"Labels replaced successfully for task {task_id}.")
            else:
                logger.warning(f"Update task labels API call returned {is_success} for task {task_id}.")
            return is_success
        except Exception as e:
            logger.error(f"Error replacing labels for task {task_id}: {e}", exc_info=True)
            return False

    def add_task(self, content: str, due_string: Optional[str] = None, project_id: Optional[str] = None, labels: Optional[List[str]] = None, section_id: Optional[str] = None, **kwargs: Any) -> Optional[Task]:
        """
        Adds a new task. Accepts standard Todoist arguments and extra kwargs.
        """
        if not content or not content.strip():
            logger.warning("Attempted to add task with empty or whitespace-only content.")
            return None
        logger.debug(f"Adding task: {content[:20]}...")
        try:
            task = self.api.add_task(
                content=content,
                due_string=due_string,
                project_id=project_id,
                labels=labels,
                section_id=section_id,
                **kwargs
            )
            logger.info(f"Task '{task.content}' added successfully with ID: {task.id}")
            return task
        except Exception as e:
            logger.error(f"Error adding task '{content[:20]}...': {e}", exc_info=True)
            return None
    
    def update_task(self, task_id: str, **updates: Any) -> bool:
        """
        Updates a task with the provided keyword arguments.
        Example: update_task(task_id, content="New name", priority=2)
        Valid kwargs include: content, description, labels, priority, due_string,
                              due_date, due_datetime, due_lang, assignee_id.
        Note: Using 'labels' here will *replace* all existing labels.
        """
        if not updates:
            logger.warning(f"Called update_task for task {task_id} with no updates specified.")
            return False

        logger.debug(f"Updating task {task_id} with data: {updates}")
        try:
            is_success = self.api.update_task(task_id=task_id, **updates)
            if is_success:
                logger.info(f"Task {task_id} updated successfully with provided data.")
            else:
                logger.warning(f"General update task API call returned {is_success} for task {task_id}.")
            return is_success
        except Exception as e:
            logger.error(f"Error updating task {task_id} with data {updates}: {e}", exc_info=True)
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """Marks a task as complete. : recieve and ID """
        logger.debug(f"Completing task {task_id}")
        try:
            is_success = self.api.close_task(task_id=task_id)
            if is_success:
                 logger.info(f"Task {task_id} completed successfully.")
            else:
                 logger.warning(f"Close task API call returned {is_success} for task {task_id}.")
            return is_success
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}", exc_info=True)
            return False

    def delete_project(self, project_id: str) -> bool:
        """Deletes a project by its ID.
        Args:
            project_id: The ID of the project to delete.
        Returns:
            True if the project was successfully deleted, False otherwise.
        """
        try:
            is_success = self.api.delete_project(project_id=project_id)
            if is_success:
                logger.info(f"Project {project_id} deleted successfully.")
            else:
                logger.warning(f"Delete project API call returned {is_success} for project {project_id}.")
            return is_success
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}", exc_info=True)
            return False
    
    def create_project(self, name: str) -> Optional[Dict]:
        """Creates a new project.
        Args:
            name: The name of the project.
        Returns:
            The newly created project as a dictionary, or None on failure.
        """
        try:
            project = self.api.add_project(name=name)
            logger.info(f"Project '{name}' created successfully with ID: {project.id}")
            return project
        except Exception as e:
            logger.error(f"Error creating project '{name}': {e}", exc_info=True)
            return None
            

    def get_sections(self, project_id: str) -> Optional[List[Dict]]:
        """Retrieves all sections for a given project ID.
        Args:
            project_id: The ID of the project to retrieve sections from.
        Returns:
            A list of dictionaries representing the sections, or None if an error occurs.
        """
        logger.debug(f"Fetching sections for project ID: {project_id}")
        try:
            sections = self.api.get_sections(project_id=project_id)
            logger.info(f"Found {len(sections)} sections for project {project_id}.")
            return sections
        except Exception as e:
            logger.error(f"Error fetching sections for project {project_id}: {e}", exc_info=True)
            return None

    def create_section(self, project_id: str, name: str) -> Optional[Dict]:
        """Creates a new section in a project.
        Args:
            project_id: The ID of the project to create the section in.
            name: The name of the section.
        Returns:
            The newly created section as a dictionary, or None on failure.
        """
        logger.debug(f"Creating section '{name}' in project ID: {project_id}")
        try:
            section = self.api.add_section(name=name, project_id=project_id)
            logger.info(f"Section '{name}' created successfully in project {project_id} with ID: {section.id}")
            return section
        except Exception as e:
            logger.error(f"Error creating section '{name}' in project {project_id}: {e}", exc_info=True)
            return None

    def delete_section(self,section_id: str) -> bool:
        try:
            is_success = self.api.delete_section(section_id=section_id)
            logger.info(f"Section '{section_id}' deleted successfully")
            return True
        except Exception as error:
            logger.error(f"Error deleting: {error}", exc_info=True)
            return False

    def get_task_comments(self, task_id: str) -> Optional[List[Comment]]:
        """Retrieves all comments for a given task ID.
        Args:
            task_id: The ID of the task to retrieve comments from.
        Returns:
            A list of Comment objects, or None if an error occurs.
        """
        logger.debug(f"Fetching comments for task ID: {task_id}")
        try:
            comments = self.api.get_comments(task_id=task_id)
            logger.info(f"Found {len(comments)} comments for task {task_id}.")
            return comments
        except Exception as e:
            logger.error(f"Error fetching comments for task {task_id}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    import sys

    import time

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    try:
        from config import ConfigManager
    except ImportError:
        print("Error: Could not import ConfigManager. Make sure 'config.py' exists in the parent directory.")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Initializing ConfigManager to get Todoist Key...")
    try:
        config = ConfigManager()
        api_key = config.get_setting("TODOIST_API_KEY")

        if not api_key:
            print("TODOIST_API_KEY not found in config. Exiting test.")
            logger.error("TODOIST_API_KEY not found in configuration.")
        else:
            print("Initializing TodoistService...")
            todoist_service = TodoistService(api_key=api_key)

            print("\n--- Testing Task Fetching ---")
            test_filter = "@arturito" # @buscar, @arturito
            print(f"Fetching tasks with filter: '{test_filter}'...")
            filtered_tasks = todoist_service.get_tasks_by_filter(test_filter)
            
            if filtered_tasks:
                print(f"Found {len(filtered_tasks)} tasks:")
                for t in filtered_tasks:
                    print(f"task ID: {t.id}")
            else:
                print(f"No tasks found with filter '{test_filter}'. Cannot run update tests on existing tasks.")
            

            test_task_id = filtered_tasks[0].id if filtered_tasks else ""
            
            print("\n--- Testing task id fetching ---")
            test_get_task_by_id = todoist_service.get_task_by_id(test_task_id)
            #print(test_get_task_by_id)
            print(f"task: {test_get_task_by_id.content} - ID: {test_get_task_by_id.id}")

            print("\n--- Testing adding a comment to a task by id ---")
            comment_test = "hey I am a comment!"
            todoist_service.add_comment(test_task_id, comment_test)
            print("--- comment added --- ")

            time.sleep(1)
            print("\n--- Testing update labels of a task ---")
            labels_to_add = ["revisado"]
            
            current_labels = test_get_task_by_id.labels
            new_labels = current_labels + labels_to_add
            label_added = todoist_service.update_task_labels(test_task_id, new_labels)
            test_get_task_by_id = todoist_service.get_task_by_id(test_task_id)

            if "revisado" in test_get_task_by_id.labels:
                print("label added successfully ", test_get_task_by_id.labels)

            print("\n--- labels updated! ---")
            
            time.sleep(1)
            print("\n--- Testing create task ---")
            project_id = test_get_task_by_id.project_id if test_get_task_by_id.project_id else ""
            section_id = test_get_task_by_id.section_id if test_get_task_by_id.section_id else ""
            due_string = ""
            labels = []
            test_create_task = todoist_service.add_task(
                content="test task",
                due_string=due_string,
                project_id=project_id,
                labels=labels,
                section_id=section_id
            )
            print("\n--- task added! ---")

            time.sleep(1)
            print(f"\n--- Testing Content Update on Task ID: {test_create_task.id} ---")
            general_updates = {
                    "content": f"General Update @ {datetime.now().strftime('%H:%M:%S')}",
                    "priority": 4
                }
            print(f"  Applying general updates: {general_updates}")
            general_updated = todoist_service.update_task(test_create_task.id, **general_updates)
            
            
            time.sleep(1)
            print("\n--- Testing complete task ---")
            completed = todoist_service.complete_task(test_create_task.id)
            print("\n--- task completed! ---")

            time.sleep(1)
            print("\n--- Testing Project Creation and Deletion ---")
            test_project_name = "Test Project"
            print(f"Creating project '{test_project_name}'...")
            new_project = todoist_service.create_project(name=test_project_name)
            time.sleep(1)
            print("\n--- Testing Section Creation, Retrieval, and Deletion ---")
            test_section_name = "Test Section"
            print(f"Creating section '{test_section_name}' in project {new_project.id}...")
            new_section = todoist_service.create_section(project_id=new_project.id, name=test_section_name)

            if section_task:
                print(f"Task '{section_task.content}' added to section '{test_section_name}' (ID: {new_section.id}).")

                time.sleep(1)
                print("\n--- Testing Task Comments ---")
                comment_text1 = "This is comment 1."
                comment_text2 = "This is comment 2."

                comment1 = todoist_service.add_comment(section_task.id, comment_text1)
                comment2 = todoist_service.add_comment(section_task.id, comment_text2)

                if comment1 and comment2:
                    print("Comments added successfully.")

                    time.sleep(1)
                    print("\n--- Testing Get Task Comments ---")
                    task_comments = todoist_service.get_task_comments(section_task.id)

                    if task_comments:
                        print(f"Found {len(task_comments)} comments for task '{section_task.content}':")
                        for comment in task_comments:
                            print(f"- {comment.content}")
                    else:
                        print(f"No comments found for task '{section_task.content}'.")

                else:
                    print("Failed to add comments to the task.")

            else:
                print(f"Failed to add task to section '{test_section_name}'.")
            

            if new_section:
                time.sleep(10)
                print(f"Retrieving sections for project {new_project.id}...")
                sections = todoist_service.get_sections(project_id=new_project.id)

                if sections:
                    print(f"Found {len(sections)} sections.")
                    section_to_delete_id = new_section.id
                    print(f"Deleting section '{test_section_name}' (ID: {section_to_delete_id})...")
                    deleted_section = todoist_service.delete_section(section_id=section_to_delete_id)

                    if deleted_section:
                        print(f"Section '{test_section_name}' (ID: {section_to_delete_id}) deleted successfully.")
                    else:
                        print(f"Failed to delete section '{test_section_name}' (ID: {section_to_delete_id}).")
                else:
                    print(f"No sections found for project {new_project.id}.")
            else:
                print(f"Failed to create section '{test_section_name}' in project {new_project.id}.")


            if new_project:
                time.sleep(1)
                deleted = todoist_service.delete_project(new_project.id)
                if deleted:
                    print(f"Project '{test_project_name}' (ID: {new_project.id}) deleted successfully.")
            print("\n--- Testing Project Creation and Deletion ---")
            test_project_name = "Test Project"
            print(f"Creating project '{test_project_name}'...")
            new_project = todoist_service.create_project(name=test_project_name)



            if new_project:
                time.sleep(1)
                deleted = todoist_service.delete_project(new_project.id)
                if deleted:
                    print(f"Project '{test_project_name}' (ID: {new_project.id}) deleted successfully.")

    except FileNotFoundError as e:
        print(f"File Not Found Error: {e}")
        logger.exception("File Not Found error during testing.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        logger.exception("Configuration error during testing.")
    except ConnectionError as e:
        print(f"Connection Error: {e}")
        logger.exception("Connection error during testing.")
    except ImportError as e:
         print(f"Import Error: {e}")
         logger.exception("Import error during testing.")
    except TypeError as e:
        print(f"Type Error during initialization or testing: {e}")
        logger.exception("Type Error during testing.")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        logger.exception("Unexpected error during testing.")