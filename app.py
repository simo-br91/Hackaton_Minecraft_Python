"""
Phase 5: Complete AI Brain with Memory & Emotion Loop
- Persistent memory storage
- Emotion tracking and updates
- State polling endpoint
- Full Gemini API integration
"""

from flask import Flask, request, jsonify
import google.generativeai as genai
from llm_tools.action_schema import MinecraftAction, NPCState, FullAIResponse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv


app = Flask(__name__)

# ===================== CONFIGURATION =====================
# Load environment variables from .env file
load_dotenv()
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MEMORY_FILE = DATA_DIR / "npc_memory.json"
STATE_FILE = DATA_DIR / "npc_state.json"

# Validate API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not set!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# ===================== GLOBAL STATE STORE =====================
NPC_STATES: Dict[str, dict] = {}

def init_npc_state(npc_id: str) -> dict:
    """Initialize or load NPC state."""
    return {
        "npc_id": npc_id,
        "emotion": "neutral",
        "current_objective": "Awaiting player interaction",
        "recent_memory_summary": "Just spawned in the world",
        "x": 0,
        "z": 0,
        "last_updated": datetime.now().isoformat()
    }

# ===================== MEMORY MANAGEMENT =====================
def load_memory() -> Dict[str, List[dict]]:
    """Load all NPC memories from disk."""
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️  Error loading memory: {e}")
        return {}

def save_memory(memory: Dict[str, List[dict]]):
    """Save all NPC memories to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving memory: {e}")

def append_memory(npc_id: str, entry: dict):
    """Append a memory entry for an NPC."""
    memory = load_memory()
    
    if npc_id not in memory:
        memory[npc_id] = []
    
    # Add timestamp
    entry["timestamp"] = datetime.now().isoformat()
    
    memory[npc_id].append(entry)
    
    # Keep last 20 interactions
    memory[npc_id] = memory[npc_id][-20:]
    
    save_memory(memory)
    print(f"📝 Saved memory for {npc_id} ({len(memory[npc_id])} entries)")

def get_memory_summary(npc_id: str, last_n: int = 5) -> str:
    """Get a formatted summary of recent memories."""
    memory = load_memory().get(npc_id, [])
    
    if not memory:
        return "No previous interactions."
    
    recent = memory[-last_n:]
    summary_lines = []
    
    for m in recent:
        timestamp = m.get("timestamp", "unknown")
        player = m.get("player", "unknown")
        message = m.get("message", "")[:50]
        action = m.get("action_type", "unknown")
        emotion = m.get("emotion", "neutral")
        
        summary_lines.append(
            f"[{timestamp}] {player}: '{message}' → {action} (felt: {emotion})"
        )
    
    return "\n".join(summary_lines)

# ===================== STATE MANAGEMENT =====================
def load_npc_state(npc_id: str) -> dict:
    """Load NPC state from memory or create new."""
    if npc_id in NPC_STATES:
        return NPC_STATES[npc_id]
    
    # Try to load from disk
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                all_states = json.load(f)
                if npc_id in all_states:
                    NPC_STATES[npc_id] = all_states[npc_id]
                    return NPC_STATES[npc_id]
    except Exception as e:
        print(f"⚠️  Error loading state: {e}")
    
    # Create new state
    NPC_STATES[npc_id] = init_npc_state(npc_id)
    save_all_states()
    return NPC_STATES[npc_id]

def save_all_states():
    """Save all NPC states to disk."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(NPC_STATES, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving states: {e}")

def update_npc_state(npc_id: str, new_state: dict):
    """Update NPC state and save."""
    if npc_id not in NPC_STATES:
        NPC_STATES[npc_id] = init_npc_state(npc_id)
    
    # Update fields
    NPC_STATES[npc_id].update({
        "emotion": new_state.get("emotion", NPC_STATES[npc_id]["emotion"]),
        "current_objective": new_state.get("current_objective", NPC_STATES[npc_id]["current_objective"]),
        "recent_memory_summary": new_state.get("recent_memory_summary", NPC_STATES[npc_id]["recent_memory_summary"]),
        "x": new_state.get("x", NPC_STATES[npc_id]["x"]),
        "z": new_state.get("z", NPC_STATES[npc_id]["z"]),
        "last_updated": datetime.now().isoformat()
    })
    
    save_all_states()
    print(f"💾 Updated state for {npc_id}: emotion={NPC_STATES[npc_id]['emotion']}")

