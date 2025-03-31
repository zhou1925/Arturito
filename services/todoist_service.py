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
        """ Get tasks matching a Todoist filter string: (e.g: 'today', '@arturito' )"""
        logger.debug(f"fetching tasks with filter: {filter_string}")
        try:
            tasks = self.api.get_tasks(filter=filter_string)
            logger.info(f"Found {len(tasks)} tasks matching filter '{filter_string}'.")
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks with filter '{filter_string}': {e}", exc_info=True)
            return []


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
    print("todoist config manager init correclty")