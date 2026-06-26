"""
Multi-Agent LangGraph System
============================
Supervisor → routes to:
  - WeatherAgent  (with human-in-the-loop interrupt for missing location)
  - MathAgent     (add / subtract tools)
  - SearchAgent   (Google Search via Tavily MCP-style tool)
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt,Command

# ─────────────────────────────────────────────
# 1.  SHARED STATE
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    # Which sub-agent the supervisor chose
    next_agent: str
    # Populated by the weather agent when it needs a location from the user
    pending_location_request: bool


# ─────────────────────────────────────────────
# 2.  TOOLS
# ─────────────────────────────────────────────

# ── Weather tools ──────────────────────────────
@tool
def get_weather(location: str) -> str:
    """Return the current weather for a given location.

    Args:
        location: City name or 'City, Country' string.
    """
    # In production replace with a real API call (OpenWeatherMap, etc.)
    mock_data = {
        "london":    "☁️  London: 14 °C, overcast, 80 % humidity",
        "new york":  "🌤  New York: 22 °C, partly cloudy, 55 % humidity",
        "tokyo":     "🌧  Tokyo: 18 °C, light rain, 90 % humidity",
        "paris":     "☀️  Paris: 25 °C, sunny, 40 % humidity",
        "lucknow":   "🌡  Lucknow: 38 °C, hot & humid, 60 % humidity",
    }
    key = location.lower().split(",")[0].strip()
    return mock_data.get(key, f"🌍 {location}: 20 °C, clear skies, 50 % humidity (mock)")


# ── Math tools ─────────────────────────────────
@tool
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: First number.
        b: Second number.
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a.

    Args:
        a: First number.
        b: Number to subtract.
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.
    """
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b.

    Args:
        a: Numerator.
        b: Denominator (must not be zero).
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


# ── Search tool ────────────────────────────────
@tool
def google_search(query: str) -> str:
    """Search the web using Google (via Tavily) and return a summary.

    Args:
        query: The search query string.
    """
    try:
        from tavily import TavilyClient          # pip install tavily-python
        import os
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        results = client.search(query, max_results=3)
        snippets = [
            f"• {r['title']}: {r['content'][:200]}"
            for r in results.get("results", [])
        ]
        return "\n".join(snippets) if snippets else "No results found."
    except Exception as exc:
        # Graceful fallback so the demo runs without an API key
        return (
            f"[Search mock – Tavily not configured: {exc}]\n"
            f"Top result for '{query}': This is a placeholder search result. "
            "Configure TAVILY_API_KEY for live results."
        )


# ─────────────────────────────────────────────
# 3.  LLMs  (swap model names as needed)
# ─────────────────────────────────────────────

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

supervisor_llm = _llm
weather_llm    = _llm.bind_tools([get_weather])
math_llm       = _llm.bind_tools([add, subtract, multiply, divide])
search_llm     = _llm.bind_tools([google_search])


# ─────────────────────────────────────────────
# 4.  SUPERVISOR NODE
# ─────────────────────────────────────────────

SUPERVISOR_SYSTEM = """You are a routing supervisor. Analyse the user's latest message
and decide which specialist agent should handle it.

Reply with ONLY one of these words (no punctuation, no explanation):
  weather   – questions about weather / temperature / forecast
  math      – arithmetic, calculations, numbers
  search    – general knowledge, news, facts, anything else

Examples:
  "What's the weather in Paris?" → weather
  "What is 42 + 58?"            → math
  "Who invented the telephone?"  → search
"""

def supervisor_node(state: AgentState) -> dict:
    """Route the conversation to the right sub-agent."""
    response = supervisor_llm.invoke(
        [{"role": "system", "content": SUPERVISOR_SYSTEM}] + state["messages"]
    )
    route = response.content.strip().lower()
    if route not in {"weather", "math", "search"}:
        route = "search"          # safe default

    return {
        "messages": [AIMessage(content=f"[Supervisor] Routing to → {route} agent")],
        "next_agent": route,
        "pending_location_request": False,
    }


def supervisor_router(state: AgentState) -> Literal["weather_agent", "math_agent", "search_agent"]:
    mapping = {
        "weather": "weather_agent",
        "math":    "math_agent",
        "search":  "search_agent",
    }
    return mapping[state["next_agent"]]


# ─────────────────────────────────────────────
# 5.  WEATHER AGENT  (with human-in-the-loop)
# ─────────────────────────────────────────────

WEATHER_SYSTEM = """You are a weather assistant. Use the get_weather tool to answer
weather queries. If the user has NOT mentioned any location, do NOT guess —
instead reply with exactly: LOCATION_NEEDED"""

