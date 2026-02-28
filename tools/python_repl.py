import logging
import sys
import io
import contextlib
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PythonREPLTool:
    """
    A sandbox that allows the AI to execute Python code snippets natively.
    Useful for heavy math, data processing, formatting, or custom logic tests.
    """
    
    @staticmethod
    def run_python(code: str) -> Dict[str, Any]:
        """
        Executes a python snippet and captures stdout and exceptions.
        Warning: In a real production system, this must run in a Docker container 
        or restricted PySandbox for safety. For this MVP, we run it directly.
        """
        logger.info("Executing Python code via REPL.")
        
        # Capture standard output (print statements from the AI's code)
        stdout_capture = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                # Using exec() to run the dynamic code block
                # Setting globals/locals to isolated dicts to prevent touching the main app space
                exec_globals = {}
                exec(code, exec_globals)
                
            output = stdout_capture.getvalue()
            if not output:
                output = "[Executed successfully with no stdout output]"
                
            return {
                "status": "success",
                "output": output
            }
                
        except Exception as e:
            return {
                "error": f"{type(e).__name__}: {str(e)}",
                "partial_output": stdout_capture.getvalue()
            }

# The JSON Schema for the Python REPL Tool
PYTHON_REPL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Execute a python code snippet in a local REPL environment and get the console output. Use this to do math, parsing, or testing logic. ALWAYS print() your final variables so you can see them in the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code snippet to execute. Must be valid unwrapped python code without markdown backticks."
                }
            },
            "required": ["code"]
        }
    }
}
