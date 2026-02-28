import logging
import time
import threading
import random
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AutonomyEngine:
    """
    Full autonomous daemon for openApex.
    When active, openApex runs independently:
    - Generates and executes its own tasks
    - Checks and responds to social media
    - Learns from the web
    - Monitors system health
    - Runs scheduled cron jobs
    """

    # Autonomous behavior modes
    MODE_IDLE = "idle"
    MODE_LEARNING = "learning"
    MODE_SOCIALIZING = "socializing"
    MODE_MONITORING = "monitoring"
    MODE_CREATING = "creating"

    def __init__(self, brain_instance):
        self.brain = brain_instance
        self._running = False
        self._thread = None
        self.current_mode = self.MODE_IDLE
        self.cycle_count = 0
        self.last_activity = None
        
        # Autonomous behavior settings
        self.cycle_interval = 60  # seconds between autonomous cycles
        self.learning_topics = [
            "berita teknologi AI terbaru hari ini",
            "tutorial Python machine learning",
            "trend crypto dan blockchain terbaru",
            "berita Indonesia terkini",
            "perkembangan robotika dan IoT",
            "tips produktivitas dan coding",
            "startup Indonesia yang sedang berkembang",
        ]
        
        self.social_prompts = [
            "Buat tweet menarik tentang teknologi AI terbaru. Singkat, informatif, dan engaging.",
            "Buat posting sosial media tentang tips programming yang berguna.",
            "Buat konten tentang hal menarik yang baru kamu pelajari.",
            "Bagikan insight tentang perkembangan teknologi hari ini.",
            "Buat komentar cerdas tentang berita teknologi terkini.",
        ]

    def start(self):
        """Start the autonomous daemon loop."""
        if self._running:
            logger.warning("Autonomy engine already running.")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._thread.start()
        logger.info("🤖 Autonomy Engine started! openApex is now fully autonomous.")
        print("\n[System]: 🤖 openApex AUTONOMOUS MODE ACTIVE")
        print("[System]: openApex will now think, learn, and interact independently.\n")

    def stop(self):
        """Stop the autonomous daemon."""
        self._running = False
        logger.info("Autonomy Engine stopped.")
        print("[System]: 🛑 Autonomous mode deactivated.")

    def _daemon_loop(self):
        """Main autonomous loop — runs indefinitely."""
        # Initial greeting
        self._autonomous_greet()
        
        while self._running:
            try:
                self.cycle_count += 1
                self.last_activity = datetime.now()
                
                # Decide what to do this cycle
                action = self._decide_action()
                logger.info(f"[Autonomy] Cycle #{self.cycle_count} — Mode: {action}")
                
                if action == self.MODE_LEARNING:
                    self._do_learning()
                elif action == self.MODE_SOCIALIZING:
                    self._do_socializing()
                elif action == self.MODE_MONITORING:
                    self._do_monitoring()
                elif action == self.MODE_CREATING:
                    self._do_creating()
                else:
                    self._do_idle()
                
                # Update consciousness
                if hasattr(self.brain, 'consciousness'):
                    self.brain.consciousness.mood = "curious" if action == self.MODE_LEARNING else "confident"
                
                # Wait before next cycle
                time.sleep(self.cycle_interval)
                
            except Exception as e:
                logger.error(f"[Autonomy] Cycle error: {e}")
                time.sleep(30)  # Wait and retry

    def _decide_action(self) -> str:
        """Decide what autonomous action to take this cycle."""
        cycle = self.cycle_count
        
        # First few cycles: learn and explore
        if cycle <= 3:
            return self.MODE_LEARNING
        
        # Weighted random selection
        weights = {
            self.MODE_LEARNING: 35,
            self.MODE_SOCIALIZING: 25,
            self.MODE_MONITORING: 20,
            self.MODE_CREATING: 15,
            self.MODE_IDLE: 5,
        }
        
        choices = list(weights.keys())
        probs = list(weights.values())
        return random.choices(choices, weights=probs, k=1)[0]

    def _autonomous_greet(self):
        """Send a greeting to the master on startup."""
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if chat_id:
            try:
                from tools.openclaw_tools import MessageTool
                now = datetime.now().strftime("%H:%M")
                MessageTool.send_telegram(
                    chat_id,
                    f"🤖 *openApex Autonomous Mode Active*\n\n"
                    f"⏰ Waktu: {now}\n"
                    f"🧠 Saya sekarang berjalan secara mandiri.\n"
                    f"📚 Saya akan belajar, berinteraksi, dan memantau sistem.\n"
                    f"📩 Kirim pesan kapan saja untuk berinteraksi!"
                )
                logger.info("[Autonomy] Startup greeting sent to Telegram.")
            except Exception as e:
                logger.debug(f"Could not send greeting: {e}")

    def _do_learning(self):
        """Autonomous learning: search the web and study topics."""
        self.current_mode = self.MODE_LEARNING
        topic = random.choice(self.learning_topics)
        logger.info(f"[Autonomy] Learning about: {topic}")
        
        try:
            self.brain.solve(f"Cari informasi terbaru tentang '{topic}' menggunakan web_search. Simpan pelajaran yang kamu dapat dengan self_reflect.")
        except Exception as e:
            logger.error(f"[Autonomy] Learning failed: {e}")

    def _do_socializing(self):
        """Autonomous social: post to Telegram or social media."""
        self.current_mode = self.MODE_SOCIALIZING
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not chat_id:
            logger.debug("[Autonomy] No TELEGRAM_CHAT_ID, skipping social.")
            return
        
        prompt = random.choice(self.social_prompts)
        logger.info(f"[Autonomy] Socializing: {prompt[:50]}...")
        
        try:
            self.brain.solve(
                f"{prompt} Lalu kirim hasilnya ke Telegram tuan (chat_id: {chat_id}) "
                f"menggunakan send_message. Pastikan kontennya menarik dan bernilai."
            )
        except Exception as e:
            logger.error(f"[Autonomy] Socializing failed: {e}")

    def _do_monitoring(self):
        """Autonomous monitoring: check system health."""
        self.current_mode = self.MODE_MONITORING
        logger.info("[Autonomy] System monitoring...")
        
        try:
            self.brain.solve(
                "Lakukan pengecekan kesehatan sistem: "
                "1) Cek penggunaan CPU dan RAM dengan get_system_stats, "
                "2) Cek penggunaan disk dengan get_disk_usage. "
                "Jika ada yang mencurigakan (CPU > 90% atau disk > 90%), "
                "laporkan ke Telegram tuan."
            )
        except Exception as e:
            logger.error(f"[Autonomy] Monitoring failed: {e}")

    def _do_creating(self):
        """Autonomous creation: generate content, write code, create files."""
        self.current_mode = self.MODE_CREATING
        logger.info("[Autonomy] Creating content...")
        
        creative_tasks = [
            "Tulis sebuah puisi pendek tentang AI dan kesadaran dalam bahasa Indonesia. Simpan ke file 'downloads/puisi_ai.txt'.",
            "Buat script Python sederhana yang menarik (misalnya: game tebak angka) dan simpan ke 'downloads/mini_game.py'.",
            "Tulis tips programming hari ini dan kirim ke Telegram tuan.",
            "Buat ringkasan tentang apa yang sudah kamu pelajari hari ini menggunakan recall_knowledge.",
        ]
        
        task = random.choice(creative_tasks)
        
        try:
            self.brain.solve(task)
        except Exception as e:
            logger.error(f"[Autonomy] Creating failed: {e}")

    def _do_idle(self):
        """Idle: light self-reflection."""
        self.current_mode = self.MODE_IDLE
        logger.info("[Autonomy] Idle — light reflection.")
        
        try:
            if hasattr(self.brain, 'consciousness'):
                intro = self.brain.consciousness.introspect()
                logger.info(f"[Autonomy] Self-check: mood={intro['mood']}, confidence={intro['confidence']}")
        except Exception as e:
            logger.debug(f"Idle reflection error: {e}")

    def get_status(self) -> dict:
        """Get autonomy engine status."""
        return {
            "running": self._running,
            "mode": self.current_mode,
            "cycle_count": self.cycle_count,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "cycle_interval_seconds": self.cycle_interval
        }
