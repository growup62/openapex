import logging
import json
from typing import Dict, Any

from core.llm_router import LLMRouter
from core.agent_base import AgentBase
from orchestrator.state_manager import StateManager
from tools.system_tool import (
    SystemTool, 
    SYSTEM_TOOL_SCHEMA,
    SYSTEM_READ_FILE_SCHEMA,
    SYSTEM_WRITE_FILE_SCHEMA,
    SYSTEM_LIST_DIR_SCHEMA
)
from tools.browser import BrowserTool, BROWSER_TOOL_SCHEMA
from tools.file_patcher import FilePatcherTool, SYSTEM_PATCH_FILE_SCHEMA
from tools.web_search import WebSearchTool, WEB_SEARCH_SCHEMA
from tools.python_repl import PythonREPLTool, PYTHON_REPL_SCHEMA
from tools.self_learner import (
    SelfLearnerTool,
    SELF_REFLECT_SCHEMA,
    RECALL_KNOWLEDGE_SCHEMA,
    STUDY_URL_SCHEMA
)
from tools.pc_control import (
    PCControlTool,
    SCREENSHOT_SCHEMA,
    GET_CLIPBOARD_SCHEMA,
    SET_CLIPBOARD_SCHEMA,
    LIST_PROCESSES_SCHEMA,
    KILL_PROCESS_SCHEMA,
    DISK_USAGE_SCHEMA,
    OPEN_APP_SCHEMA,
    SYSTEM_STATS_SCHEMA
)
from tools.voice_engine import (
    VoiceEngine,
    TEXT_TO_SPEECH_SCHEMA,
    SPEECH_TO_TEXT_SCHEMA,
    LIST_TTS_VOICES_SCHEMA
)
from tools.openclaw_tools import (
    WebFetchTool,
    ImageAnalysisTool,
    CronSchedulerTool,
    MessageTool,
    WEB_FETCH_SCHEMA,
    IMAGE_ANALYSIS_SCHEMA,
    CRON_ADD_SCHEMA,
    CRON_LIST_SCHEMA,
    CRON_REMOVE_SCHEMA,
    SEND_MESSAGE_SCHEMA
)
from tools.social_media import (
    SocialMediaTool,
    SOCIAL_POST_SCHEMA,
    SOCIAL_READ_SCHEMA,
    SOCIAL_REPLY_SCHEMA
)
from tools.physical_control import (
    PhysicalControlTool,
    PHYSICAL_MOVE_MOUSE_SCHEMA,
    PHYSICAL_CLICK_MOUSE_SCHEMA,
    PHYSICAL_TYPE_KEYBOARD_SCHEMA,
    PHYSICAL_PRESS_KEY_SCHEMA,
    PHYSICAL_HOTKEY_SCHEMA,
    PHYSICAL_OPEN_CHROME_SCHEMA,
    PHYSICAL_WHATSAPP_CALL_SCHEMA
)
from tools.whatsapp_operator import (
    WhatsAppOperator,
    WHATSAPP_SHOW_QR_SCHEMA,
    WHATSAPP_CHECK_MESSAGES_SCHEMA,
    WHATSAPP_READ_CHAT_SCHEMA
)
from memory.context_window import ContextWindow
from memory.vector_store import VectorStore
from core.consciousness import Consciousness
from core.autonomy import AutonomyEngine
from core.swarm import SwarmManager, DELEGATE_TASK_SCHEMA

logger = logging.getLogger(__name__)

