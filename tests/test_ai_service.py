
from unittest.mock import MagicMock
import pytest

from src.capabilities import mcp_client
from src.config import config
from src.models.model_client import (
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.services.ai_service import AIService, generate_response


@pytest.fixture(autouse=True)
def no_mcp_server(monkeypatch):
    """Tests must not start a real MCP server."""
    monkeypatch.setattr(mcp_client, "get_tools", lambda: [])


def test_config_loading():
    """Verify configuration settings."""
    assert config.ollama_base_url is not None
    assert config.model_name is not None
    assert isinstance(config.ollama_base_url, str)
    assert isinstance(config.model_name, str)


def test_empty_input_validation():
    """Verify that empty inputs are rejected."""
    mock_client = MagicMock()
    service = AIService(model_client=mock_client)

    response_empty = service.process_message("")
    assert response_empty.success is False
    assert "Please enter a message" in response_empty.content
    assert mock_client.chat.call_count == 0

    response_spaces = service.process_message("   ")
    assert response_spaces.success is False
    assert mock_client.chat.call_count == 0


def test_successful_response_generation():
    """Verify successful model response."""
    mock_client = MagicMock()
    mock_client.chat.return_value = MagicMock(
        content="Hello! I am an AI assistant.",
        tool_calls=None
    )

    service = AIService(model_client=mock_client)

    result_text = generate_response("Hello, AI", service=service)

    assert result_text == "Hello! I am an AI assistant."
    mock_client.chat.assert_called_once()


def test_ollama_connection_error_handling():
    """Verify friendly connection error messages."""
    mock_client = MagicMock()
    mock_client.chat.side_effect = OllamaConnectionError(
        "Connection refused at http://localhost:11434"
    )

    service = AIService(model_client=mock_client)
    response = service.process_message("Test message")

    assert response.success is False
    assert "Could not connect to Ollama" in response.content
    assert "Connection refused" in response.error_message


def test_model_not_found_error_handling():
    """Verify missing model error handling."""
    mock_client = MagicMock()
    mock_client.chat.side_effect = ModelNotFoundError(
        "Model qwen2.5 not found locally"
    )

    service = AIService(model_client=mock_client)
    response = service.process_message("Test message")

    assert response.success is False
    assert "configured AI model is unavailable" in response.content
    assert "qwen2.5 not found" in response.error_message
