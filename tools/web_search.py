import logging
from typing import Dict, Any, List

# To fully enable this, user requires: `pip install duckduckgo-search`
try:
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("duckduckgo-search not installed. Web Search API disabled.")

logger = logging.getLogger(__name__)

class WebSearchTool:
    """
    Empowers openApex to search the internet for real-time information and URLs.
    """
    
    @staticmethod
    def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Executes a web search and returns top results with URLs.
        """
        if not DDGS_AVAILABLE:
            return {"error": "duckduckgo-search is not installed. Please run: pip install duckduckgo-search"}
            
        logger.info(f"Searching web for query: '{query}'")
        
        try:
            results: List[Dict[str, str]] = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get('title', ''),
                        "url": r.get('href', ''),
                        "snippet": r.get('body', '')
                    })
            
            if not results:
                 return {"status": "no_results", "message": f"No search results found for: {query}"}
                 
            return {"status": "success", "results": results}
                
        except Exception as e:
             logger.error(f"Search API critical failure: {e}")
             return {"error": str(e)}

# The JSON Schema for the Web Search Tool
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the internet using DuckDuckGo to find real-time information, news, or URLs related to a user query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'Latest Python 3.12 features' or 'OpenRouter API docs')."
                },
                "max_results": {
                    "type": "integer",
                    "description": "The maximum number of result snippets to return (default is 5, max is 10).",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}
