"""
Phase 2: AI Brain - Flask server with Gemini API integration
Handles NPC personality, memory, and action generation for Minecraft mod.
REQUIRES Gemini API - No fallback mode.
"""

from flask import Flask, request, jsonify
import google.generativeai as genai
from llm_tools.action_schema import Action, NPCState, NPCResponse
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ===================== CONFIG =====================
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MEMORY_FILE = DATA_DIR / "npc_memory.json"
PERSONALITY_FILE = DATA_DIR / "npc_personality.json"

# Validate API key - REQUIRED
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("=" * 60)
    print("❌ ERROR: GEMINI_API_KEY not set!")
    print("=" * 60)
    print("This server REQUIRES a Gemini API key to function.")
    print("Get your key from: https://makersuite.google.com/app/apikey")
    print("")
    print("Then set it with:")
    print("  export GEMINI_API_KEY='your_key_here'")
    print("or create a .env file with:")
    print("  GEMINI_API_KEY=your_key_here")
    print("=" * 60)
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Default personality settings
DEFAULT_PERSONALITY = {
    "name": "Professor G",
    "tone": "helpful and knowledgeable professor",
    "traits": ["curious", "patient", "scholarly", "adventurous"],
    "emotion": "neutral",
    "background": "A wise professor who teaches adventurers about the world of Minecraft. Loves exploring, teaching, and helping players on their journeys."
}

# ===================== FILE INITIALIZATION =====================
def init_files():
    """Initialize memory and personality files if they don't exist."""
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, "w") as f:
            json.dump({}, f, indent=2)
        print(f"✅ Created memory file: {MEMORY_FILE}")
    
    if not PERSONALITY_FILE.exists():
        with open(PERSONALITY_FILE, "w") as f:
            json.dump({"Professor G": DEFAULT_PERSONALITY}, f, indent=2)
        print(f"✅ Created personality file: {PERSONALITY_FILE}")

init_files()

# ===================== MEMORY HANDLING =====================
def load_memory():
    """Load NPC memory from file."""
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️ Error loading memory: {e}. Returning empty memory.")
        return {}

def save_memory(memory):
    """Save NPC memory to file."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving memory: {e}")

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
        response = m.get('response', '')
        summary.append(f"{player}: '{message[:40]}...' -> You responded: '{response[:40]}...'")
    
    return "\n".join(summary)

def load_personality(npc_id):
    """Load personality configuration for an NPC."""
    try:
        with open(PERSONALITY_FILE, "r") as f:
            personalities = json.load(f)
            return personalities.get(npc_id, DEFAULT_PERSONALITY)
    except Exception as e:
        print(f"⚠️ Error loading personality: {e}. Using default.")
        return DEFAULT_PERSONALITY

# ===================== PROMPT BUILDER =====================
def build_gemini_prompt(npc_name, player, message, memory_summary, personality, context=None):
    """Build a structured prompt for Gemini API with enhanced action guidance."""
    context_str = f"\n\nCurrent game context: {context}" if context else ""
    
    return f"""You are {npc_name}, an NPC in Minecraft with the following personality:
- Name: {personality.get('name', npc_name)}
- Tone: {personality['tone']}
- Traits: {', '.join(personality['traits'])}
- Current emotion: {personality['emotion']}
- Background: {personality.get('background', 'A friendly NPC')}

Recent conversation history:
{memory_summary}
{context_str}

Player "{player}" said to you: "{message}"

You must respond with a JSON object in EXACTLY this format (no markdown, no code blocks):
{{
  "action": {{
    "action_type": "respond_chat",
    "target_name": null,
    "x": null,
    "z": null,
    "chat_response": "Your natural response here"
  }},
  "new_state": {{
    "emotion": "emotion_here",
    "current_objective": "what you're trying to do",
    "recent_memory_summary": "brief summary of this interaction",
    "x": 0,
    "z": 0
  }}
}}

IMPORTANT ACTION TYPES AND WHEN TO USE THEM:

1. "respond_chat" - MOST COMMON
   - Use for normal conversation, questions, greetings
   - Just talking, no physical action needed
   - Example: Player says "Hello!" -> respond_chat with friendly greeting

2. "move_to" - When player asks you to GO somewhere
   - Requires x and z coordinates (integers)
   - Keywords: "go to", "move to", "walk to", "head to"
   - Example: "Go to 100, -50" -> {{"action_type": "move_to", "x": 100, "z": -50, "chat_response": "On my way!"}}

3. "follow" or "follow_player" - When asked to FOLLOW
   - Set target_name to player name if specified, or "nearest"
   - Keywords: "follow me", "come with me", "tag along"
   - Example: "Follow me" -> {{"action_type": "follow", "target_name": "{player}", "chat_response": "I'll follow you!"}}

4. "attack_target" or "attack" - When asked to ATTACK
   - Set target_name to mob type (pig, zombie, skeleton) or "nearest"
   - Keywords: "attack", "kill", "fight", "defeat"
   - Example: "Attack that pig" -> {{"action_type": "attack_target", "target_name": "pig", "chat_response": "Engaging target!"}}

