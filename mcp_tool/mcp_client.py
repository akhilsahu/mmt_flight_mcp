# graph.py
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent          
from dotenv import load_dotenv
import os
import asyncio
 

#from ..chatbot import AgenticChatBot

load_dotenv()

def mcp_client_tool():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/math_server.py"],
                "transport": "stdio",
            },
            "weather_forecast": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/weather_server.py"],
                "transport": "stdio",
            },
            "flight_search": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/flight_search_server.py"],
                "transport": "stdio",
            },
            
            # "weather": {
            #     # make sure you start your weather server on port 8000
            #     "url": "http://localhost:8000/mcp",
            #     "transport": "streamable_http",
            # }
        }
    )
    return client

async def make_graph():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/math_server.py"],
                "transport": "stdio",
            },
            "weather_forecast": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/weather_server.py"],
                "transport": "stdio",
            },
            "flight_search": {
                "command": "python",
                # Make sure to update to the full absolute path to your math_server.py file
                "args": ["mcp/flight_search_server.py"],
                "transport": "stdio",
            },
            # "weather": {
            #     # make sure you start your weather server on port 8000
            #     "url": "http://localhost:8000/mcp",
            #     "transport": "streamable_http",
            # }
        }
    )
    tools = await client.get_tools()
    agent = create_agent("openai:gpt-4.1", tools)
    response = await agent.ainvoke({"messages": "What up?"})
 
    #math_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
    print(response)


def chaties():
    pass
    #chatbot = AgenticChatBot()
    #response,data = chatbot.process_message("Wats up?")

# if __name__ == "__main__":
#     #   import sys
#     #   print(sys.path)
#       #chaties()
#       asyncio.run(make_graph())