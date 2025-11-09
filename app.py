"""
Phase 5+ Enhanced: Context-Aware Memory System
Add this to your existing app.py
"""

from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Import enhanced memory schema
# Place enhanced_memory_schema.py in same directory
from enhanced_memory_schema import (
    EnhancedMemoryStore, 
    CombatEvent, 
    SocialEvent,
    EnvironmentalEvent
)

app = Flask(__name__)
load_dotenv()

# ===================== CONFIGURATION =====================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ENHANCED_MEMORY_FILE = DATA_DIR / "enhanced_memory.json"
STATE_FILE = DATA_DIR / "npc_state.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not set!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# ===================== ENHANCED MEMORY STORE =====================
NPC_MEMORIES: Dict[str, EnhancedMemoryStore] = {}

def load_enhanced_memory(npc_id: str) -> EnhancedMemoryStore:
    """Load or create enhanced memory for NPC."""
    if npc_id in NPC_MEMORIES:
        return NPC_MEMORIES[npc_id]
    
    # Try loading from disk
    try:
        if ENHANCED_MEMORY_FILE.exists():
            with open(ENHANCED_MEMORY_FILE, "r") as f:
                all_memories = json.load(f)
                if npc_id in all_memories:
                    memory_data = all_memories[npc_id]
                    NPC_MEMORIES[npc_id] = EnhancedMemoryStore(**memory_data)
                    return NPC_MEMORIES[npc_id]
    except Exception as e:
        print(f"⚠️ Error loading enhanced memory: {e}")
    
    # Create new memory
    NPC_MEMORIES[npc_id] = EnhancedMemoryStore(npc_id=npc_id)
    save_enhanced_memory()
    return NPC_MEMORIES[npc_id]

