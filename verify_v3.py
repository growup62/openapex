import os
import sys
import json
from orchestrator.brain import Brain
from dotenv import load_dotenv

def test_v3_features():
    load_dotenv()
    print("--- Starting openApex V3 Verification ---")
    
    brain = Brain()
    
    # 1. Test PC Control Tool (Disk Usage)
    print("\n[Test 1] PC Control - Disk Usage...")
    disk_res = brain._execute_tool("get_disk_usage", {})
    print(f"Result: {disk_res[:100]}...")
    assert "total" in disk_res.lower()
    
    # 2. Test PC Control Tool (System Stats)
    print("\n[Test 2] PC Control - System Stats...")
    stats_res = brain._execute_tool("get_system_stats", {})
    print(f"Result: {stats_res[:100]}...")
    assert "cpu" in stats_res.lower()
    
    # 3. Test Self-Learner (Reflection)
    print("\n[Test 3] Self-Learner - Reflection...")
    reflect_res = brain._execute_tool("self_reflect", {
        "task": "Test Task",
        "result": "Success"
    })
    print(f"Result: {reflect_res}")
    assert "success" in reflect_res.lower()
    
    # 4. Test Knowledge Recall
    print("\n[Test 4] Self-Learner - Recall...")
    recall_res = brain._execute_tool("recall_knowledge", {"query": "Test Task"})
    print(f"Result: {recall_res[:100]}...")
    assert "success" in recall_res.lower()
    
    print("\n--- All Internal Tool Tests Passed! ---")

if __name__ == "__main__":
    try:
        test_v3_features()
    except Exception as e:
        print(f"\nVerification Failed: {e}")
        sys.exit(1)
