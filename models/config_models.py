"""Configuration models for the chatbot system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: ModelProvider
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPServerConfig:
    """Configuration for MCP server connection."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30