from typing import Literal

from pydantic import BaseModel, Field


class IntentExtractResponse(BaseModel):
    action: str
    subject: str
    category: Literal[
        "engineering",
        "research",
        "writing",
        "admin",
        "personal",
        "other",
    ]
    urgency: Literal["low", "normal", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool