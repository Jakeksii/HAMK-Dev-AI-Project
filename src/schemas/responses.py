from pydantic import BaseModel, Field

# Long enough for a forwarded email, short enough to keep the prompt small.
MAX_MESSAGE_LENGTH = 4000


class UserRequest(BaseModel):
    """Minimal schema for validating incoming user input."""

    message: str = Field(..., max_length=MAX_MESSAGE_LENGTH, description="The user's prompt or message.")


class AIResponse(BaseModel):
    """Minimal schema for structured response output from the AI service layer."""

    content: str = Field(..., description="The generated response text or user-friendly error message.")
    success: bool = Field(True, description="Flag indicating if the operation succeeded.")
    error_message: str | None = Field(None, description="Detailed error description if success is False.")