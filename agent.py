import logging
import os
import importlib
import inspect
from typing import Dict, Any, Optional, Type, List
import re
from datetime import datetime, timezone
# Import service types for type hinting
from services.todoist_service import TodoistService
from services.gemini_service import GeminiService
from services.gdocs_service import GDocsService
from config import ConfigManager


from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class Agent:
    """
    The core agent logic for "Arturito".
    Manages tools, processes tagged tasks, and runs proactive routines.
    """

    AGENT_TAG = "@arturito" # The primary tag to identify tasks for the agent

    def __init__(self,
                 config_manager: ConfigManager,
                 todoist_service: TodoistService,
                 gemini_service: GeminiService,
                 gdocs_service: GDocsService):
        """
        Initializes the Agent with all required services.
        Args: all services and config
        """
        self.config = config_manager
        self.todoist = todoist_service
        self.gemini = gemini_service
        self.gdocs = gdocs_service

        self.services_for_tools = {
            'todoist': self.todoist,
            'gemini': self.gemini,
            'gdocs': self.gdocs,
            'config': {
                'SERPER_API_KEY': self.config.get_setting('SERPER_API_KEY')
                # Add other config vals if tools need them
             }
        }

        self.tool_registry: Dict[str, BaseTool] = {} # to save our tools
        self._load_tools()
        logger.info(f"Agent initialized. Found {len(self.tool_registry)} tools.")

    def _load_tools(self):
        """Dynamically discovers and loads tools from the 'tools' directory."""
        tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
        logger.info(f"Loading tools from directory: {tools_dir}")
        if not os.path.isdir(tools_dir):
             logger.error(f"Tools directory not found: {tools_dir}")
             return

        for filename in os.listdir(tools_dir):
            if filename.endswith('_tool.py') and filename != 'base_tool.py':
                module_name = f"tools.{filename[:-3]}"
                try:
                    # Dynamic import
                    module = importlib.import_module(module_name)

                    # Inspect the module for classes that inherit from BaseTool
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                            # Check if it's a concrete class (not abstract)
                            if not inspect.isabstract(obj):
                                logger.debug(f"Found potential tool class: {obj.__name__} in {module_name}")
                                try:
                                    
                                    tool_instance = obj(self.services_for_tools)
                                    trigger_tag = tool_instance.TRIGGER_TAG

                                    if trigger_tag in self.tool_registry:
                                         logger.warning(f"Duplicate trigger tag '{trigger_tag}' found! Tool {obj.__name__} will overwrite {self.tool_registry[trigger_tag].__class__.__name__}.")

                                    self.tool_registry[trigger_tag] = tool_instance
                                    logger.info(f"Successfully loaded tool: '{obj.__name__}' with trigger tag: '{trigger_tag}'")

                                except Exception as e:
                                     logger.error(f"Failed to instantiate tool {obj.__name__} from {module_name}: {e}", exc_info=True)
                            else:
                                 logger.debug(f"Skipping abstract class {obj.__name__} in {module_name}")

                except ImportError as e:
                    logger.error(f"Failed to import module {module_name}: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error processing module {module_name}: {e}", exc_info=True)

        if not self.tool_registry:
             logger.warning("No tools were loaded successfully!")

    def process_tagged_tasks(self):
        """
        Fetches tasks tagged for the agent, finds the appropriate tool based on
        other tags, executes the tool, and updates the task in Todoist.
        """
        logger.info("Starting 'process_tagged_tasks' routine...")
        try:
            tasks_for_agent = self.todoist.get_tasks_by_filter(self.AGENT_TAG)
        except Exception as e:
            logger.error(f"Failed to fetch tasks for agent tag '{self.AGENT_TAG}': {e}", exc_info=True)
            return

        if not tasks_for_agent:
            logger.info(f"No tasks found with the tag '{self.AGENT_TAG}'.")
            return

        logger.info(f"Found {len(tasks_for_agent)} tasks tagged with '{self.AGENT_TAG}'. Processing...")

        for task in tasks_for_agent:
            task_id = task.id
            task_content = task.content
            task_description = task.description
            labels = task.labels or []
            logger.debug(f"Processing Task ID: {task_id}, Content: '{task_content[:50]}...', Labels: {labels}")

            action_tag: Optional[str] = None
            tool_to_execute: Optional[BaseTool] = None

            for label in labels:
                if label != self.AGENT_TAG and label in self.tool_registry:
                    action_tag = label
                    tool_to_execute = self.tool_registry[action_tag]
                    logger.info(f"Found action tag '{action_tag}' for task {task_id}. Matched tool: {tool_to_execute.__class__.__name__}")
                    break

            if not tool_to_execute:
                logger.warning(f"Task {task_id} has '{self.AGENT_TAG}' but no matching/loaded tool tag found in labels: {labels}. Skipping.")
                continue

            task_details = {
                "id": task_id,
                "content": task_content,
                "description": task_description,
                "labels": labels,
                # Future: Extract links, specific parameters from description/content
            }

            # Execute the tool
            result_comment = ""
            execution_successful = False
            try:
                logger.info(f"Executing tool '{tool_to_execute.__class__.__name__}' for task {task_id}...")
                result_comment = tool_to_execute.execute(task_details)
                execution_successful = True
                logger.info(f"Tool '{tool_to_execute.__class__.__name__}' executed successfully for task {task_id}.")
            except Exception as e:
                logger.error(f"Error executing tool '{tool_to_execute.__class__.__name__}' for task {task_id}: {e}", exc_info=True)
                result_comment = f"Error: Fallo al ejecutar la acción '{action_tag}'.\nDetalles: {e}"
                execution_successful = False

            # Update Todoist task (comment and labels)
            self.update_task_after_processing(task_id, labels, action_tag, execution_successful, result_comment)

        logger.info("'process_tagged_tasks' routine finished.")
    
    def update_task_after_processing(self, task_id: str, original_labels: List[str], action_tag: Optional[str], success: bool, comment: Optional[str]):
         """Helper function to add comment and update labels after tool execution."""
         logger.debug(f"Updating task {task_id} after processing. Success: {success}, Action Tag: {action_tag}")

         if comment:
             self.todoist.add_comment(task_id, comment)
         else:
              logger.debug(f"No comment provided for task {task_id}.")

         new_labels = [label for label in original_labels if label != self.AGENT_TAG and label != action_tag]
         if success:
             new_labels.append("@arturito_hecho")
             logger.info(f"Task {task_id} processed successfully by action '{action_tag}'. Removing agent/action tags.")
         else:
             logger.warning(f"Task {task_id} failed processing for action '{action_tag}'. Removing agent/action tags and leaving potential error tag.")

         # Only update if labels actually changed
         if sorted(new_labels) != sorted(original_labels):
              logger.debug(f"Attempting to update labels for task {task_id} from {original_labels} to {new_labels}")
              update_success = self.todoist.update_task_labels(task_id, new_labels)
              if not update_success:
                   logger.error(f"Failed to update labels for task {task_id} after processing.")
         else:
              logger.debug(f"No label changes required for task {task_id}.")

    

    def run_weekly_review_routine(self):
        logger.warning("Method 'run_weekly_review_routine' not implemented yet.")
        pass

    def run_task_completion_monitor(self):
         logger.warning("Method 'run_task_completion_monitor' not implemented yet.")
         pass

