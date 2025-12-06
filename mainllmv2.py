"""
Multi-Agent System with Supervisor and MCP Tools
Uses LangGraph for orchestration with specialized math and weather agents
"""
from models.response_models import GeneralResponse

from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain.agents import create_agent
from langgraph.types import Command
from dotenv import load_dotenv
import os
from agents.supervisor_agent import supervisor_node
from config import AGENT_CONFIG
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
  
async def get_agent(model_config,system_prompt,tool_config):
    client = MultiServerMCPClient({
        **tool_config
    })
    tools = await client.get_tools()
    agent = create_agent(
        model_config,
        tools,
        system_prompt=system_prompt,
        response_format=GeneralResponse )
    return agent

async def create_agent_react(agent_name: str):
    print(f"Agent name: {agent_name}")
    agent_config = AGENT_CONFIG[agent_name]
    return await get_agent(agent_config["model"],agent_config["system_prompt"],
    agent_config["tool_config"] )  
    

def get_agent_node(agent_name: str):
    async def agent_node(state: SupervisorState):
        agent = await create_agent_react(agent_name)
        result = await agent.ainvoke(state)
        return {
            "messages": result["messages"],
            "next": "supervisor"
        }
    return agent_node


# Routing function
def route_after_supervisor(state: SupervisorState) -> Literal["math_agent", "weather_agent", "flight_search_agent", "__end__"]:
    """Route based on supervisor's decision"""
    next_agent = state.get("next", "FINISH").lower()
    print(f"Next agent: {next_agent}")
    if next_agent == "math_agent":
        return "math_agent"
    elif next_agent == "weather_agent":
        return "weather_agent"
    # el
    if next_agent == "flight_search_agent":
        return "flight_search_agent"
    else:
        return "__end__"


def route_after_agent(state: SupervisorState) -> Literal["supervisor", "__end__"]:
    """Route back to supervisor or end"""
    next_step = state.get("next", "FINISH").lower()
    print(f"Next step: {next_step}")
    if next_step == "supervisor":
        return "supervisor"
    else:
        return "__end__"


# Build the graph
async def create_supervisor_graph():
    """Create the multi-agent graph with supervisor"""
    
    # Initialize graph
    workflow = StateGraph(SupervisorState)
 
    workflow.add_node("supervisor", supervisor_node)
    for agent_name, agent_config in AGENT_CONFIG.items():
        workflow.add_node(agent_name, get_agent_node(agent_name))
    
    # Add edges
    workflow.add_edge(START, "supervisor")
    
    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        { 
            **{agent_name: agent_name for agent_name in AGENT_CONFIG.keys()},
            "__end__": END
        }
    )
    
    # Route back from agents to supervisor for potential follow-up
    for agent_name in AGENT_CONFIG.keys():
        workflow.add_conditional_edges(
            agent_name,
            route_after_agent,
            {
                "supervisor": "supervisor",   
                "__end__": END
            }
        )
    # Compile the graph
    graph = workflow.compile()
    
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
    
    async for event in graph.astream(
        input_state,
        config={"recursion_limit": 100},
        stream_mode="values"
    ):
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
            
           # "What is 25 * 47 + 123/5?",
            #"What's the weather in New York?",
           "Use flight search agent to search for flights",
            "Search for some flights from IXL to LKO on 2025-12-10",
            #"Calculate the square root of 144"
        ]
        
        for query in queries:
            await run_multi_agent_system(query)
            print("\n" + "="*60 + "\n")
    
    asyncio.run(main())