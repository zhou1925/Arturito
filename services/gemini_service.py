import google.generativeai as genai
import os
import logging
import time
from typing import Optional, Dict, Any, List, Union
from google.api_core.exceptions import ResourceExhausted, InternalServerError, DeadlineExceeded, GoogleAPIError, NotFound

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GenaiContent = Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]

class GeminiService:
    """
    Handles interactions with the Google Generative AI (Gemini) models.
    Sends prompts, receives generated content, and includes basic retry logic
    for transient API errors.
    """

    DEFAULT_MODEL = "models/gemini-1.5-flash"

    DEFAULT_GENERATION_CONFIG = {
        "temperature": 0.7,
        "top_p": 1.0,
        "top_k": 40,
        # "max_output_tokens": 8192, # Example: Max for gemini-1.5-flash
    }

    # --- Retry Settings ---
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 2
    BACKOFF_FACTOR = 2

    def __init__(self, google_api_key: Optional[str] = None, default_model: str = DEFAULT_MODEL):
        """
        Initializes the Gemini Service.

        Args:
            google_api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            default_model: The default model name (e.g., "models/gemini-1.5-flash").
                           Must start with 'models/' or 'tunedModels/'.
        """
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("Google API Key not provided or found in GOOGLE_API_KEY environment variable.")
            raise ValueError("Google API Key is required for GeminiService.")
        
        # Validate the default model name format
        if not (default_model.startswith("models/") or default_model.startswith("tunedModels/")):
             logger.error(f"Invalid default_model format: '{default_model}'. Must start with 'models/' or 'tunedModels/'.")
             raise ValueError(f"Invalid default_model format: '{default_model}'.")

        try:
            genai.configure(api_key=api_key)
            self.default_model = default_model
            logger.info(f"GeminiService configured with default model: {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI: {e}", exc_info=True)
            raise ConnectionError(f"Failed to initialize GeminiService: {e}") from e


    def generate_content(self,
                         prompt_parts: GenaiContent,
                         model_name: Optional[str] = None,
                         generation_config: Optional[Dict] = None,
                         stream: bool = False) -> Optional[str]:
        """
        Generates content using the specified model and prompt with retry logic.
        Args:
            prompt_parts: The prompt content (string, list of parts, etc.).
            model_name: Override the default model (must start with 'models/' or 'tunedModels/').
            generation_config: Override default generation parameters.
            stream: Set to True to stream response (returns final concatenated string here).
        Returns:
            The generated text content as a string, or None if generation failed
            or was blocked.
        """
        model_to_use = model_name or self.default_model
        # Validate override model name format
        if not (model_to_use.startswith("models/") or model_to_use.startswith("tunedModels/")):
            logger.error(f"Invalid model_name format: '{model_to_use}'. Must start with 'models/' or 'tunedModels/'.")
            return None

        gen_config = generation_config if generation_config is not None else self.DEFAULT_GENERATION_CONFIG
        safe_settings = None

        retries = 0
        backoff_time = self.INITIAL_BACKOFF_SECONDS

        while retries < self.MAX_RETRIES:
            try:
                logger.info(f"Generating content with {model_to_use} (Attempt {retries + 1}/{self.MAX_RETRIES})...")

                model = genai.GenerativeModel(
                    model_name=model_to_use,
                    generation_config=gen_config,
                    safety_settings=safe_settings
                )

                response = model.generate_content(prompt_parts, stream=stream)

                # Check if the response was blocked or empty
                if not response.candidates or not hasattr(response.candidates[0], 'content') or not response.candidates[0].content.parts:
                    block_reason = "N/A"
                    finish_reason = "N/A"
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                        block_reason = response.prompt_feedback.block_reason
                    if response.candidates and hasattr(response.candidates[0], 'finish_reason'):
                        finish_reason = response.candidates[0].finish_reason

                    logger.warning(f"Content generation returned no parts. Block Reason: {block_reason}, Finish Reason: {finish_reason}")
                    return None # Indicates blocked or empty response

                # Extract text
                full_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))

                logger.info(f"Content generation successful (Model: {model_to_use}).")
                return full_text.strip()

            except (ResourceExhausted, InternalServerError, DeadlineExceeded) as e:
                 logger.warning(f"API Error (Attempt {retries + 1}): {type(e).__name__}. Retrying in {backoff_time}s...")
                 retries += 1
                 if retries < self.MAX_RETRIES:
                     time.sleep(backoff_time)
                     backoff_time *= self.BACKOFF_FACTOR
                 else:
                     logger.error(f"Max retries reached. Failed to generate content due to {type(e).__name__}.", exc_info=False)
                     return None
            # Catch NotFound specifically - model doesn't exist or isn't supported
            except NotFound as e:
                 logger.error(f"Model not found or not supported for generateContent: {model_to_use}. Error: {e}", exc_info=False) # No need for full traceback
                 return None # Cannot retry if model is wrong
            # Catch other Google API errors
            except GoogleAPIError as e:
                 logger.error(f"Non-retryable Google API Error during generation: {e}", exc_info=True)
                 return None
            # Catch any other unexpected errors
            except Exception as e:
                 logger.error(f"Unexpected error during content generation: {e}", exc_info=True)
                 return None

        return None




if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file.")
    except ImportError:
        logger.info(".env file or python-dotenv not found, relying on environment variables.")

    try:
        print("\nInitializing GEMINI Service...")
        gemini = GeminiService()

        # --- Test Simple Generation ---
        print("\n--- Testing Simple Generation (using default flash model) ---")
        simple_prompt = "Explica qué es un Large Language Model (LLM) en 3 frases."
        print(f"Prompt: {simple_prompt}")
        response_text = gemini.generate_content(simple_prompt)

        if response_text:
            print("\nResponse:")
            print(response_text)
        else:
            print("\nFailed to generate simple response (check logs for details).")

        print("\n--- Testing Simple Generation (using default flash model) ENG ---")
        simple_prompt = "Explain what is a  Large Language Model (LLM) in 3 sentences."
        print(f"Prompt: {simple_prompt}")
        response_text = gemini.generate_content(simple_prompt)

        if response_text:
            print("\nResponse:")
            print(response_text)
        else:
            print("\nFailed to generate simple response (check logs for details).")

        # --- Test with a different models ---
        MODELOS = {
            "fast": "gemini-2.0-flash-lite",
            "deep": "gemini-2.5-pro-exp-03-25",
            "long_text": "gemini-1.5-flash"
        }

        target_model = "models/" + MODELOS.get('deep')
        print(f"\n--- Testing with Specific Model ({target_model}) ---")
        pro_prompt = "Explain potential benefits of using geothermal energy."
        print(f"Prompt: {pro_prompt}")
        pro_response = gemini.generate_content(pro_prompt, model_name=target_model)

        if pro_response:
            print(f"\nResponse (from {target_model}):")
            print(pro_response)
        else:
            print(f"\nFailed to generate response with {target_model} (check logs).")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except ConnectionError as e:
        print(f"Connection Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the main script: {e}", exc_info=True)