import logging
import os
import importlib
import inspect
from typing import Dict, Any, Type
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ToolLoader:
    """
    Handles dynamic discovery and loading of tools from the tools directory.
    """
    
    def __init__(self, services_for_tools: Dict[str, Any]):
        self.services_for_tools = services_for_tools
        self.tool_registry: Dict[str, BaseTool] = {}

    def load_tools(self, tools_dir: str) -> Dict[str, BaseTool]:
        """Dynamically discovers and loads tools from the specified directory."""
        logger.info(f"Loading tools from directory: {tools_dir}")
        if not os.path.isdir(tools_dir):
            logger.error(f"Tools directory not found: {tools_dir}")
            return self.tool_registry

        for filename in os.listdir(tools_dir):
            if filename.endswith('_tool.py') and filename != 'base_tool.py':
                module_name = f"tools.{filename[:-3]}"
                try:
                    self._load_tool_from_module(module_name)
                except ImportError as e:
                    logger.error(f"Failed to import module {module_name}: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error processing module {module_name}: {e}", exc_info=True)

        if not self.tool_registry:
            logger.warning("No tools were loaded successfully!")
        return self.tool_registry

    def _load_tool_from_module(self, module_name: str):
        """Loads tools from a single module."""
        module = importlib.import_module(module_name)
        
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                if not inspect.isabstract(obj):
                    logger.debug(f"Found potential tool class: {obj.__name__} in {module_name}")
                    self._instantiate_and_register_tool(obj, module_name)

    def _instantiate_and_register_tool(self, tool_class: Type[BaseTool], module_name: str):
        """Instantiates and registers a single tool."""
        try:
            tool_instance = tool_class(self.services_for_tools)
            trigger_tag = tool_instance.TRIGGER_TAG

            if trigger_tag in self.tool_registry:
                logger.warning(f"Duplicate trigger tag '{trigger_tag}' found! Tool {tool_class.__name__} will overwrite {self.tool_registry[trigger_tag].__class__.__name__}.")

            self.tool_registry[trigger_tag] = tool_instance
            logger.info(f"Successfully loaded tool: '{tool_class.__name__}' with trigger tag: '{trigger_tag}'")
        except Exception as e:
            logger.error(f"Failed to instantiate tool {tool_class.__name__} from {module_name}: {e}", exc_info=True)