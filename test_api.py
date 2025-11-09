"""
Test script for Phase 2 AI Brain API
Run this after starting app.py to verify everything works
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("🏥 Testing Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"✅ Gemini Available: {data['gemini_available']}")
            print(f"✅ Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure app.py is running!")
        return False

def test_npc_interact(player, message, npc_id="Professor G"):
    """Test the NPC interaction endpoint."""
    print(f"\n🗣️  {player}: {message}")
    
    payload = {
        "player": player,
        "npc_id": npc_id,
        "message": message
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_interact",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Print action
            action = data.get('action', {})
            action_type = action.get('action_type', 'unknown')
            chat = action.get('chat_response', '')
            
            print(f"🤖 {npc_id}: {chat}")
            print(f"   └─ Action: {action_type}")
            
            # Print state
            state = data.get('new_state', {})
            emotion = state.get('emotion', 'unknown')
            objective = state.get('current_objective', 'none')
            
            print(f"   └─ Emotion: {emotion}")
            print(f"   └─ Objective: {objective}")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_conversation_test():
    """Run a full conversation test."""
    print("\n" + "="*60)
    print("💬 Testing Conversation Flow")
    print("="*60)
    
    test_messages = [
        ("Steve", "Hello Professor!"),
        ("Steve", "Can you help me find diamonds?"),
        ("Steve", "Where should I look?"),
        ("Alex", "Hi Professor, what are you doing?"),
        ("Steve", "Thanks for your help!"),
    ]
    
    success_count = 0
    for player, message in test_messages:
        if test_npc_interact(player, message):
            success_count += 1
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "="*60)
    print(f"✅ Passed: {success_count}/{len(test_messages)} tests")
    print("="*60)

def test_action_commands():
    """Test different action types."""
    print("\n" + "="*60)
    print("⚙️  Testing Action Commands")
    print("="*60)
    
    test_cases = [
        ("Steve", "Can you move to coordinates 100, -50?"),
        ("Steve", "Please chop down that oak tree"),
        ("Steve", "Follow me!"),
        ("Steve", "Attack that zombie!"),
    ]
    
    for player, message in test_cases:
        test_npc_interact(player, message)
        time.sleep(1)

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 Phase 2 API Test Suite")
    print("="*60)
    print("Make sure app.py is running on http://localhost:5000")
    print("="*60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Server is not responding. Exiting.")
        return
    
    # Small delay
    time.sleep(1)
    
    # Test 2: Conversation
    run_conversation_test()
    
    # Test 3: Action commands
    test_action_commands()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check data/npc_memory.json to see stored conversations")
    print("2. Try modifying data/npc_personality.json to change Professor G's personality")
    print("3. Move to Phase 3 - Java integration")
    print("="*60)

if __name__ == "__main__":
    main()