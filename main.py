"""
Multi-Agent System with Supervisor and MCP Tools
Uses LangGraph for orchestration with specialized math and weather agents
"""

from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import uuid
from models.config_models import ModelConfig, ModelProvider
from core.model_settings import ModelSettings
from dotenv import load_dotenv
import os

from workflow.langgraph_system import LanggraphMultiAgentSystem

# Load .env file from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__),'.env')
if not load_dotenv(dotenv_path):
    print(f"Warning: Could not find .env file at {dotenv_path}. Please ensure it exists and contains the necessary environment variables.")
    # Depending on your application's needs, you might want to exit here
    # sys.exit("Exiting: .env file not found.")
    exit(1)
load_dotenv(dotenv_path)



# Main execution function
async def run_multi_agent_system(query: str):
    """Run the multi-agent system with a query"""
    
    model_manager = ModelSettings()
    default_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            temperature=0.7
        )
    model_manager.register_model("openai", default_config)
    # Create the graph
    graph = await LanggraphMultiAgentSystem(model_manager).create_supervisor_graph()
    
    # Prepare input
    input_state = {
        "messages": [HumanMessage(content=query)]
    }
    
    # Stream the execution
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    # langgraph_state = {
    #             "messages": [message],
    #             "context": {**(context or {}), **workflow_context},
    #             "chat_history": chat_history,  # Pass BaseMessage objects directly
    #             "conversation_id": conversation_id
    #         }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
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
            "What is 25 * 47 + 123 /4?",
            "What's the weather in New York?",
            #"Calculate the square root of 144"
        ]
        
        for query in queries:
            await run_multi_agent_system(query)
            print("\n" + "="*60 + "\n")
    
    asyncio.run(main())