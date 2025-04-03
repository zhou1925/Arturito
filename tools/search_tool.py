import logging
import requests
import json
from typing import Dict, Any, Optional, List

from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class SearchTool(BaseTool):
    """
    Performs a web search using Serper.dev API based on task content
    and summarizes the results using Gemini.
    """
    TRIGGER_TAG: str = "buscar" # The tag that activates this tool, basic search

    SEARCH_URL = "https://google.serper.dev/search"
    DEFAULT_NUM_RESULTS = 10
    MAX_SNIPPET_LENGTH = 250 # Max length of snippet to feed to summarizer

    def __init__(self, services: Dict[str, Any]):
        super().__init__(services)
        self.serper_api_key = self.services.get('config', {}).get('SERPER_API_KEY')
        if not self.serper_api_key:
            logger.warning(f"SERPER_API_KEY not found in config for SearchTool. Tool will be disabled.")

    def _perform_search(self, query: str) -> Optional[List[Dict[str, Any]]]:
        headers = {"X-API-KEY": self.serper_api_key, "Content-Type": "application/json"}
        payload = json.dumps({"q": query, "num": self.DEFAULT_NUM_RESULTS})

        logger.debug(f"Calling Serper API for query: {query}")
        try:
            response = requests.post(self.SEARCH_URL, headers=headers, data=payload, timeout=15)
            response.raise_for_status()
            results = response.json()
            logger.info(f"Serper API call successful for query '{query}'. Found {len(results.get('organic', []))} organic results.")
            return results.get("organic", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Serper API for query '{query}': {e}", exc_info=True)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding Serper API response for query '{query}': {e}", exc_info=True)
            return None
    
    def execute(self, task_details: Dict[str, Any]) -> str:
        """
        Executes the web search and summarization.
        Args:
            task_details: Dictionary with task info. Expects 'content'.
        Returns:
            A string summarizing the search results, or an error message.
        """
        if not self.serper_api_key:
            return "Error: SearchTool is disabled because SERPER_API_KEY is not configured."

        query = task_details.get('content')
        if not query:
            return "Error: Task content is empty, cannot perform search."

        # Refine query? Remove trigger tags? Basic cleaning for now.
        query = query.replace(f"@{self.TRIGGER_TAG}", "").replace("@arturito", "").strip()
        if not query:
             return "Error: Query became empty after removing tags."

        logger.info(f"Executing SearchTool for query: '{query}' (Task ID: {task_details.get('id')})")

        # 1. Perform Search
        search_results = self._perform_search(query)
        if not search_results:
            return f"No search results found for '{query}' or search failed."

        # 2. Prepare snippets for summarization
        snippets_for_summary = []
        formatted_links = []
        for result in search_results[:self.DEFAULT_NUM_RESULTS]:
            title = result.get('title')
            link = result.get('link')
            snippet = result.get('snippet', '')
            if title and link:
                 snippets_for_summary.append(f"Title: {title}\nSnippet: {snippet[:self.MAX_SNIPPET_LENGTH]}...\nSource: {link}\n---\n")
                 formatted_links.append(f"- {title}: {link}")

        if not snippets_for_summary:
             return f"Could not extract usable snippets from search results for '{query}'."

        # 3. Summarize with Gemini
        gemini_svc = self._get_service('gemini')
        summary_prompt = f"""
        Se realizó una búsqueda web sobre "{query}". A continuación se muestran los fragmentos (snippets) de los primeros resultados.
        Resume la información clave encontrada en estos fragmentos en 3-5 puntos principales. Cita las fuentes si es posible (aunque no es estrictamente necesario basándose solo en los snippets).

        Fragmentos:
        {''.join(snippets_for_summary)}

        Resumen conciso:
        """

        logger.debug(f"Sending prompt to Gemini for summarization (Query: {query})")
        summary = gemini_svc.generate_content(summary_prompt)

        if not summary:
            return f"Search completed for '{query}', but failed to generate a summary. Links found:\n" + "\n".join(formatted_links)

        # 4. Format final result
        final_result = f"**Resumen de Búsqueda sobre: {query}**\n\n"
        final_result += f"{summary}\n\n"
        final_result += "**Fuentes Principales Consultadas:**\n"
        final_result += "\n".join(formatted_links)

        return final_result

