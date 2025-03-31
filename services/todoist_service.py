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