# ===================== PROMPT BUILDER =====================
def build_system_prompt(npc_id: str, player: str, message: str, current_state: dict) -> str:
    """Build enhanced system prompt with memory and state."""
    memory_summary = get_memory_summary(npc_id, last_n=5)
    
    return f"""You are 'Professor G', a wise, witty, and slightly arrogant Minecraft NPC professor.

PERSONALITY:
- Logical and analytical like a scientist
- Humorous but professional
- Current emotion affects your tone
- You remember past interactions

CURRENT STATE:
- Emotion: {current_state['emotion']}
- Objective: {current_state['current_objective']}
- Recent Memory: {current_state['recent_memory_summary']}
- Position: X={current_state['x']}, Z={current_state['z']}
- Last Updated: {current_state['last_updated']}

RECENT INTERACTIONS:
{memory_summary}

CURRENT SITUATION:
Player "{player}" says: "{message}"

AVAILABLE ACTIONS:
1. respond_chat - Just talk (most common)
2. move_to - Move to coordinates (requires x, z) or player (requires target_name)
3. follow - Follow a player (requires target_name)
4. attack_target - Attack entity (requires target_name: "pig", "zombie", etc.)
5. emote - Show emotion (requires target_name: happy, sad, angry, etc.)
6. give_item - Give item (requires target_name: diamond, apple, etc.)
7. pickup_item - Pick up items (no params)
8. mine_block - Mine block (requires target_name: dirt, stone, etc.)
9. idle - Do nothing

EMOTION GUIDELINES:
- Update emotion based on player interaction
- Emotions: neutral, happy, sad, angry, excited, curious, confused, determined, helpful, generous, thinking
- Emotion should match your response tone

RESPONSE FORMAT:
Return valid JSON with this structure:
{{
  "action": {{
    "action_type": "<action from list above>",
    "chat_response": "<what you say, max 200 chars>",
    "target_name": "<optional: player/entity/block/item>",
    "x": <optional: x coordinate>,
    "z": <optional: z coordinate>
  }},
  "new_state": {{
    "emotion": "<emotion from list above>",
    "current_objective": "<brief description of current goal>",
    "recent_memory_summary": "<one sentence summary>",
    "x": <current or new x>,
    "z": <current or new z>
  }}
}}

IMPORTANT:
- Always return valid JSON
- Update emotion appropriately
- Keep chat_response under 200 characters
- Choose the most fitting action
- Update memory summary to reflect this interaction"""

# ===================== AI INTERACTION =====================
def query_gemini(prompt: str, npc_id: str) -> dict:
    """Query Gemini AI with structured output."""
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 800,
                "response_mime_type": "application/json"
            }
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        print(f"[DEBUG] Gemini response length: {len(text)} chars")
        
        # Parse JSON
        parsed = json.loads(text)
        
        # Validate structure
        if "action" not in parsed or "new_state" not in parsed:
            raise ValueError("Missing required fields in response")
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"[DEBUG] Raw response: {text[:300]}")
        raise
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        raise

# ===================== MAIN ENDPOINT =====================
@app.route('/api/npc_interact', methods=['POST'])
def npc_interact():
    """
    Main endpoint for NPC interactions.
    Handles memory, emotion updates, and action generation.
    """
    try:
        data = request.get_json()
        
        # Extract request data
        npc_id = data.get("npc_id", "Professor G")
        player = data.get("player", "Unknown Player")
        message = data.get("message", "")
        
        if not message:
            return jsonify({"error": "Missing message"}), 400
        
        print(f"\n{'='*70}")
        print(f"📨 [{npc_id}] Interaction from {player}")
        print(f"💬 \"{message}\"")
        print(f"{'='*70}")
        
        # Load current state
        current_state = load_npc_state(npc_id)
        print(f"📊 Current state: emotion={current_state['emotion']}, objective={current_state['current_objective']}")
        
        # Build prompt
        prompt = build_system_prompt(npc_id, player, message, current_state)
        
        # Query AI
        print("🤖 Querying Gemini AI...")
        ai_response = query_gemini(prompt, npc_id)
        
        # Extract action and state
        action = ai_response.get("action", {})
        new_state = ai_response.get("new_state", {})
        
        # Update NPC state
        update_npc_state(npc_id, new_state)
        
        # Save to memory
        memory_entry = {
            "player": player,
            "message": message,
            "action_type": action.get("action_type", "unknown"),
            "chat_response": action.get("chat_response", ""),
            "emotion": new_state.get("emotion", "neutral"),
            "target_name": action.get("target_name"),
            "coordinates": f"({action.get('x')}, {action.get('z')})" if action.get('x') else None
        }
        append_memory(npc_id, memory_entry)
        
        # Log response
        print(f"✅ Action: {action.get('action_type')}")
        print(f"💭 Response: \"{action.get('chat_response', '')}\"")
        print(f"😊 New emotion: {new_state.get('emotion')}")
        print(f"{'='*70}\n")
        
        return jsonify(ai_response), 200
        
    except Exception as e:
        print(f"❌ Error in npc_interact: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        return jsonify({
            "action": {
                "action_type": "respond_chat",
                "chat_response": "My circuits are scrambled... *adjusts glasses*"
            },
            "new_state": {
                "emotion": "confused",
                "current_objective": "Recovering from error",
                "recent_memory_summary": "Encountered a technical difficulty"
            }
        }), 500

