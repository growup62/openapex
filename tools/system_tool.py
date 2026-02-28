import subprocess
import os
import platform
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemTool:
    """
    A tool that allows the AI to interact with the local operating system:
    - Running shell commands
    - Reading/Writing files
    - Checking environment info
    """
    
    @staticmethod
    def run_command(command: str) -> Dict[str, Any]:
        """Executes a shell command and returns the output/error."""
        logger.info(f"Executing system command: {command}")
        try:
            # shell=True is needed for Windows commands like 'dir'
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30 # Safety timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 30 seconds."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Returns basic OS and environment details."""
        return {
            "os": platform.system(),
            "version": platform.version(),
            "cwd": os.getcwd(),
            "python_version": platform.python_version()
        }

    @staticmethod
    def list_directory(path: str = ".") -> Dict[str, Any]:
        """Lists files in a given directory."""
        try:
            items = os.listdir(path)
            return {"items": items}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def read_file(filepath: str) -> Dict[str, Any]:
        """Reads content of a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content[:10000]} # cap length
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def write_file(filepath: str, content: str) -> Dict[str, Any]:
        """Writes content to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

# The JSON Schema that will be passed to the LLM Router
SYSTEM_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_run_command",
        "description": "Execute a command in the system terminal (Windows PowerShell/CMD). Use this to install packages, run scripts, or manage files.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command string to execute."
                }
            },
            "required": ["command"]
        }
    }
}

SYSTEM_READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_read_file",
        "description": "Read the text content of a file on the local system.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to read."
                }
            },
            "required": ["filepath"]
        }
    }
}

SYSTEM_WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_write_file",
        "description": "Write or overwrite text content to a file on the local system.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to write to."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write."
                }
            },
            "required": ["filepath", "content"]
        }
    }
}

SYSTEM_LIST_DIR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_list_directory",
        "description": "List the files and directories inside a given directory path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list. Defaults to the current directory '.'."
                }
            }
        }
    }
}
