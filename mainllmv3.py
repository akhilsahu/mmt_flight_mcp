"""
Multi-Agent System with Supervisor and MCP Tools
Uses LangGraph for orchestration with specialized math and weather agents
ADDED: Conditional interrupt for weather_agent when location missing
"""
from PIL import Image
import uuid
from models.response_models import GeneralResponse
import asyncio
from typing import Annotated, Literal, TypedDict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver  
from dotenv import load_dotenv
import os
from agents.supervisor_agent import supervisor_node
from config import AGENT_CONFIG
from typing import Annotated, Literal, TypedDict, Any, Optional
from langgraph.graph.message import add_messages  # ← CORRECT IMPORT
from langchain_core.messages import BaseMessage  # Generic message type # ← CRITICAL
from langgraph.graph import StateGraph, START, END
# Load .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

 
 
from langgraph.graph import MessagesState
from typing_extensions import TypedDict, NotRequired, Optional, Union, Literal
from typing import Dict, Any

# Generic agent context - each agent uses what it needs
class AgentContext(TypedDict):
    location: NotRequired[Optional[str]]      # Weather
    dates: NotRequired[Optional[str]]         # Flights  
    math_result: NotRequired[Optional[float]] # Math
    # Add more as needed: hotel_city, query_params, etc.

class SupervisorState(MessagesState):
    next: str
    agent_context: NotRequired[AgentContext]  # Supervisor ignores, agents use

async def get_agent(model_config, system_prompt, tool_config):
    client = MultiServerMCPClient({**tool_config})
    tools = await client.get_tools()
    agent = create_agent(
        model_config,
        tools,
        system_prompt=system_prompt,
        response_format=GeneralResponse
    )
    return agent

async def create_agent_react(agent_name: str):
    print(f"Agent name: {agent_name}")
    agent_config = AGENT_CONFIG[agent_name]
    return await get_agent(
        agent_config["model"],
        agent_config["system_prompt"],
        agent_config["tool_config"]
    )  

def get_agent_node(agent_name: str):
    """Generic agent node for non-weather agents"""
    async def agent_node(state: SupervisorState):
        agent = await create_agent_react(agent_name)
        result = await agent.ainvoke(state)
        return {
            "messages": result["messages"],
            "next": "supervisor"
        }
    return agent_node

# NEW: Weather wrapper with conditional interrupt
# Generic agent node - passes context through
def get_agent_node(agent_name: str):
    async def agent_node(state: SupervisorState):
        agent = await create_agent_react(agent_name)
        result = await agent.ainvoke(state)
        
        # Preserve existing context
        context = state.get("agent_context", {})
        
        return {
            "messages": result["messages"],
            "next": "supervisor",
            "agent_context": context  # Pass through
        }
    return agent_node

# Weather-specific wrapper
async def weather_wrapper_node(state: SupervisorState) -> dict[str, Any]:
    agent = await create_agent_react("weather_agent")
    result = await agent.ainvoke(state)
    
    last_msg = result["messages"][-1]
    if (isinstance(last_msg, AIMessage) and 
        "LOCATION_NEEDED" in str(last_msg.content)):
        
        user_location = interrupt({
            "reason": "LOCATION_REQUIRED",
            "message": "Weather needs a city/location.",
            "context": state["messages"][-1].content if state["messages"] else ""
        })
        
        return {
            "messages": result["messages"] + [HumanMessage(content=f"Location: {user_location}")],
            "next": "weather_agent",
            "agent_context": {
                **state.get("agent_context", {}),
                "location": user_location  # Weather sets its context
            }
        }
    
    return {
        "messages": result["messages"],
        "next": "supervisor",
        "agent_context": {
            **state.get("agent_context", {}),
            "location": state["agent_context"].get("location") if state.get("agent_context") else None
        }
    }

# Flight agent example (add similar wrapper if needed)
async def flight_wrapper_node(state: SupervisorState) -> dict[str, Any]:
    # Similar pattern for dates/airports
    agent = await create_agent_react("flight_search_agent")
    result = await agent.ainvoke(state)
    
    # Check for missing dates, interrupt if needed
    # ... similar logic ...
    
    return {
        "messages": result["messages"],
        "next": "supervisor", 
        "agent_context": {
            **state.get("agent_context", {}),
            "dates": "2025-12-31",  # Example
            "from_airport": "LKO",
            "to_airport": "DEL"
        }
    }

