import logging
import os
import json
import re
import requests
import html
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebFetchTool:
    """
    Fetch and extract content from a URL.
    Inspired by OpenClaw's web_fetch tool.
    Converts HTML to clean text or markdown.
    """

    @staticmethod
    def fetch(url: str, extract_mode: str = "text", max_chars: int = 10000) -> Dict[str, Any]:
        """Fetch URL content and extract text."""
        if not url:
            return {"status": "error", "message": "No URL provided"}

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True, verify=False)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            # Handle non-HTML content
            if "json" in content_type:
                try:
                    data = response.json()
                    text = json.dumps(data, indent=2, ensure_ascii=False)[:max_chars]
                    return {"status": "success", "url": url, "content_type": "json", "text": text}
                except:
                    pass

            if "text/plain" in content_type:
                text = response.text[:max_chars]
                return {"status": "success", "url": url, "content_type": "text", "text": text}

            # HTML extraction
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script, style, nav, footer, header elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            if extract_mode == "markdown":
                text = _html_to_markdown(soup)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text[:max_chars]

            return {
                "status": "success",
                "url": url,
                "title": title,
                "content_type": "html",
                "extract_mode": extract_mode,
                "text": text,
                "char_count": len(text)
            }

        except requests.exceptions.Timeout:
            return {"status": "error", "message": f"Timeout fetching {url}"}
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": f"HTTP error: {e}"}
        except Exception as e:
            logger.error(f"web_fetch error: {e}")
            return {"status": "error", "message": str(e)}


def _html_to_markdown(soup) -> str:
    """Simple HTML to markdown converter."""
    lines = []

    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code", "blockquote", "a"]):
        tag = element.name
        text = element.get_text(strip=True)
        if not text:
            continue

        if tag == "h1":
            lines.append(f"\n# {text}\n")
        elif tag == "h2":
            lines.append(f"\n## {text}\n")
        elif tag == "h3":
            lines.append(f"\n### {text}\n")
        elif tag == "h4":
            lines.append(f"\n#### {text}\n")
        elif tag == "p":
            lines.append(f"{text}\n")
        elif tag == "li":
            lines.append(f"- {text}")
        elif tag in ("pre", "code"):
            lines.append(f"```\n{text}\n```")
        elif tag == "blockquote":
            lines.append(f"> {text}")
        elif tag == "a":
            href = element.get("href", "")
            if href and text:
                lines.append(f"[{text}]({href})")

    return "\n".join(lines)


class ImageAnalysisTool:
    """
    Analyze/describe images using vision-capable LLMs.
    Inspired by OpenClaw's image tool.
    Uses the LLM router for vision analysis.
    """

    @staticmethod
    def analyze_image(image_path: str, prompt: str = "Describe this image in detail.", llm_router=None) -> Dict[str, Any]:
        """Analyze a local image using a vision model."""
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}

        try:
            import base64

            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Detect MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            mime_type = mime_map.get(ext, "image/png")

            if llm_router:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}}
                        ]
                    }
                ]

                response = llm_router.generate_response(messages, task_type="reasoning")
                description = response.get("choices", [{}])[0].get("message", {}).get("content", "No description generated.")

                return {
                    "status": "success",
                    "image_path": image_path,
                    "description": description,
                    "prompt": prompt
                }
            else:
                return {"status": "error", "message": "No LLM router available for image analysis"}

        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {"status": "error", "message": str(e)}


