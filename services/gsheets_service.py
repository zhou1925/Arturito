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

    def _extract_spreadsheet_id_from_url(self, url: str) -> Optional[str]:
        """Extracts Google Sheets ID from various URL formats."""
        if not isinstance(url, str):
            return None
        # Example: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit...
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
        if match:
            sheet_id = match.group(1)
            logger.debug(f"Extracted Spreadsheet ID: {sheet_id} from URL: {url}")
            return sheet_id
        logger.warning(f"Could not extract Spreadsheet ID from URL: {url}")
        return None

    def get_public_sheet_data(self, spreadsheet_id_or_url: str, sheet_name: str) -> Optional['pd.DataFrame']:
        """
        Retrieves data from a specific sheet within a PUBLICLY SHARED Google Sheet
        as a pandas DataFrame.

        Requires the 'pandas' library to be installed.
        The Google Sheet MUST be shared publicly ('Anyone with the link can view').
        Args:
            spreadsheet_id_or_url: The Google Sheet ID or its full URL.
            sheet_name: The exact name of the sheet/tab within the spreadsheet.
        Returns:
            A pandas DataFrame containing the sheet data, or None on error or
            if pandas is not installed.
        """
        if not PANDAS_AVAILABLE:
             logger.error("Pandas library is required for get_public_sheet_data but is not installed.")
             return None

        spreadsheet_id = spreadsheet_id_or_url

        if '/' in spreadsheet_id_or_url and 'spreadsheets/d/' in spreadsheet_id_or_url:
             extracted_id = self._extract_spreadsheet_id_from_url(spreadsheet_id_or_url)
             if extracted_id:
                 spreadsheet_id = extracted_id
             else:
                 logger.error(f"Could not extract valid Spreadsheet ID from the provided URL: {spreadsheet_id_or_url}")
                 return None
        elif '/' in spreadsheet_id_or_url:
             logger.error(f"Input '{spreadsheet_id_or_url}' looks like an invalid URL or path. Please provide a valid Sheet ID or full Google Sheets URL.")
             return None

        if not spreadsheet_id:
             logger.error(f"Invalid or empty Spreadsheet ID derived from: {spreadsheet_id_or_url}")
             return None

        if not sheet_name:
             logger.error("Sheet name must be provided.")
             return None

        # URL encode the sheet name in case it has spaces or special characters
        encoded_sheet_name = quote_plus(sheet_name)

        # Construct the CSV export URL using the gviz API endpoint
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

        logger.info(f"Attempting to fetch public sheet data from URL: {csv_export_url}")

        try:
            df = pd.read_csv(csv_export_url, on_bad_lines='warn', low_memory=False)
            logger.info(f"Successfully retrieved data from public Google Sheet ID: {spreadsheet_id}, Sheet: '{sheet_name}'. Shape: {df.shape}")
            return df
        except pd.errors.EmptyDataError:
             logger.warning(f"No data found (EmptyDataError) in sheet '{sheet_name}' at {csv_export_url}. The sheet might be empty.")
             return pd.DataFrame()
        except Exception as e:
            error_str = str(e).lower()
            if "http error" in error_str or "404" in error_str or "not found" in error_str:
                 logger.error(f"HTTP error accessing {csv_export_url}. Check if Sheet ID '{spreadsheet_id}' is correct and exists. Error: {e}", exc_info=True)
            elif "html" in error_str or "forbidden" in error_str or "403" in error_str or "parsererror" in error_str:
                 logger.error(f"Failed to read CSV, likely a permission issue or incorrect URL. Ensure Sheet ID '{spreadsheet_id}' is shared publicly ('Anyone with the link can view'). URL: {csv_export_url}. Error: {e}", exc_info=True)
            else:
                 logger.error(f"Failed to read or parse CSV from {csv_export_url} for sheet '{sheet_name}'. Error: {e}", exc_info=True)
            return None



# --- Example Usage (for testing gsheets_service.py directly) ---
if __name__ == '__main__':
    # Configure basic logging JUST for this test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    TEST_PUBLIC_SHEET_ID = "1V-DddZHq8lLyoqSm61D6LdJoSa_qBAqECsCVB2-sQmk"
    TEST_PUBLIC_SHEET_NAME = "Hoja1"
    TEST_PUBLIC_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{TEST_PUBLIC_SHEET_ID}/edit#gid=0" # Example URL

    if not PANDAS_AVAILABLE:
        print("\n--- Skipping Public Google Sheet Test: Pandas library not installed ---")
        logger.warning("Pandas not installed. Cannot run GSheetsService test.")
    elif ("YOUR_TEST_PUBLIC_GOOGLE_SHEET_ID_HERE" in TEST_PUBLIC_SHEET_ID or "YOUR_TEST_PUBLIC_GOOGLE_SHEET_NAME_HERE" in TEST_PUBLIC_SHEET_NAME):
         print("Please edit the script and set TEST_PUBLIC_SHEET_ID and TEST_PUBLIC_SHEET_NAME to test.")
    else:
        print("Initializing GSheetsService (Public Sheets Mode)...")
        try:
            gsheets_service = GSheetsService()

            print(f"\n--- Testing Public Google Sheet Data Fetching (using ID) ---")
            print(f"Attempting to fetch data from Sheet ID: '{TEST_PUBLIC_SHEET_ID}', Sheet Name: '{TEST_PUBLIC_SHEET_NAME}'")
            df_data_from_id = gsheets_service.get_public_sheet_data(TEST_PUBLIC_SHEET_ID, TEST_PUBLIC_SHEET_NAME)

            if df_data_from_id is not None:
                if df_data_from_id.empty:
                     print("\nSuccessfully fetched data (using ID), but the DataFrame is empty (Sheet might be empty).")
                else:
                     print("\nSuccessfully fetched public sheet data (using ID):")
                     print("-" * 20)
                     print(df_data_from_id.head())
                     print("-" * 20)
                     print(f"(DataFrame shape: {df_data_from_id.shape})")
            else:
                print("\nFailed to fetch public sheet data (using ID). Check logs.")
                print("Ensure the Sheet ID/Name are correct AND the sheet sharing is set to 'Anyone with the link can view'.")

            # --- Optional: Test using URL ---
            print(f"\n--- Testing Public Google Sheet Data Fetching (using URL) ---")
            print(f"Attempting to fetch data from URL: '{TEST_PUBLIC_SHEET_URL}', Sheet Name: '{TEST_PUBLIC_SHEET_NAME}'")
            df_data_from_url = gsheets_service.get_public_sheet_data(TEST_PUBLIC_SHEET_URL, TEST_PUBLIC_SHEET_NAME)

            if df_data_from_url is not None:
                if df_data_from_url.empty:
                     print("\nSuccessfully fetched data (using URL), but the DataFrame is empty (Sheet might be empty).")
                else:
                     print("\nSuccessfully fetched public sheet data (using URL):")
                     print("-" * 20)
                     print(df_data_from_url.head())
                     print("-" * 20)
                     print(f"(DataFrame shape: {df_data_from_url.shape})")
            else:
                print("\nFailed to fetch public sheet data (using URL). Check logs.")
                print("Ensure the URL is correct, Sheet Name is correct AND the sheet sharing is set to 'Anyone with the link can view'.")

        except Exception as e:
            print(f"An unexpected error occurred during the test: {e}")
            logger.exception("Unexpected error in GSheetsService test.")