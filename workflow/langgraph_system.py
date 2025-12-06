from typing import Callable, Dict, List, Optional
import uuid

from langgraph.graph import StateGraph, START, END
from agents.supervisor_agent import supervisor_node
from agents.weather_agent import WeatherAgent
from agents.math_agent import MathAgent
from workflow.agent_state import AgentState
from langgraph.checkpoint.memory import InMemorySaver


class LanggraphMultiAgentSystem:

    def __init__(self,model_manager,memory_manager=None):
        self.model_manager = model_manager
        self.memory_manager = memory_manager
        self.agents = {}
        self.graph = None
        self.agents = {
            "weather_agent": {"agent": WeatherAgent(self.model_manager ),"node": self._get_agent_node(WeatherAgent,"weather_agent")},
            "math_agent": {"agent": MathAgent(self.model_manager ),"node": self._get_agent_node(MathAgent,"math_agent")},
        #     "data_agent": DataAnalyst(self.model_manager, self.tool_registry.get_tools(['math', 'utility'])),
        #     "conversation_agent": ConversationAgent(self.model_manager, self.tool_registry.get_tools(['conversation', 'memory'])),
        #     "flight_agent": FlightSearchAgent(self.model_manager, self.tool_registry.get_tools(['flight_search']))
        # 
        }
         
    
    def _get_agent_node(self, func: Callable,agent_name: str):
        async def create_agent_node( state: AgentState):
            """Execute weather agent
                func: create_weather_agent or create_math_agent
            
            """
            #agent = await func(self.model_manager).create_agent_react()
            agent = await self.agents[agent_name]["agent"].create_agent_react()
            #config = {"configurable": {"thread_id": str(uuid.uuid4())}}

            result = await agent.ainvoke(state)#, config=config)
            return {
                "messages": result["messages"],
                "next": "supervisor"
            }
       
        return create_agent_node
        
    # Build the graph
    async def create_supervisor_graph(self):
        """Create the multi-agent graph with supervisor"""
        
        # Initialize graph
        workflow = StateGraph(AgentState)
       
        # Add nodes
        workflow.add_node("supervisor", supervisor_node)
        
        for agent_name, agent_node in self.agents.items():
            workflow.add_node(agent_name, agent_node["node"])
        
        
        # Add edges
        workflow.add_edge(START, "supervisor")
        
        route_after_supervisor = lambda state: (
            "math_agent" if state.get("next", "FINISH").lower() == "math_agent"
            else "weather_agent" if state.get("next", "FINISH").lower() == "weather_agent"
            else "__end__"
        )
        # Conditional routing from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            {
                **{agent_name: agent_name for agent_name in self.agents.keys()},
                "__end__": END
            }
        ) 
        route_after_agent = lambda state: (
            "supervisor" 
            if state.get("next", "FINISH").lower() == "supervisor" 
            else "__end__"
        )
        for agent_name, agent_node in self.agents.items():
            workflow.add_conditional_edges(agent_name,route_after_agent, {
            "supervisor": "supervisor",   
            "__end__": END
        })
        # Compile the graph
        workflow.set_entry_point("supervisor")
        # self.graph = workflow.compile(checkpointer=self.checkpointer)  # Temporarily disabled
        memory_store = InMemorySaver()

        graph = workflow.compile(checkpointer=memory_store)
        
        self.show_wf_image(graph)
        print("Displayed")
        return graph

    def show_wf_image(self,graph):
        from PIL import Image as img
        from IPython.display import Image, display
        import IPython.display as Disp
        i =  graph.get_graph().draw_mermaid_png()
        display(Image(i))
        with open("/tmp/graph.png", "wb") as f:
            f.write(i)
        img_s = img.open("/tmp/graph.png")
        img_s.show()