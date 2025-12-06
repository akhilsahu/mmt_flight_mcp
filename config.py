from langchain_openai import ChatOpenAI
AGENT_CONFIG = {
    "math_agent": {
        "model": ChatOpenAI(model="gpt-4o"),
        "system_prompt": "You are a specialized math agent. Use the available math tools to solve calculations accurately.",
        "tool_config": {
            "math": {
                "command": "python",
                "args": ["mcp_tool/math_server.py"],
                "transport": "stdio",
            }
        }
    },
    "weather_agent": {
        "model": ChatOpenAI(model="gpt-4o"),
        "system_prompt": "You are a specialized weather agent. Use the available weather tools to provide accurate forecasts and meteorological information.",
        "tool_config": {
            "weather": {
                "command": "python",
                "args": ["mcp_tool/weather_server.py"],
                "transport": "stdio",
            }
        }
    },
    "flight_search_agent": {
        "model": ChatOpenAI(model="gpt-4o"),
        "system_prompt": "You are a specialized flight search agent. Use the available flight search tools to search for flights between two cities on a given date.",
        "tool_config": {
            "flight_search": {
                "command": "python",
                "args": ["mcp_tool/flight_search_server.py"],
                "transport": "stdio",
            }
        }
    }
}