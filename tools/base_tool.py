import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING


logger = logging.getLogger(__name__)

class BaseTool(ABC):
    """
    Abstract Base Class for all tools the agent can use.
    Each tool is triggered by a specific Todoist tag.
    """
    # Class attribute that MUST be overridden by subclasses
    TRIGGER_TAG: str = ""

    def __init__(self, services: Dict[str, Any]):
        """
        Initializes the tool with access to necessary services.
        Args:
            services: A dictionary containing instances of required services,
                      e.g., {'todoist': TodoistService, 'gemini': GeminiService, ...}
        """
        if not self.TRIGGER_TAG:
            raise NotImplementedError(f"Tool subclass {self.__class__.__name__} must define a TRIGGER_TAG class attribute.")

        self.services = services

        if not isinstance(self.services, dict):
             raise TypeError("Services must be provided as a dictionary.")

        logger.debug(f"Tool '{self.__class__.__name__}' initialized for tag '{self.TRIGGER_TAG}'.")
    
    @abstractmethod
    def execute(self, task_details: Dict[str, Any]) -> str:
        """
        The main execution logic for the tool.
        Args:
            task_details: A dictionary containing relevant information about the
                          Todoist task that triggered this tool (e.g., id, content,
                          description, labels, extracted_links).
        Returns:
            A string containing the result of the execution (e.g., summary,
            search results, status message) to be added as a comment,
            or an empty string/specific code if no comment is needed but success,
            or raise an exception on failure.
        """
        pass
    
    def _get_service(self, service_name: str) -> Any:
        service = self.services.get(service_name)
        if service is None:
            logger.error(f"Required service '{service_name}' not found for tool {self.__class__.__name__}")
            raise RuntimeError(f"Missing required service '{service_name}' for tool {self.__class__.__name__}")
        return service