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

    