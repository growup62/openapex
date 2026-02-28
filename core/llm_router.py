import os
import json
import logging
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMRouter:
    def __init__(self):
        load_dotenv(override=True)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.hf_api_token = os.getenv("HF_API_TOKEN")
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.default_reasoning_model = os.getenv("DEFAULT_REASONING_MODEL", "gemini/gemini-2.0-flash-lite-preview-02-05")
        self.default_tooling_model = os.getenv("DEFAULT_TOOLING_MODEL", "gemini/gemini-2.0-flash-lite-preview-02-05")

    def _call_openai_style(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic OpenAI-compatible API caller."""
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"OpenAI-style call failed to {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                return {"error": str(e), "status_code": e.response.status_code, "body": e.response.text}
            return {"error": str(e)}

    def _call_gemini_native(self, model: str, messages: list[Dict[str, str]], tools: Optional[list] = None) -> Dict[str, Any]:
        """Native Google Gemini API caller (generateContent)."""
        # Convert OpenAI messages to Gemini contents
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        # Clean model name: e.g. "gemini/gemini-1.5-flash" -> "gemini-1.5-flash"
        api_model = model.split("/")[-1]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={self.gemini_api_key}"
        
        payload = {"contents": contents}
        try:
            response = requests.post(url=url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Extract text to match OpenAI response format
            if "candidates" in data and len(data["candidates"]) > 0:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "choices": [{
                        "message": {"role": "assistant", "content": text}
                    }]
                }
            return {"error": f"No content returned from Gemini: {data}"}
        except Exception as e:
            logger.error(f"Native Gemini call failed for {api_model}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                return {"error": str(e), "body": e.response.text}
            return {"error": str(e)}

    def generate_response(self, 
                          messages: list[Dict[str, str]], 
                          task_type: str = "reasoning", 
                          tools: Optional[list[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Routes and falls back through providers: gemini -> groq -> hf -> or -> ollama."""
        primary_model = self.default_reasoning_model if task_type == "reasoning" else self.default_tooling_model
        if task_type == "swarm_worker":
             primary_model = "groq/llama-3.1-8b-instant"

        # List of provider attempts (Priority order)
        providers = [
            {"name": "primary", "model": primary_model},
            {"name": "gemini_flash_lite", "model": "gemini/gemini-2.0-flash-lite-preview-02-05"},
            {"name": "gemini_flash_1_5", "model": "gemini/gemini-1.5-flash"},
            {"name": "nvidia_nim", "model": "nv/meta/llama-3.1-70b-instruct"},
            {"name": "groq_llama_8b", "model": "groq/llama-3.1-8b-instant"},
            {"name": "groq_llama_70b", "model": "groq/llama-3.3-70b-versatile"},
            {"name": "hf_llama_8b", "model": "hf/meta-llama/Llama-3.1-8B-Instruct"},
            {"name": "ollama_fallback", "model": "ollama/llama3"},
        ]

        for p in providers:
            model = p["model"]
            if not model: continue
            
            logger.info(f"Attempting provider '{p['name']}' with model: {model}")
            
            # Skip if keys are missing
            if "gemini/" in model and not self.gemini_api_key: continue
            if "groq/" in model and not self.groq_api_key: continue
            if "hf/" in model and not self.hf_api_token: continue
            
            result = None
            if model.startswith("gemini/"):
                # Try native first if it's Gemini
                result = self._call_gemini_native(model, messages, tools)
            elif model.startswith("groq/"):
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
                result = self._call_openai_style(url, headers, {"model": model.replace("groq/", ""), "messages": messages, "tools": tools} if tools else {"model": model.replace("groq/", ""), "messages": messages})
            elif model.startswith("nv/"):
                url = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.nvidia_api_key}", "Content-Type": "application/json"}
                result = self._call_openai_style(url, headers, {"model": model.replace("nv/", ""), "messages": messages, "tools": tools} if tools else {"model": model.replace("nv/", ""), "messages": messages})
            elif model.startswith("hf/"):
                url = "https://router.huggingface.co/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.hf_api_token}", "Content-Type": "application/json"}
                result = self._call_openai_style(url, headers, {"model": model.replace("hf/", ""), "messages": messages})
            elif model.startswith("ollama/"):
                url = f"{self.ollama_base_url}/v1/chat/completions"
                result = self._call_openai_style(url, {"Content-Type": "application/json"}, {"model": model.replace("ollama/", ""), "messages": messages})
            else: # Default to OpenRouter
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.openrouter_api_key}", "Content-Type": "application/json", "X-Title": "openApex"}
                result = self._call_openai_style(url, headers, {"model": model, "messages": messages, "tools": tools} if tools else {"model": model, "messages": messages})

            if result and "error" not in result:
                logger.info(f"Successfully got response from provider: {p['name']}")
                return result
            
            logger.warning(f"Provider '{p['name']}' failed. Error: {result.get('error') if result else 'Unknown'}")
            if result and "body" in result:
                logger.debug(f"Response body: {result['body']}")

        return {"error": "All providers failed. Please check your API keys and internet connection."}

    def generate_json_response(self, messages: list[Dict[str, str]], model: Optional[str] = None):
         """Force JSON output (Ollama/Groq/OR support this via response_format)."""
         # Simplified for multi-provider: just add a system prompt or use generate_response
         messages.append({"role": "system", "content": "You MUST return a valid JSON object."})
         return self.generate_response(messages)

if __name__ == "__main__":
    # Simple test execution
    router = LLMRouter()
    print(f"Router initialized. Reasoning model: {router.default_reasoning_model}")
    print(f"Router initialized. Tooling model: {router.default_tooling_model}")
