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
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        self.default_reasoning_model = os.getenv("DEFAULT_REASONING_MODEL", "anthropic/claude-3.5-sonnet")
        self.default_tooling_model = os.getenv("DEFAULT_TOOLING_MODEL", "meta-llama/llama-3-8b-instruct")

        self.or_headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/rahfi/openApex", # Optional, for OpenRouter rankings
            "X-Title": "openApex", # Optional, for OpenRouter rankings
        }
        
        self.groq_headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        # Mapping table: Groq model names -> OpenRouter equivalents
        self.groq_to_openrouter_map = {
            "llama-3.3-70b-versatile": "meta-llama/llama-3.3-70b-instruct",
            "llama-3.1-70b-versatile": "meta-llama/llama-3.1-70b-instruct",
            "llama-3.1-8b-instant": "meta-llama/llama-3.1-8b-instruct",
            "llama3-70b-8192": "meta-llama/llama-3-70b-instruct",
            "llama3-8b-8192": "meta-llama/llama-3-8b-instruct",
            "gemma2-9b-it": "google/gemma-2-9b-it",
            "mixtral-8x7b-32768": "mistralai/mixtral-8x7b-instruct",
        }

    def generate_response(self, 
                          messages: list[Dict[str, str]], 
                          task_type: str = "reasoning", 
                          tools: Optional[list[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Routes the request to the appropriate model based on task_type.
        """
        model = self.default_reasoning_model if task_type == "reasoning" else self.default_tooling_model
        logger.info(f"Routing task '{task_type}' to model: {model}")
        
        is_groq = model.startswith("groq/")
        # Remove 'groq/' prefix if calling native Groq API, else keep as is for OpenRouter
        api_model = model.replace("groq/", "") if is_groq else model
        
        payload = {
            "model": api_model,
            "messages": messages
        }
        if tools:
            payload["tools"] = tools

        try:
            target_url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://openrouter.ai/api/v1/chat/completions"
            headers = self.groq_headers if is_groq else self.or_headers
            
            response = requests.post(
                url=target_url,
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            # Handle Groq's known issue where it outputs XML-like function calls instead of native JSON calls
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_obj = error_data.get("error", {})
                    if error_obj.get("code") == "tool_use_failed" and "failed_generation" in error_obj:
                        failed_gen = error_obj["failed_generation"]
                        # Example: <function=web_search>{"query": "cuaca Jakarta hari ini"}</function>
                        import re
                        match = re.search(r'<function=([^>]+)>(.*?)</function>', failed_gen, re.DOTALL)
                        if match:
                            func_name = match.group(1).strip()
                            func_args = match.group(2).strip()
                            logger.info(f"Intercepted Groq XML tool call: {func_name}")
                            
                            # Simulate a successful OpenAI-compatible tool call response
                            import uuid
                            return {
                                "choices": [{
                                    "message": {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": [{
                                            "id": f"call_{str(uuid.uuid4())[:8]}",
                                            "type": "function",
                                            "function": {
                                                "name": func_name,
                                                "arguments": func_args
                                            }
                                        }]
                                    }
                                }]
                            }
                except Exception as parse_error:
                    logger.error(f"Failed to parse Groq failed_generation fallback: {parse_error}")

            if is_groq:
                logger.warning(f"Groq API failed with error {e}. Attempting OpenRouter Fallback...")
                # Translate groq model name to OpenRouter equivalent
                or_model = self.groq_to_openrouter_map.get(api_model, f"meta-llama/llama-3.3-70b-instruct")
                print(f"[System]: Groq API error. Switching to OpenRouter with model: {or_model}...")
                try:
                    # Retry with OpenRouter using the translated model name
                    fallback_payload = payload.copy()
                    fallback_payload["model"] = or_model
                    
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers=self.or_headers,
                        data=json.dumps(fallback_payload)
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as fallback_e:
                     logger.error(f"OpenRouter Fallback also failed: {fallback_e}")
                     if hasattr(fallback_e, 'response') and fallback_e.response is not None:
                         logger.error(f"OpenRouter error body: {fallback_e.response.text}")
                     return {"error": str(fallback_e)}

            logger.error(f"Error calling LLM API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return {"error": str(e)}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return {"error": str(e)}

    # Helper method specifically to force JSON object returns if needed by the reasoning engine
    def generate_json_response(self, messages: list[Dict[str, str]], model: Optional[str] = None):
         _model = model or self.default_reasoning_model
         payload = {
            "model": _model,
            "messages": messages,
            "response_format": {"type": "json_object"}
         }
         
         try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()
         except Exception as e:
             logger.error(f"Error in JSON response generation: {e}")
             return {"error": str(e)}

if __name__ == "__main__":
    # Simple test execution
    router = LLMRouter()
    print(f"Router initialized. Reasoning model: {router.default_reasoning_model}")
    print(f"Router initialized. Tooling model: {router.default_tooling_model}")
