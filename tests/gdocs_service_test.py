import pytest
import requests
from unittest.mock import patch, MagicMock
from services.gdocs_service import GDocsService

@pytest.fixture
def gdocs_service():
    """Fixture to create an instance of GDocsService."""
    return GDocsService()

def test_get_export_url_valid(gdocs_service):
    """Test that a valid Google Doc URL is correctly converted to an export URL."""
    doc_url = "https://docs.google.com/document/d/12345/edit"
    expected_export_url = "https://docs.google.com/document/d/12345/export?format=txt"
    assert gdocs_service._get_export_url(doc_url) == expected_export_url

def test_get_export_url_invalid(gdocs_service):
    """Test that an invalid Google Doc URL returns None."""
    invalid_url = "https://example.com/document/12345/edit"
    assert gdocs_service._get_export_url(invalid_url) is None

@patch("services.gdocs_service.requests.get")
def test_get_public_google_doc_content_success(mock_get, gdocs_service):
    """Test successfully retrieving Google Doc content."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "This is a test document."
    mock_response.apparent_encoding = "utf-8"
    mock_get.return_value = mock_response

    doc_url = "https://docs.google.com/document/d/12345/edit"
    content = gdocs_service.get_public_google_doc_content(doc_url)
    
    assert content == "This is a test document."

@patch("services.gdocs_service.requests.get")
def test_get_public_google_doc_content_403(mock_get, gdocs_service):
    """Test Google Doc that is not publicly shared (403 Forbidden)."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_get.return_value = mock_response

    doc_url = "https://docs.google.com/document/d/12345/edit"
    content = gdocs_service.get_public_google_doc_content(doc_url)
    
    assert content is None

@patch("services.gdocs_service.requests.get")
def test_get_public_google_doc_content_404(mock_get, gdocs_service):
    """Test Google Doc that does not exist (404 Not Found)."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    doc_url = "https://docs.google.com/document/d/12345/edit"
    content = gdocs_service.get_public_google_doc_content(doc_url)
    
    assert content is None

@patch("services.gdocs_service.requests.get")
def test_get_public_google_doc_content_request_exception(mock_get, gdocs_service):
    """Test handling of a network failure (e.g., timeout or connection error)."""
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")

    doc_url = "https://docs.google.com/document/d/12345/edit"
    content = gdocs_service.get_public_google_doc_content(doc_url)
    
    assert content is None
