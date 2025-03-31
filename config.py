# config.py
import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages loading and accessing application configuration settings,
    primarily from environment variables and .env files.
    """
    
    EXPECTED_KEYS = [
        "TODOIST_API_KEY",
        "GOOGLE_API_KEY",
        "SERPER_API_KEY",
    ]

    def __init__(self, dotenv_path: Optional[str] = None, override_dotenv: bool = False):
        """
        Initializes the ConfigManager and loads configuration.
        Override is False: .env file takes precedence over existing env vars.
        """
        loaded_path = load_dotenv(dotenv_path=dotenv_path, override=override_dotenv)
        if loaded_path:
            logger.info(f"Configuration loaded from .env file: {loaded_path}")
        else:
            # It's usually critical to have a .env file for this setup
            logger.warning("No .env file found or specified. Application might fail if env vars are not set externally.")


    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a configuration setting by its key from environment variables.
        """
        value = os.getenv(key, default)
        return value

    def get_all_config_dict(self) -> Dict[str, Optional[str]]:
         """Returns a dictionary of the expected configuration values."""
         return {key: os.getenv(key) for key in self.EXPECTED_KEYS}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Initializing Config Manager...")
    try:
        config_manager = ConfigManager()
        print("\n--- Accessing Settings ---")
        todoist_key = config_manager.get_setting("TODOIST_API_KEY")
        print(f"Todoist Key Set: {bool(todoist_key)}")

        print("\n--- All Loaded Config ---")
        all_conf = config_manager.get_all_config_dict()
        for k, v in all_conf.items():
             is_sensitive = 'KEY' in k.upper() or 'PASSWORD' in k.upper()
             print(f"- {k}: {'******' if is_sensitive and v else v if v else 'Not Set'}")

    except Exception as e:
        print(f"Error initializing ConfigManager: {e}")