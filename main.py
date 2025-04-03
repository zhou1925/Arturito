import schedule
import time
import logging
import sys
import os

# Import configuration and services
from config import ConfigManager
from services.todoist_service import TodoistService
from services.gemini_service import GeminiService
from services.gdocs_service import GDocsService
from agent import Agent

# --- Global Configuration: Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the Arturito Agent application.
    Initializes services, sets up the scheduler, and runs the main loop.
    """
    logger.info("--- [[[ Starting Arturito Agent ]]] ---")

    # 1. Load Configuration
    logger.info("Loading configuration from .env...")
    try:
        config_manager = ConfigManager()
    except Exception as e:
        logger.critical(f"FATAL: Failed to load configuration: {e}. Exiting.", exc_info=True)
        sys.exit(1)

    # 2. Initialize Services (with Dependency Injection)
    logger.info("Initializing services...")
    try:
        # Order matters if services depend on each other implicitly
        todoist_service = TodoistService(
            api_key=config_manager.get_setting("TODOIST_API_KEY")
        )
        gemini_service = GeminiService(
            google_api_key=config_manager.get_setting("GOOGLE_API_KEY")
        )
        gdocs_service = GDocsService()

        logger.info("Services initialized.")

    except (ValueError, ConnectionError, FileNotFoundError, Exception) as e:
         logger.critical(f"FATAL: Failed to initialize core services: {e}. Exiting.", exc_info=True)
         sys.exit(1)


    # 3. Initialize Agent (Inject services)
    logger.info("Initializing Agent...")
    try:
        agent = Agent(
            config_manager=config_manager,
            todoist_service=todoist_service,
            gemini_service=gemini_service,
            gdocs_service= gdocs_service,
        )
        logger.info("Agent initialized successfully.")
    except Exception as e:
         logger.critical(f"FATAL: Failed to initialize Agent: {e}. Exiting.", exc_info=True)
         sys.exit(1)


    # 4. Setup Scheduler
    logger.info("Setting up scheduled jobs...")
    try:
        # --- Define Schedule ---
        # Process tagged tasks frequently (e.g., every 5 minutes)
        schedule.every(5).minutes.do(agent.process_tagged_tasks)
        logger.info("Scheduled 'process_tagged_tasks' every 5 minutes.")
    except Exception as e:
        logger.critical(f"FATAL: Failed to set up schedule: {e}. Exiting.", exc_info=True)
        sys.exit(1)

    # 5. Run Main Loop
    logger.info("--- [[[ Arturito Agent Running ]]] ---")
    logger.info("Scheduler started. Waiting for jobs...")
    while True:
        try:
            schedule.run_pending()
            # Calculate seconds until the next scheduled job to sleep efficiently
            idle_seconds = schedule.idle_seconds()
            sleep_time = min(idle_seconds, 60) if idle_seconds is not None and idle_seconds > 0 else 60
            logger.debug(f"Scheduler idle. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received (KeyboardInterrupt). Exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"ERROR: An unexpected error occurred in the main loop: {e}", exc_info=True)
            logger.error("Attempting to continue main loop after a short delay...")
            time.sleep(30)

    # 6. Cleanup on Shutdown
    logger.info("--- [[[ Shutting Down Arturito Agent ]]] ---")
    # If services needed explicit cleanup (like DB connections)
    # e.g., if MemoryService was used: memory_service.close()
    logger.info("Application shutdown complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()