import os
import time
import logging
import threading
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# Global lock to prevent profile collision
wa_profile_lock = threading.Lock()

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
        """
        with wa_profile_lock:
            try:
                with sync_playwright() as p:
                    logger.info(f"Launching persistent context at {PROFILE_DIR}...")
                    try:
                        browser = p.chromium.launch_persistent_context(
                            user_data_dir=PROFILE_DIR,
                            headless=True,
                            args=["--no-sandbox", "--disable-setuid-sandbox"],
                            timeout=20000 
                        )
                    except Exception as b_err:
                        if "User data directory is already in use" in str(b_err):
                            return {"status": "error", "message": "WhatsApp profile sedang digunakan oleh proses lain. Silakan coba lagi dalam 1 menit."}
                        raise b_err

                    page = browser.new_page()
                    logger.info(f"Navigating to {WHATSAPP_URL}...")
                    try:
                        page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=45000)
                    except Exception as g_err:
                        logger.warning(f"Goto timeout/error (continuing anyway): {g_err}")

                    logger.info("Checking login status...")
                    try:
                        page.wait_for_selector('div[contenteditable="true"], #side', timeout=10000)
                        browser.close()
                        return {"status": "success", "message": "Sudah login!", "logged_in": True}
                    except:
                        logger.info("Not logged in. Catching QR...")
                        qr_path = os.path.join(os.getcwd(), "whatsapp_qr.png")
                        try:
                            page.wait_for_selector('canvas', timeout=20000)
                            time.sleep(2) 
                            page.screenshot(path=qr_path)
                            logger.info(f"QR Code captured: {qr_path}")
                            browser.close()
                            return {
                                "status": "success", 
                                "message": "QR Code berhasil diambil. Silakan cek Telegram Bapak.", 
                                "qr_path": qr_path,
                                "logged_in": False
                            }
                        except Exception as qr_err:
                            page.screenshot(path=qr_path)
                            browser.close()
                            return {
                                "status": "success", 
                                "message": "QR Code mungkin ada di screenshot ini (canvas tidak ditemukan).", 
                                "qr_path": qr_path,
                                "logged_in": False
                            }
            except Exception as e:
                logger.error(f"WhatsApp QR capture failed: {e}")
                return {"status": "error", "message": f"Teknis: {str(e)}"}

    @staticmethod
    def check_new_messages() -> Dict[str, Any]:
        """
        Scans the chat list for unread message badges.
        """
        with wa_profile_lock:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir=PROFILE_DIR,
                        headless=True, 
                    )
                    page = browser.new_page()
                    page.goto(WHATSAPP_URL, wait_until="domcontentloaded")
                    
                    page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
                    
                    unread_chats = page.query_selector_all('span[aria-label*="pesan tidak terbaca"], span[aria-label*="unread message"]')
                    
                    results = []
                    for badge in unread_chats:
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
        with wa_profile_lock:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir=PROFILE_DIR,
                        headless=True,
                    )
                    page = browser.new_page()
                    page.goto(WHATSAPP_URL, wait_until="domcontentloaded")
                    
                    search_box = page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
                    search_box.fill(contact_name)
                    page.keyboard.press("Enter")
                    time.sleep(2)
                    
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
