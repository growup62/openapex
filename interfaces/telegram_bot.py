import logging
import os
import io
import threading
from typing import Optional
from contextlib import redirect_stdout

logger = logging.getLogger(__name__)

# Optional dependency
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Run: pip install python-telegram-bot")


class TelegramBot:
    """
    Telegram interface for openApex.
    Supports text messages, voice messages, and voice replies.
    """

    def __init__(self, token: str, brain_instance):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot is not installed. Run: pip install python-telegram-bot")
        
        self.token = token
        self.brain = brain_instance
        self.app = None
        self._thread = None
        self.voice_mode = {}  # chat_id -> bool, when True all replies include voice
        logger.info("Telegram Bot interface initialized.")

    # ===== Command Handlers =====

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command."""
        welcome = (
            "🤖 *openApex AI Agent V3.1*\n\n"
            "Halo! Saya adalah openApex, AI otonom yang bisa:\n"
            "• 🔍 Mencari informasi di web\n"
            "• 🐍 Menjalankan kode Python\n"
            "• 📂 Mengakses file di PC\n"
            "• 🧠 Belajar dan mengingat\n"
            "• 🎤 Berinteraksi dengan suara\n\n"
            "Kirim pesan teks atau *voice note* dan saya akan merespons!\n"
            "Ketik /help untuk bantuan."
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command."""
        help_text = (
            "📋 *Perintah openApex:*\n\n"
            "/start - Mulai bot\n"
            "/help - Tampilkan bantuan\n"
            "/status - Cek status sistem\n"
            "/search <query> - Cari di web\n"
            "/voice <teks> - Konversi teks ke suara\n"
            "/voiceon - Aktifkan mode balasan suara\n"
            "/voiceoff - Matikan mode balasan suara\n\n"
            "🎤 Kirim voice note untuk berinteraksi dengan suara!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command."""
        chat_id = update.message.chat_id
        voice_status = "🟢 ON" if self.voice_mode.get(chat_id, False) else "🔴 OFF"
        status = (
            "✅ *openApex Status*\n\n"
            f"🟢 AI Engine: Online\n"
            f"🟢 Telegram Bot: Connected\n"
            f"🧠 Memory: Active (ChromaDB)\n"
            f"🎤 Voice Mode: {voice_status}\n"
        )
        await update.message.reply_text(status, parse_mode="Markdown")

    async def _search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /search command."""
        query = ' '.join(context.args) if context.args else None
        if not query:
            await update.message.reply_text("⚠️ Gunakan: /search <kata kunci>")
            return
        
        await update.message.reply_text(f"🔍 Mencari: *{query}*...", parse_mode="Markdown")
        
        try:
            response = self._run_brain(f"Carikan informasi di web tentang: {query}")
            await update.message.reply_text(f"🔍 *Hasil:*\n{response[:4000]}", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def _voice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /voice command - converts text to voice note."""
        text = ' '.join(context.args) if context.args else None
        if not text:
            await update.message.reply_text("⚠️ Gunakan: /voice <teks yang ingin diucapkan>")
            return

        await update.message.reply_text("🎤 Mengkonversi teks ke suara...")

        try:
            from tools.voice_engine import VoiceEngine
            engine = VoiceEngine()
            result = engine.text_to_speech(text, filename=f"tg_voice_{update.message.chat_id}.mp3")

            if result["status"] == "success":
                audio_path = result["file_path"]
                with open(audio_path, "rb") as audio:
                    await update.message.reply_voice(voice=audio, caption="🤖 openApex Voice")
            else:
                await update.message.reply_text(f"❌ TTS Error: {result['message']}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def _voiceon_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable voice reply mode."""
        self.voice_mode[update.message.chat_id] = True
        await update.message.reply_text("🎤 Mode suara *AKTIF*! Semua balasan akan disertai voice note.", parse_mode="Markdown")

    async def _voiceoff_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable voice reply mode."""
        self.voice_mode[update.message.chat_id] = False
        await update.message.reply_text("🔇 Mode suara *NONAKTIF*. Balasan hanya teks.", parse_mode="Markdown")

    # ===== Message Handlers =====

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for general text messages."""
        user_msg = update.message.text
        chat_id = update.message.chat_id
        
        logger.info(f"[Telegram] Message from {chat_id}: {user_msg[:50]}...")
        await update.message.reply_text("🤔 Sedang berpikir...")
        
        try:
            response = self._run_brain(user_msg)
            
            # Telegram has a 4096 char limit
            if len(response) > 4000:
                response = response[:4000] + "\n...(dipotong)"
            
            await update.message.reply_text(f"🤖 {response}")

            # If voice mode is ON, also send a voice reply
            if self.voice_mode.get(chat_id, False):
                await self._send_voice_reply(update, response)

        except Exception as e:
            logger.error(f"[Telegram] Error processing message: {e}")
            await update.message.reply_text(f"❌ Terjadi error: {str(e)[:500]}")

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for incoming voice messages - STT -> Brain -> TTS reply."""
        chat_id = update.message.chat_id
        logger.info(f"[Telegram] Voice message from {chat_id}")
        await update.message.reply_text("🎤 Mendengarkan voice note Anda...")

        try:
            from tools.voice_engine import VoiceEngine
            engine = VoiceEngine()

            # 1. Download the voice file from Telegram
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            downloads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            audio_path = os.path.join(downloads_dir, f"tg_incoming_{chat_id}.ogg")
            
            await file.download_to_drive(audio_path)
            logger.info(f"[Telegram] Voice downloaded to {audio_path}")

            # 2. Speech-to-Text
            stt_result = engine.speech_to_text(audio_path, language="id")
            
            if stt_result["status"] != "success":
                await update.message.reply_text(f"❌ Gagal mentranskripsi suara: {stt_result['message']}")
                return

            transcription = stt_result["text"]
            await update.message.reply_text(f"📝 *Transkripsi:* {transcription}", parse_mode="Markdown")

            # 3. Process through Brain
            await update.message.reply_text("🤔 Memproses permintaan Anda...")
            response = self._run_brain(transcription)

            if len(response) > 4000:
                response = response[:4000] + "\n...(dipotong)"
            
            await update.message.reply_text(f"🤖 {response}")

            # 4. Text-to-Speech reply
            await self._send_voice_reply(update, response)

        except Exception as e:
            logger.error(f"[Telegram] Voice handler error: {e}")
            await update.message.reply_text(f"❌ Error memproses voice: {str(e)[:500]}")

    async def _send_voice_reply(self, update: Update, text: str):
        """Generate TTS audio and send as voice note."""
        try:
            from tools.voice_engine import VoiceEngine
            engine = VoiceEngine()

            # Limit text length for TTS
            tts_text = text[:1000] if len(text) > 1000 else text
            result = engine.text_to_speech(tts_text, filename=f"tg_reply_{update.message.chat_id}.mp3")

            if result["status"] == "success":
                with open(result["file_path"], "rb") as audio:
                    await update.message.reply_voice(voice=audio)
        except Exception as e:
            logger.error(f"[Telegram] Voice reply error: {e}")

    # ===== Helpers =====

    def _run_brain(self, message: str) -> str:
        """Process a message through the Brain and extract the response."""
        f = io.StringIO()
        with redirect_stdout(f):
            self.brain.solve(message)
        
        output = f.getvalue()
        
        response_lines = []
        capture = False
        for line in output.split("\n"):
            if "[openApex]:" in line:
                capture = True
                response_lines.append(line.split("[openApex]:")[-1].strip())
            elif capture and line.strip() and not line.startswith("202"):
                response_lines.append(line.strip())
            elif capture and line.startswith("202"):
                capture = False
        
        return "\n".join(response_lines) if response_lines else "Task selesai. Cek terminal untuk detail."

    def run_in_background(self):
        """Starts the Telegram bot in a background thread."""
        def _run():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.app = Application.builder().token(self.token).build()
            
            # Register command handlers
            self.app.add_handler(CommandHandler("start", self._start_command))
            self.app.add_handler(CommandHandler("help", self._help_command))
            self.app.add_handler(CommandHandler("status", self._status_command))
            self.app.add_handler(CommandHandler("search", self._search_command))
            self.app.add_handler(CommandHandler("voice", self._voice_command))
            self.app.add_handler(CommandHandler("voiceon", self._voiceon_command))
            self.app.add_handler(CommandHandler("voiceoff", self._voiceoff_command))
            
            # Register message handlers
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            self.app.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
            
            logger.info("🤖 Telegram Bot is now running with voice support!")
            print("\n[System]: 🤖 Telegram Bot is online with voice support! Send a message or voice note.\n")
            
            loop.run_until_complete(self.app.run_polling(drop_pending_updates=True))
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info("Telegram bot thread started.")
