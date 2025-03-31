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

    def add_comment(self, task_id: str, content: str) -> Optional[Comment]:
        """Adds a comment to a specific task."""
        if not content or not content.strip():
            logger.warning(f"Attempted to add empty or whitespace-only comment to task {task_id}")
            return None
        if not task_id:
            logger.warning(f"Attempted to add a comment but ID not received")

        logger.debug(f"Adding comment to task {task_id}: {content[:20]}...")
        try:
            comment = self.api.add_comment(task_id=task_id, content=content)
            logger.info(f"Comment added successfully to task {task_id}.")
            return comment
        except Exception as e:
            logger.error(f"Error adding comment to task {task_id}: {e}", exc_info=True)
            return None

if __name__ == '__main__':
    import sys

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
            print(f"task: {test_get_task_by_id.content} - ID: {test_get_task_by_id.id}")

            print("\n--- Testing adding a comment to a task by id ---")
            comment_test = "hey I am a comment!"
            todoist_service.add_comment(test_get_task_by_id.id, comment_test)
            print("--- comment added --- ")



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