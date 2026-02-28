import logging
import re
import uuid
from typing import Dict, Any, Optional

from core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

class AgentBase:
    """
    Base class for any agent within the openApex swarm (e.g., Coder Agent, System Agent).
    Orchestrates memory management, tool execution, and thinking loops.
    """
    def __init__(self, name: str, role_description: str, router: LLMRouter = None):
        self.name = name
        self.role_description = role_description
        self.router = router or LLMRouter()
        self.tools = []
        
        # Immediate context window
        self.conversation_history = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        logger.info(f"Agent '{self.name}' initialized.")

    def _build_system_prompt(self) -> str:
        prompt = f"You are {self.name}. {self.role_description}\n\n"
        prompt += "CRITICAL GUIDELINES FOR TOOL USAGE:\n"
        prompt += "1. You have access to tools. You MUST use them if you need external information or need to affect the system.\n"
        prompt += "2. When calling a tool, you MUST output a valid JSON tool call according to the provided schema.\n"
        prompt += "3. If asked to search the web, USE the web_search tool.\n"
        prompt += "4. Think step-by-step before acting.\n"
        return prompt

    def register_tool(self, tool_schema: Dict[str, Any]):
        """Registers a tool schema (JSON format) that the agent can invoke."""
        self.tools.append(tool_schema)
        logger.debug(f"[{self.name}] Registered tool: {tool_schema.get('name', 'unknown')}")

    def add_message(self, role: str, content: str = None, **kwargs):
        """Adds a message to the agent's context window with optional extra fields like tool_calls."""
        message = {"role": role}
        if content is not None:
             message["content"] = content
        message.update(kwargs)
        self.conversation_history.append(message)

    def _parse_xml_tool_call(self, text: str):
        """
        Detects and parses XML-style tool calls that Groq's Llama model sometimes
        outputs as plain text instead of proper JSON tool_calls.
        Examples:
          <function>run_python</function>{"code": "print(2**100)"}</function>
          <function=web_search>{"query": "AI news"}</function>
        Returns a list of synthetic tool_calls if found, else None.
        """
        # Pattern 1: <function=tool_name>{json_args}</function>
        match = re.search(r'<function=(\w+)\s*>\s*(\{.*?\})\s*</function>', text, re.DOTALL)
        if not match:
            # Pattern 2: <function>tool_name</function>{json_args}</function>
            match = re.search(r'<function>(\w+)</function>\s*(\{.*?\})', text, re.DOTALL)
        if not match:
            # Pattern 3: <function=tool_name {"key": "val"}> (no closing tag)
            match = re.search(r'<function=(\w+)\s+(\{.*?\})\s*>', text, re.DOTALL)
        
        if match:
            func_name = match.group(1).strip()
            func_args = match.group(2).strip()
            logger.info(f"[{self.name}] Intercepted XML tool call from content: {func_name}")
            return [{
                "id": f"call_{str(uuid.uuid4())[:8]}",
                "type": "function",
                "function": {
                    "name": func_name,
                    "arguments": func_args
                }
            }]
        return None

    def run_cycle(self, user_input: str = None, force_reasoning: bool = True) -> Dict[str, Any]:
        """
        Executes a fundamental agent cycle: Receive input -> Think/Call Tool -> Return output.
        """
        if user_input:
            self.add_message("user", user_input)
            logger.info(f"[{self.name}] Processing input: {user_input[:50]}...")
        
        task_verbosity = "reasoning" if force_reasoning else "toolcalling"

        # Ask the LLM for the next step (could be a message or a tool call request)
        response = self.router.generate_response(
            messages=self.conversation_history,
            task_type=task_verbosity,
            tools=self.tools if self.tools else None
        )
        
        # Response handling framework
        if "error" in response:
            return {"status": "failed", "error": response["error"]}

        try:
             # Just extract the content/tool calls from the first choice
             choice = response.get("choices", [])[0]
             message_data = choice.get("message", {})
             
             # Priority 1: Check for proper JSON tool_calls (ideal path)
             if message_data.get("tool_calls"):
                 cnt = message_data.get("content")
                 if cnt is None:
                     cnt = ""
                 self.add_message("assistant", content=cnt, tool_calls=message_data["tool_calls"])
                 return {"status": "tool_requested", "tool_calls": message_data["tool_calls"]}
             
             # Priority 2: Check content for hidden XML-style tool calls
             if message_data.get("content"):
                 content_text = message_data["content"]
                 
                 xml_tool_calls = self._parse_xml_tool_call(content_text)
                 if xml_tool_calls:
                     self.add_message("assistant", content="", tool_calls=xml_tool_calls)
                     return {"status": "tool_requested", "tool_calls": xml_tool_calls}
                 
                 # Normal text response
                 self.add_message("assistant", content_text)
                 return {"status": "success", "response": content_text}
                 
        except IndexError:
             return {"status": "failed", "error": "Empty response from LLM"}
             
        return {"status": "unknown", "raw": response}
