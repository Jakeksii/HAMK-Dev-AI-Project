
from typing import Optional
from pydantic import ValidationError
from src.capabilities import mcp_client
from src.capabilities.mcp_client import ToolError
from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.source import build_system_prompt
from src.schemas.responses import UserRequest, AIResponse


# Maximum number of tool-calling rounds per user message.
MAX_TOOL_ROUNDS = 5


def _history_to_messages(history: Optional[list]) -> list:
    """
    Convert Gradio chat history to Ollama message format.
    """
    messages = []

    for item in history or []:
        content = item.get("content")

        if isinstance(content, list):
            text = ""
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text += part.get("text", "")
            content = text

        if isinstance(content, str) and content:
            messages.append({
                "role": item["role"],
                "content": content
            })

    return messages


class AIService:
    """
    Validates user input, communicates with the model,
    executes MCP tools, and handles errors.
    """

    def __init__(self, model_client: Optional[OllamaModelClient] = None):
        self.model_client = model_client

    def _get_client(self) -> OllamaModelClient:
        if self.model_client is None:
            self.model_client = OllamaModelClient()
        return self.model_client

    def process_message(
        self,
        user_message: str,
        history: Optional[list] = None
    ) -> AIResponse:

        # Step 1: Validate empty input.
        if not user_message or not user_message.strip():
            return AIResponse(
                content="Please enter a message before sending.",
                success=False,
                error_message="User message was empty.",
            )

        # Step 2: Validate request schema.
        try:
            request = UserRequest(message=user_message.strip())
        except ValidationError as err:
            return AIResponse(
                content="Your message is too long. Please shorten it and try again.",
                success=False,
                error_message=str(err),
            )

        try:
            client = self._get_client()

            # Step 3: Get available tools from MCP.
            tools = mcp_client.get_tools()

            # Step 4: Build conversation.
            messages = [
                {
                    "role": "system",
                    "content": build_system_prompt()
                }
            ]

            messages += _history_to_messages(history)

            messages.append({
                "role": "user",
                "content": request.message
            })

            # Step 5: Tool calling loop.
            empty_retries = 0

            for _ in range(MAX_TOOL_ROUNDS):

                reply = client.chat(messages, tools)

                print("Thinking: " + str(getattr(reply, "thinking", None)))
                print("Response: " + str(reply.content))

                if not reply.tool_calls:

                    if not reply.content:

                        if empty_retries >= 1:
                            return AIResponse(
                                content="Sorry, I couldn't complete that. Please try again.",
                                success=False,
                                error_message="The model gave an empty reply twice.",
                            )

                        empty_retries += 1

                        tool_names = ", ".join(
                            t["function"]["name"] for t in tools
                        )

                        messages.append({
                            "role": "user",
                            "content": (
                                "(Message from the app, not from the user) "
                                "Your last reply was empty. "
                                "If you tried to call a tool, that tool does not exist. "
                                f"The only tools you have are: {tool_names}. "
                                "Answer the user now in plain text."
                            ),
                        })

                        continue

                    return AIResponse(
                        content=reply.content,
                        success=True
                    )

                # Add assistant tool requests to the conversation.
                messages.append(reply)

                for tool_call in reply.tool_calls:

                    name = tool_call.function.name
                    arguments = tool_call.function.arguments

                    print(f"[tool call] {name} {arguments}")

                    try:
                        result = mcp_client.call_tool(
                            name,
                            arguments
                        )
                    except ToolError as err:
                        result = f"ERROR: {err}"

                    print(f"[tool result] {str(result)[:300]}")

                    messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_name": name
                    })

            return AIResponse(
                content=(
                    "[Error] The assistant needed too many steps to answer. "
                    "Please try again with a simpler request."
                ),
                success=False,
                error_message=(
                    f"Tool loop stopped after {MAX_TOOL_ROUNDS} rounds."
                ),
            )

        except ToolError as err:
            return AIResponse(
                content=(
                    "[Error] Could not connect to the calendar service (MCP server).\n\n"
                    "Please check the MCP server settings in your .env file."
                ),
                success=False,
                error_message=str(err),
            )

        except OllamaConnectionError as err:
            return AIResponse(
                content=(
                    "[Error] Could not connect to Ollama.\n\n"
                    "Please verify that Ollama is installed and running locally."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content=(
                    "[Error] The configured AI model is unavailable in Ollama.\n\n"
                    "Please verify MODEL_NAME or install the model."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content="[Error] An unexpected communication error occurred with the AI model.",
                success=False,
                error_message=str(err),
            )

        except Exception as err:
            return AIResponse(
                content="[Error] An unexpected application error occurred.",
                success=False,
                error_message=str(err),
            )


def generate_response(
    user_message: str,
    history: Optional[list] = None,
    service: Optional[AIService] = None
) -> str:
    """
    Entry point used by the Gradio user interface.
    """

    active_service = service or AIService()

    response = active_service.process_message(
        user_message,
        history
    )

    if not response.success:
        print(f"[error] {response.error_message}")

    return response.content
