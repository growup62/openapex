import logging
import json
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# To fully enable this, user requires: `pip install playwright` and `playwright install`
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Browser features disabled.")

class BrowserTool:
    """
    Empowers openApex to browse the web, take screenshots, 
    and extract DOM elements autonomously.
    """
    
    def __init__(self):
        self.download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
        
    def execute_browser_action(self, action: str, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a specific action via a headless browser.
        Options: 'extract_text', 'screenshot', 'get_html'
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright is not installed. Please run: pip install playwright && playwright install"}
            
        logger.info(f"Browser action '{action}' requested for URL: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(15000) # 15 seconds
                
                try:
                    page.goto(url)
                    
                    if action == "extract_text":
                        if selector:
                            content = page.locator(selector).inner_text()
                        else:
                            content = page.evaluate("document.body.innerText")
                        result = {"text": content[:5000]} # Cap length
                        
                    elif action == "screenshot":
                        filename = f"screenshot_{hash(url)}.png"
                        filepath = os.path.join(self.download_dir, filename)
                        page.screenshot(path=filepath, full_page=True)
                        result = {"file_path": filepath, "status": "saved"}
                        
                    elif action == "get_html":
                        if selector:
                            content = page.locator(selector).inner_html()
                        else:
                            content = page.content()
                        result = {"html": content[:10000]} # Cap length
                        
                    else:
                        result = {"error": f"Unknown action: {action}"}
                        
                except PlaywrightTimeout:
                    result = {"error": "Page load or element selection timed out."}
                except Exception as e:
                    result = {"error": str(e)}
                    
                browser.close()
                return result
                
        except Exception as e:
             logger.error(f"Browser framework critical failure: {e}")
             return {"error": str(e)}

# The JSON Schema for the Browser Tool
BROWSER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "browser_act",
        "description": "Utilizes a headless browser to visit a URL and extract text, HTML, or take a screenshot.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["extract_text", "screenshot", "get_html"],
                    "description": "The type of action to perform on the page."
                },
                "url": {
                    "type": "string",
                    "description": "The full HTTPS URL to visit."
                },
                "selector": {
                    "type": "string",
                    "description": "(Optional) CSS Selector to target a specific element on the page."
                }
            },
            "required": ["action", "url"]
        }
    }
}