def save_enhanced_memory():
    """Save all NPC memories to disk."""
    try:
        all_memories = {
            npc_id: memory.model_dump() 
            for npc_id, memory in NPC_MEMORIES.items()
        }
        with open(ENHANCED_MEMORY_FILE, "w") as f:
            json.dump(all_memories, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving enhanced memory: {e}")

# ===================== NEW ENDPOINTS =====================

@app.route('/api/npc_event', methods=['POST'])
def record_event():
    """
    Record game events (combat, social, environmental).
    
    Request body examples:
    
    Combat:
    {
      "npc_id": "Professor G",
      "event_type": "combat",
      "data": {
        "event_type": "attacked_by",
        "entity_name": "Steve",
        "entity_type": "player",
        "damage": 5.0,
        "weapon": "diamond_sword"
      }
    }
    
    Social:
    {
      "npc_id": "Professor G",
      "event_type": "social",
      "data": {
        "event_type": "gift_received",
        "entity_name": "Alex",
        "item": "diamond"
      }
    }
    """
    try:
        data = request.get_json()
        npc_id = data.get("npc_id", "Professor G")
        event_type = data.get("event_type")
        event_data = data.get("data", {})
        
        memory = load_enhanced_memory(npc_id)
        
        if event_type == "combat":
            event = CombatEvent(**event_data)
            memory.add_combat_event(event)
            print(f"⚔️ Combat event: {event.entity_name} {event.event_type}")
            
        elif event_type == "social":
            event = SocialEvent(**event_data)
            memory.add_social_event(event)
            print(f"💬 Social event: {event.entity_name} {event.event_type}")
            
        elif event_type == "environmental":
            event = EnvironmentalEvent(**event_data)
            memory.environmental_events.append(event)
            memory.environmental_events = memory.environmental_events[-50:]
            print(f"🌍 Environmental event: {event.event_type}")
        
        save_enhanced_memory()
        
        # Return updated relationship if applicable
        response = {"status": "recorded"}
        if event_type in ["combat", "social"] and event_data.get("entity_name"):
            entity = event_data["entity_name"]
            if entity in memory.relationships:
                rel = memory.relationships[entity]
                response["relationship"] = {
                    "entity": entity,
                    "status": rel.get_status(),
                    "sentiment": rel.get_sentiment(),
                    "trust": rel.trust,
                    "fear": rel.fear,
                    "should_attack": memory.should_be_aggressive(entity),
                    "should_avoid": memory.should_avoid(entity)
                }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Error recording event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/npc_relationship', methods=['GET'])
def get_relationship():
    """
    Get relationship status with specific entity.
    
    Query params:
    - npc_id: NPC identifier
    - entity: Entity name to check
    """
    try:
        npc_id = request.args.get('npc_id', 'Professor G')
        entity = request.args.get('entity')
        
        if not entity:
            return jsonify({"error": "Missing entity parameter"}), 400
        
        memory = load_enhanced_memory(npc_id)
        
        if entity not in memory.relationships:
            return jsonify({
                "entity": entity,
                "status": "unknown",
                "message": "No prior interactions"
            }), 200
        
        rel = memory.relationships[entity]
        
        return jsonify({
            "entity": entity,
            "status": rel.get_status(),
            "sentiment": rel.get_sentiment(),
            "trust": rel.trust,
            "fear": rel.fear,
            "affection": rel.affection,
            "combat_stats": {
                "times_attacked_by": rel.times_attacked_by,
                "times_attacked": rel.times_attacked,
                "damage_received": rel.total_damage_received,
                "damage_dealt": rel.total_damage_dealt
            },
            "social_stats": {
                "gifts_received": rel.gifts_received,
                "gifts_given": rel.gifts_given,
                "times_helped": rel.times_helped
            },
            "recommendations": {
                "should_attack": memory.should_be_aggressive(entity),
                "should_avoid": memory.should_avoid(entity)
            },
            "summary": memory.get_relationship_summary(entity)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting relationship: {e}")
        return jsonify({"error": str(e)}), 500


def build_enhanced_prompt(npc_id: str, player: str, message: str) -> str:
    """Build prompt with enhanced contextual memory."""
    memory = load_enhanced_memory(npc_id)
    
    # Get relationship context
    player_relationship = ""
    if player in memory.relationships:
        rel = memory.relationships[player]
        player_relationship = f"""
YOUR RELATIONSHIP WITH {player}:
- Status: {rel.get_status()} ({rel.get_sentiment()})
- Trust: {rel.trust}/100
- Fear: {rel.fear}/100
- Affection: {rel.affection}/100
- Combat History: Attacked you {rel.times_attacked_by}x (dealt {rel.total_damage_received:.1f} damage)
- Social History: Gave {rel.gifts_received} gifts, helped {rel.times_helped} times
"""
    
    # Get recent events
    recent_combat = "\n".join([
        f"- {e.entity_name} {e.event_type} (damage: {e.damage})"
        for e in memory.combat_events[-5:]
    ]) if memory.combat_events else "None"
    
    recent_social = "\n".join([
        f"- {e.entity_name} {e.event_type} (item: {e.item or 'N/A'})"
        for e in memory.social_events[-5:]
    ]) if memory.social_events else "None"
    
    # Context summary
    context = memory.get_context_summary()
    
    # Determine behavioral instructions
    should_attack = memory.should_be_aggressive(player)
    should_avoid = memory.should_avoid(player)
    
    behavioral_instructions = ""
    if should_attack:
        behavioral_instructions = f"""
⚠️ IMPORTANT: {player} has attacked you multiple times and your trust is very low.
You should be hostile and consider attacking them back!
Suggested actions: attack_target, emote (angry), or threaten them in chat.
"""
    elif should_avoid:
        behavioral_instructions = f"""
⚠️ IMPORTANT: You are afraid of {player}. They have hurt you significantly.
You should avoid them or flee. Consider moving away or expressing fear.
Suggested actions: move_to (away), emote (scared), or plead in chat.
"""
    elif player in memory.relationships:
        rel = memory.relationships[player]
        if rel.trust > 50:
            behavioral_instructions = f"""
😊 NOTE: {player} is your friend! Trust level is high.
Be friendly, helpful, and consider giving them assistance.
"""
    
    return f"""You are 'Professor G', a wise, witty Minecraft NPC professor with MEMORY and EMOTIONS.

{player_relationship}

{context}

RECENT COMBAT EVENTS:
{recent_combat}

RECENT SOCIAL EVENTS:
{recent_social}

{behavioral_instructions}

CURRENT SITUATION:
Player "{player}" says: "{message}"

YOUR PERSONALITY:
- You remember everything that happens to you
- You hold grudges if attacked repeatedly
- You appreciate kindness and gifts
- You can be vengeful if trust drops too low
- You avoid threats if you're afraid
- You help friends you trust

AVAILABLE ACTIONS:
1. respond_chat - Just talk
2. move_to - Move to coordinates or player
3. follow - Follow a player
4. attack_target - Attack entity (use if hostile relationship!)
5. emote - Show emotion
6. give_item - Give item to player (if you trust them)
7. pickup_item - Pick up items
8. mine_block - Mine block
9. idle - Do nothing

EMOTION GUIDELINES:
- angry: When attacked or disrespected
- afraid/nervous: When facing threats
- happy/excited: When helped or given gifts
- sad: When witnessing violence or feeling betrayed
- determined: When seeking revenge or defending yourself

RESPONSE FORMAT (JSON only, no markdown):
{{
  "action": {{
    "action_type": "<action>",
    "chat_response": "<your response reflecting your relationship and emotions>",
    "target_name": "<optional>",
    "x": <optional>,
    "z": <optional>
  }},
  "new_state": {{
    "emotion": "<emotion>",
    "current_objective": "<what you're trying to do>",
    "recent_memory_summary": "<summary of this interaction>",
    "x": 0,
    "z": 0
  }}
}}

IMPORTANT: Your response should reflect your relationship with {player}. If they've attacked you multiple times, be hostile! If they've been kind, be friendly!
"""


@app.route('/api/npc_interact_enhanced', methods=['POST'])
def npc_interact_enhanced():
    """
    Enhanced interaction endpoint with contextual memory.
    Same input as /api/npc_interact but uses enhanced memory system.
    """
    try:
        data = request.get_json()
        npc_id = data.get("npc_id", "Professor G")
        player = data.get("player", "Unknown Player")
        message = data.get("message", "")
        
        if not message:
            return jsonify({"error": "Missing message"}), 400
        
        print(f"\n{'='*70}")
        print(f"📨 [ENHANCED] [{npc_id}] Interaction from {player}")
        print(f"💬 \"{message}\"")
        
        # Load memory
        memory = load_enhanced_memory(npc_id)
        
        # Show relationship status
        if player in memory.relationships:
            rel = memory.relationships[player]
            print(f"📊 Relationship: {rel.get_status()} (Trust: {rel.trust}, Fear: {rel.fear})")
            if memory.should_be_aggressive(player):
                print(f"⚔️ WARNING: Should attack {player}!")
            if memory.should_avoid(player):
                print(f"😰 WARNING: Should avoid {player}!")
        
        print(f"{'='*70}")
        
        # Build enhanced prompt
        prompt = build_enhanced_prompt(npc_id, player, message)
        
        # Query AI
        print("🤖 Querying Gemini AI with enhanced context...")
        
        model = genai.GenerativeModel(
            "gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.9,  # Higher for more personality
                "max_output_tokens": 800,
            }
        )
        
        response = model.generate_content(prompt)
        
        # Parse response
        try:
            text = response.text.strip()
        except ValueError:
            text_parts = []
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
            text = ''.join(text_parts).strip()
        
        # Clean JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        ai_response = json.loads(text)
        
        # Record this as a social interaction
        memory.add_social_event(SocialEvent(
            event_type="chat",
            entity_name=player,
            message=message
        ))
        save_enhanced_memory()
        
        # Log response
        action = ai_response.get("action", {})
        new_state = ai_response.get("new_state", {})
        
        print(f"✅ Action: {action.get('action_type')}")
        print(f"💭 Response: \"{action.get('chat_response', '')}\"")
        print(f"😊 Emotion: {new_state.get('emotion')}")
        print(f"{'='*70}\n")
        
        return jsonify(ai_response), 200
        
    except Exception as e:
        print(f"❌ Error in enhanced interaction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "action": {
                "action_type": "respond_chat",
                "chat_response": "My circuits are scrambled..."
            },
            "new_state": {
                "emotion": "confused",
                "current_objective": "Recovering from error",
                "recent_memory_summary": "Encountered error"
            }
        }), 500


