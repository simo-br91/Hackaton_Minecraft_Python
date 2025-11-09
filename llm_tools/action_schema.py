"""
Pydantic models for NPC action schema and state management.
Defines the contract between Minecraft Java mod and Python AI backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class Action(BaseModel):
    """Represents an action the NPC should take in Minecraft."""
    action_type: Literal[
        "move_to",
        "mine_block",
        "attack",
        "collect_item",
        "respond_chat",
        "emote",
        "follow_player",
        "idle"
    ] = Field(..., description="Type of action the NPC should take")
    
    target_name: Optional[str] = Field(
        None, 
        description="Target block, mob, or item name (e.g., 'oak_log', 'pig', 'diamond')"
    )
    x: Optional[int] = Field(None, description="X coordinate for movement or action")
    z: Optional[int] = Field(None, description="Z coordinate for movement or action")
    chat_response: Optional[str] = Field(
        None, 
        description="What the NPC should say in chat",
        max_length=256  # Minecraft chat limit
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "respond_chat",
                "chat_response": "Hello there, adventurer!"
            }
        }


class NPCState(BaseModel):
    """Represents the current state of an NPC."""
    emotion: Literal["happy", "neutral", "angry", "sad", "excited", "curious"] = Field(
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
                "current_objective": "Helping the player",
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
                    "chat_response": "I'd be happy to help!"
                },
                "new_state": {
                    "emotion": "happy",
                    "current_objective": "Assisting player",
                    "x": 100,
                    "z": -50
                }
            }
        }