"""
Phase 5+: Complete Action Schema with Memory & State + Potion System
Pydantic models for structured AI responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class MinecraftAction(BaseModel):
    """Action the NPC should perform in Minecraft."""
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
        "drink_potion",
        "idle"
    ] = Field(..., description="Type of action to perform")
    
    target_name: Optional[str] = Field(
        None,
        description="Target player, entity, block, item name, or potion type"
    )
    
    x: Optional[int] = Field(
        None,
        description="X coordinate for movement"
    )
    
    z: Optional[int] = Field(
        None,
        description="Z coordinate for movement"
    )
    
    chat_response: Optional[str] = Field(
        None,
        max_length=256,
        description="What the NPC says in chat"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action_type": "respond_chat",
                    "chat_response": "Hello adventurer!"
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
                    "action_type": "drink_potion",
                    "chat_response": "*drinks healing potion* That's better!",
                    "target_name": "healing"
                }
            ]
        }


class NPCState(BaseModel):
    """Current state of the NPC."""
    emotion: Literal[
        "neutral",
        "happy",
        "sad",
        "angry",
        "excited",
        "curious",
        "confused",
        "determined",
        "helpful",
        "generous",
        "thinking",
        "calm",
        "nervous",
        "afraid",
        "hurt",
        "relieved"
    ] = Field(
        default="neutral",
        description="Current emotional state"
    )
    
    current_objective: str = Field(
        ...,
        max_length=200,
        description="Current goal or task the NPC is pursuing"
    )
    
    recent_memory_summary: str = Field(
        ...,
        max_length=300,
        description="Brief summary of recent interaction"
    )
    
    x: int = Field(
        default=0,
        description="Current X position"
    )
    
    z: int = Field(
        default=0,
        description="Current Z position"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "emotion": "helpful",
                "current_objective": "Assisting player with mining",
                "recent_memory_summary": "Player asked for help finding diamonds",
                "x": 100,
                "z": -50
            }
        }


class FullAIResponse(BaseModel):
    """Complete AI response with action and new state."""
    action: MinecraftAction
    new_state: NPCState
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": {
                    "action_type": "drink_potion",
                    "chat_response": "*drinks healing potion* Much better!",
                    "target_name": "healing"
                },
                "new_state": {
                    "emotion": "relieved",
                    "current_objective": "Recovering from injuries",
                    "recent_memory_summary": "Drank healing potion after being hurt",
                    "x": 100,
                    "z": 200
                }
            }
        }