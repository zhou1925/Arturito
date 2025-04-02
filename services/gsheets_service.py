import os
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

logger = logging.getLogger(__name__)


class GSheetsService:
    """
    Handles interactions with PUBLIC Google Sheets using simple CSV export.
    NOTE: This version DOES NOT use authentication and only works for
          sheets shared publicly ('Anyone with the link can view').
    Requires 'pandas' library to be installed.
    """

    def __init__(self):
        """Initializes the GSheetsService."""
        if not PANDAS_AVAILABLE:
             logger.warning("Pandas library not found. Google Sheets functionality will be unavailable.")
        logger.info("GSheetsService (Public Sheets Mode) initialized.")

