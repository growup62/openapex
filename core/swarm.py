import logging
import uuid
from typing import Dict, Any, List

# To avoid circular imports, we don't import Brain here, we pass the dependencies
# or import AgentBase directly.
from core.agent_base import AgentBase
from core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

class SwarmManager:
    """
    Manages the dynamic creation and execution of specialized sub-agents.
    This enables the 'Swarm Intelligence' aspect of openApex V5.
    """
    
    def __init__(self, main_brain):
        """
        Takes the main brain instance so sub-agents can share the central LLMRouter
        and toolset if necessary.
        """
        self.brain = main_brain
        self.active_agents: Dict[str, AgentBase] = {}
        
    def delegate_task(self, role_name: str, task_description: str, allowed_tools: List[str] = None) -> str:
        """
        Spawns a new temporary agent specialized for the requested role,
        assigns it the task, and returns the result to the main agent.
        """
        agent_id = f"SubAgent-{role_name}-{str(uuid.uuid4())[:6]}"
        logger.info(f"[SwarmManager] Spawning new sub-agent: {agent_id} for role: {role_name}")
        
        # Create a tailored system prompt for the sub-agent
        role_prompt = (
            f"Kamu adalah {agent_id}, sebuah Sub-Agen dari sistem Induk openApex. "
            f"Peran dan keahlian utamamu adalah: {role_name}. "
            f"Tugasmu spesifik dan difokuskan hanya untuk menyelesaikan perintah berikut. "
            f"Berikan hasil akhir yang sangat komprehensif agar Indukmu bisa langsung menggunakannya."
        )
        
        # We share the same router to ensure model parameters are consistent
        sub_agent = AgentBase(name=agent_id, role_description=role_prompt, router=self.brain.router, is_subagent=True)
        self.active_agents[agent_id] = sub_agent
        
        # Transfer specified tools from the main agent to the sub agent
        if allowed_tools is None:
            # If no specific tools mentioned, give them access to safe retrieval/web tools
            allowed_tools = ["web_search", "web_fetch", "run_python", "analyze_image", "system_read_file"]
            
        for tool in self.brain.main_agent.tools:
            tool_fn_name = tool["function"]["name"]
            if tool_fn_name in allowed_tools:
                sub_agent.register_tool(tool)
        
        # Execute the task
        logger.info(f"[SwarmManager] Executing task on {agent_id}...")
        try:
            # We bypass the Brain's generic solve and run the agent raw thinking loop
            result = sub_agent.run(
                objective=task_description,
                execute_tool_callback=self.brain._execute_tool
            )
            logger.info(f"[SwarmManager] Sub-agent {agent_id} completed the task.")
        except Exception as e:
            logger.error(f"[SwarmManager] Sub-agent {agent_id} failed: {e}")
            result = f"Error evaluating sub-task: {e}"
        finally:
            # Cleanup
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
                
        return result

# Registerable Tool Schema for passing to the LLM Router
DELEGATE_TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delegate_task",
        "description": "Spawn a specialized sub-agent to handle a specific sub-task. The sub-agent runs independently and returns the final comprehensive result to you. Use this to divide and conquer complex tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string", "description": "The specific role of the sub-agent (e.g. 'Python Programmer', 'Web Researcher', 'Data Analyst')."},
                "task_description": {"type": "string", "description": "A highly detailed description of exactly what the sub-agent needs to accomplish."},
                "allowed_tools": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Optional list of tool names the sub-agent is allowed to use. e.g. ['web_search', 'run_python']. If omitted, safe defaults are provided."
                }
            },
            "required": ["role_name", "task_description"]
        }
    }
}
