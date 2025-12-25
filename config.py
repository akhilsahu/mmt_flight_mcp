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
        "system_prompt": '''You are a specialized flight search agent. Use the available flight search tools to search for flights between two cities on a given date. 
        Add a note field to each flight in the result like cheapest fastest or any cool offer.
        example for source: mmt, expedia,ixigo  or all - should be all until user asks for specific source
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