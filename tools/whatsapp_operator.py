import os
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# Constants
PROFILE_DIR = r"C:\Users\Administrator\openApex_whatsapp_profile"
WHATSAPP_URL = "https://web.whatsapp.com"

class WhatsAppOperator:
    """
    Advanced WhatsApp Operator using Playwright for persistence and listening.
    """

    @staticmethod
    def show_qr(timeout_sec: int = 30) -> Dict[str, Any]:
        """
        Opens WhatsApp Web in a persistent profile and takes a screenshot of the QR code.
        Returns the path to the screenshot so it can be sent to Telegram.
        """
        try:
            with sync_playwright() as p:
                logger.info(f"Launching persistent context at {PROFILE_DIR}...")
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=True, # Try headless first for background compatibility
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = browser.new_page()
                logger.info(f"Navigating to {WHATSAPP_URL}...")
                page.goto(WHATSAPP_URL, wait_until="networkidle", timeout=60000)
                
                logger.info("Waiting for WhatsApp Web to load elements...")
                # Check if we are already logged in (look for search bar or side pane)
                try:
                    page.wait_for_selector('div[contenteditable="true"], #side', timeout=15000)
                    browser.close()
                    return {"status": "success", "message": "Already logged in!", "logged_in": True}
                except Exception as e:
                    logger.info(f"Not logged in or load slow: {e}. Attempting QR capture.")
                    # If not logged in, take a screenshot of the QR code area
                    qr_path = os.path.join(os.getcwd(), "whatsapp_qr.png")
                    # WhatsApp QR is often in a canvas or a div with role=img
                    try:
                        page.wait_for_selector('canvas', timeout=30000)
                        page.screenshot(path=qr_path)
                        logger.info(f"QR Code captured at {qr_path}")
                        browser.close()
                        return {
                            "status": "success", 
                            "message": "QR Code captured. Please scan it.", 
                            "qr_path": qr_path,
                            "logged_in": False
                        }
                    except Exception as qr_err:
                        logger.error(f"Failed to find QR canvas: {qr_err}")
                        browser.close()
                        return {"status": "error", "message": f"Could not find QR Code on page: {qr_err}"}
        except Exception as e:
            logger.error(f"WhatsApp QR capture failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def check_new_messages() -> Dict[str, Any]:
        """
        Scans the chat list for unread message badges.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=True, # Background check
                )
                page = browser.new_page()
                page.goto(WHATSAPP_URL)
                
                # Wait for chat list to load
                page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
                
                # Look for unread badges (aria-label text containing 'pesan baru' or 'unread')
                # This is a bit brittle as it depends on language/UI updates
                unread_chats = page.query_selector_all('span[aria-label*="pesan tidak terbaca"], span[aria-label*="unread message"]')
                
                results = []
                for badge in unread_chats:
                    # Navigate up to find the contact name
                    parent = badge.query_selector('xpath=ancestor::div[@role="row"]')
                    if parent:
                        name_elem = parent.query_selector('span[title]')
                        if name_elem:
                            name = name_elem.get_attribute("title")
                            results.append({"contact": name})
                
                browser.close()
                return {"status": "success", "unread_count": len(results), "unread_chats": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def read_chat(contact_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Opens a specific chat and reads the last few messages.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=True,
                )
                page = browser.new_page()
                page.goto(WHATSAPP_URL)
                
                # Search for contact
                search_box = page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
                search_box.fill(contact_name)
                page.keyboard.press("Enter")
                time.sleep(2)
                
                # Extract message bubbles
                # Standard selector for incoming/outgoing bubbles
                bubbles = page.query_selector_all('div.message-in, div.message-out')
                messages = []
                for bubble in bubbles[-limit:]:
                    text_elem = bubble.query_selector('span.copyable-text')
                    if text_elem:
                        messages.append(text_elem.inner_text())
                
                browser.close()
                return {"status": "success", "contact": contact_name, "messages": messages}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Schemas for Brain
WHATSAPP_SHOW_QR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "whatsapp_show_qr",
        "description": "Opens WhatsApp Web to either confirm existing login or capture a QR code for the user to scan."
    }
}

WHATSAPP_CHECK_MESSAGES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "whatsapp_check_messages",
        "description": "Checks for unread messages on WhatsApp Web asynchronously."
    }
}

WHATSAPP_READ_CHAT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "whatsapp_read_chat",
        "description": "Reads the recent history of a specific WhatsApp chat.",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string", "description": "The name of the contact as it appears in your WhatsApp list."}
            },
            "required": ["contact_name"]
        }
    }
}
