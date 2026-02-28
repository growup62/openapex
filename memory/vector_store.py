import logging
import os
import uuid
from typing import List, Dict, Any

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages Long-Term Memory using embeddings via ChromaDB.
    """
    
    def __init__(self):
        self.kb_enabled = CHROMA_AVAILABLE
        if self.kb_enabled:
            logger.info("Initializing Long-Term Vector Store (ChromaDB)")
            # Create a local persistent database in the 'memory/db' folder
            db_path = os.path.join(os.getcwd(), "memory", "chroma_db")
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name="openApex_episodes")
        else:
            logger.warning("Initializing Long-Term Vector Store Interface (Mock Mode) - chromadb not installed")
        
    def store_episode(self, task_description: str, solution_summary: str, linked_task_id: str = None):
        """
        Saves a resolved task into long-term storage so the agent 
        doesn't have to relearn how to solve identical problems.
        """
        if not self.kb_enabled:
            logger.debug(f"Knowledge Base disabled. Skipping save for: {task_description[:30]}...")
            return
            
        doc_id = str(uuid.uuid4())
        content = f"Task: {task_description}\nSolution/Result: {solution_summary}"
        
        metadata = {"task": task_description}
        if linked_task_id:
            metadata["linked_to"] = linked_task_id
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info(f"Stored episode in long-term memory: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to store episode: {e}")
        
    def search_similar_tasks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves similar past scenarios to help the active agent.
        """
        if not self.kb_enabled:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results into a clean dictionary list
            formatted_results = []
            if results and 'documents' in results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "id": results['ids'][0][i] if 'ids' in results else "unknown",
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
                    })
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query Vector Store: {e}")
            return []
