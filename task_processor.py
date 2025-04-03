import logging
from typing import Dict, List, Optional
from tools.base_tool import BaseTool
from services.todoist_service import TodoistService

logger = logging.getLogger(__name__)

class TaskProcessor:
    """
    Handles processing of tagged tasks, including tool execution and task updates.
    """
    
    def __init__(self, todoist_service: TodoistService, tool_registry: Dict[str, BaseTool], agent_tag: str = "@arturito"):
        self.todoist = todoist_service
        self.tool_registry = tool_registry
        self.AGENT_TAG = agent_tag

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

            action_tag, tool_to_execute = self._find_matching_tool(labels)
            if not tool_to_execute:
                continue

            task_details = {
                "id": task_id,
                "content": task_content,
                "description": task_description,
                "labels": labels,
            }

            result_comment, execution_successful = self._execute_tool(tool_to_execute, action_tag, task_id, task_details)
            self._update_task_after_processing(task_id, labels, action_tag, execution_successful, result_comment)

        logger.info("'process_tagged_tasks' routine finished.")

    def _find_matching_tool(self, labels: List[str]) -> tuple[Optional[str], Optional[BaseTool]]:
        """Finds the matching tool for the given task labels."""
        for label in labels:
            if label != self.AGENT_TAG and label in self.tool_registry:
                action_tag = label
                tool_to_execute = self.tool_registry[action_tag]
                logger.info(f"Found action tag '{action_tag}'. Matched tool: {tool_to_execute.__class__.__name__}")
                return action_tag, tool_to_execute
        logger.warning(f"Task has '{self.AGENT_TAG}' but no matching/loaded tool tag found in labels: {labels}. Skipping.")
        return None, None

    def _execute_tool(self, tool: BaseTool, action_tag: str, task_id: str, task_details: dict) -> tuple[str, bool]:
        """Executes the given tool and returns the result and success status."""
        logger.info(f"Executing tool '{tool.__class__.__name__}' for task {task_id}...")
        try:
            result_comment = tool.execute(task_details)
            logger.info(f"Tool '{tool.__class__.__name__}' executed successfully for task {task_id}.")
            return result_comment, True
        except Exception as e:
            logger.error(f"Error executing tool '{tool.__class__.__name__}' for task {task_id}: {e}", exc_info=True)
            return f"Error: Fallo al ejecutar la acción '{action_tag}'.\nDetalles: {e}", False

    def _update_task_after_processing(self, task_id: str, original_labels: List[str], 
                                    action_tag: Optional[str], success: bool, comment: Optional[str]):
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
            logger.warning(f"Task {task_id} failed processing for action '{action_tag}'. Removing agent/action tags.")

        if sorted(new_labels) != sorted(original_labels):
            logger.debug(f"Attempting to update labels for task {task_id} from {original_labels} to {new_labels}")
            update_success = self.todoist.update_task_labels(task_id, new_labels)
            if not update_success:
                logger.error(f"Failed to update labels for task {task_id} after processing.")