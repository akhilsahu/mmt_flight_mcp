from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
 
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


class ModelSettings:
    """Manages different language models."""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.current_model: Optional[str] = None
        self.base_model:Any = None
         
    def register_model(self, name: str, config: ModelConfig):
        """Register a new model."""
        self.config_dict = {
                    'model':config.model_name,
                    'temperature':config.temperature,
                    'max_tokens':config.max_tokens,
                    'api_key':config.api_key,
                    **config.additional_params}
        try:
            if config.provider.name == ModelProvider.OPENAI.name:
                self.base_model = ChatOpenAI
                model = ChatOpenAI(**self.config_dict)
            elif config.provider == ModelProvider.ANTHROPIC:
                self.base_model = ChatAnthropic
                model = ChatAnthropic(**self.config_dict)
            elif config.provider == ModelProvider.GOOGLE:
                self.base_model = ChatGoogleGenerativeAI
                model = ChatGoogleGenerativeAI(**self.config_dict)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
            
            self.models[name] = {"model": model, "config": config}
            if not self.current_model:
                self.current_model = name
        except Exception as e:
            print(f"Warning: Failed to register model {name}: {e}")
            print("Continuing without this model...")
    
    def switch_model(self, name: str):
        """Switch to a different model."""
        if name not in self.models:
            raise ValueError(f"Model {name} not found")
        self.current_model = name
    
    def get_current_model(self):
        """Get the current active model."""
        if not self.current_model:
            raise ValueError("No model selected")
        return self.models[self.current_model]["model"]
    
    def list_models(self) -> List[str]:
        """List all registered models."""
        return list(self.models.keys())

 