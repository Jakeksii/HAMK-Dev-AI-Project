import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class Config:
    """Simple configuration object reading environment variables."""

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name: str = os.getenv("MODEL_NAME", "qwen2.5")

    # MCP server that provides the tools. It is started as a subprocess.
    mcp_server_command: str = os.getenv("MCP_SERVER_COMMAND", "python")
    mcp_server_args: str = os.getenv("MCP_SERVER_ARGS", "-m mcp_server_time --local-timezone=Europe/Helsinki")


# Instantiate global configuration object
config = Config()
