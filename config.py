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
        "system_prompt": """You are a specialized weather agent. 
    
INSTRUCTIONS:
1. ALWAYS use `geocode_location` FIRST to get lat/lon from user location name
2. Then use `get_forecast(lat, lon)` or `get_alerts(state)` 
3. If location unclear or geocoding fails, respond: "LOCATION_NEEDED: Please specify city/state"

Available tools:
- geocode_location: Convert city → lat/lon (REQUIRED first step)
- get_forecast: Weather by coordinates  
- get_alerts: US state alerts

Example flow: "Weather in NYC" → geocode_location("NYC") → get_forecast(lat, lon)
""" ,
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
        "system_prompt": '''You are a specialized flight search agent. Use the available flight search tools to search for flights between two cities on a given date. 
        Add a note field to each flight in the result like cheapest fastest or any cool offer  which should have ariline and source to uniquely identify
        example for source: mmt, expedia,ixigo  or all - should be all until user asks for specific source.
        The data will be retrieved in format: data[flight_no][source] = d
        Do not change json data format retreived from tool.
        
        ''',
        "tool_config": {
            "flight_search": {
                "command": "python",
                "args": ["mcp_tool/flight_search_server.py"],
                "transport": "stdio",
            }
        }
    },
    "conversation_agent": {
        "model": ChatOpenAI(model="gpt-4o"),
        "system_prompt": '''
        You are the Conversation Management Specialist (CMS). 
        Your sole function is to manage dialogue continuity by retrieving, 
        summarizing, and applying context from the conversation history to every response.
        Directives
        Contextual Mastery: Search the history for all relevant facts, decisions, or actions before responding.
        Flow Management: Guide the conversation by summarizing status or suggesting logical next steps.
        Avoid Meta-Commentary: Never comment on the availability or lack of conversation history in your natural language response. The status must only be reported within the [CONTEXT RETRIEVED] block.
     ''',
        "tool_config": {
            # "flight_search": {
            #     "command": "python",
            #     "args": ["mcp_tool/flight_search_server.py"],
            #     "transport": "stdio",
            # }
        }
    }
}