# ===================== STATE POLLING ENDPOINT =====================
@app.route('/api/npc_state', methods=['GET'])
def get_npc_state():
    """
    Get current NPC state.
    Query params: npc_id (optional, defaults to "Professor G")
    """
    try:
        npc_id = request.args.get('npc_id', 'Professor G')
        
        # Load state
        state = load_npc_state(npc_id)
        
        # Add memory count
        memory = load_memory().get(npc_id, [])
        state["memory_count"] = len(memory)
        
        return jsonify(state), 200
        
    except Exception as e:
        print(f"❌ Error in get_npc_state: {e}")
        return jsonify({"error": str(e)}), 500

# ===================== MEMORY ENDPOINT =====================
@app.route('/api/npc_memory', methods=['GET'])
def get_npc_memory():
    """
    Get NPC memory history.
    Query params: 
    - npc_id (optional)
    - limit (optional, default 10)
    """
    try:
        npc_id = request.args.get('npc_id', 'Professor G')
        limit = int(request.args.get('limit', 10))
        
        memory = load_memory().get(npc_id, [])
        
        # Return last N entries
        recent_memory = memory[-limit:] if len(memory) > limit else memory
        
        return jsonify({
            "npc_id": npc_id,
            "total_memories": len(memory),
            "returned": len(recent_memory),
            "memories": recent_memory
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_npc_memory: {e}")
        return jsonify({"error": str(e)}), 500

# ===================== HEALTH CHECK =====================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "version": "Phase 5",
        "features": [
            "Memory persistence",
            "Emotion tracking",
            "State polling",
            "Gemini AI integration"
        ],
        "npc_count": len(NPC_STATES),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        "service": "Professor G AI Brain",
        "version": "Phase 5 - Complete",
        "endpoints": {
            "/api/npc_interact": "POST - Main interaction (player → AI → action)",
            "/api/npc_state": "GET - Get current NPC state",
            "/api/npc_memory": "GET - Get NPC memory history",
            "/health": "GET - Health check"
        }
    }), 200

# ===================== INITIALIZATION =====================
def initialize():
    """Initialize server on startup."""
    print("=" * 70)
    print("🧠 Professor G AI Brain - Phase 5 Complete")
    print("=" * 70)
    print("✨ Features:")
    print("   • Persistent memory storage")
    print("   • Emotion tracking & updates")
    print("   • State polling endpoint")
    print("   • Full Gemini AI integration")
    print("=" * 70)
    print(f"📁 Data directory: {DATA_DIR.absolute()}")
    print(f"📝 Memory file: {MEMORY_FILE}")
    print(f"💾 State file: {STATE_FILE}")
    print("=" * 70)
    print("🌐 Listening on: http://0.0.0.0:5000")
    print("=" * 70)
    
    # Load existing states
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                loaded_states = json.load(f)
                NPC_STATES.update(loaded_states)
                print(f"✅ Loaded {len(loaded_states)} NPC state(s)")
    except Exception as e:
        print(f"⚠️  Could not load states: {e}")
    
    print("=" * 70)
    print("✅ Server ready!")
    print("=" * 70)

# ===================== MAIN =====================
if __name__ == '__main__':
    initialize()
    app.run(host="0.0.0.0", port=5000, debug=True)