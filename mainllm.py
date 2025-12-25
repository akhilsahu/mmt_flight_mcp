"""
Multi-Agent System with Supervisor and MCP Tools
Uses LangGraph for orchestration with specialized math and weather agents
"""

from typing import Annotated, Literal, TypedDict
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langgraph.types import Command
from dotenv import load_dotenv
import os

# Load .env file from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__),'.env')
if not load_dotenv(dotenv_path):
    print(f"Warning: Could not find .env file at {dotenv_path}. Please ensure it exists and contains the necessary environment variables.")
    # Depending on your application's needs, you might want to exit here
    # sys.exit("Exiting: .env file not found.")
    exit(1)
load_dotenv(dotenv_path)

# Define the state for our supervisor
class SupervisorState(MessagesState):
    next: str


# Supervisor function to route to appropriate agent
async def supervisor_node(state: SupervisorState):
    """Supervisor agent that decides which specialized agent to call"""
    
    messages = state["messages"]
    
    # Create supervisor LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = """You are a supervisor agent that routes queries to specialized agents.
    
Available agents:
- math_agent: Handles mathematical calculations, equations, and numerical problems
- weather_agent: Handles weather queries, forecasts, and meteorological information
- FINISH: Use this when the task is complete or doesn't require specialized agents

Analyze the user's query and decide which agent should handle it.
Respond with ONLY the agent name: math_agent, weather_agent, or FINISH."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        *messages
    ])
    
    # Determine next agent
    next_agent = response.content.strip().lower()
    
    # Validate the choice
    if next_agent not in ["math_agent", "weather_agent", "finish"]:
        next_agent = "FINISH"
    
    return {"next": next_agent}


# Create specialized agents
async def create_math_agent():
    """Create math agent with MCP tools"""
    client = MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["mcp_tool/math_server.py"],
            "transport": "stdio",
        }
    })
    
    tools = await client.get_tools()
    
    # Create react agent with system prompt
    agent = create_agent(
        ChatOpenAI(model="gpt-4o"),
        tools,
        system_prompt="You are a specialized math agent. Use the available math tools to solve calculations accurately."
    )
    
    return agent



async def create_weather_agent():
    """Create weather agent with MCP tools"""
    client = MultiServerMCPClient({
        "weather": {
           "command": "python",
            # Update this path to your math_server.py location
            "args": ["mcp_tool/weather_server.py"],
            "transport": "stdio",
        }
    })
    
    tools = await client.get_tools()
    
    # Create react agent with system prompt
    agent = create_agent(
        ChatOpenAI(model="gpt-4o"),
        tools,
        system_prompt="You are a specialized weather agent. Use the available weather tools to provide accurate forecasts and meteorological information."
    )
    
    return agent


# Create specialized agents
async def create_flight_search_agent():
    """Create math agent with MCP tools"""
    client = MultiServerMCPClient({
        "flight_search": {
            "command": "python",
            "args": ["mcp_tool/flight_search_server.py"],
            "transport": "stdio",
        }
    })
    
    tools = await client.get_tools()
    
    # Create react agent with system prompt
    agent = create_agent(
        ChatOpenAI(model="gpt-4o"),
        tools,
        system_prompt='''You are a specialized Flight Search agent. 
        Use the available flight search tools to search for flights between two cities on a given date.
        
        '''
    )
    
    return agent

async def flight_search_agent_node(state: SupervisorState):
    """Execute flight search agent"""
    agent = await create_flight_search_agent()
    result = await agent.ainvoke(state)
    return {
        "messages": result["messages"],
        "next": "supervisor"
    }

# Agent wrapper nodes
async def math_agent_node(state: SupervisorState):
    """Execute math agent"""
    agent = await create_math_agent()
    result = await agent.ainvoke(state)
    return {
        "messages": result["messages"],
        "next": "supervisor"
    }


async def weather_agent_node(state: SupervisorState):
    """Execute weather agent"""
    agent = await create_weather_agent()
    result = await agent.ainvoke(state)
    return {
        "messages": result["messages"],
        "next": "supervisor"
    }


# Routing function
def route_after_supervisor(state: SupervisorState) -> Literal["math_agent", "weather_agent", "__end__"]:
    """Route based on supervisor's decision"""
    next_agent = state.get("next", "FINISH").lower()
    
    if next_agent == "math_agent":
        return "math_agent"
    elif next_agent == "weather_agent":
        return "weather_agent"
    else:
        return "__end__"


def route_after_agent(state: SupervisorState) -> Literal["supervisor", "__end__"]:
    """Route back to supervisor or end"""
    next_step = state.get("next", "FINISH").lower()
    
    if next_step == "supervisor":
        return "supervisor"
    else:
        return "__end__"


# Build the graph
async def create_supervisor_graph():
    """Create the multi-agent graph with supervisor"""
    
    # Initialize graph
    workflow = StateGraph(SupervisorState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("math_agent", math_agent_node)
    workflow.add_node("weather_agent", weather_agent_node)
    
    # Add edges
    workflow.add_edge(START, "supervisor")
    
    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "math_agent": "math_agent",
            "weather_agent": "weather_agent",
            "__end__": END
        }
    )
    
    # Route back from agents to supervisor for potential follow-up
    workflow.add_conditional_edges(
        "math_agent",
        route_after_agent,
        {
            "supervisor": "supervisor",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "weather_agent",
        route_after_agent,
        {
            "supervisor": "supervisor",
            "__end__": END
        }
    )
    checkpointer = InMemorySaver()  
    # Compile the graph
    graph = workflow.compile(checkpointer=checkpointer)
    
    show_wf_image(graph)
    return graph

def show_wf_image(graph):
        from PIL import Image as img
        from IPython.display import Image, display
        import IPython.display as Disp
        i =  graph.get_graph().draw_mermaid_png()
        display(Image(i))
        with open("/tmp/graph.png", "wb") as f:
            f.write(i)
        img_s = img.open("/tmp/graph.png")
        img_s.show()

# Main execution function
async def run_multi_agent_system(query: str):
    """Run the multi-agent system with a query"""
    
    # Create the graph
    graph = await create_supervisor_graph()
    
    # Prepare input
    input_state = {
        "messages": [HumanMessage(content=query)]
    }
    
    # Stream the execution
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    config = {"configurable": {"thread_id": str(uuid.uuid4())},"recursion_limit": 100}
    
    async for event in graph.astream(input_state, config, stream_mode="values"):
        if "messages" in event:
            last_message = event["messages"][-1]
            print(f"{last_message.type}: {last_message.content}\n")
    
    return event


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example queries
        queries = [
            "hi! I'm bob",
            "What is 25 * 47 + 123/5?",
            "Now add 10 to the result?",

            "What's the weather in New York?",
            "What is my name?",
           # "Calculate the square root of 144"
        ]
        
        for query in queries:
            await run_multi_agent_system(query)
            print("\n" + "="*60 + "\n")
    
    asyncio.run(main())