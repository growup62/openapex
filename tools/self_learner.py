import logging
import requests
import re
from typing import Dict, Any, Optional
from memory.vector_store import VectorStore

logger = logging.getLogger(__name__)

class SelfLearnerTool:
    """
    Gives openApex the ability to learn autonomously.
    - Reflect on completed tasks and extract lessons
    - Recall past knowledge before starting new tasks
    - Study web documentation and save summaries to memory
    """

    def __init__(self, memory: VectorStore, llm_router=None):
        self.memory = memory
        self.router = llm_router  # Optional: used for summarizing docs

    def reflect_on_task(self, task: str, result: str) -> Dict[str, Any]:
        """
        After completing a task, the AI reflects on what it learned
        and stores the lesson in long-term memory with metadata.
        """
        logger.info(f"Self-reflecting on task: {task[:50]}...")

        # Create a structured reflection entry
        reflection = {
            "task": task,
            "result": result[:2000],
            "type": "reflection"
        }

        # Store with enriched metadata
        doc_id = self.memory.store_episode(
            task_description=f"[REFLECTION] {task}",
            solution_summary=f"Task: {task}\nResult: {result[:2000]}\nLesson: Completed successfully."
        )

        logger.info(f"Reflection stored in memory: {doc_id}")
        return {
            "status": "success",
            "message": f"Reflected on task and stored lesson in long-term memory.",
            "memory_id": str(doc_id)
        }

    def recall_similar(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Before starting a new task, search memory for similar past experiences.
        Returns relevant past solutions the AI can learn from.
        """
        logger.info(f"Recalling knowledge for: {query[:50]}...")

        results = self.memory.search_similar_tasks(query, top_k=n_results)

        if not results:
            return {
                "status": "no_memories",
                "message": "No relevant past experiences found in memory."
            }

        memories = []
        for item in results:
            memories.append({
                "memory": item.get("content", "")[:500],
                "metadata": item.get("metadata", {})
            })

        logger.info(f"Recalled {len(memories)} relevant memories.")
        return {
            "status": "success",
            "relevant_memories": memories
        }

    def study_documentation(self, url: str) -> Dict[str, Any]:
        """
        Fetches a URL, extracts text content, and stores a summary in memory.
        This allows the AI to learn from online documentation autonomously.
        """
        logger.info(f"Studying documentation from: {url}")

        try:
            response = requests.get(url, timeout=15, headers={
                "User-Agent": "openApex/1.0 (Autonomous AI Agent)"
            })
            response.raise_for_status()

            # Basic HTML to text extraction
            text = response.text
            # Remove HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Truncate to reasonable size
            text = text[:5000]

            if not text:
                return {"error": "Could not extract text from the URL."}

            # Store in memory
            doc_id = self.memory.store_episode(
                task_description=f"[STUDY] Documentation from: {url}",
                solution_summary=f"Source: {url}\nContent Summary: {text[:3000]}"
            )

            logger.info(f"Documentation studied and stored: {doc_id}")
            return {
                "status": "success",
                "message": f"Successfully studied documentation from {url}. Content saved to memory.",
                "content_preview": text[:500],
                "memory_id": str(doc_id)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch documentation: {e}")
            return {"error": f"Failed to fetch URL: {str(e)}"}


# JSON Schemas for LLM Tool Registration

SELF_REFLECT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "self_reflect",
        "description": "Reflect on a completed task to extract lessons learned and store them in long-term memory for future reference. Use this after completing any task to build up your knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task that was completed."
                },
                "result": {
                    "type": "string",
                    "description": "The result or outcome of the task."
                }
            },
            "required": ["task", "result"]
        }
    }
}

RECALL_KNOWLEDGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recall_knowledge",
        "description": "Search your long-term memory for relevant past experiences, solutions, and lessons learned. Use this BEFORE starting a new task to check if you have solved something similar before.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant past memories."
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of relevant memories to retrieve (default: 3).",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
}

STUDY_URL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "study_url",
        "description": "Study and learn from online documentation or web pages. Fetches the URL content, extracts the text, and saves it to your long-term memory so you can reference it later.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the documentation or web page to study."
                }
            },
            "required": ["url"]
        }
    }
}
