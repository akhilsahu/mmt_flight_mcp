# Multi-Agent Flight Search System

This project implements a multi-agent system using LangGraph for orchestrating specialized agents to perform tasks like searching for flights, providing weather forecasts, and performing calculations.

## Features

- **Flight Search:** Search for flights on MakeMyTrip.
- **Weather Forecast:** Get weather forecasts for a given location.
- **Math Calculations:** Perform basic mathematical calculations.
- **Multi-Agent Orchestration:** Uses a supervisor agent to delegate tasks to the appropriate specialized agent.

## Architecture

The system is built using the following components:

- **LangGraph:** A library for building stateful, multi-agent applications with LLMs.
- **Supervisor Agent:** A central agent that manages the workflow and delegates tasks to other agents based on the user's query.
- **Specialized Agents:**
    - `FlightSearchAgent`: Interacts with the flight search tool.
    - `WeatherAgent`: Interacts with the weather tool.
    - `MathAgent`: Interacts with the math tool.
- **MCP Tool Servers:** Each specialized agent communicates with a corresponding MCP (Model-Client-Protocol) server that exposes the tools for that agent's domain. These servers run as separate processes.

## How to Run

### Prerequisites

- Python 3.10+
- An OpenAI API key

### 1. Setup Environment

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The `mcp` library is used in this project. If you have issues with this dependency, you may need to install it from a custom source.*

4.  **Create a `.env` file** in the root directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-openai-api-key"
    ```

### 2. Run the Tool Servers

Open three separate terminal windows and run the following commands, one in each terminal:

-   **Math Server:**
    ```bash
    python mcp_tool/math_server.py
    ```

-   **Weather Server:**
    ```bash
    python mcp_tool/weather_server.py
    ```

-   **Flight Search Server:**
    ```bash
    python mcp_tool/flight_search_server.py
    ```

### 3. Run the Main Application

Once the tool servers are running, open a new terminal and run the main application:

```bash
python main.py
```

The application will then process the example queries defined in `main.py`.

## Example Usage

You can modify the `queries` list in `main.py` to ask the system different questions:

```python
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example queries
        queries = [
            "What is 25 * 47 + 123 /4?",
            "What's the weather in New York?",
            # "Search for flights from LKO to IXL on 10/10/2024" # This requires the flight server
        ]
        
        for query in queries:
            await run_multi_agent_system(query)
            print("\n" + "="*60 + "\n")
    
    asyncio.run(main())
```