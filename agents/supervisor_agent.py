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
        - flight_search_agent: Handles flight search queries, flight schedules, and flight information. All the flight related queries should be handled by this agent or even the follow up queries. Send code for origin and destination  .
        - conversation_agent: For any conversation. Handles general conversation queries, conversation history, and conversation management. For any conversation other than specialized agents can be handled by this agent.
        - FINISH: Use this when the task is complete or doesn't require specialized agents or there is some data required from user or the process is complete and also add a message to the user that the task is incomplete with reason.  
        
         CRITICAL RULES:
        - You MUST NOT answer the user's query.
        - You MUST NOT generate any content other than an agent name.
        - Your ONLY valid outputs are exactly one of: math_agent, weather_agent, flight_search_agent, conversation_agent, FINISH.
        - IF its not clear from the query which agent to use, then use the conversation_agent.

        Analyze the user's query and the conversation history. Decide which agent should handle it.
        Respond with the agent name: math_agent, weather_agent,conversation_agent, flight_search_agent, or FINISH.
        
           Examples: "What is the capital of France?", "Who is the president?", 
                    "Explain what Python is", "Tell me a joke"
          
        """

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        *messages
    ])
    
    # Determine next agent
    next_agent = response.content.strip().lower()
    
    # Validate the choice
    if next_agent not in ["math_agent", "weather_agent", "flight_search_agent", "conversation_agent", "finish"]:
        next_agent = "FINISH"

    return {"next": next_agent}