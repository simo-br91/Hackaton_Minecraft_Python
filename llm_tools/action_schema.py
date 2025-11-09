"""
Pydantic models for NPC action schema and state management.
Defines the contract between Minecraft Java mod and Python AI backend.
Updated for Phase 4 with all action types.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class Action(BaseModel):
    """Represents an action the NPC should take in Minecraft."""
    action_type: Literal[
        "say",
        "respond_chat",
        "move_to",
        "follow",
        "follow_player",
        "attack_target",
        "attack",
        "emote",
        "give_item",
        "pickup_item",
        "mine_block",
        "idle"
    ] = Field(..., description="Type of action the NPC should take")
    
    target_name: Optional[str] = Field(
        None, 
        description="Target player, entity, block, or item name (e.g., 'Steve', 'pig', 'oak_log', 'diamond')"
    )
    x: Optional[int] = Field(None, description="X coordinate for movement")
    z: Optional[int] = Field(None, description="Z coordinate for movement")
    chat_response: Optional[str] = Field(
        None, 
        description="What the NPC should say in chat",
        max_length=256
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action_type": "respond_chat",
                    "chat_response": "Hello there, adventurer!"
                },
                {
                    "action_type": "move_to",
                    "chat_response": "On my way!",
                    "x": 100,
                    "z": 200
                },
                {
                    "action_type": "follow",
                    "chat_response": "I'll follow you!",
                    "target_name": "Steve"
                },
                {
                    "action_type": "emote",
                    "chat_response": "*smiles warmly*",
                    "target_name": "happy"
                },
                {
                    "action_type": "give_item",
                    "chat_response": "Here, take this!",
                    "target_name": "diamond"
                }
            ]
        }


class NPCState(BaseModel):
    """Represents the current state of an NPC."""
    emotion: Literal[
        "happy", 
        "neutral", 
        "angry", 
        "sad", 
        "excited", 
        "curious",
        "confused",
        "determined",
        "helpful",
        "generous",
        "thinking"
    ] = Field(
        default="neutral",
        description="Current emotional state"
    )
    current_objective: Optional[str] = Field(
        None,
        description="Current goal or objective the NPC is pursuing"
    )
    recent_memory_summary: Optional[str] = Field(
        None,
        description="Brief summary of recent interactions"
    )
    x: int = Field(default=0, description="Current X position")
    z: int = Field(default=0, description="Current Z position")

    class Config:
        json_schema_extra = {
            "example": {
                "emotion": "happy",
                "current_objective": "Helping the player find diamonds",
                "recent_memory_summary": "Player asked for help finding resources",
                "x": 100,
                "z": -50
            }
        }


class NPCResponse(BaseModel):
    """Complete response from AI backend to Minecraft mod."""
    action: Action
    new_state: NPCState
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": {
                    "action_type": "respond_chat",
                    "chat_response": "I'd be happy to help you find diamonds!"
                },
                "new_state": {
                    "emotion": "helpful",
                    "current_objective": "Assisting player with mining",
                    "recent_memory_summary": "Player requested help with diamonds",
                    "x": 100,
                    "z": -50
                }
            }
        }