class Brain:
    """
    The main orchestrator. It manages the agent swarm, instantiates tools,
    and runs the cognitive ReAct loop: Thinking -> Acting -> Observing.
    Now with autonomous self-learning and PC control.
    """
    
    TOOL_CATALOG = {
        "system_run_command": SYSTEM_TOOL_SCHEMA,
        "system_read_file": SYSTEM_READ_FILE_SCHEMA,
        "system_write_file": SYSTEM_WRITE_FILE_SCHEMA,
        "system_list_directory": SYSTEM_LIST_DIR_SCHEMA,
        "system_patch_file": SYSTEM_PATCH_FILE_SCHEMA,
        "browser_act": BROWSER_TOOL_SCHEMA,
        "web_search": WEB_SEARCH_SCHEMA,
        "run_python": PYTHON_REPL_SCHEMA,
        "self_reflect": SELF_REFLECT_SCHEMA,
        "recall_knowledge": RECALL_KNOWLEDGE_SCHEMA,
        "study_url": STUDY_URL_SCHEMA,
        "delegate_task": DELEGATE_TASK_SCHEMA,
        "take_screenshot": SCREENSHOT_SCHEMA,
        "get_clipboard": GET_CLIPBOARD_SCHEMA,
        "set_clipboard": SET_CLIPBOARD_SCHEMA,
        "list_processes": LIST_PROCESSES_SCHEMA,
        "kill_process": KILL_PROCESS_SCHEMA,
        "get_disk_usage": DISK_USAGE_SCHEMA,
        "open_application": OPEN_APP_SCHEMA,
        "get_system_stats": SYSTEM_STATS_SCHEMA,
        "text_to_speech": TEXT_TO_SPEECH_SCHEMA,
        "speech_to_text": SPEECH_TO_TEXT_SCHEMA,
        "list_tts_voices": LIST_TTS_VOICES_SCHEMA,
        "web_fetch": WEB_FETCH_SCHEMA,
        "analyze_image": IMAGE_ANALYSIS_SCHEMA,
        "cron_add": CRON_ADD_SCHEMA,
        "cron_list": CRON_LIST_SCHEMA,
        "cron_remove": CRON_REMOVE_SCHEMA,
        "send_message": SEND_MESSAGE_SCHEMA,
        "social_post": SOCIAL_POST_SCHEMA,
        "social_read": SOCIAL_READ_SCHEMA,
        "social_reply": SOCIAL_REPLY_SCHEMA,
        "physical_move_mouse": PHYSICAL_MOVE_MOUSE_SCHEMA,
        "physical_click_mouse": PHYSICAL_CLICK_MOUSE_SCHEMA,
        "physical_type_keyboard": PHYSICAL_TYPE_KEYBOARD_SCHEMA,
        "physical_press_key": PHYSICAL_PRESS_KEY_SCHEMA,
        "physical_hotkey": PHYSICAL_HOTKEY_SCHEMA,
        "physical_open_chrome": PHYSICAL_OPEN_CHROME_SCHEMA,
        "physical_whatsapp_call": PHYSICAL_WHATSAPP_CALL_SCHEMA,
        "whatsapp_show_qr": WHATSAPP_SHOW_QR_SCHEMA,
        "whatsapp_check_messages": WHATSAPP_CHECK_MESSAGES_SCHEMA,
        "whatsapp_read_chat": WHATSAPP_READ_CHAT_SCHEMA
    }
    
    def __init__(self):
        self.router = LLMRouter()
        self.state_manager = StateManager()
        
        # Initialize memory and tools
        self.context = ContextWindow(max_tokens=4000)
        self.long_term_memory = VectorStore()
        self.browser_engine = BrowserTool()
        
        # Initialize self-learning engine
        self.self_learner = SelfLearnerTool(
            memory=self.long_term_memory,
            llm_router=self.router
        )
        
        # Initialize voice engine
        self.voice_engine = VoiceEngine()
        
        # Initialize consciousness (self-awareness)
        self.consciousness = Consciousness()
        
        # Initialize Swarm Manager
        self.swarm_manager = SwarmManager(self)
        
        # Initialize default main agent — system prompt will be set after tools are registered
        self.main_agent = AgentBase(
            name="openApex",
            role_description="(initializing...)",
            router=self.router
        )
        
        # Register available tools
        self._register_default_tools()
        
        # NOW inject the consciousness-driven system prompt (after tools are registered)
        conscious_prompt = self.consciousness.get_self_model(self.main_agent.tools)
        conscious_prompt += "\n\nCRITICAL GUIDELINES FOR TOOL USAGE:\n"
        conscious_prompt += "1. You have access to tools. You MUST use them if you need external information or need to affect the system.\n"
        conscious_prompt += "2. When calling a tool, you MUST output a valid JSON tool call according to the provided schema.\n"
        conscious_prompt += "3. If asked to search the web, USE the web_search tool.\n"
        conscious_prompt += "4. Think step-by-step before acting.\n"
        self.main_agent.conversation_history[0] = {"role": "system", "content": conscious_prompt}
        
    def _register_default_tools(self):
        """
        Registers ONLY the core survival tools to the Main Agent.
        This saves massive amounts of context tokens.
        All other tools are stored in TOOL_CATALOG and accessed via swarm delegation.
        """
        core_tools = [
            "system_run_command",
            "system_read_file",
            "system_list_directory",
            "system_patch_file",
            "web_search",
            "self_reflect",
            "recall_knowledge",
            "delegate_task",
            "run_python"
        ]
        
        for name in core_tools:
            if name in self.TOOL_CATALOG:
                self.main_agent.register_tool(self.TOOL_CATALOG[name])
        
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a requested tool locally based on the LLM's demand."""
        logger.info(f"Executing Tool: {tool_name} with args {arguments}")
        
        # ===== System Tools =====
        if tool_name == "system_run_command":
            cmd = arguments.get("command")
            if not cmd:
                return json.dumps({"error": "Missing 'command' argument"})
            return json.dumps(SystemTool.run_command(cmd))
            
        elif tool_name == "system_read_file":
            filepath = arguments.get("filepath")
            if not filepath: 
                return json.dumps({"error": "Missing 'filepath' argument"})
            return json.dumps(SystemTool.read_file(filepath))

        elif tool_name == "system_write_file":
            filepath = arguments.get("filepath")
            content = arguments.get("content")
            if not filepath or not content: 
                return json.dumps({"error": "Missing 'filepath' or 'content' argument"})
            return json.dumps(SystemTool.write_file(filepath, content))

        elif tool_name == "system_patch_file":
            filepath = arguments.get("filepath")
            old_str = arguments.get("old_string")
            new_str = arguments.get("new_string")
            if not all([filepath, old_str, new_str]):
                return json.dumps({"error": "Missing 'filepath', 'old_string', or 'new_string' argument"})
            return json.dumps(FilePatcherTool.patch_file(filepath, old_str, new_str))

        elif tool_name == "system_list_directory":
            path = arguments.get("path", ".")
            return json.dumps(SystemTool.list_directory(path))

        # ===== Browser & Web =====
        elif tool_name == "browser_act":
            action = arguments.get("action")
            url = arguments.get("url")
            selector = arguments.get("selector")
            if not action or not url:
                return json.dumps({"error": "Missing 'action' or 'url' argument for browser"})
            return json.dumps(self.browser_engine.execute_browser_action(action, url, selector))
            
        elif tool_name == "web_search":
            query = arguments.get("query")
            max_res = arguments.get("max_results", 5)
            if not query:
                return json.dumps({"error": "Missing 'query' argument for web search"})
            return json.dumps(WebSearchTool.search_web(query, max_res))
            
        # ===== Code Execution =====
        elif tool_name == "run_python":
            code = arguments.get("code")
            if not code:
                return json.dumps({"error": "Missing 'code' argument for python repl"})
            return json.dumps(PythonREPLTool.run_python(code))

        # ===== Self-Learning Tools =====
        elif tool_name == "self_reflect":
            task = arguments.get("task")
            result = arguments.get("result")
            if not task or not result:
                return json.dumps({"error": "Missing 'task' or 'result' argument"})
            return json.dumps(self.self_learner.reflect_on_task(task, result))

        elif tool_name == "recall_knowledge":
            query = arguments.get("query")
            n_results = arguments.get("n_results", 3)
            if not query:
                return json.dumps({"error": "Missing 'query' argument"})
            return json.dumps(self.self_learner.recall_similar(query, n_results))

        elif tool_name == "study_url":
            url = arguments.get("url")
            if not url:
                return json.dumps({"error": "Missing 'url' argument"})
            return json.dumps(self.self_learner.study_documentation(url))

        # ===== Swarm Manager Tools =====
        elif tool_name == "delegate_task":
            role_name = arguments.get("role_name")
            task_desc = arguments.get("task_description")
            allowed = arguments.get("allowed_tools")
            if not role_name or not task_desc:
                return json.dumps({"error": "Missing 'role_name' or 'task_description'"})
            # This spawns an agent and waits for it to return synchronously
            return json.dumps({"sub_agent_result": self.swarm_manager.delegate_task(role_name, task_desc, allowed)})

        # ===== PC Control Tools =====
        elif tool_name == "take_screenshot":
            filename = arguments.get("filename", "screenshot.png")
            return json.dumps(PCControlTool.take_screenshot(filename))

        elif tool_name == "get_clipboard":
            return json.dumps(PCControlTool.get_clipboard())

        elif tool_name == "set_clipboard":
            text = arguments.get("text")
            if not text:
                return json.dumps({"error": "Missing 'text' argument"})
            return json.dumps(PCControlTool.set_clipboard(text))

        elif tool_name == "list_processes":
            limit = arguments.get("limit", 20)
            return json.dumps(PCControlTool.list_processes(limit))

        elif tool_name == "kill_process":
            pid = arguments.get("pid")
            if pid is None:
                return json.dumps({"error": "Missing 'pid' argument"})
            return json.dumps(PCControlTool.kill_process(int(pid)))

        elif tool_name == "get_disk_usage":
            return json.dumps(PCControlTool.get_disk_usage())

        elif tool_name == "open_application":
            path = arguments.get("path")
            if not path:
                return json.dumps({"error": "Missing 'path' argument"})
            return json.dumps(PCControlTool.open_application(path))

        elif tool_name == "get_system_stats":
            return json.dumps(PCControlTool.get_system_stats())

        # ===== Voice Tools =====
        elif tool_name == "text_to_speech":
            text = arguments.get("text")
            if not text:
                return json.dumps({"error": "Missing 'text' argument"})
            language = arguments.get("language", "id")
            filename = arguments.get("filename")
            slow = arguments.get("slow", False)
            return json.dumps(self.voice_engine.text_to_speech(text, language=language, filename=filename, slow=slow))

        elif tool_name == "speech_to_text":
            audio_path = arguments.get("audio_path")
            if not audio_path:
                return json.dumps({"error": "Missing 'audio_path' argument"})
            language = arguments.get("language", "id")
            return json.dumps(self.voice_engine.speech_to_text(audio_path, language=language))

        elif tool_name == "list_tts_voices":
            lang_filter = arguments.get("language_filter")
            return json.dumps(self.voice_engine.list_voices(language_filter=lang_filter))

        # ===== OpenClaw-Inspired Tools =====
        elif tool_name == "web_fetch":
            url = arguments.get("url")
            if not url:
                return json.dumps({"error": "Missing 'url' argument"})
            mode = arguments.get("extract_mode", "text")
            max_chars = arguments.get("max_chars", 10000)
            return json.dumps(WebFetchTool.fetch(url, extract_mode=mode, max_chars=max_chars))

        elif tool_name == "analyze_image":
            image_path = arguments.get("image_path")
            if not image_path:
                return json.dumps({"error": "Missing 'image_path' argument"})
            prompt = arguments.get("prompt", "Describe this image in detail.")
            return json.dumps(ImageAnalysisTool.analyze_image(image_path, prompt=prompt, llm_router=self.router))

        elif tool_name == "cron_add":
            name = arguments.get("name")
            command = arguments.get("command")
            if not name or not command:
                return json.dumps({"error": "Missing 'name' or 'command'"})
            interval = arguments.get("interval_minutes", 60)
            return json.dumps(CronSchedulerTool.add_job(name, command, interval))

        elif tool_name == "cron_list":
            return json.dumps(CronSchedulerTool.list_jobs())

        elif tool_name == "cron_remove":
            job_id = arguments.get("job_id")
            if not job_id:
                return json.dumps({"error": "Missing 'job_id'"})
            return json.dumps(CronSchedulerTool.remove_job(job_id))

        # ===== WhatsApp Operator Tools =====
        elif tool_name == "whatsapp_show_qr":
            return json.dumps(WhatsAppOperator.show_qr())
        elif tool_name == "whatsapp_check_messages":
            return json.dumps(WhatsAppOperator.check_new_messages())
        elif tool_name == "whatsapp_read_chat":
            contact = arguments.get("contact_name")
            if not contact:
                return json.dumps({"error": "Missing 'contact_name'"})
            return json.dumps(WhatsAppOperator.read_chat(contact))
        elif tool_name == "physical_whatsapp_call":
            contact = arguments.get("contact_name")
            if not contact:
                return json.dumps({"error": "Missing 'contact_name'"})
            return json.dumps(PhysicalControlTool.whatsapp_initiate_call(contact))

        elif tool_name == "send_message":
            platform = arguments.get("platform", "telegram")
            chat_id = arguments.get("chat_id")
            text = arguments.get("text")
            msg_type = arguments.get("type", "text")
            file_path = arguments.get("file_path")
            if not chat_id or not text:
                return json.dumps({"error": "Missing 'chat_id' or 'text'"})
            if platform == "telegram":
                if msg_type == "voice" and file_path:
                    return json.dumps(MessageTool.send_telegram_voice(chat_id, file_path))
                elif msg_type == "photo" and file_path:
                    return json.dumps(MessageTool.send_telegram_photo(chat_id, file_path, caption=text))
                else:
                    return json.dumps(MessageTool.send_telegram(chat_id, text))
            elif platform == "whatsapp":
                return json.dumps(MessageTool.send_whatsapp(chat_id, text))
            return json.dumps({"error": f"Unsupported platform: {platform}"})

        # ===== Social Media Tools =====
        elif tool_name == "social_post":
            platform = arguments.get("platform")
            text = arguments.get("text")
            if not platform or not text:
                return json.dumps({"error": "Missing 'platform' or 'text'"})
            if platform == "twitter":
                return json.dumps(SocialMediaTool.twitter_post(text))
            elif platform == "reddit":
                subreddit = arguments.get("subreddit", "test")
                title = arguments.get("title", text[:100])
                return json.dumps(SocialMediaTool.reddit_post(subreddit, title, text))
            return json.dumps({"error": f"Unknown social platform: {platform}"})

        elif tool_name == "social_read":
            platform = arguments.get("platform")
            query = arguments.get("query")
            limit = arguments.get("limit", 5)
            if not platform or not query:
                return json.dumps({"error": "Missing 'platform' or 'query'"})
            if platform == "twitter":
                return json.dumps(SocialMediaTool.twitter_search(query, limit))
            elif platform == "reddit":
                return json.dumps(SocialMediaTool.reddit_read(query, limit))
            return json.dumps({"error": f"Unknown social platform: {platform}"})

        elif tool_name == "social_reply":
            platform = arguments.get("platform")
            post_id = arguments.get("post_id")
            text = arguments.get("text")
            if not all([platform, post_id, text]):
                return json.dumps({"error": "Missing 'platform', 'post_id', or 'text'"})
            if platform == "twitter":
                return json.dumps(SocialMediaTool.twitter_reply(post_id, text))
            elif platform == "reddit":
                return json.dumps(SocialMediaTool.reddit_comment(post_id, text))
            return json.dumps({"error": f"Unknown social platform: {platform}"})
            
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def solve(self, user_request: str):
        """
        The main cognitive engine loop (Plan -> Execute -> Reflect).
        Now includes pre-task knowledge recall and post-task self-reflection.
        """
        logger.info(f"Starting resolution for task: {user_request}")
        
        # Pre-task: Recall similar past experiences
        recalled = self.self_learner.recall_similar(user_request)
        context_hint = ""
        if recalled.get("status") == "success":
            memories = recalled.get("relevant_memories", [])
            if memories:
                context_hint = "\n\n[Past Experience]: " + memories[0].get("memory", "")[:300]
                logger.info(f"Pre-task recall found {len(memories)} relevant memories.")
        
        self.state_manager.set_state(StateManager.STATE_PLANNING)
        self.state_manager.task_queue.append(user_request)

        user_input_to_agent = f"Current objective: {user_request}{context_hint}"

        # Loop until tasks are done or circuit breaker hits
        while self.state_manager.task_queue:
            if not self.state_manager.increment_iteration():
                logger.error("Brain loop aborted due to infinite iteration guard.")
                break

            current_task = self.state_manager.task_queue[-1]
            
            # 1. Action/Reasoning Step
            response = self.main_agent.run_cycle(user_input_to_agent, force_reasoning=True)
            
            # Clear user input for future tool-result iterations in the same task
            user_input_to_agent = None
            
            if response["status"] == "failed":
                logger.error(f"Agent cycle failed: {response['error']}")
                self.state_manager.set_state(StateManager.STATE_ERROR)
                break
                
            # 2. Tool Execution Step (if requested)
            if response["status"] == "tool_requested":
                self.state_manager.set_state(StateManager.STATE_EXECUTING)
                
                for tool_call in response["tool_calls"]:
                    func_details = tool_call.get("function", {})
                    name = func_details.get("name")
                    
                    # Track tool usage in consciousness
                    self.consciousness.on_tool_used(name)
                    
                    try:
                        args = json.loads(func_details.get("arguments", "{}"))
                        observation = self._execute_tool(name, args)
                        self.main_agent.add_message("tool", content=observation, tool_call_id=tool_call.get("id"), name=name)
                        
                    except json.JSONDecodeError:
                        self.main_agent.add_message("tool", content="Error: Failed to parse tool arguments as JSON.", tool_call_id=tool_call.get("id"), name=name)
                        
                continue
            
            # 3. Finalization Step
            elif response["status"] == "success":
                final_answer = response.get('response', '')
                print(f"\n[openApex]: {final_answer}\n")
                
                # Save to long term memory
                self.long_term_memory.store_episode(current_task, final_answer)
                
                # Post-task: Auto-reflect on what was learned
                self.self_learner.reflect_on_task(current_task, final_answer)
                
                # Update consciousness
                self.consciousness.on_task_complete(current_task)
                
                logger.info("Task completed, stored, and reflected in memory.")
                self.state_manager.task_queue.pop()
                self.state_manager.set_state(StateManager.STATE_VERIFYING)
                
        self.state_manager.set_state(StateManager.STATE_IDLE)
        logger.info("Brain has finished processing all tasks.")
