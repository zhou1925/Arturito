import os
import io
import logging
import re
import requests
from typing import Optional
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class GDocsService:
    """
    Handles interactions with PUBLIC Google Docs using simple HTTP export.
    NOTE: This version DOES NOT use authentication and only works for
          documents shared publicly ('Anyone with the link can view').
    """
    def __init__(self):
        """Initializes the GDOCS service (no credentials needed)."""
        logger.info("GDocs (Public Docs Mode) initialized.")
    

    def _get_export_url(self, doc_url: str) -> Optional[str]:
        """
        Converts a standard Google Doc URL (/edit, /view) to a text export URL.
        Args:
            doc_url: The standard URL of the Google Doc.
        Returns:
            The URL for plain text export, or None if the input URL is invalid.
        """
        base_url_match = re.match(r'(https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+)/', doc_url)
        if base_url_match:
            base_url = base_url_match.group(1)
            export_url = f"{base_url}/export?format=txt"
            logger.debug(f"Generated export URL: {export_url}")
            return export_url
        else:
            logger.warning(f"Could not extract base URL structure from: {doc_url}")
            return None
    
    def get_public_google_doc_content(self, doc_url: str) -> Optional[str]:
        """
        Retrieves the text content of a PUBLICLY SHARED Google Doc via export.
        Args:
            doc_url: The standard Google Doc URL (e.g., ending in /edit).
                     The document MUST be shared publicly ('Anyone with link').
        Returns:
            The text content of the document, or None on error or if not public.
        """
        export_url = self._get_export_url(doc_url)
        if not export_url:
            return None
        logger.debug(f"Attempting to fetch public content from: {export_url}")

        try:
            response = requests.get(export_url, timeout=30)
            if response.status_code == 404:
                logger.error(f"Document not found (404) at export URL: {export_url}")
                return None
            if response.status_code == 403:
                 logger.error(f"Permission denied (403) for export URL: {export_url}. Ensure the document is shared publicly ('Anyone with the link can view').")
                 return None
            response.raise_for_status()

            # Decode using the detected encoding, falling back to UTF-8
            response.encoding = response.apparent_encoding or 'utf-8'
            doc_text = response.text
            logger.info(f"Successfully retrieved content from public Google Doc: {doc_url} (Length: {len(doc_text)})")
            return doc_text

        except RequestException as e:
            logger.error(f"HTTP request failed for {export_url}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching public Google Doc {doc_url}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    from config import ConfigManager
    # !!! IMPORTANT !!!
    # Replace with a URL of a Google Doc that IS PUBLICLY SHARED
    # ('Anyone with the link can view'). Otherwise, it will fail.
    # Use the one from your example code for testing:
    config = ConfigManager()
    TEST_PUBLIC_DOC_URL = config.get_setting("TEST_PUBLIC_DOC_URL")
    if not TEST_PUBLIC_DOC_URL:
        print("TEST_PUBLIC_DOC_URL not found in config. Exiting test.")
        logger.error("TEST_PUBLIC_DOC_URL not found in configuration.")

    try:
        gdoc_service = GDocsService()
        doc_content = gdoc_service.get_public_google_doc_content(TEST_PUBLIC_DOC_URL)
        print(f"\n--- Testing Public Google Doc Content Fetching ---")
        print(f"Attempting to fetch content from public URL: {TEST_PUBLIC_DOC_URL}")     

        if doc_content is not None:
            print("\nSuccessfully fetched public document content:")
            print("-" * 20)
            print(doc_content[:1000] + "..." if len(doc_content) > 1000 else doc_content)
            print("-" * 20)
            print(f"(Total length: {len(doc_content)})")
        else:
            print("\nFailed to fetch public document content. Check logs.")
    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")
        logger.exception("Unexpected error in GDriveService test.")