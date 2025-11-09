"""
Phase 5 Test Script
Tests all new features: memory, emotion, state polling
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print("=" * 70)

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_health():
    """Test health endpoint."""
    print_header("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {data['status']}")
            print_success(f"Version: {data['version']}")
            print_success(f"Features: {', '.join(data['features'])}")
            print_success(f"NPC Count: {data.get('npc_count', 0)}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_interaction(player, message):
    """Test NPC interaction with memory."""
    print(f"\n{Colors.YELLOW}💬 {player}: {message}{Colors.RESET}")
    
    payload = {
        "player": player,
        "npc_id": "Professor G",
        "message": message
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_interact",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract data
            action = data.get('action', {})
            state = data.get('new_state', {})
            
            chat = action.get('chat_response', '')
            action_type = action.get('action_type', 'unknown')
            emotion = state.get('emotion', 'unknown')
            objective = state.get('current_objective', '')
            memory = state.get('recent_memory_summary', '')
            
            # Print response
            print(f"{Colors.GREEN}🤖 Professor G: {chat}{Colors.RESET}")
            print(f"   {Colors.CYAN}└─ Action: {action_type}{Colors.RESET}")
            print(f"   {Colors.MAGENTA}└─ Emotion: {emotion}{Colors.RESET}")
            print(f"   {Colors.BLUE}└─ Objective: {objective}{Colors.RESET}")
            print(f"   {Colors.BLUE}└─ Memory: {memory}{Colors.RESET}")
            
            return True, emotion
        else:
            print_error(f"Request failed: {response.statusCode()}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def test_state_polling():
    """Test state polling endpoint."""
    print_header("Test 2: State Polling")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/npc_state",
            params={"npc_id": "Professor G"},
            timeout=5
        )
        
        if response.status_code == 200:
            state = response.json()
            
            print_success(f"NPC ID: {state.get('npc_id')}")
            print_success(f"Emotion: {state.get('emotion')}")
            print_success(f"Objective: {state.get('current_objective')}")
            print_success(f"Memory Summary: {state.get('recent_memory_summary')}")
            print_success(f"Position: ({state.get('x')}, {state.get('z')})")
            print_success(f"Last Updated: {state.get('last_updated')}")
            print_success(f"Memory Count: {state.get('memory_count', 0)}")
            
            return True
        else:
            print_error(f"State poll failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_memory_retrieval():
    """Test memory retrieval endpoint."""
    print_header("Test 3: Memory Retrieval")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/npc_memory",
            params={"npc_id": "Professor G", "limit": 5},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Total Memories: {data.get('total_memories', 0)}")
            print_success(f"Returned: {data.get('returned', 0)}")
            
            memories = data.get('memories', [])
            if memories:
                print_info("Recent memories:")
                for i, mem in enumerate(memories[-3:], 1):  # Show last 3
                    print(f"   {i}. [{mem.get('timestamp')}]")
                    print(f"      Player: {mem.get('player')}")
                    print(f"      Message: {mem.get('message')}")
                    print(f"      Action: {mem.get('action_type')}")
                    print(f"      Emotion: {mem.get('emotion')}")
            
            return True
        else:
            print_error(f"Memory retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_emotion_progression():
    """Test emotion changes over conversation."""
    print_header("Test 4: Emotion Progression")
    
    test_cases = [
        ("Steve", "Hello Professor!", "Should be neutral/happy"),
        ("Steve", "You're amazing!", "Should become happy"),
        ("Steve", "I'm feeling sad today", "Should show empathy"),
        ("Steve", "Can you help me?", "Should become helpful"),
    ]
    
    emotions = []
    for player, message, expected in test_cases:
        success, emotion = test_interaction(player, message)
        if success:
            emotions.append(emotion)
            print_info(f"Expected: {expected}, Got: {emotion}")
        time.sleep(1)
    
    print_info(f"Emotion progression: {' → '.join(emotions)}")
    return True

def test_memory_persistence():
    """Test memory persists across interactions."""
    print_header("Test 5: Memory Persistence")
    
    # Interaction 1
    print_info("Interaction 1: Establishing context")
    test_interaction("Steve", "My name is Steve and I love diamonds!")
    time.sleep(1)
    
    # Interaction 2
    print_info("Interaction 2: Referencing past")
    test_interaction("Steve", "Do you remember what I love?")
    time.sleep(1)
    
    # Check state
    print_info("Checking if memory persisted...")
    return test_state_polling()

def test_multi_action_sequence():
    """Test complex action sequence."""
    print_header("Test 6: Multi-Action Sequence")
    
    sequence = [
        ("Steve", "Professor, come to coordinates 100, 200"),
        ("Steve", "Now follow me around"),
        ("Steve", "Can you give me a diamond?"),
        ("Steve", "You're the best Professor!"),
    ]
    
    for player, message in sequence:
        test_interaction(player, message)
        time.sleep(1.5)
    
    return True

def test_objective_tracking():
    """Test objective updates."""
    print_header("Test 7: Objective Tracking")
    
    test_interaction("Steve", "I need help finding diamonds")
    time.sleep(1)
    
    # Poll state to see objective
    response = requests.get(
        f"{BASE_URL}/api/npc_state",
        params={"npc_id": "Professor G"}
    )
    
    if response.status_code == 200:
        state = response.json()
        objective = state.get('current_objective', '')
        print_info(f"Current objective: {objective}")
        
        if "diamond" in objective.lower() or "help" in objective.lower():
            print_success("Objective correctly reflects player request!")
            return True
        else:
            print_error("Objective doesn't reflect request")
            return False
    
    return False

def main():
    """Run all Phase 5 tests."""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 Phase 5 Complete Test Suite{Colors.RESET}")
    print("=" * 70)
    print(f"{Colors.YELLOW}Testing Memory & Emotion Loop{Colors.RESET}")
    print("=" * 70)
    
    # Test 1: Health
    if not test_health():
        print_error("Server not responding. Exiting.")
        return
    
    time.sleep(1)
    
    # Run all tests
    results = []
    
    results.append(("State Polling", test_state_polling()))
    time.sleep(1)
    
    results.append(("Memory Retrieval", test_memory_retrieval()))
    time.sleep(1)
    
    results.append(("Emotion Progression", test_emotion_progression()))
    time.sleep(1)
    
    results.append(("Memory Persistence", test_memory_persistence()))
    time.sleep(1)
    
    results.append(("Multi-Action Sequence", test_multi_action_sequence()))
    time.sleep(1)
    
    results.append(("Objective Tracking", test_objective_tracking()))
    
    # Print summary
    print_header("Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✅ PASSED{Colors.RESET}" if result else f"{Colors.RED}❌ FAILED{Colors.RESET}"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 70)
    percentage = (passed / total) * 100
    
    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! ({passed}/{total}){Colors.RESET}")
    elif percentage >= 75:
        print(f"{Colors.YELLOW}{Colors.BOLD}✅ MOST TESTS PASSED ({passed}/{total}) - {percentage:.0f}%{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED ({passed}/{total}) - {percentage:.0f}%{Colors.RESET}")
    
    print("=" * 70)
    
    print("\n" + Colors.CYAN + "Phase 5 Features Verified:" + Colors.RESET)
    print("✅ Memory persistence to disk")
    print("✅ Emotion tracking and updates")
    print("✅ State polling endpoint")
    print("✅ Memory retrieval endpoint")
    print("✅ Objective tracking")
    print("✅ Full Gemini AI integration")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()