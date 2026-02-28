import logging
import os
import platform
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


class PCControlTool:
    """
    Advanced PC control tools for openApex.
    Provides screenshot, clipboard, process management, and disk info.
    """

    @staticmethod
    def take_screenshot(filename: str = "screenshot.png") -> Dict[str, Any]:
        """Takes a screenshot of the current screen."""
        try:
            from PIL import ImageGrab
            save_path = os.path.join(os.getcwd(), "downloads", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img = ImageGrab.grab()
            img.save(save_path)
            logger.info(f"Screenshot saved to {save_path}")
            return {"status": "success", "path": save_path}
        except ImportError:
            return {"error": "Pillow not installed. Run: pip install Pillow"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_clipboard() -> Dict[str, Any]:
        """Reads the current clipboard content."""
        if not CLIPBOARD_AVAILABLE:
            return {"error": "pyperclip not installed. Run: pip install pyperclip"}
        try:
            content = pyperclip.paste()
            return {"status": "success", "content": content[:5000]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def set_clipboard(text: str) -> Dict[str, Any]:
        """Copies text to the clipboard."""
        if not CLIPBOARD_AVAILABLE:
            return {"error": "pyperclip not installed. Run: pip install pyperclip"}
        try:
            pyperclip.copy(text)
            return {"status": "success", "message": "Text copied to clipboard."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def list_processes(limit: int = 20) -> Dict[str, Any]:
        """Lists running processes sorted by memory usage."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                procs.append(proc.info)
            # Sort by memory usage
            procs.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
            return {"status": "success", "processes": procs[:limit]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def kill_process(pid: int) -> Dict[str, Any]:
        """Terminates a process by PID."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return {"status": "success", "message": f"Process {pid} ({proc.name()}) terminated."}
        except psutil.NoSuchProcess:
            return {"error": f"No process found with PID {pid}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_disk_usage() -> Dict[str, Any]:
        """Returns disk usage information for all drives."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            drives = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drives.append({
                        "drive": partition.device,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": usage.percent
                    })
                except PermissionError:
                    continue
            return {"status": "success", "drives": drives}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def open_application(path: str) -> Dict[str, Any]:
        """Opens an application or file."""
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['open' if platform.system() == 'Darwin' else 'xdg-open', path])
            return {"status": "success", "message": f"Opened: {path}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Returns comprehensive system stats (CPU, RAM, uptime)."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            import datetime
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            return {
                "status": "success",
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "cpu_cores": psutil.cpu_count(),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "ram_percent": psutil.virtual_memory().percent,
                "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                "os": platform.system(),
                "os_version": platform.version()
            }
        except Exception as e:
            return {"error": str(e)}


# JSON Schemas for LLM Tool Registration

SCREENSHOT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "take_screenshot",
        "description": "Take a screenshot of the current screen and save it as an image file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename for the screenshot (default: screenshot.png).",
                    "default": "screenshot.png"
                }
            }
        }
    }
}

GET_CLIPBOARD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_clipboard",
        "description": "Read the current text content from the system clipboard.",
        "parameters": {"type": "object", "properties": {}}
    }
}

SET_CLIPBOARD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "set_clipboard",
        "description": "Copy text to the system clipboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to copy to clipboard."
                }
            },
            "required": ["text"]
        }
    }
}

LIST_PROCESSES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_processes",
        "description": "List running processes on the PC sorted by memory usage.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of processes to return (default: 20).",
                    "default": 20
                }
            }
        }
    }
}

KILL_PROCESS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "kill_process",
        "description": "Terminate/kill a running process by its PID.",
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "The Process ID to terminate."
                }
            },
            "required": ["pid"]
        }
    }
}

DISK_USAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_disk_usage",
        "description": "Get disk usage information for all drives on the PC.",
        "parameters": {"type": "object", "properties": {}}
    }
}

OPEN_APP_SCHEMA = {
    "type": "function",
    "function": {
        "name": "open_application",
        "description": "Open an application, file, or URL on the local PC.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the application or file to open."
                }
            },
            "required": ["path"]
        }
    }
}

SYSTEM_STATS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_system_stats",
        "description": "Get comprehensive system statistics: CPU usage, RAM usage, disk space, uptime, and OS info.",
        "parameters": {"type": "object", "properties": {}}
    }
}
