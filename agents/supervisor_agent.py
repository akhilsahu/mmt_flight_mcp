from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from workflow.agent_state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
# Supervisor function to route to appropriate agent
from datetime import date

async def supervisor_node(state: AgentState):
    """Supervisor agent that decides which specialized agent to call"""
    
    messages = state["messages"]
    
    # Create supervisor LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = f"""You are a supervisor agent that routes queries to specialized agents.
        Current date is  {date.today()}
        Available agents:
        - math_agent: Handles mathematical calculations, equations, and numerical problems
        - weather_agent: Handles weather queries, forecasts, and meteorological information
        - flight_search_agent: Handles flight search queries, flight schedules, and flight information. Send code for origin and destination  .
        - FINISH: Use this when the task is complete or doesn't require specialized agents or there is some data required from user

        Analyze the user's query and the conversation history. Decide which agent should handle it.
        If the last message is from an agent and it contains the answer to the user's query, you MUST choose FINISH.
        Respond with ONLY the agent name: math_agent, weather_agent, flight_search_agent, or FINISH."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        *messages
    ])
    
    # Determine next agent
    next_agent = response.content.strip().lower()
    
    # Validate the choice
    if next_agent not in ["math_agent", "weather_agent", "flight_search_agent", "finish"]:
        next_agent = "FINISH"
    
    return {"next": next_agent}