def weather_agent_node(state: AgentState) -> dict:
    """Weather agent with interrupt() when location is missing."""
    response = weather_llm.invoke(
        [{"role": "system", "content": WEATHER_SYSTEM}] + state["messages"]
    )

    # ── Human-in-the-loop: ask for location ───────────────────────────────
    if isinstance(response.content, str) and "LOCATION_NEEDED" in response.content:
        # interrupt() pauses execution and surfaces a question to the caller.
        # The graph resumes once the caller supplies the answer via
        #   graph.invoke(Command(resume="London"), config=config)
        location = interrupt("🌍 Please provide your location (e.g. 'London' or 'Tokyo'):")

        # Inject the user's answer as a new HumanMessage and re-invoke
        updated_messages = state["messages"] + [HumanMessage(content=location)]
        response = weather_llm.invoke(
            [{"role": "system", "content": WEATHER_SYSTEM}] + updated_messages
        )
        # Fall through to tool-call handling below with the enriched response
        state = {**state, "messages": updated_messages}

    # ── Handle tool calls ─────────────────────────────────────────────────
    new_messages: list[BaseMessage] = [response]
    if response.tool_calls:
        tool_node = ToolNode([get_weather])
        tool_result = tool_node.invoke({"messages": state["messages"] + [response]})
        new_messages += tool_result["messages"]

        # Final answer after tool execution
        final = weather_llm.invoke(
            [{"role": "system", "content": WEATHER_SYSTEM}]
            + state["messages"]
            + new_messages
        )
        new_messages.append(final)

    return {"messages": new_messages, "pending_location_request": False}


# ─────────────────────────────────────────────
# 6.  MATH AGENT
# ─────────────────────────────────────────────

MATH_SYSTEM = """You are a precise math assistant. Use the provided arithmetic tools
(add, subtract, multiply, divide) to solve problems step by step. Always show
which tool you called and what result you got before giving the final answer."""

def math_agent_node(state: AgentState) -> dict:
    response = math_llm.invoke(
        [{"role": "system", "content": MATH_SYSTEM}] + state["messages"]
    )

    new_messages: list[BaseMessage] = [response]
    if response.tool_calls:
        tool_node = ToolNode([add, subtract, multiply, divide])
        tool_result = tool_node.invoke({"messages": state["messages"] + [response]})
        new_messages += tool_result["messages"]

        final = math_llm.invoke(
            [{"role": "system", "content": MATH_SYSTEM}]
            + state["messages"]
            + new_messages
        )
        new_messages.append(final)

    return {"messages": new_messages}


# ─────────────────────────────────────────────
# 7.  SEARCH AGENT
# ─────────────────────────────────────────────

SEARCH_SYSTEM = """You are a helpful research assistant. Use the google_search tool
to find current, accurate information. Summarise the search results clearly and
cite key facts."""

def search_agent_node(state: AgentState) -> dict:
    response = search_llm.invoke(
        [{"role": "system", "content": SEARCH_SYSTEM}] + state["messages"]
    )

    new_messages: list[BaseMessage] = [response]
    if response.tool_calls:
        tool_node = ToolNode([google_search])
        tool_result = tool_node.invoke({"messages": state["messages"] + [response]})
        new_messages += tool_result["messages"]

        final = search_llm.invoke(
            [{"role": "system", "content": SEARCH_SYSTEM}]
            + state["messages"]
            + new_messages
        )
        new_messages.append(final)

    return {"messages": new_messages}


# ─────────────────────────────────────────────
# 8.  BUILD THE GRAPH
# ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────
    builder.add_node("supervisor",    supervisor_node)
    builder.add_node("weather_agent", weather_agent_node)
    builder.add_node("math_agent",    math_agent_node)
    builder.add_node("search_agent",  search_agent_node)

    # ── Edges ──────────────────────────────────
    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "weather_agent": "weather_agent",
            "math_agent":    "math_agent",
            "search_agent":  "search_agent",
        },
    )

    builder.add_edge("weather_agent", END)
    builder.add_edge("math_agent",    END)
    builder.add_edge("search_agent",  END)

    # MemorySaver persists state across interrupt/resume cycles
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# ─────────────────────────────────────────────
# 9.  CONVENIENCE RUNNER  (for quick testing)
# ─────────────────────────────────────────────

def run(query: str, thread_id: str = "default") -> str:
    """
    Run the multi-agent graph for a single query.

    Returns the last assistant message as a string.

    For weather queries without a location the graph will return an
    ``{'__interrupt__': ...}`` dict – call ``resume(location, thread_id)``
    to continue.
    """
    graph = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "",
        "pending_location_request": False,
    }
    result = graph.invoke(initial_state, config=config)

    if "__interrupt__" in result:
        return f"[INTERRUPT] {result['__interrupt__'][0].value}"

    last_msg = result["messages"][-1]
    return last_msg.content if hasattr(last_msg, "content") else str(last_msg)


