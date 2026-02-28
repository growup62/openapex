import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ContextWindow:
    """
    Manages short-term memory (the immediate conversation history)
    to prevent context window overflow when communicating with LLMs.
    """
    def __init__(self, max_tokens: int = 4000):
        # A simple estimation: ~4 chars per token roughly
        self.max_chars = max_tokens * 4
        self.history: List[Dict[str, str]] = []

    def get_total_length(self) -> int:
        """Returns the approximate character count of the current history."""
        return sum(len(msg.get("content", "")) for msg in self.history)

    def add_message(self, role: str, content: str):
        """Adds a message and prunes if necessary."""
        self.history.append({"role": role, "content": content})
        self._prune_history()

    def _prune_history(self):
        """
        Removes oldest messages (except the strict System prompt which should be at index 0) 
        if the window exceeds max_chars.
        """
        if not self.history:
            return

        while self.get_total_length() > self.max_chars and len(self.history) > 2:
            # Pop the oldest user/assistant message (index 1), keeping the System Prompt (index 0)
            removed = self.history.pop(1)
            logger.debug(f"Pruned message to save context space: {removed.get('role')}")

    def get_messages(self) -> List[Dict[str, str]]:
        """Returns the current window."""
        return self.history