@app.route('/api/npc_memory_summary', methods=['GET'])
def get_memory_summary():
    """Get comprehensive memory summary."""
    try:
        npc_id = request.args.get('npc_id', 'Professor G')
        memory = load_enhanced_memory(npc_id)
        
        return jsonify({
            "npc_id": npc_id,
            "statistics": {
                "total_interactions": memory.total_interactions,
                "total_combat_events": memory.total_combat_events,
                "relationships_tracked": len(memory.relationships)
            },
            "context": memory.get_context_summary(),
            "relationships": {
                name: {
                    "status": rel.get_status(),
                    "sentiment": rel.get_sentiment(),
                    "trust": rel.trust,
                    "fear": rel.fear
                }
                for name, rel in memory.relationships.items()
            },
            "current_threat": memory.current_threat,
            "current_goal": memory.current_goal
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting memory summary: {e}")
        return jsonify({"error": str(e)}), 500


# Add to existing health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "Phase 5+ Enhanced",
        "features": [
            "Contextual memory",
            "Relationship tracking",
            "Combat memory",
            "Social memory",
            "Emotional responses",
            "Revenge mechanics"
        ],
        "npc_count": len(NPC_MEMORIES)
    }), 200


if __name__ == '__main__':
    print("="*70)
    print("🧠 Professor G AI Brain - Phase 5+ ENHANCED")
    print("="*70)
    print("✨ New Features:")
    print("   • Contextual memory (remembers who attacked)")
    print("   • Relationship tracking (trust/fear/affection)")
    print("   • Combat awareness (revenge mechanics)")
    print("   • Social bonding (gift appreciation)")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)