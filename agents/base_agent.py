from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from core.model_settings import ModelSettings
from abc import ABC, abstractmethod
class BaseAgent:
    def __init__(self,name: str="Agent",model_settings: ModelSettings=None,system_prompt: str=None,tool_config:dict=None,role: str=None):
        self.name = name
        self.system_prompt = system_prompt or self.get_system_prompt()
        self.tool_config = tool_config or {}
        self.client = None
        self.model = model_settings.get_current_model() if model_settings else None

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt - to be overridden by subclasses."""
        return f"You are {self.name}, a {self.role} specialist."  
    
    async def create_agent_react(self):
        """Create math agent with MCP tools"""
        client = MultiServerMCPClient({
            **self.tool_config
        })
        tools = await client.get_tools()
        agent = create_agent(
            self.model,
            tools,
            system_prompt=self.system_prompt
        )
        return agent


