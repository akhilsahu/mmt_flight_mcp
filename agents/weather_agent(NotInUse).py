"""Weather specialist agent."""

from typing import List
from .base_agent import BaseAgent
from models.response_models import WeatherResponse
from typing import List, Type
from langchain_core.tools import BaseTool

class WeatherAgent(BaseAgent):
    """Weather specialist using structured output."""
    
    def __init__(self, model, tools=None):
        tool_config = { "weather": {
           "command": "python",
            # Update this path to your math_server.py location
            "args": ["mcp_tool/weather_server.py"],
            "transport": "stdio",
        }
        }
        super().__init__(name="WeatherSpecialist", model_settings=model, tool_config=tool_config,role="weather expert")
    
    
    # @classmethod
    # async def create(cls, modelManager, tools: List[BaseTool]):
    #     # This line calls the BaseAgent.create factory which includes:
    #     # await instance._build_agent()
    #     return await super().create( 
    #         name="WeatherSpecialist",
    #         role="weather expert",
    #         modelManager=modelManager,
    #         tools=tools,
    #         response_model=WeatherResponse
    #     )
    
    def get_system_prompt(self) -> str:
        return """ You are a specialized weather agent. Use the available weather tools to provide accurate forecasts and meteorological information.
"""