from typing import Dict, Any, Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent  # Or use langchain.agents.create_agent for v1
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import AgentState
from langgraph.graph import StateGraph, START, END

 
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class SupervisorState(AgentState):
    messages: list
    next: str 

# Tool 1: Get approximate location from IP (used by location_agent)
@tool
def get_user_location() -> str:
    """Get the approximate location (city, region) of the user from their IP address.
    Use this FIRST if the user doesn't specify a location.
    """
    import requests
    try:
        response = requests.get("https://ipapi.co/json/")
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country_name', 'Unknown')}"
    except Exception:
        return "New York, NY, USA"  # Fallback

# Tool 2: Get weather (used by weather_agent) - replace with real API like OpenWeatherMap
@tool
def get_weather(location: str) -> str:
    """Get current weather for a specific location (city/region/country).
    Use ONLY after getting a valid location.
    """
    # Mock implementation - replace with real weather API key/call
    return f"Weather in {location}: Sunny, 72°F (22°C), humidity 60%"

# Location Agent: Handles location detection
location_llm = llm 
location_agent = create_agent(location_llm, [get_user_location], 
                                   system_prompt="You get the user's location. If needed, call get_user_location. Respond with just the location.")

def location_node(state: AgentState):
    result = location_agent.invoke(state)
    return {"messages": result["messages"]}

# Weather Agent: Handles weather queries
weather_llm = llm 
weather_agent = create_agent(weather_llm, [get_weather],
                                  system_prompt="You fetch weather. ALWAYS require a location first. Respond with weather info.")

def weather_node(state: AgentState):
    result = weather_agent.invoke(state)
    return {"messages": result["messages"]}

# Supervisor: Routes to location_agent, weather_agent, or finishes
members = ["location_agent", "weather_agent", END]
system_prompt = """You are a supervisor managing a weather multi-agent team.
Route to:
- location_agent: If no location given or need to detect user location
- weather_agent: For weather queries with location
Finish when weather info is ready.
Always use location first!"""

options = "\n".join([f"{m}: {m.replace('_agent', '')}" for m in members[:-1]])
prompt = HumanMessage(content=f"{system_prompt}\n\nOptions: {options}")

supervisor_llm = llm 
supervisor_agent = create_agent(supervisor_llm, state_schema=SupervisorState
                                              , system_prompt=prompt)

def supervisor_node(state: AgentState):
    result = supervisor_agent.invoke(state)
    # Parse route from tool call
    last_msg = result["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        route = last_msg.tool_calls[0]["args"]["member"]
        return {"next": route}
    return {"next": END}

def route_after_supervisor(state: SupervisorState) -> Literal[  "weather_agent" , "__end__"]:
    """Route based on supervisor's decision"""
    next_agent = state.get("next", "FINISH").lower()
    print(f"Next agent: {next_agent}")
    if next_agent == "math_agent":
        return "math_agent"
    elif next_agent == "weather_agent":
        return "weather_agent"
 
    if next_agent == "flight_search_agent":
        return "flight_search_agent"
    elif next_agent == "conversation_agent":
        return "conversation_agent"
    else:
        return "__end__"
# Build multi-agent graph
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("location_agent", location_node)
workflow.add_node("weather_agent", weather_node)

# Add edges to connect nodes
workflow.add_edge(START, "supervisor_node")
workflow.add_conditional_edges(
    "supervisor_node",
    route_after_supervisor,
    {  # Name returned by route_decision : Name of next node to visit
        "weather_agent": "weather_agent",
        "location_agent": "location_agent", 
    },
)

workflow.add_edge("weather_agent",END)
workflow.add_edge("location_agent",END)
# for member in members[:-1]:
#     workflow.add_edge(member, "supervisor")

workflow.set_entry_point("supervisor")
app = workflow.compile()

# Usage examples
if __name__ == "__main__":
    # No location provided - auto-detects
    result1 = app.invoke({"messages": [HumanMessage(content="What's the weather?")]})
    print("No location:", result1["messages"][-1].content)

    # With location
    result2 = app.invoke({"messages": [HumanMessage(content="Weather in San Francisco")]})
    print("With location:", result2["messages"][-1].content)