class CronSchedulerTool:
    """
    Simple cron-like task scheduler for openApex.
    Inspired by OpenClaw's cron tool.
    Stores scheduled tasks and runs them at intervals.
    """

    _jobs = {}
    _job_counter = 0

    @classmethod
    def add_job(cls, name: str, command: str, interval_minutes: int = 60, enabled: bool = True) -> Dict[str, Any]:
        """Add a scheduled job."""
        cls._job_counter += 1
        job_id = f"job_{cls._job_counter}"

        cls._jobs[job_id] = {
            "id": job_id,
            "name": name,
            "command": command,
            "interval_minutes": interval_minutes,
            "enabled": enabled,
            "runs": 0,
            "last_run": None
        }

        logger.info(f"Cron job added: {name} (every {interval_minutes}min)")
        return {"status": "success", "job": cls._jobs[job_id]}

    @classmethod
    def list_jobs(cls) -> Dict[str, Any]:
        """List all scheduled jobs."""
        return {"status": "success", "jobs": list(cls._jobs.values()), "count": len(cls._jobs)}

    @classmethod
    def remove_job(cls, job_id: str) -> Dict[str, Any]:
        """Remove a scheduled job."""
        if job_id in cls._jobs:
            removed = cls._jobs.pop(job_id)
            return {"status": "success", "removed": removed["name"]}
        return {"status": "error", "message": f"Job {job_id} not found"}

    @classmethod
    def update_job(cls, job_id: str, enabled: Optional[bool] = None, interval_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Update a scheduled job."""
        if job_id not in cls._jobs:
            return {"status": "error", "message": f"Job {job_id} not found"}

        job = cls._jobs[job_id]
        if enabled is not None:
            job["enabled"] = enabled
        if interval_minutes is not None:
            job["interval_minutes"] = interval_minutes

        return {"status": "success", "job": job}


class MessageTool:
    """
    Enhanced messaging tool for openApex.
    Inspired by OpenClaw's message tool.
    Supports sending messages to Telegram and WhatsApp.
    """

    @staticmethod
    def send_telegram(chat_id: str, text: str, token: str = None) -> Dict[str, Any]:
        """Send a message to Telegram."""
        token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return {"status": "error", "message": "TELEGRAM_BOT_TOKEN not set"}

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return {"status": "success", "platform": "telegram", "message": "Sent successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_telegram_voice(chat_id: str, audio_path: str, token: str = None) -> Dict[str, Any]:
        """Send a voice message to Telegram."""
        token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return {"status": "error", "message": "TELEGRAM_BOT_TOKEN not set"}
        if not os.path.exists(audio_path):
            return {"status": "error", "message": f"Audio file not found: {audio_path}"}

        try:
            url = f"https://api.telegram.org/bot{token}/sendVoice"
            with open(audio_path, "rb") as audio:
                files = {"voice": audio}
                data = {"chat_id": chat_id}
                response = requests.post(url, data=data, files=files, timeout=15)
                response.raise_for_status()
            return {"status": "success", "platform": "telegram", "type": "voice"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_telegram_photo(chat_id: str, photo_path: str, caption: str = "", token: str = None) -> Dict[str, Any]:
        """Send a photo to Telegram."""
        token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return {"status": "error", "message": "TELEGRAM_BOT_TOKEN not set"}

        try:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(photo_path, "rb") as photo:
                files = {"photo": photo}
                data = {"chat_id": chat_id, "caption": caption}
                response = requests.post(url, data=data, files=files, timeout=15)
                response.raise_for_status()
            return {"status": "success", "platform": "telegram", "type": "photo"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def send_whatsapp(phone_no: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message using pywhatkit web automation.
        Requires user to be logged in to WhatsApp Web on Chrome.
        """
        if not phone_no:
            # Fallback to env default
            phone_no = os.getenv("WHATSAPP_TARGET_NUMBER")
            if not phone_no:
                return {"status": "error", "message": "Missing phone number and WHATSAPP_TARGET_NUMBER is not set in .env."}
        
        try:
            import pywhatkit
            logger.info(f"Opening WhatsApp Web to send message to {phone_no}...")
            # We use sendwhatmsg_instantly which opens a new tab, types, sends, and optionally closes it
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone_no, 
                message=message, 
                wait_time=15, 
                tab_close=True, 
                close_time=5
            )
            return {"status": "success", "platform": "whatsapp", "message": f"Message sent automagically via web UI to {phone_no}"}
        except Exception as e:
            logger.error(f"WhatsApp sending error: {e}")
            return {"status": "error", "message": str(e)}


# ===== JSON Schemas =====

WEB_FETCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch and extract text content from any URL. Converts HTML to clean text or markdown. Good for reading documentation, articles, API responses.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch"},
                "extract_mode": {"type": "string", "description": "'text' or 'markdown'. Default: 'text'"},
                "max_chars": {"type": "integer", "description": "Max characters to return. Default: 10000"}
            },
            "required": ["url"]
        }
    }
}

IMAGE_ANALYSIS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_image",
        "description": "Analyze and describe an image using AI vision. Provide a local file path to the image.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to the image file"},
                "prompt": {"type": "string", "description": "What to analyze. Default: 'Describe this image in detail.'"}
            },
            "required": ["image_path"]
        }
    }
}

CRON_ADD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "cron_add",
        "description": "Add a scheduled recurring task. The task will be executed at the specified interval.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the scheduled task"},
                "command": {"type": "string", "description": "Command or task description to execute"},
                "interval_minutes": {"type": "integer", "description": "Run interval in minutes. Default: 60"}
            },
            "required": ["name", "command"]
        }
    }
}

CRON_LIST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "cron_list",
        "description": "List all scheduled tasks (cron jobs).",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

CRON_REMOVE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "cron_remove",
        "description": "Remove a scheduled task by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID of the job to remove (e.g. 'job_1')"}
            },
            "required": ["job_id"]
        }
    }
}

SEND_MESSAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "send_message",
        "description": "Send a message to Telegram or WhatsApp. Can send text, voice, or photo messages.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "'telegram' or 'whatsapp'"},
                "chat_id": {"type": "string", "description": "Chat/user ID to send to"},
                "text": {"type": "string", "description": "Text message content"},
                "type": {"type": "string", "description": "'text', 'voice', or 'photo'. Default: 'text'"},
                "file_path": {"type": "string", "description": "Path to voice/photo file (required for voice/photo type)"}
            },
            "required": ["platform", "chat_id", "text"]
        }
    }
}
