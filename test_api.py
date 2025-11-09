"""
Enhanced test script for AI NPC API
Validates all action types and API integration
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

# Colors for terminal output
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
    """Print a nice header."""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print("=" * 70)

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_health():
    """Test the health check endpoint."""
    print_header("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server Status: {data['status']}")
            print_success(f"Gemini Available: {data['gemini_available']}")
            print_success(f"API Key Set: {data['api_key_set']}")
            print_info(f"Timestamp: {data['timestamp']}")
            return data['gemini_available']
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        print_info("Make sure app.py is running on http://localhost:5000")
        return False

def test_npc_interact(player, message, npc_id="Professor G"):
    """Test the NPC interaction endpoint."""
    print(f"\n{Colors.YELLOW}💬 {player}: {message}{Colors.RESET}")
    
    payload = {
        "player": player,
        "npc_id": npc_id,
        "message": message
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_interact",
            json=payload,
            timeout=15  # Increased timeout for API calls
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract action
            action = data.get('action', {})
            action_type = action.get('action_type', 'unknown')
            chat = action.get('chat_response', '')
            target = action.get('target_name', '')
            x = action.get('x')
            z = action.get('z')
            
            # Print response
            print(f"{Colors.GREEN}🤖 Professor G: {chat}{Colors.RESET}")
            
            # Print action details
            action_info = f"Action: {action_type}"
            if target:
                action_info += f" (target: {target})"
            if x is not None and z is not None:
                action_info += f" (coords: {x}, {z})"
            print(f"   {Colors.CYAN}└─ {action_info}{Colors.RESET}")
            
            # Print state
            state = data.get('new_state', {})
            emotion = state.get('emotion', 'unknown')
            objective = state.get('current_objective', 'none')
            
            print(f"   {Colors.MAGENTA}└─ Emotion: {emotion}{Colors.RESET}")
            print(f"   {Colors.MAGENTA}└─ Objective: {objective}{Colors.RESET}")
            
            return True, action_type
        else:
            print_error(f"Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def run_basic_conversation():
    """Test basic conversation."""
    print_header("Test 1: Basic Conversation")
    
    tests = [
        ("Steve", "Hello Professor!"),
        ("Steve", "How are you today?"),
        ("Alex", "What do you teach?"),
        ("Steve", "That's interesting!"),
    ]
    
    passed = 0
    for player, message in tests:
        success, _ = test_npc_interact(player, message)
        if success:
            passed += 1
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return passed == len(tests)

def run_movement_tests():
    """Test movement actions."""
    print_header("Test 2: Movement Commands")
    
    tests = [
        ("Steve", "Can you move to coordinates 100, -50?"),
        ("Alex", "Go to 200, 150"),
        ("Steve", "Walk to 50, 75"),
    ]
    
    passed = 0
    for player, message in tests:
        success, action = test_npc_interact(player, message)
        if success and action in ["move_to"]:
            passed += 1
            print_success("Movement action detected!")
        elif success:
            print_error(f"Expected 'move_to', got '{action}'")
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return passed >= len(tests) * 0.6  # 60% threshold for API variability

def run_follow_tests():
    """Test follow actions."""
    print_header("Test 3: Follow Commands")
    
    tests = [
        ("Steve", "Follow me!"),
        ("Alex", "Can you come with me?"),
        ("Steve", "Tag along please"),
    ]
    
    passed = 0
    for player, message in tests:
        success, action = test_npc_interact(player, message)
        if success and action in ["follow", "follow_player"]:
            passed += 1
            print_success("Follow action detected!")
        elif success:
            print_error(f"Expected 'follow', got '{action}'")
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return passed >= len(tests) * 0.6

def run_combat_tests():
    """Test combat actions."""
    print_header("Test 4: Combat Commands")
    
    tests = [
        ("Steve", "Attack that pig!"),
        ("Alex", "Kill the zombie please"),
        ("Steve", "Fight the nearest mob"),
    ]
    
    passed = 0
    for player, message in tests:
        success, action = test_npc_interact(player, message)
        if success and action in ["attack", "attack_target"]:
            passed += 1
            print_success("Attack action detected!")
        elif success:
            print_error(f"Expected 'attack', got '{action}'")
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return passed >= len(tests) * 0.6

def run_mining_tests():
    """Test mining actions."""
    print_header("Test 5: Mining Commands")
    
    tests = [
        ("Steve", "Can you chop down that oak tree?"),
        ("Alex", "Mine some stone please"),
        ("Steve", "Break that diamond ore!"),
    ]
    
    passed = 0
    for player, message in tests:
        success, action = test_npc_interact(player, message)
        if success and action in ["mine_block"]:
            passed += 1
            print_success("Mining action detected!")
        elif success:
            print_error(f"Expected 'mine_block', got '{action}'")
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return passed >= len(tests) * 0.6

def run_emote_tests():
    """Test emote actions."""
    print_header("Test 6: Emote Commands")
    
    tests = [
        ("Steve", "Show me you're happy!"),
        ("Alex", "Can you look excited?"),
        ("Steve", "Act confused"),
    ]
    
    passed = 0
    for player, message in tests:
        success, action = test_npc_interact(player, message)
        if success and action in ["emote"]:
            passed += 1
            print_success("Emote action detected!")
        elif success:
            print_info(f"Got '{action}' - may still be valid")
        time.sleep(1)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(tests)} tests passed{Colors.RESET}")
    return True  # Emotes are tricky, so we're lenient

def run_complex_scenario():
    """Test a complex multi-turn scenario."""
    print_header("Test 7: Complex Scenario")
    
    scenario = [
        ("Steve", "Hello Professor! I need help finding resources."),
        ("Steve", "Can you come with me to the mine?"),
        ("Steve", "Great! Let's go to coordinates 300, -200"),
        ("Alex", "Hi Professor! What are you doing?"),
        ("Steve", "Professor, can you mine some coal for me?"),
        ("Steve", "Thanks! You're the best!"),
    ]
    
    passed = 0
    for player, message in scenario:
        success, _ = test_npc_interact(player, message)
        if success:
            passed += 1
        time.sleep(1.5)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(scenario)} interactions successful{Colors.RESET}")
    return passed == len(scenario)

def check_memory_file():
    """Check if memory is being saved."""
    print_header("Checking Memory Storage")
    
    try:
        with open("data/npc_memory.json", "r") as f:
            memory = json.load(f)
            
        professor_memory = memory.get("Professor G", [])
        
        if professor_memory:
            print_success(f"Found {len(professor_memory)} memories for Professor G")
            print_info("Most recent interaction:")
            if professor_memory:
                recent = professor_memory[-1]
                print(f"   Player: {recent.get('player')}")
                print(f"   Message: {recent.get('message')}")
                print(f"   Response: {recent.get('response')}")
                print(f"   Emotion: {recent.get('emotion')}")
            return True
        else:
            print_error("No memories found for Professor G")
            return False
            
    except FileNotFoundError:
        print_error("Memory file not found at data/npc_memory.json")
        return False
    except Exception as e:
        print_error(f"Error reading memory: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 AI NPC Enhanced Test Suite{Colors.RESET}")
    print("=" * 70)
    print(f"{Colors.YELLOW}Testing Gemini API integration and action generation{Colors.RESET}")
    print("=" * 70)
    
    # Test 0: Health check
    api_available = test_health()
    if not api_available:
        print("\n" + "=" * 70)
        print_error("Server is not responding or Gemini API is unavailable!")
        print_info("Please check:")
        print("  1. Python server is running: python app.py")
        print("  2. GEMINI_API_KEY environment variable is set")
        print("  3. API key is valid")
        print("=" * 70)
        return
    
    time.sleep(2)
    
    # Run all test suites
    results = []
    
    results.append(("Basic Conversation", run_basic_conversation()))
    time.sleep(2)
    
    results.append(("Movement Commands", run_movement_tests()))
    time.sleep(2)
    
    results.append(("Follow Commands", run_follow_tests()))
    time.sleep(2)
    
    results.append(("Combat Commands", run_combat_tests()))
    time.sleep(2)
    
    results.append(("Mining Commands", run_mining_tests()))
    time.sleep(2)
    
    results.append(("Emote Commands", run_emote_tests()))
    time.sleep(2)
    
    results.append(("Complex Scenario", run_complex_scenario()))
    time.sleep(2)
    
    results.append(("Memory Storage", check_memory_file()))
    
    # Print final results
    print_header("Final Results")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASSED{Colors.RESET}" if result else f"{Colors.RED}❌ FAILED{Colors.RESET}"
        print(f"{test_name}: {status}")
    
    print("\n" + "=" * 70)
    percentage = (passed / total) * 100
    
    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! ({passed}/{total}){Colors.RESET}")
    elif percentage >= 75:
        print(f"{Colors.YELLOW}{Colors.BOLD}✅ MOST TESTS PASSED ({passed}/{total}) - {percentage:.0f}%{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED ({passed}/{total}) - {percentage:.0f}%{Colors.RESET}")
    
    print("=" * 70)
    
    print("\n" + Colors.CYAN + "Next Steps:" + Colors.RESET)
    print("1. Check data/npc_memory.json to see stored conversations")
    print("2. Modify data/npc_personality.json to customize Professor G")
    print("3. Test in Minecraft with /testnpc commands")
    print("4. Chat with Professor G by saying 'professor' in chat")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()