def resume(location: str, thread_id: str = "default") -> str:
    """Resume a paused weather query after the user provides a location."""
    from langgraph.types import Command

    graph = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(Command(resume=location), config=config)

    last_msg = result["messages"][-1]
    return last_msg.content if hasattr(last_msg, "content") else str(last_msg)


# ─────────────────────────────────────────────
# 10.  ENTRY POINT
# ─────────────────────────────────────────────

THREAD_ID = "chat-session-1"          # fixed thread → persistent context
_graph    = build_graph()             # compiled once, reused every turn
_config   = {"configurable": {"thread_id": THREAD_ID}}
 
 
def chat(user_message: str) -> str:
    """
    Send a message to the multi-agent graph and return the final reply.
 
    Context is automatically preserved across calls via MemorySaver —
    no need to manage history manually.
 
    If the weather agent needs a location it will raise an interrupt.
    The caller must handle it via `chat_resume(location)`.
 
    Args:
        user_message: Plain text from the user.
 
    Returns:
        The agent's response as a string.
        If an interrupt occurs, returns a special string starting with
        "INTERRUPT:" followed by the question to ask the user.
    """
    initial: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "next_agent": "",
    }
    result = _graph.invoke(initial, config=_config)
 
    # ── Handle interrupt (missing location for weather) ───────────────────────
    if "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        return f"INTERRUPT:{question}"
 
    # ── Return the last meaningful AI message ─────────────────────────────────
    ai_msgs = [
        m for m in result["messages"]
        if isinstance(m, AIMessage) and not m.content.startswith("[supervisor")
    ]
    return ai_msgs[-1].content if ai_msgs else "No response."
 
 
def chat_resume(location: str) -> str:
    """
    Resume a paused weather query after the user provides a location.
 
    Args:
        location: The city/location string supplied by the user.
 
    Returns:
        The weather agent's response.
    """
    result = _graph.invoke(Command(resume=location), config=_config)
 
    if "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        return f"INTERRUPT:{question}"
 
    ai_msgs = [
        m for m in result["messages"]
        if isinstance(m, AIMessage) and not m.content.startswith("[supervisor")
    ]
    return ai_msgs[-1].content if ai_msgs else "No response."
 
 
def reset_chat() -> None:
    """Clear the conversation context (start a new thread)."""
    global _graph, _config
    _graph  = build_graph()
    _config = {"configurable": {"thread_id": THREAD_ID}}
    print("Chat context reset.")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE CLI  ←  run this file directly
# ─────────────────────────────────────────────────────────────────────────────
 
BANNER = """
╔══════════════════════════════════════════════════════╗
║        LangGraph Multi-Agent Chatbot                 ║
║                                                      ║
║  Agents: supervisor · weather · math · search        ║
║  Commands: 'reset' to clear context, 'quit' to exit  ║
╚══════════════════════════════════════════════════════╝
"""
 
def _agent_label(reply: str) -> str:
    """Detect which agent replied based on content heuristics."""
    low = reply.lower()
    if any(w in low for w in ["°c", "humidity", "rain", "sunny", "cloudy", "forecast"]):
        return "[weather agent]"
    if any(w in low for w in ["result", "equals", "calculation", "add(", "multiply("]):
        return "[math agent]"
    return "[search agent]"
 
 
def main():
    print(BANNER)
    print("Context is preserved across the entire session.\n")
 
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
 
        if not user_input:
            continue
 
        if user_input.lower() in {"quit", "exit", "bye"}:
            print("Goodbye!")
            break
 
        if user_input.lower() == "reset":
            reset_chat()
            continue
 
        reply = chat(user_input)
 
        # ── Handle weather interrupt ──────────────────────────────────────────
        if reply.startswith("INTERRUPT:"):
            question = reply[len("INTERRUPT:"):]
            print(f"\nWeather Agent: {question}")
            try:
                location = input("You (location): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
            if not location:
                print("No location provided. Skipping.\n")
                continue
            reply = chat_resume(location)
 
        label = _agent_label(reply)
        print(f"\nAgent {label}:\n{reply}\n")
 
 
if __name__ == "__main__":
    main()

# if __name__ == "__main__":
#     import sys

#     queries = [
#         "What is 128 + 256?",
#         "What's the weather like?",          # ← will trigger interrupt
#         "What's the weather in Tokyo?",
#         "Who invented the World Wide Web?",
#     ]

#     for q in queries:
#         print(f"\n{'='*60}")
#         print(f"USER: {q}")
#         ans = run(q, thread_id=q[:20])
#         print(f"AGENT: {ans}")

#         # Simulate human-in-the-loop resume for the missing-location case
#         if ans.startswith("[INTERRUPT]"):
#             location = input("Enter location: ")
#             print(f"  → User provides location: {location}")
#             ans2 = resume(location, thread_id=q[:20])
#             print(f"AGENT (resumed): {ans2}")