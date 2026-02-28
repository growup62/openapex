import os
import time
import subprocess
import logging
from typing import Dict, Any

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = True
    # Add a slight pause after every PyAutoGUI call
    pyautogui.PAUSE = 0.5 
except ImportError:
    PYAUTOGUI_AVAILABLE = False

logger = logging.getLogger(__name__)

class PhysicalControlTool:
    """
    Tools that allow openApex to physically control the host machine,
    enabling Real-World GUI Interaction.
    """
    
    @staticmethod
    def move_mouse(x: int, y: int) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui is not installed."}
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            # Return current position to verify
            curr_x, curr_y = pyautogui.position()
            return {"success": True, "position": {"x": curr_x, "y": curr_y}}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def click_mouse(button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui is not installed."}
        try:
            pyautogui.click(button=button, clicks=clicks)
            return {"success": True, "action": f"clicked {button} {clicks} times"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def type_keyboard(text: str, interval: float = 0.05) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui is not installed."}
        try:
            # interval adds a slight delay between keystrokes to mimic human typing
            pyautogui.write(text, interval=interval)
            return {"success": True, "text_typed": text}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def press_key(key: str) -> Dict[str, Any]:
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui is not installed."}
        try:
            pyautogui.press(key)
            return {"success": True, "key_pressed": key}
        except Exception as e:
            return {"error": str(e)}
            
    @staticmethod
    def hotkey(*keys) -> Dict[str, Any]:
         if not PYAUTOGUI_AVAILABLE:
             return {"error": "pyautogui is not installed."}
         try:
             pyautogui.hotkey(*keys)
             return {"success": True, "keys_pressed": list(keys)}
         except Exception as e:
             return {"error": str(e)}

    @staticmethod
    def open_chrome(url: str = "https://www.google.com") -> Dict[str, Any]:
        """
        Opens a real, visible Google Chrome window. 
        """
        try:
            # Common Windows Chrome paths
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            executable_path = None
            for path in chrome_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    executable_path = expanded_path
                    break
                    
            if executable_path:
                # Open as a new window
                subprocess.Popen([executable_path, "--new-window", url])
                time.sleep(2) # Give it time to open
                return {"success": True, "message": f"Opened real Chrome at {url}"}
            else:
                # Fallback to default OS browser handler
                import webbrowser
                webbrowser.open_new(url)
                time.sleep(2)
                return {"success": True, "message": f"Opened default browser at {url} (Chrome executable not found)"}
                
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def whatsapp_initiate_call(contact_name: str) -> Dict[str, Any]:
        """
        Initiates a WhatsApp voice call by searching for a contact and clicking the call icon.
        Requires WhatsApp Web to be open and the search bar to be accessible.
        """
        if not PYAUTOGUI_AVAILABLE:
            return {"error": "pyautogui is not installed."}
        try:
            # Focus on browser
            pyautogui.hotkey('alt', 'tab') 
            time.sleep(1)
            pyautogui.press('esc') 
            time.sleep(0.5)
            # Click search (rough estimate top left)
            pyautogui.click(200, 150) 
            time.sleep(0.5)
            pyautogui.write(contact_name, interval=0.1)
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(2)
            
            return {
                "success": True, 
                "message": f"Navigated to {contact_name} chat. If call icon is visible, I can attempt to click it if given coordinates.",
                "next_step": "TAKE_SCREENSHOT"
            }
        except Exception as e:
            return {"error": str(e)}

# Reusable Schemas for Brain
PHYSICAL_MOVE_MOUSE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_move_mouse",
        "description": "Moves the physical physical mouse cursor to the specified X and Y coordinates on the screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"}
            },
            "required": ["x", "y"]
        }
    }
}

PHYSICAL_CLICK_MOUSE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_click_mouse",
        "description": "Performs a physical mouse click at the current cursor location.",
        "parameters": {
            "type": "object",
            "properties": {
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "clicks": {"type": "integer", "default": 1}
            }
        }
    }
}

PHYSICAL_TYPE_KEYBOARD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_type_keyboard",
        "description": "Types a string of text using the physical keyboard. Mimics human keystrokes.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    }
}

PHYSICAL_PRESS_KEY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_press_key",
        "description": "Presses a single physical key (e.g. 'enter', 'esc', 'tab', 'win'). For shortcuts use hotkey.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "The key name (e.g., 'enter', 'space', 'tab', 'a', '1')"}
            },
            "required": ["key"]
        }
    }
}

PHYSICAL_HOTKEY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_hotkey",
        "description": "Presses a combination of keys together (e.g. ['ctrl', 'c'] or ['alt', 'tab']).",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {"type": "array", "items": {"type": "string"}, "description": "List of key names to press together."}
            },
            "required": ["keys"]
        }
    }
}

PHYSICAL_OPEN_CHROME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_open_chrome",
        "description": "Opens a real, visible Google Chrome window on the host computer. The AI can then use taking screenshots and clicking to interact with it.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to open."}
            }
        }
    }
}

PHYSICAL_WHATSAPP_CALL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "physical_whatsapp_call",
        "description": "Attempts to initiate a WhatsApp voice call to a specific contact using GUI automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string", "description": "The name of the contact as it appears in WhatsApp."}
            },
            "required": ["contact_name"]
        }
    }
}
