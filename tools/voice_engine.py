import logging
import os
import json
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ===== Optional Dependencies =====
TTS_ENGINE = None
try:
    from gtts import gTTS
    TTS_ENGINE = "gtts"
except ImportError:
    pass

if not TTS_ENGINE:
    try:
        import edge_tts
        TTS_ENGINE = "edge_tts"
    except ImportError:
        pass

if not TTS_ENGINE:
    logger.warning("No TTS engine installed. Run: pip install gTTS")


class VoiceEngine:
    """
    Voice interaction engine for openApex.
    - TTS: gTTS (primary, free Google TTS) or edge-tts (fallback)
    - STT: Groq Whisper API (free tier, ultra-fast)
    """

    DEFAULT_LANG = "id"  # Indonesian

    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
        os.makedirs(self.output_dir, exist_ok=True)

    # ===== Text-to-Speech =====

    def text_to_speech(self, text: str, language: str = None, filename: str = None, slow: bool = False) -> Dict[str, Any]:
        """Convert text to speech audio file."""
        if not TTS_ENGINE:
            return {"status": "error", "message": "No TTS engine. Run: pip install gTTS"}

        if not text:
            return {"status": "error", "message": "No text provided"}

        language = language or self.DEFAULT_LANG
        filename = filename or "tts_output.mp3"
        if not filename.endswith(".mp3"):
            filename += ".mp3"

        output_path = os.path.join(self.output_dir, filename)

        try:
            if TTS_ENGINE == "gtts":
                tts = gTTS(text=text, lang=language, slow=slow)
                tts.save(output_path)
            elif TTS_ENGINE == "edge_tts":
                import asyncio
                voice_map = {
                    "id": "id-ID-ArdiNeural",
                    "en": "en-US-GuyNeural",
                    "ja": "ja-JP-KeitaNeural"
                }
                voice = voice_map.get(language, "id-ID-ArdiNeural")

                async def _generate():
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(output_path)

                loop = asyncio.new_event_loop()
                loop.run_until_complete(_generate())
                loop.close()

            file_size = os.path.getsize(output_path)
            logger.info(f"TTS generated: {output_path} ({file_size} bytes)")

            return {
                "status": "success",
                "file_path": output_path,
                "engine": TTS_ENGINE,
                "language": language,
                "file_size_bytes": file_size,
                "text_length": len(text)
            }
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return {"status": "error", "message": str(e)}

    # ===== Speech-to-Text =====

    def speech_to_text(self, audio_path: str, language: str = "id") -> Dict[str, Any]:
        """Convert audio file to text using Groq Whisper API."""
        if not self.groq_api_key:
            return {"status": "error", "message": "GROQ_API_KEY not found"}

        if not os.path.exists(audio_path):
            return {"status": "error", "message": f"Audio file not found: {audio_path}"}

        try:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {self.groq_api_key}"}

            with open(audio_path, "rb") as audio_file:
                files = {"file": (os.path.basename(audio_path), audio_file)}
                data = {
                    "model": "whisper-large-v3",
                    "language": language,
                    "response_format": "json"
                }
                response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                response.raise_for_status()

            result = response.json()
            transcription = result.get("text", "")
            logger.info(f"STT result: {transcription[:100]}...")

            return {
                "status": "success",
                "text": transcription,
                "language": language,
                "audio_file": audio_path
            }

        except requests.exceptions.HTTPError as e:
            error_body = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                except:
                    error_body = e.response.text[:200]
            logger.error(f"STT API error: {e} - {error_body}")
            return {"status": "error", "message": str(e), "details": str(error_body)}

        except Exception as e:
            logger.error(f"STT error: {e}")
            return {"status": "error", "message": str(e)}

    # ===== List Available Voices =====

    def list_voices(self, language_filter: str = None) -> Dict[str, Any]:
        """List available TTS voices/languages."""
        if TTS_ENGINE == "gtts":
            # gTTS supports these languages
            langs = {
                "id": "Indonesian", "en": "English", "ja": "Japanese",
                "ko": "Korean", "zh-CN": "Chinese", "ar": "Arabic",
                "fr": "French", "de": "German", "es": "Spanish",
                "pt": "Portuguese", "ru": "Russian", "hi": "Hindi",
                "ms": "Malay", "th": "Thai", "vi": "Vietnamese",
                "tr": "Turkish", "it": "Italian", "nl": "Dutch"
            }
            if language_filter:
                langs = {k: v for k, v in langs.items() if language_filter.lower() in k.lower() or language_filter.lower() in v.lower()}

            voice_list = [{"code": k, "language": v, "engine": "gTTS"} for k, v in langs.items()]
            return {"status": "success", "count": len(voice_list), "voices": voice_list}

        elif TTS_ENGINE == "edge_tts":
            try:
                import asyncio

                async def _get_voices():
                    return await edge_tts.list_voices()

                loop = asyncio.new_event_loop()
                voices = loop.run_until_complete(_get_voices())
                loop.close()

                if language_filter:
                    voices = [v for v in voices if language_filter.lower() in v.get("Locale", "").lower()]

                voice_list = [{"name": v.get("ShortName"), "locale": v.get("Locale"), "gender": v.get("Gender")} for v in voices[:50]]
                return {"status": "success", "count": len(voice_list), "voices": voice_list}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "No TTS engine available"}


# ===== Tool JSON Schemas =====

TEXT_TO_SPEECH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "text_to_speech",
        "description": "Convert text to speech audio file (MP3). Supports Indonesian, English, and many languages.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to convert to speech"},
                "language": {"type": "string", "description": "Language code: 'id' (Indonesian), 'en' (English), 'ja' (Japanese), etc. Default: 'id'"},
                "filename": {"type": "string", "description": "Output filename. Default: tts_output.mp3"},
                "slow": {"type": "boolean", "description": "Speak slowly. Default: false"}
            },
            "required": ["text"]
        }
    }
}

SPEECH_TO_TEXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "speech_to_text",
        "description": "Convert audio file to text using Groq Whisper (free, ultra-fast). Supports MP3, WAV, OGG, FLAC.",
        "parameters": {
            "type": "object",
            "properties": {
                "audio_path": {"type": "string", "description": "Path to the audio file"},
                "language": {"type": "string", "description": "Language code ('id', 'en', etc). Default: 'id'"}
            },
            "required": ["audio_path"]
        }
    }
}

LIST_TTS_VOICES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_tts_voices",
        "description": "List available text-to-speech voices/languages.",
        "parameters": {
            "type": "object",
            "properties": {
                "language_filter": {"type": "string", "description": "Filter by language code or name. Optional."}
            },
            "required": []
        }
    }
}
