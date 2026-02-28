import sys
import os
import logging

# Add the current directory to sys.path to import core
sys.path.append(os.getcwd())

from core.llm_router import LLMRouter

# Set up logging for the test
logging.basicConfig(level=logging.INFO)

def test_router_cycling():
    router = LLMRouter()
    messages = [{"role": "user", "content": "Say 'System OK' if you can read this."}]
    
    print("\n--- Starting Multi-Provider Routing Test ---")
    result = router.generate_response(messages)
    
    if "error" in result:
        print(f"\nFAILED: {result['error']}")
    else:
        content = result["choices"][0]["message"]["content"]
        print(f"\nSUCCESS! AI Response: {content}")

if __name__ == "__main__":
    test_router_cycling()
