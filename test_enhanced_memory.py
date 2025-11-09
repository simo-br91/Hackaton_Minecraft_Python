"""
Test script for Phase 5+ Enhanced Memory System
Tests combat memory, relationships, and contextual responses
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_header(text):
    print("\n" + "=" * 70)
    print(f"🧪 {text}")
    print("=" * 70)

def record_combat_event(entity_name, damage, weapon="fist"):
    """Simulate combat event."""
    payload = {
        "npc_id": "Professor G",
        "event_type": "combat",
        "data": {
            "event_type": "attacked_by",
            "entity_name": entity_name,
            "entity_type": "player",
            "damage": damage,
            "weapon": weapon
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/npc_event", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"⚔️ Recorded: {entity_name} attacked with {weapon} ({damage} damage)")
        
        if "relationship" in data:
            rel = data["relationship"]
            # Use .get() with defaults
            status = rel.get('status', 'unknown')
            trust = rel.get('trust', 0)
            fear = rel.get('fear', 0)
            should_attack = rel.get('should_attack', False)
            should_avoid = rel.get('should_avoid', False)
            
            print(f"   Status: {status} (Trust: {trust}, Fear: {fear})")
            print(f"   Should attack: {should_attack}")
            print(f"   Should avoid: {should_avoid}")
    else:
        print(f"❌ Failed to record event: {response.status_code}")
        print(f"   Response: {response.text}")

def record_gift(entity_name, item):
    """Simulate gift giving."""
    payload = {
        "npc_id": "Professor G",
        "event_type": "social",
        "data": {
            "event_type": "gift_received",
            "entity_name": entity_name,
            "item": item
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/npc_event", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"🎁 Recorded: {entity_name} gave {item}")
        
        if "relationship" in data:
            rel = data["relationship"]
            # Use .get() with defaults to avoid KeyError
            trust = rel.get('trust', 0)
            affection = rel.get('affection', 0)
            status = rel.get('status', 'unknown')
            print(f"   Status: {status} (Trust: {trust}, Affection: {affection})")
    else:
        print(f"❌ Failed to record gift: {response.status_code}")
        print(f"   Response: {response.text}")

def chat_with_npc(player, message):
    """Chat with NPC and see contextual response."""
    payload = {
        "npc_id": "Professor G",
        "player": player,
        "message": message
    }
    
    print(f"\n💬 {player}: \"{message}\"")
    
    try:
        response = requests.post(f"{BASE_URL}/api/npc_interact_enhanced", json=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            action = data.get("action", {})
            state = data.get("new_state", {})
            
            chat_response = action.get('chat_response', '')
            action_type = action.get('action_type', 'unknown')
            emotion = state.get('emotion', 'neutral')
            
            print(f"🤖 Professor G: \"{chat_response}\"")
            print(f"   Action: {action_type}")
            print(f"   Emotion: {emotion}")
            
            # Check if NPC is attacking
            if action_type == 'attack_target':
                target = action.get('target_name', 'unknown')
                print(f"   ⚔️ ATTACKING: {target}!")
        else:
            print(f"❌ Failed to chat: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"⏱️ Request timed out - AI is thinking too long")
    except Exception as e:
        print(f"❌ Error: {e}")

def get_relationship(entity):
    """Get relationship details."""
    response = requests.get(
        f"{BASE_URL}/api/npc_relationship",
        params={"npc_id": "Professor G", "entity": entity}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Relationship with {entity}:")
        print(f"   Status: {data['status']}")
        print(f"   Sentiment: {data['sentiment']}")
        print(f"   Trust: {data['trust']}/100")
        print(f"   Fear: {data['fear']}/100")
        print(f"   Affection: {data['affection']}/100")
        
        combat = data['combat_stats']
        print(f"   Combat: Attacked {combat['times_attacked_by']}x, Dealt {combat['damage_received']:.1f} damage")
        
        social = data['social_stats']
        print(f"   Social: Received {social['gifts_received']} gifts, Helped {social['times_helped']}x")
        
        rec = data['recommendations']
        print(f"   Recommendations: Attack={rec['should_attack']}, Avoid={rec['should_avoid']}")
    else:
        print(f"❌ Failed to get relationship: {response.status_code}")

def get_memory_summary():
    """Get full memory summary."""
    response = requests.get(
        f"{BASE_URL}/api/npc_memory_summary",
        params={"npc_id": "Professor G"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n📝 Memory Summary:")
        print(f"   Total interactions: {data['statistics']['total_interactions']}")
        print(f"   Combat events: {data['statistics']['total_combat_events']}")
        print(f"   Relationships tracked: {data['statistics']['relationships_tracked']}")
        print(f"\n{data['context']}")
    else:
        print(f"❌ Failed to get summary: {response.status_code}")

# ============================================
# TEST SCENARIOS
# ============================================

def test_scenario_1_revenge():
    """Test: Player attacks NPC multiple times, NPC seeks revenge."""
    print_header("SCENARIO 1: Revenge Arc")
    
    # Attack 1
    print("\n--- Attack 1 ---")
    record_combat_event("Steve", damage=3.0, weapon="wooden_sword")
    time.sleep(0.5)
    chat_with_npc("Steve", "Hey Professor!")
    time.sleep(1)
    
    # Attack 2
    print("\n--- Attack 2 ---")
    record_combat_event("Steve", damage=4.0, weapon="stone_sword")
    time.sleep(0.5)
    chat_with_npc("Steve", "How are you?")
    time.sleep(1)
    
    # Attack 3 - Should trigger hostility
    print("\n--- Attack 3 (Breaking Point) ---")
    record_combat_event("Steve", damage=5.0, weapon="iron_sword")
    time.sleep(0.5)
    chat_with_npc("Steve", "Can you help me?")
    time.sleep(1)
    
    # Check final relationship
    get_relationship("Steve")

def test_scenario_2_friendship():
    """Test: Player gives gifts, builds friendship."""
    print_header("SCENARIO 2: Building Friendship")
    
    # Gift 1
    print("\n--- Gift 1 ---")
    record_gift("Alex", "diamond")
    time.sleep(0.5)
    chat_with_npc("Alex", "Hello Professor! I brought you a gift.")
    time.sleep(1)
    
    # Gift 2
    print("\n--- Gift 2 ---")
    record_gift("Alex", "gold_ingot")
    time.sleep(0.5)
    chat_with_npc("Alex", "Do you need any help with research?")
    time.sleep(1)
    
    # Gift 3
    print("\n--- Gift 3 ---")
    record_gift("Alex", "emerald")
    time.sleep(0.5)
    chat_with_npc("Alex", "You're my favorite NPC!")
    time.sleep(1)
    
    # Check final relationship
    get_relationship("Alex")

def test_scenario_3_mixed():
    """Test: Complex relationship with both positive and negative interactions."""
    print_header("SCENARIO 3: Complex Relationship")
    
    # Start friendly
    print("\n--- Friendly Start ---")
    record_gift("Bob", "apple")
    time.sleep(0.5)
    chat_with_npc("Bob", "Hi Professor, here's an apple!")
    time.sleep(1)
    
    # Accidental attack
    print("\n--- Accidental Attack ---")
    record_combat_event("Bob", damage=2.0, weapon="fist")
    time.sleep(0.5)
    chat_with_npc("Bob", "Sorry! That was an accident!")
    time.sleep(1)
    
    # Make amends with gift
    print("\n--- Making Amends ---")
    record_gift("Bob", "diamond")
    time.sleep(0.5)
    chat_with_npc("Bob", "Here, to make up for it.")
    time.sleep(1)
    
    # Check relationship
    get_relationship("Bob")

def test_scenario_4_fear():
    """Test: Powerful player instills fear."""
    print_header("SCENARIO 4: Fear and Avoidance")
    
    # Heavy attack 1
    print("\n--- Heavy Attack 1 ---")
    record_combat_event("Herobrine", damage=8.0, weapon="diamond_sword")
    time.sleep(0.5)
    
    # Heavy attack 2
    print("\n--- Heavy Attack 2 ---")
    record_combat_event("Herobrine", damage=10.0, weapon="diamond_axe")
    time.sleep(0.5)
    
    # NPC should be afraid
    chat_with_npc("Herobrine", "Come here, Professor.")
    time.sleep(1)
    
    get_relationship("Herobrine")

def main():
    """Run all test scenarios."""
    print("\n" + "="*70)
    print("🧪 Enhanced Memory System - Full Test Suite")
    print("="*70)
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server returned error")
            return
    except:
        print("❌ Cannot connect to server. Is it running?")
        return
    
    input("\nPress Enter to start tests...")
    
    # Run scenarios
    test_scenario_1_revenge()
    time.sleep(2)
    
    test_scenario_2_friendship()
    time.sleep(2)
    
    test_scenario_3_mixed()
    time.sleep(2)
    
    test_scenario_4_fear()
    time.sleep(2)
    
    # Final summary
    print_header("FINAL MEMORY STATE")
    get_memory_summary()
    
    print("\n" + "="*70)
    print("✅ All tests complete!")
    print("="*70)

if __name__ == "__main__":
    main()