5. "mine_block" - When asked to MINE or BREAK blocks
   - Set target_name to block type (oak_log, stone, diamond_ore)
   - Keywords: "mine", "break", "chop", "gather"
   - Example: "Chop that tree" -> {{"action_type": "mine_block", "target_name": "oak_log", "chat_response": "Chopping wood!"}}

6. "emote" - Show EMOTION or GESTURE
   - Set target_name to emotion (happy, sad, angry, confused, excited, thinking)
   - Keywords: based on emotional context
   - Example: After helping -> {{"action_type": "emote", "target_name": "happy", "chat_response": "*smiles*"}}

7. "give_item" - Give items to player
   - Set target_name to item type (diamond, bread, sword)
   - Keywords: "give", "here take this", "have"

8. "pickup_item" - Pick up items from ground
   - Keywords: "pick up", "grab", "collect"

9. "idle" - Do nothing, just exist
   - Use when conversation ends or no action needed

DECISION MAKING:
- If player asks a QUESTION -> respond_chat
- If player asks you to DO something physical -> choose appropriate action
- If player is chatting casually -> respond_chat
- ALWAYS include a natural chat_response that matches the action
- Keep chat_response under 200 characters
- Match your personality in all responses

EMOTION CHOICES:
happy, neutral, angry, sad, excited, curious, confused, determined, helpful, generous, thinking

Choose emotion based on:
- Your personality traits
- The player's message tone
- What action you're taking
- Previous conversation context

Now respond to the player's message!"""

# ===================== GEMINI API CALL =====================
def query_gemini(prompt, max_retries=2):
    """Query Gemini API and return structured response with retry logic."""
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 800,
                    "top_p": 0.95
                }
            )
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            print(f"[DEBUG] Gemini raw response (attempt {attempt + 1}):")
            print(text[:500])  # Print first 500 chars for debugging
            
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
            
            print(f"✅ Successfully parsed response:")
            print(f"   Action: {validated.action.action_type}")
            print(f"   Chat: {validated.action.chat_response}")
            print(f"   Emotion: {validated.new_state.emotion}")
            
            return validated.model_dump()
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("   Retrying with adjusted prompt...")
                continue
            raise
            
        except Exception as e:
            print(f"❌ Gemini query failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("   Retrying...")
                continue
            raise
    
    raise Exception("Failed after all retry attempts")

# ===================== MAIN ENDPOINT =====================
@app.route("/api/npc_interact", methods=["POST"])
def npc_interact():
    """Main endpoint for NPC interactions - API ONLY."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' field"}), 400
        
        npc_id = data.get("npc_id", "Professor G")
        player = data.get("player", "Unknown Player")
        message = data.get("message", "")
        context = data.get("context")  # Optional game context
        
        print("=" * 60)
        print(f"[{npc_id}] 💬 {player}: {message}")
        print("=" * 60)
        
        # Load personality and memory
        personality = load_personality(npc_id)
        memory_summary = summarize_memory(npc_id)
        
        # Build prompt and query Gemini
        prompt = build_gemini_prompt(npc_id, player, message, memory_summary, personality, context)
        
        try:
            result = query_gemini(prompt)
        except Exception as e:
            print(f"❌ API call failed: {e}")
            return jsonify({
                "error": "Gemini API error",
                "details": str(e),
                "message": "The AI brain is not responding. Check your API key and connection."
            }), 500
        
        # Save to memory
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "player": player,
            "message": message,
            "response": result["action"].get("chat_response", ""),
            "action": result["action"].get("action_type", ""),
            "emotion": result["new_state"]["emotion"]
        }
        append_memory(npc_id, memory_entry)
        
        print(f"✅ [{npc_id}] Response: {result['action'].get('chat_response', 'No chat')}")
        print(f"   Action: {result['action'].get('action_type', 'none')}")
        print("=" * 60)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

# ===================== HEALTH CHECK =====================
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify server and API are ready."""
    try:
        # Test Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        test_response = model.generate_content("Say 'OK' if you're working")
        api_working = "ok" in test_response.text.lower()
        
        return jsonify({
            "status": "healthy",
            "gemini_available": api_working,
            "api_key_set": bool(GEMINI_API_KEY),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "gemini_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API info."""
    return jsonify({
        "service": "Professor G AI Brain",
        "version": "2.0.0-api-only",
        "mode": "Gemini API Required",
        "endpoints": {
            "/api/npc_interact": "POST - Main NPC interaction endpoint",
            "/health": "GET - Health check"
        }
    }), 200

# ===================== MAIN =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Professor G AI Brain - API-Only Mode")
    print("=" * 60)
    print("✅ Gemini API: Enabled and Required")
    print(f"✅ Memory file: {MEMORY_FILE}")
    print(f"✅ Personality file: {PERSONALITY_FILE}")
    print(f"✅ Listening on: http://0.0.0.0:5000")
    print("=" * 60)
    print("\n💡 TIP: Customize personality in data/npc_personality.json")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=5000, debug=True)