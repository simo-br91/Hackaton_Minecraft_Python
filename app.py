"""
Phase 2: AI Brain - Flask server with Gemini API integration
Handles NPC personality, memory, and action generation for Minecraft mod.
"""

from flask import Flask, request, jsonify
import google.generativeai as genai
from llm_tools.action_schema import Action, NPCState, NPCResponse
import json
import os
from datetime import datetime
from pathlib import Path

# ===================== CONFIG =====================
app = Flask(__name__)

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MEMORY_FILE = DATA_DIR / "npc_memory.json"
PERSONALITY_FILE = DATA_DIR / "npc_personality.json"

# Validate API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set. Using fallback mode only.")
    USE_GEMINI = False
else:
    genai.configure(api_key=GEMINI_API_KEY)
    USE_GEMINI = True

# Default personality settings
DEFAULT_PERSONALITY = {
    "tone": "helpful and knowledgeable professor",
    "traits": ["curious", "patient", "scholarly"],
    "emotion": "neutral",
    "background": "A wise professor who teaches adventurers about the world"
}

# ===================== FILE INITIALIZATION =====================
def init_files():
    """Initialize memory and personality files if they don't exist."""
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, "w") as f:
            json.dump({}, f, indent=2)
        print(f"Created memory file: {MEMORY_FILE}")
    
    if not PERSONALITY_FILE.exists():
        with open(PERSONALITY_FILE, "w") as f:
            json.dump({"Professor G": DEFAULT_PERSONALITY}, f, indent=2)
        print(f"Created personality file: {PERSONALITY_FILE}")

init_files()

# ===================== MEMORY HANDLING =====================
def load_memory():
    """Load NPC memory from file."""
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading memory: {e}. Returning empty memory.")
        return {}

def save_memory(memory):
    """Save NPC memory to file."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def append_memory(npc_id, entry):
    """Append a new memory entry for an NPC."""
    memory = load_memory()
    if npc_id not in memory:
        memory[npc_id] = []
    
    memory[npc_id].append(entry)
    # Keep only last 10 interactions to prevent memory bloat
    memory[npc_id] = memory[npc_id][-10:]
    save_memory(memory)

def summarize_memory(npc_id):
    """Get a brief summary of recent interactions."""
    memory = load_memory().get(npc_id, [])
    if not memory:
        return "No previous interactions."
    
    # Format last 5 interactions
    recent = memory[-5:]
    summary = []
    for m in recent:
        timestamp = m.get('timestamp', 'unknown time')
        player = m.get('player', 'unknown')
        message = m.get('message', '')
        summary.append(f"{player} at {timestamp}: {message[:50]}")
    
    return " | ".join(summary)

def load_personality(npc_id):
    """Load personality configuration for an NPC."""
    try:
        with open(PERSONALITY_FILE, "r") as f:
            personalities = json.load(f)
            return personalities.get(npc_id, DEFAULT_PERSONALITY)
    except Exception as e:
        print(f"Error loading personality: {e}. Using default.")
        return DEFAULT_PERSONALITY

# ===================== PROMPT BUILDER =====================
def build_gemini_prompt(npc_name, player, message, memory_summary, personality, context=None):
    """Build a structured prompt for Gemini API."""
    context_str = f"\n\nCurrent context: {context}" if context else ""
    
    return f"""You are {npc_name}, an NPC in Minecraft with the following personality:
- Tone: {personality['tone']}
- Traits: {', '.join(personality['traits'])}
- Current emotion: {personality['emotion']}
- Background: {personality.get('background', 'A friendly NPC')}

Recent memory of interactions:
{memory_summary}
{context_str}

Player "{player}" said to you: "{message}"

Respond with a JSON object in EXACTLY this format (no markdown, no extra text):
{{
  "action": {{
    "action_type": "respond_chat",
    "target_name": null,
    "x": null,
    "z": null,
    "chat_response": "Your response here (max 200 chars)"
  }},
  "new_state": {{
    "emotion": "happy|neutral|angry|sad|excited|curious",
    "current_objective": "Brief description of current goal",
    "recent_memory_summary": "One sentence summary of this interaction",
    "x": 0,
    "z": 0
  }}
}}

