# tools/doc_summary_tool.py
import logging
import re
from typing import Dict, Any, Optional

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class DocSummaryTool(BaseTool):
    """
    Summarizes the content of a Google Document linked in the task description or content.
    """
    TRIGGER_TAG: str = "resumir_doc"

    # Simple regex to find Google Docs URLs
    DOC_URL_REGEX = re.compile(r'https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)[^\s]*')

    def execute(self, task_details: Dict[str, Any]) -> str:
        """
        Extracts Google Doc URL, fetches content, and summarizes using Gemini.

        Args:
            task_details: Dictionary with task info. Expects 'content' or 'description'.

        Returns:
            A string containing the summary or an error message.
        """
        task_id = task_details.get('id', 'N/A')
        task_content = task_details.get('content', '')
        task_description = task_details.get('description', '')
        logger.info(f"Executing DocSummaryTool for Task ID: {task_id}")

        # 1. Find Google Doc URL/ID
        doc_url = self._find_doc_url(task_content) or self._find_doc_url(task_description)

        if not doc_url:
            logger.warning(f"No Google Doc URL found in task content or description for task {task_id}.")
            return "Error: No se encontró un enlace a Google Docs válido en la tarea."

        logger.debug(f"Found Google Doc URL: {doc_url} for task {task_id}")

        # 2. Get Document Content
        gdocs_svc = self._get_service('gdocs')
        try:
            doc_text = gdocs_svc.get_public_google_doc_content(doc_url)
        except Exception as e:
            return f"Error: No se pudo obtener el contenido del Google Doc ({doc_url}). Verifica permisos o URL. ({e})"

        if doc_text is None:
             return f"Error: No se pudo obtener el contenido del Google Doc ({doc_url}). Verifica permisos o URL."
        if not doc_text.strip():
            return f"El Google Doc ({doc_url}) parece estar vacío."


        # 3. Summarize with Gemini
        gemini_svc = self._get_service('gemini')
        max_len_for_prompt = 15000 # Limit input to avoid hitting token limits 
        summary_prompt = f"""
        El siguiente es el contenido de un Google Document. Por favor, genera un resumen conciso pero informativo de los puntos clave o temas principales.

        Contenido (primeros {max_len_for_prompt} caracteres):
        {doc_text[:max_len_for_prompt]}
        {'...' if len(doc_text) > max_len_for_prompt else ''}

        Resumen:
        """
        logger.debug(f"Sending content from Doc ({doc_url}) to Gemini for summarization (Task {task_id}).")

        try:
             summary = gemini_svc.generate_content(summary_prompt)
        except Exception as e:
             logger.error(f"Error calling Gemini for doc summary (Task {task_id}): {e}", exc_info=True)
             return f"Error al generar el resumen del documento ({doc_url})."

        if not summary:
            return f"Se obtuvo el contenido del documento ({doc_url}), pero no se pudo generar un resumen."

        # 4. Format Result
        final_result = f"**Resumen del Documento:** {doc_url}\n\n{summary}"
        return final_result

    def _find_doc_url(self, text: str) -> Optional[str]:
        """Finds the first Google Doc URL in a block of text."""
        if not text:
            return None
        match = self.DOC_URL_REGEX.search(text)
        return match.group(0) if match else None
