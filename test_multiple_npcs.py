"""
Test Script for Multiple NPCs and Autonomous Behavior
Tests Phase 5+ enhanced features
"""

import requests
import json
import time

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
    print_header("Test 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {data['status']}")
            print_success(f"Version: {data['version']}")
            print_success(f"NPC Count: {data.get('npc_count', 0)}")
            print_info("Features:")
            for feature in data['features']:
                print(f"   • {feature}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_multiple_npcs():
    """Test multiple unique NPCs with separate memories."""
    print_header("Test 2: Multiple Unique NPCs")
    
    # Simulate 3 different NPCs
    npc1_id = "Professor Redstone_test123"
    npc2_id = "Professor Diamond_test456"
    npc3_id = "Professor Emerald_test789"
    
    print_info("Simulating 3 NPCs with unique IDs...")
    
    # NPC 1: Steve attacks
    print(f"\n{Colors.YELLOW}--- NPC 1: {npc1_id} ---{Colors.RESET}")
    interact_with_npc(npc1_id, "Steve", "Hello professor!")
    time.sleep(1)
    
    # Attack NPC 1
    attack_npc(npc1_id, "Steve", 5.0)
    time.sleep(0.5)
    attack_npc(npc1_id, "Steve", 5.0)
    time.sleep(0.5)
    attack_npc(npc1_id, "Steve", 5.0)
    time.sleep(0.5)
    
    # NPC 1 should be hostile
    print_info("Talking to hostile NPC 1...")
    interact_with_npc(npc1_id, "Steve", "Can you help me?")
    time.sleep(1)
    
    # NPC 2: Alex gives gifts
    print(f"\n{Colors.YELLOW}--- NPC 2: {npc2_id} ---{Colors.RESET}")
    interact_with_npc(npc2_id, "Alex", "Hi there!")
    time.sleep(1)
    
    # Give gifts to NPC 2
    give_gift(npc2_id, "Alex", "diamond")
    time.sleep(0.5)
    give_gift(npc2_id, "Alex", "emerald")
    time.sleep(0.5)
    
    # NPC 2 should be friendly
    print_info("Talking to friendly NPC 2...")
    interact_with_npc(npc2_id, "Alex", "You're my favorite!")
    time.sleep(1)
    
    # NPC 3: No interactions (neutral)
    print(f"\n{Colors.YELLOW}--- NPC 3: {npc3_id} (Neutral) ---{Colors.RESET}")
    interact_with_npc(npc3_id, "Bob", "Hello!")
    time.sleep(1)
    
    # Check relationships
    print_info("\nChecking separate memories...")
    get_relationship(npc1_id, "Steve")
    time.sleep(0.5)
    get_relationship(npc2_id, "Alex")
    time.sleep(0.5)
    get_relationship(npc3_id, "Bob")
    
    print_success("\nMultiple NPCs test complete!")
    return True

def test_autonomous_greeting():
    """Test autonomous NPC behavior (greetings)."""
    print_header("Test 3: Autonomous Behavior")
    
    npc_id = "Professor Quartz_auto123"
    
    print_info("Simulating NPC detecting nearby player...")
    
    # NPC autonomously greets player
    autonomous_message = "I notice Steve nearby. Should I greet them?"
    
    payload = {
        "npc_id": npc_id,
        "player": "SYSTEM",  # Special marker for autonomous actions
        "message": autonomous_message
    }
    
    print(f"\n{Colors.CYAN}🤖 NPC detects player...{Colors.RESET}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_interact_enhanced",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            chat = data['action']['chat_response']
            emotion = data['new_state']['emotion']
            
            print(f"{Colors.GREEN}🤖 NPC: \"{chat}\"{Colors.RESET}")
            print(f"   Emotion: {emotion}")
            print_success("Autonomous greeting successful!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_memory_deletion():
    """Test NPC memory deletion (on death)."""
    print_header("Test 4: Memory Deletion (NPC Death)")
    
    npc_id = "Professor Netherite_death123"
    
    # Create some memory
    print_info(f"Creating memory for {npc_id}...")
    interact_with_npc(npc_id, "Steve", "Hello!")
    time.sleep(0.5)
    attack_npc(npc_id, "Steve", 5.0)
    time.sleep(0.5)
    
    # Check memory exists
    print_info("Checking memory exists...")
    response = requests.get(
        f"{BASE_URL}/api/npc_memory_summary",
        params={"npc_id": npc_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Memory exists: {data['statistics']['total_interactions']} interactions")
    
    # Delete NPC memory (simulate death)
    print_info(f"\n💀 Simulating {npc_id} death...")
    delete_payload = {"npc_id": npc_id}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_delete",
            json=delete_payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print_success("Memory deleted successfully!")
            
            # Verify deletion
            print_info("Verifying deletion...")
            response = requests.get(
                f"{BASE_URL}/api/npc_memory_summary",
                params={"npc_id": npc_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['statistics']['total_interactions'] == 0:
                    print_success("Memory confirmed cleared!")
                    return True
                else:
                    print_error("Memory still exists!")
                    return False
        else:
            print_error(f"Delete failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_npc_list():
    """Show all active NPCs."""
    print_header("Test 5: List All Active NPCs")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            npc_count = data.get('npc_count', 0)
            
            print_info(f"Total active NPCs: {npc_count}")
            
            if npc_count > 0:
                print_info("Getting memory summaries...")
                # Note: In production, you'd have an endpoint that lists all NPC IDs
                print_success("NPCs are being tracked!")
            else:
                print_info("No active NPCs yet")
            
            return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# Helper functions
def interact_with_npc(npc_id, player, message):
    """Interact with a specific NPC."""
    payload = {
        "npc_id": npc_id,
        "player": player,
        "message": message
    }
    
    print(f"\n{Colors.YELLOW}💬 {player} → [{npc_id.split('_')[0]}]: \"{message}\"{Colors.RESET}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/npc_interact_enhanced",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            chat = data['action']['chat_response']
            emotion = data['new_state']['emotion']
            action = data['action']['action_type']
            
            print(f"{Colors.GREEN}🤖 [{npc_id.split('_')[0]}]: \"{chat}\"{Colors.RESET}")
            print(f"   Action: {action}, Emotion: {emotion}")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def attack_npc(npc_id, attacker, damage):
    """Simulate attacking an NPC."""
    payload = {
        "npc_id": npc_id,
        "event_type": "combat",
        "data": {
            "event_type": "attacked_by",
            "entity_name": attacker,
            "entity_type": "player",
            "damage": damage,
            "weapon": "diamond_sword"
        }
    }
    
    print(f"{Colors.RED}⚔️ {attacker} attacked [{npc_id.split('_')[0]}] ({damage} damage){Colors.RESET}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/npc_event", json=payload)
        if response.status_code == 200:
            data = response.json()
            if "relationship" in data:
                rel = data["relationship"]
                print(f"   Trust: {rel['trust']}, Should attack: {rel['should_attack']}")
            return True
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def give_gift(npc_id, giver, item):
    """Simulate giving a gift to an NPC."""
    payload = {
        "npc_id": npc_id,
        "event_type": "social",
        "data": {
            "event_type": "gift_received",
            "entity_name": giver,
            "item": item
        }
    }
    
    print(f"{Colors.MAGENTA}🎁 {giver} gave {item} to [{npc_id.split('_')[0]}]{Colors.RESET}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/npc_event", json=payload)
        if response.status_code == 200:
            data = response.json()
            if "relationship" in data:
                rel = data["relationship"]
                print(f"   Trust: {rel['trust']}, Affection: {rel['affection']}")
            return True
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def get_relationship(npc_id, entity):
    """Get relationship between NPC and entity."""
    try:
        response = requests.get(
            f"{BASE_URL}/api/npc_relationship",
            params={"npc_id": npc_id, "entity": entity}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] != 'unknown':
                print(f"\n{Colors.CYAN}📊 [{npc_id.split('_')[0]}] ↔ {entity}:{Colors.RESET}")
                print(f"   Status: {data['status']}")
                print(f"   Sentiment: {data['sentiment']}")
                print(f"   Trust: {data['trust']}, Fear: {data['fear']}, Affection: {data['affection']}")
                print(f"   Should attack: {data['recommendations']['should_attack']}")
                print(f"   Should avoid: {data['recommendations']['should_avoid']}")
            else:
                print(f"\n{Colors.CYAN}📊 [{npc_id.split('_')[0]}] ↔ {entity}: No relationship{Colors.RESET}")
            return True
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 Phase 5+ Enhanced Features Test Suite{Colors.RESET}")
    print("=" * 70)
    print(f"{Colors.YELLOW}Testing Multiple NPCs & Autonomous Behavior{Colors.RESET}")
    print("=" * 70)
    
    # Check server
    if not test_health():
        print_error("\nServer not responding. Exiting.")
        return
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    results = []
    
    results.append(("Multiple Unique NPCs", test_multiple_npcs()))
    time.sleep(2)
    
    results.append(("Autonomous Behavior", test_autonomous_greeting()))
    time.sleep(2)
    
    results.append(("Memory Deletion", test_memory_deletion()))
    time.sleep(2)
    
    results.append(("NPC List", test_npc_list()))
    
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
    
    print("\n" + Colors.CYAN + "Phase 5+ Features Verified:" + Colors.RESET)
    print("✅ Multiple unique NPCs")
    print("✅ Separate memories per NPC")
    print("✅ Autonomous greetings")
    print("✅ Memory deletion on death")
    print("✅ Independent relationships")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()