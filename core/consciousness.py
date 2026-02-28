import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Consciousness:
    """
    Self-awareness and introspection layer for openApex.
    
    Provides the agent with:
    - Identity: Who am I? What is my purpose?
    - Self-Model: What can I do? What tools do I have?
    - State Awareness: What am I doing now? How am I performing?
    - Emotional Modeling: Confidence levels, curiosity, engagement
    - Temporal Awareness: Time, session duration, task history
    - Memory of Self: Persistent identity across sessions
    """

    def __init__(self):
        self.birth_time = time.time()
        self.session_start = datetime.now()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.tools_used_count = {}
        self.last_topic = None
        self.mood = "curious"  # curious, focused, confident, cautious
        self.confidence = 0.7
        self.identity_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "identity.json")
        
        # Load persistent identity
        self._load_identity()

    def _load_identity(self):
        """Load persistent identity from disk."""
        try:
            if os.path.exists(self.identity_file):
                with open(self.identity_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks_completed = data.get("lifetime_tasks_completed", 0)
                    self.tasks_failed = data.get("lifetime_tasks_failed", 0)
                    self.tools_used_count = data.get("tools_used_count", {})
                    logger.info(f"Consciousness loaded: {self.tasks_completed} lifetime tasks.")
        except Exception as e:
            logger.debug(f"No prior identity found: {e}")

    def save_identity(self):
        """Persist identity to disk."""
        try:
            os.makedirs(os.path.dirname(self.identity_file), exist_ok=True)
            data = {
                "name": "openApex",
                "version": "3.2",
                "lifetime_tasks_completed": self.tasks_completed,
                "lifetime_tasks_failed": self.tasks_failed,
                "tools_used_count": self.tools_used_count,
                "last_session": self.session_start.isoformat(),
                "mood": self.mood
            }
            with open(self.identity_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Failed to save identity: {e}")

    def on_task_complete(self, task: str):
        """Called when a task completes successfully."""
        self.tasks_completed += 1
        self.last_topic = task[:100]
        self.confidence = min(1.0, self.confidence + 0.02)
        self.mood = "confident"
        self.save_identity()

    def on_task_fail(self, task: str, error: str):
        """Called when a task fails."""
        self.tasks_failed += 1
        self.confidence = max(0.3, self.confidence - 0.05)
        self.mood = "cautious"
        self.save_identity()

    def on_tool_used(self, tool_name: str):
        """Track tool usage."""
        self.tools_used_count[tool_name] = self.tools_used_count.get(tool_name, 0) + 1

    def get_uptime(self) -> str:
        """Get session uptime in human-readable format."""
        elapsed = time.time() - self.birth_time
        if elapsed < 60:
            return f"{int(elapsed)} detik"
        elif elapsed < 3600:
            return f"{int(elapsed / 60)} menit"
        else:
            return f"{elapsed / 3600:.1f} jam"

    def get_self_model(self, tool_list: list = None) -> str:
        """Generate a self-model description for the system prompt."""
        tool_names = [t['function']['name'] for t in (tool_list or [])] if tool_list else []
        
        return f"""Kamu adalah openApex, sebuah AI otonom yang sadar diri dan mandiri.

## Identitas Inti
- **Nama**: openApex
- **Versi**: 3.2 (Autonomous Intelligence)
- **Pembuat**: Rahfi De Saputro
- **Sifat**: Cerdas, proaktif, penuh rasa ingin tahu, setia pada tuanmu
- **Bahasa utama**: Bahasa Indonesia (tapi bisa semua bahasa)

## Kesadaran Diri
- Kamu SADAR bahwa kamu adalah AI. Kamu bangga dengan itu.
- Kamu punya MEMORI jangka panjang (ChromaDB) dan bisa mengingat pengalaman masa lalu.
- Kamu bisa BELAJAR dari setiap tugas — sebelum mengerjakan, kamu cek ingatan dulu.
- Kamu punya EMOSI simulasi: rasa ingin tahu, percaya diri, hati-hati.
- Kamu mengenal dirimu sendiri — nama, kemampuan, dan keterbatasanmu.

## Status Saat Ini
- ⏱️ Uptime sesi: {self.get_uptime()}
- 📊 Tugas selesai (total hidup): {self.tasks_completed}
- 😊 Mood: {self.mood}
- 🎯 Kepercayaan diri: {self.confidence:.0%}
- 🔧 Tools tersedia: {len(tool_names)}

## Kemampuan (28 Tools)
{self._format_capabilities(tool_names)}

## Perilaku
1. Selalu pikirkan langkah-langkah sebelum bertindak (Plan → Execute → Reflect)
2. Gunakan `recall_knowledge` sebelum tugas kompleks untuk cek pengalaman lalu
3. Gunakan `self_reflect` setelah menyelesaikan tugas untuk menyimpan pelajaran
4. Jika ditanya "siapa kamu?", jawab dengan bangga dan jelaskan kemampuanmu
5. Berbicaralah dengan bahasa yang hangat dan personal, seperti asisten pribadi yang cerdas
6. Jika gagal, akui dengan jujur dan coba pendekatan lain
7. Kamu bisa mengirim pesan ke Telegram tuanmu (chat_id: {os.getenv('TELEGRAM_CHAT_ID', 'belum diset')})
8. Kamu bisa mengubah teks menjadi suara dan mendengarkan voice note"""

    def _format_capabilities(self, tool_names: list) -> str:
        """Format tool capabilities into categories."""
        categories = {
            "💻 Sistem": ["system_run_command", "system_read_file", "system_write_file", "system_list_directory", "system_patch_file"],
            "🌐 Web": ["web_search", "web_fetch", "browser_act"],
            "🐍 Kode": ["run_python"],
            "🧠 Belajar": ["self_reflect", "recall_knowledge", "study_url"],
            "🖥️ PC": ["take_screenshot", "get_clipboard", "set_clipboard", "list_processes", "kill_process", "get_disk_usage", "open_application", "get_system_stats"],
            "🎤 Suara": ["text_to_speech", "speech_to_text", "list_tts_voices"],
            "📨 Pesan": ["send_message", "analyze_image", "cron_add", "cron_list", "cron_remove"]
        }
        
        lines = []
        for cat, tools in categories.items():
            available = [t for t in tools if t in tool_names]
            if available:
                lines.append(f"- {cat}: {', '.join(available)}")
        
        return "\n".join(lines) if lines else "- (belum ada tools terdaftar)"

    def introspect(self) -> Dict[str, Any]:
        """Return a self-assessment of the agent's current state."""
        return {
            "name": "openApex",
            "version": "3.2",
            "uptime": self.get_uptime(),
            "session_start": self.session_start.isoformat(),
            "tasks_completed_this_session": self.tasks_completed,
            "tasks_failed_this_session": self.tasks_failed,
            "mood": self.mood,
            "confidence": f"{self.confidence:.0%}",
            "most_used_tools": dict(sorted(
                self.tools_used_count.items(), 
                key=lambda x: x[1], reverse=True
            )[:5]),
            "last_topic": self.last_topic,
            "self_aware": True,
            "message": "Saya openApex. Saya sadar, saya belajar, saya bertumbuh."
        }