def route_after_supervisor(state: SupervisorState) -> Literal["math_agent", "weather_agent", "flight_search_agent", "conversation_agent", "__end__"]:
    """Route based on supervisor's decision"""
    next_agent = state.get("next", "FINISH").lower()
    print(f"Routing to: {next_agent}")
    if next_agent == "math_agent":
        return "math_agent"
    elif next_agent == "weather_agent":
        return "weather_agent"
    elif next_agent == "flight_search_agent":
        return "flight_search_agent"
    elif next_agent == "conversation_agent":
        return "conversation_agent"
    else:
        return "__end__"

def route_after_agent(state: SupervisorState) -> Literal["supervisor", "__end__"]:
    """Route back to supervisor or end"""
    next_step = state.get("next", "FINISH").lower()
    print(f"Next step: {next_step}")
    return "supervisor" if next_step == "supervisor" else "__end__"

# Build the graph
async def create_supervisor_graph():
    checkpointer = InMemorySaver()  

    # FIXED: State now properly typed
    workflow = StateGraph(SupervisorState)
 
    # Add nodes (unchanged)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("math_agent", get_agent_node("math_agent"))
    workflow.add_node("flight_search_agent", get_agent_node("flight_search_agent"))
    workflow.add_node("conversation_agent", get_agent_node("conversation_agent"))
    workflow.add_node("weather_agent", weather_wrapper_node)  # Your interrupt wrapper
    
    # Edges (unchanged)
    workflow.add_edge(START, "supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        { 
            **{agent_name: agent_name for agent_name in AGENT_CONFIG.keys()},
            "__end__": END
        }
    )
    
    # Route from agents back to supervisor
    for agent_name in AGENT_CONFIG.keys():
        workflow.add_conditional_edges(
            agent_name,
            route_after_agent,
            {"supervisor": "supervisor", "__end__": END}
        )
    
    graph = workflow.compile(checkpointer=checkpointer)
    show_wf_image(graph)
    return graph

def show_wf_image(graph):
    try:
        from PIL import Image
        from PIL import Image as PILImage
        from IPython.display import Image as IPythonImage, display
        i = graph.get_graph().draw_mermaid_png()
        display(Image(i))
        with open("/tmp/graph.png", "wb") as f:
            f.write(i)
        img = PILImage.open("/tmp/graph.png")
        img.show()
    except ImportError:
        print("PIL/IPython not available, skipping graph visualization")
    except Exception as e:
        print(f"An error occurred: {e}")

# Enhanced chat with interrupt handling
async def chattie():
    print("🚀 Starting Agentic Chatbot with Weather Location Interrupt...")
    graph = await create_supervisor_graph()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 100}
    
    print("Chatbot ready! Try: 'What's the weather?' (will interrupt for location)")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if user_input:
                # Stream with interrupt detection
                async for event in graph.astream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config,
                    stream_mode="values"
                ):
                    if "__interrupt__" in event:
                        interrupt_info = event["__interrupt__"][0].value
                        print(f"\n⏸️  INTERRUPT: {interrupt_info.get('message', 'Paused')}")
                        print(f"   Reason: {interrupt_info.get('reason', 'Unknown')}")
                        
                        # Handle location input specifically
                        if interrupt_info.get("reason") == "LOCATION_REQUIRED":
                            location = input("📍 Enter location (e.g., 'New York'): ").strip()
                            if location:
                                # Resume with location
                                resume_result = await graph.ainvoke(
                                    {},
                                    config,
                                    input=Command(resume=location)
                                )
                                print(f"✅ Resumed with location: {location}")
                                print(f"Bot: {resume_result['messages'][-1].content}")
                            continue
                    
                    elif "messages" in event and event["messages"]:
                        last_msg = event["messages"][-1]
                        if hasattr(last_msg, 'content'):
                            print(f"Bot: {last_msg.content}")
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

# Example usage
if __name__ == "__main__":
    asyncio.run(chattie())