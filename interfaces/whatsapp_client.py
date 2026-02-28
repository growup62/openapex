import logging
import json
import os
import io
import threading
from contextlib import redirect_stdout
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

WHATSAPP_BACKEND_PORT = 5678


class WhatsAppHandler(BaseHTTPRequestHandler):
    """HTTP handler that receives WhatsApp messages from the Node.js bridge."""
    
    brain_instance = None

    def log_message(self, format, *args):
        logger.debug(f"[WhatsApp HTTP] {args}")
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if self.path == '/whatsapp/incoming':
            self._handle_text(body)
        elif self.path == '/whatsapp/voice-incoming':
            self._handle_voice(body)
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_text(self, body: str):
        """Handle incoming text messages."""
        try:
            data = json.loads(body)
            sender_raw = data.get('sender', 'unknown')
            sender = sender_raw.split('@')[0] if '@' in sender_raw else sender_raw
            message = data.get('message', '')
            
            logger.info(f"[WhatsApp] Text from {sender}: {message[:50]}...")
            response = self._process_message(message)
            
            self._send_json(200, {"response": response})
        except Exception as e:
            logger.error(f"[WhatsApp] Text error: {e}")
            self._send_json(500, {"error": str(e)})

    def _handle_voice(self, body: str):
        """Handle incoming voice messages: STT -> Brain -> TTS."""
        try:
            data = json.loads(body)
            sender_raw = data.get('sender', 'unknown')
            sender = sender_raw.split('@')[0] if '@' in sender_raw else sender_raw
            audio_path = data.get('audio_path', '')
            
            logger.info(f"[WhatsApp] Voice from {sender}: {audio_path}")

            from tools.voice_engine import VoiceEngine
            engine = VoiceEngine()

            # 1. Speech-to-Text
            stt_result = engine.speech_to_text(audio_path, language="id")
            if stt_result["status"] != "success":
                self._send_json(200, {"text_response": f"❌ STT Error: {stt_result['message']}"})
                return

            transcription = stt_result["text"]
            logger.info(f"[WhatsApp] Transcription: {transcription[:100]}")

            # 2. Process through Brain
            response = self._process_message(transcription)

            # 3. Text-to-Speech reply
            tts_text = response[:1000] if len(response) > 1000 else response
            tts_result = engine.text_to_speech(tts_text, filename=f"wa_reply_{sender}.mp3")

            reply_audio = tts_result.get("file_path") if tts_result.get("status") == "success" else None

            self._send_json(200, {
                "text_response": f"📝 *Transkripsi:* {transcription}\n\n🤖 {response[:3500]}",
                "audio_path": reply_audio
            })

        except Exception as e:
            logger.error(f"[WhatsApp] Voice error: {e}")
            self._send_json(500, {"text_response": f"❌ Error: {str(e)[:500]}"})

    def _process_message(self, message: str) -> str:
        """Processes a message through the Brain."""
        if not self.brain_instance:
            return "❌ AI Engine not initialized."
        
        try:
            f = io.StringIO()
            with redirect_stdout(f):
                self.brain_instance.solve(message)
            
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
            
            return "\n".join(response_lines) if response_lines else "Task selesai."
            
        except Exception as e:
            logger.error(f"[WhatsApp] Brain processing error: {e}")
            return f"❌ Error: {str(e)[:500]}"

    def _send_json(self, status_code: int, data: dict):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


class WhatsAppClient:
    """
    Python-side WhatsApp integration with voice support.
    Starts an HTTP server that receives messages from the Node.js bridge.
    """
    
    def __init__(self, brain_instance):
        self.brain = brain_instance
        WhatsAppHandler.brain_instance = brain_instance
        self._thread = None
    
    def run_in_background(self):
        """Starts the WhatsApp HTTP server in a background thread."""
        def _run():
            server = HTTPServer(('localhost', WHATSAPP_BACKEND_PORT), WhatsAppHandler)
            logger.info(f"[WhatsApp] HTTP backend listening on port {WHATSAPP_BACKEND_PORT}")
            print(f"\n[System]: 💬 WhatsApp backend ready on port {WHATSAPP_BACKEND_PORT} (voice enabled)")
            print("[System]: Run 'cd interfaces/whatsapp_bridge && npm start' to connect WhatsApp.\n")
            server.serve_forever()
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info("WhatsApp backend thread started.")