Action types you can use:
- respond_chat: Just talk (most common)
- move_to: Move to coordinates (requires x, z)
- follow_player: Follow the player
- mine_block: Mine a block (requires target_name like "oak_log")
- attack: Attack something (requires target_name like "zombie")
- emote: Show emotion (no chat needed)
- idle: Do nothing

Keep chat_response under 200 characters and match your personality!"""

# ===================== GEMINI API CALL =====================
def query_gemini(prompt):
    """Query Gemini API and return structured response."""
    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"temperature": 0.7, "max_output_tokens": 500}
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        
        json_str = text[start:end]
        parsed = json.loads(json_str)
        
        # Validate with Pydantic
        validated = NPCResponse(**parsed)
        return validated.model_dump()
        
    except Exception as e:
        print(f"[ERROR] Gemini query failed: {e}")
        print(f"[DEBUG] Raw response: {text if 'text' in locals() else 'No response'}")
        return None

# ===================== FALLBACK HANDLER =====================
def generate_fallback_response(message, npc_name):
    """Generate a deterministic fallback response when AI fails."""
    message_lower = message.lower()
    
    # Simple keyword matching
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        chat_response = f"Hello! I'm {npc_name}. How can I help you today?"
        emotion = "happy"
    elif any(word in message_lower for word in ["help", "quest", "task"]):
        chat_response = "I'm here to assist you on your adventure!"
        emotion = "neutral"
    elif any(word in message_lower for word in ["bye", "goodbye"]):
        chat_response = "Farewell, adventurer! Safe travels!"
        emotion = "neutral"
    else:
        chat_response = "I'm listening... tell me more."
        emotion = "curious"
    
    return NPCResponse(
        action=Action(
            action_type="respond_chat",
            chat_response=chat_response
        ),
        new_state=NPCState(
            emotion=emotion,
            current_objective="Conversing with player",
            recent_memory_summary=f"Player said: {message[:50]}"
        )
    ).model_dump()

# ===================== MAIN ENDPOINT =====================
@app.route("/api/npc_interact", methods=["POST"])
def npc_interact():
    """Main endpoint for NPC interactions."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' field"}), 400
        
        npc_id = data.get("npc_id", "Professor G")
        player = data.get("player", "Unknown Player")
        message = data.get("message", "")
        context = data.get("context")  # Optional game context
        
        print(f"[{npc_id}] Received from {player}: {message}")
        
        # Load personality and memory
        personality = load_personality(npc_id)
        memory_summary = summarize_memory(npc_id)
        
        # Try Gemini API if available
        result = None
        if USE_GEMINI:
            prompt = build_gemini_prompt(npc_id, player, message, memory_summary, personality, context)
            result = query_gemini(prompt)
        
        # Use fallback if Gemini failed or unavailable
        if result is None:
            print(f"[{npc_id}] Using fallback response")
            result = generate_fallback_response(message, npc_name=npc_id)
        
        # Save to memory
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "player": player,
            "message": message,
            "response": result["action"].get("chat_response", ""),
            "emotion": result["new_state"]["emotion"]
        }
        append_memory(npc_id, memory_entry)
        
        print(f"[{npc_id}] Response: {result['action'].get('chat_response', 'No chat')}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[ERROR] Endpoint error: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

# ===================== HEALTH CHECK =====================
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify server is running."""
    return jsonify({
        "status": "healthy",
        "gemini_available": USE_GEMINI,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API info."""
    return jsonify({
        "service": "Professor G AI Brain",
        "version": "1.0.0",
        "endpoints": {
            "/api/npc_interact": "POST - Main NPC interaction endpoint",
            "/health": "GET - Health check"
        }
    }), 200

# ===================== MAIN =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Professor G AI Brain - Phase 2")
    print("=" * 60)
    print(f"Gemini API: {'✅ Enabled' if USE_GEMINI else '⚠️  Fallback mode only'}")
    print(f"Memory file: {MEMORY_FILE}")
    print(f"Personality file: {PERSONALITY_FILE}")
    print(f"Listening on: http://0.0.0.0:5000")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=5000, debug=True)