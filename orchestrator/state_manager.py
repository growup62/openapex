import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages the current cognitive state of the agent (e.g., Planning, Executing, Verifying, Error).
    It ensures the brain doesn't get stuck in infinite loops.
    """
    
    # Valid States
    STATE_IDLE = "IDLE"
    STATE_PLANNING = "PLANNING"
    STATE_EXECUTING = "EXECUTING"
    STATE_VERIFYING = "VERIFYING"
    STATE_ERROR = "ERROR"

    def __init__(self):
        self.current_state = self.STATE_IDLE
        self.task_queue: List[str] = []
        self.completed_tasks: List[str] = []
        
        # Guardrails
        self.max_iterations_per_task = 10
        self.current_iteration = 0

    def set_state(self, new_state: str):
        if new_state not in [self.STATE_IDLE, self.STATE_PLANNING, self.STATE_EXECUTING, self.STATE_VERIFYING, self.STATE_ERROR]:
            logger.error(f"Attempted to set invalid state: {new_state}")
            return
            
        logger.info(f"State transition: {self.current_state} -> {new_state}")
        self.current_state = new_state
        
        # Reset iteration counter on major state transitions, 
        # except when dropping into ERROR or continuing execution
        if new_state in [self.STATE_PLANNING, self.STATE_IDLE]:
            self.current_iteration = 0

    def increment_iteration(self) -> bool:
        """
        Increments the iteration counter.
        Returns False if the max loop iterations are exceeded (preventing infinite loops).
        """
        self.current_iteration += 1
        logger.debug(f"Loop Iteration: {self.current_iteration}/{self.max_iterations_per_task}")
        
        if self.current_iteration > self.max_iterations_per_task:
            logger.error("Max iterations reached. Triggering circuit breaker.")
            self.set_state(self.STATE_ERROR)
            return False
            
        return True

    def get_context(self) -> Dict[str, Any]:
        """Provides the current operating context for the LLM to understand where it is."""
        return {
            "current_state": self.current_state,
            "tasks_pending": len(self.task_queue),
            "iteration": self.current_iteration
        }
