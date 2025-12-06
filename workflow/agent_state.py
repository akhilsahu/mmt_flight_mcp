from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, MessagesState, START, END

class AgentState(MessagesState):
    #messages: List[str]
    next: Optional[str] = None
    # final_response: Optional[BaseModel] = None
    # context: Dict = Field(default_factory=dict)
    #         # Add LangChain-compatible memory fields - use BaseMessage objects
    # chat_history: List[Any] = Field(default_factory=list)  # Will contain BaseMessage objects
    # conversation_id: Optional[str] = None