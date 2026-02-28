import requests
import json
import logging
import re
import os
from typing import Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SearchOptimizerTool:
    """
    Optimizes web search and content reading by stripping noise (JS, CSS, Ads)
    inspired by 'ClawHub Summarize' and 'Readability'.
    """

    @staticmethod
    def read_optimized_url(url: str, max_chars: int = 8000) -> Dict[str, Any]:
        """
        Fetches a URL and returns a lean, text-only version for LLM consumption.
        Saves massive amounts of tokens by removing UI clutter.
        """
        logger.info(f"Optimizing content for: {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove noise
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Get text and clean it
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate
            final_text = text[:max_chars]
            
            return {
                "status": "success",
                "url": url,
                "content_length_raw": len(response.text),
                "content_length_clean": len(final_text),
                "savings_ratio": f"{round((1 - len(final_text)/len(response.text))*100, 1)}%",
                "content": final_text
            }
            
        except Exception as e:
            logger.error(f"Optimization failed for {url}: {e}")
            return {"status": "error", "message": str(e)}

SEARCH_OPTIMIZER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_optimized_url",
        "description": "Read a website URL and extract only the relevant text, removing ads, navigation, and code noise. This is much more token-efficient than standard reading.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to read and optimize."},
                "max_chars": {"type": "integer", "description": "Maximum characters to return (default 8000)."}
            },
            "required": ["url"]
        }
    }
}
