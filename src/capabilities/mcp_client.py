import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.config import config


class ToolError(Exception):
    """Raised when the MCP server can't be reached or a tool call fails."""
    pass


def _server_params() -> StdioServerParameters:
    command = config.mcp_server_command
    # "python" might point to a different Python than the one running this app
    # (for example when the conda env is not activated), so use the same one.
    if command == "python":
        command = sys.executable

    return StdioServerParameters(
        command=command,
        args=config.mcp_server_args.split(),
    )


async def _list_tools_async():
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


async def _call_tool_async(name: str, arguments: dict):
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments)


def get_tools() -> list[dict]:
    """Asks the MCP server which tools it has and converts them to the format Ollama expects."""
    try:
        mcp_tools = asyncio.run(_list_tools_async())
    except Exception as err:
        raise ToolError(
            f"Could not start the MCP server '{config.mcp_server_command} {config.mcp_server_args}'. "
            f"Check MCP_SERVER_COMMAND and MCP_SERVER_ARGS in .env. ({err})"
        ) from err

    tools = []
    for tool in mcp_tools:
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })
    return tools


def call_tool(name: str, arguments: dict) -> str:
    """Runs one tool on the MCP server and returns the result as text."""
    try:
        result = asyncio.run(_call_tool_async(name, arguments))
    except Exception as err:
        raise ToolError(f"Calling tool '{name}' failed: {err}") from err

    text = ""
    for item in result.content:
        if item.type == "text":
            text += item.text + "\n"

    if result.isError:
        raise ToolError(text.strip())
    return text.strip()


if __name__ == "__main__":
    # Quick manual test: python -m src.capabilities.mcp_client
    for t in get_tools():
        print("-", t["function"]["name"], ":", t["function"]["description"][:80])