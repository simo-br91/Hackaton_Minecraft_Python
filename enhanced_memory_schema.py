"""
Enhanced Memory Schema for Phase 5+
Adds contextual awareness, relationships, and event tracking
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class CombatEvent(BaseModel):
    """Record of combat interaction."""
    event_type: Literal["attacked_by", "attacked", "witnessed_death"]
    entity_name: str
    entity_type: str  # "player", "mob", "npc"
    damage: Optional[float] = None
    weapon: Optional[str] = None
    location: Optional[str] = None  # "x,y,z"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SocialEvent(BaseModel):
    """Record of social interaction."""
    event_type: Literal["chat", "gift_received", "gift_given", "helped", "ignored"]
    entity_name: str
    message: Optional[str] = None
    item: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class EnvironmentalEvent(BaseModel):
    """Record of environmental observation."""
    event_type: Literal["block_broken", "block_placed", "explosion", "mob_spawned"]
    description: str
    location: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Relationship(BaseModel):
    """Relationship status with an entity."""
    entity_name: str
    entity_type: str  # "player", "mob"
    trust: int = Field(default=0, ge=-100, le=100)  # -100 (enemy) to +100 (best friend)
    fear: int = Field(default=0, ge=0, le=100)  # 0 (fearless) to 100 (terrified)
    affection: int = Field(default=0, ge=0, le=100)  # 0 (indifferent) to 100 (loves)
    
    # Combat stats
    times_attacked_by: int = 0
    times_attacked: int = 0
    total_damage_received: float = 0.0
    total_damage_dealt: float = 0.0
    
    # Social stats
    gifts_received: int = 0
    gifts_given: int = 0
    times_helped: int = 0
    
    last_interaction: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def get_status(self) -> str:
        """Get relationship status description."""
        if self.trust < -50:
            return "enemy"
        elif self.trust < -20:
            return "hostile"
        elif self.trust < 20:
            return "neutral"
        elif self.trust < 50:
            return "friendly"
        else:
            return "trusted_friend"
    
    def get_sentiment(self) -> str:
        """Get emotional sentiment."""
        if self.fear > 60:
            return "terrified"
        elif self.fear > 30:
            return "afraid"
        elif self.affection > 60:
            return "loves"
        elif self.affection > 30:
            return "likes"
        elif self.trust < -50:
            return "hates"
        else:
            return "indifferent"


class EnhancedMemoryStore(BaseModel):
    """Complete memory storage for an NPC."""
    npc_id: str
    
    # Event memories (keep last 50 of each)
    combat_events: List[CombatEvent] = []
    social_events: List[SocialEvent] = []
    environmental_events: List[EnvironmentalEvent] = []
    
    # Relationship tracking
    relationships: dict[str, Relationship] = {}
    
    # Current context
    current_threat: Optional[str] = None  # Who is NPC currently afraid of/fighting
    current_ally: Optional[str] = None  # Who is NPC currently helping
    current_goal: str = "idle"
    
    # Statistics
    total_interactions: int = 0
    total_combat_events: int = 0
    creation_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def add_combat_event(self, event: CombatEvent):
        """Add combat event and update relationships."""
        self.combat_events.append(event)
        self.combat_events = self.combat_events[-50:]  # Keep last 50
        self.total_combat_events += 1
        
        # Update relationship
        if event.entity_name not in self.relationships:
            self.relationships[event.entity_name] = Relationship(
                entity_name=event.entity_name,
                entity_type=event.entity_type
            )
        
        rel = self.relationships[event.entity_name]
        
        if event.event_type == "attacked_by":
            rel.times_attacked_by += 1
            rel.total_damage_received += event.damage or 0
            rel.trust -= 15  # Major trust loss
            rel.fear += 10  # Increase fear
            rel.affection -= 5
            
            # If player attacks multiple times, become enemy
            if rel.times_attacked_by >= 3:
                rel.trust = min(rel.trust, -40)
                self.current_threat = event.entity_name
                
        elif event.event_type == "attacked":
            rel.times_attacked += 1
            rel.total_damage_dealt += event.damage or 0
            
        elif event.event_type == "witnessed_death":
            rel.fear += 5  # Fear increases seeing death
        
        # Clamp values
        rel.trust = max(-100, min(100, rel.trust))
        rel.fear = max(0, min(100, rel.fear))
        rel.affection = max(0, min(100, rel.affection))
        rel.last_interaction = datetime.now().isoformat()
    
    def add_social_event(self, event: SocialEvent):
        """Add social event and update relationships."""
        self.social_events.append(event)
        self.social_events = self.social_events[-50:]
        self.total_interactions += 1
        
        if event.entity_name not in self.relationships:
            self.relationships[event.entity_name] = Relationship(
                entity_name=event.entity_name,
                entity_type="player"
            )
        
        rel = self.relationships[event.entity_name]
        
        if event.event_type == "gift_received":
            rel.gifts_received += 1
            rel.trust += 10
            rel.affection += 15
            rel.fear = max(0, rel.fear - 5)
            
        elif event.event_type == "gift_given":
            rel.gifts_given += 1
            
        elif event.event_type == "helped":
            rel.times_helped += 1
            rel.trust += 5
            rel.affection += 5
        
        # Clamp values
        rel.trust = max(-100, min(100, rel.trust))
        rel.fear = max(0, min(100, rel.fear))
        rel.affection = max(0, min(100, rel.affection))
        rel.last_interaction = datetime.now().isoformat()
    
    def get_relationship_summary(self, entity_name: str) -> str:
        """Get human-readable relationship summary."""
        if entity_name not in self.relationships:
            return f"No prior relationship with {entity_name}"
        
        rel = self.relationships[entity_name]
        status = rel.get_status()
        sentiment = rel.get_sentiment()
        
        summary = f"{entity_name} ({status}, {sentiment}): "
        summary += f"Trust={rel.trust}, Fear={rel.fear}, Affection={rel.affection}"
        
        if rel.times_attacked_by > 0:
            summary += f" | Attacked me {rel.times_attacked_by}x (took {rel.total_damage_received:.1f} damage)"
        
        if rel.gifts_received > 0:
            summary += f" | Gave me {rel.gifts_received} gift(s)"
        
        return summary
    
    def get_context_summary(self) -> str:
        """Get current contextual summary for AI prompt."""
        lines = ["=== CURRENT CONTEXT ==="]
        
        # Active threat
        if self.current_threat and self.current_threat in self.relationships:
            rel = self.relationships[self.current_threat]
            lines.append(f"⚔️ THREAT: {self.current_threat} is hostile! (Attacked {rel.times_attacked_by}x, Trust={rel.trust})")
        
        # Recent combat
        recent_combat = [e for e in self.combat_events[-5:] if e.event_type == "attacked_by"]
        if recent_combat:
            lines.append(f"⚠️ Recent attacks: {len(recent_combat)} in last 5 events")
        
        # Relationships
        enemies = [name for name, rel in self.relationships.items() if rel.trust < -30]
        friends = [name for name, rel in self.relationships.items() if rel.trust > 40]
        
        if enemies:
            lines.append(f"😠 Enemies: {', '.join(enemies)}")
        if friends:
            lines.append(f"😊 Friends: {', '.join(friends)}")
        
        # Recent events summary
        if len(self.combat_events) > 0:
            lines.append(f"Combat history: {len(self.combat_events)} events")
        if len(self.social_events) > 0:
            lines.append(f"Social history: {len(self.social_events)} events")
        
        return "\n".join(lines)
    
    def should_be_aggressive(self, entity_name: str) -> bool:
        """Determine if NPC should be aggressive toward entity."""
        if entity_name not in self.relationships:
            return False
        
        rel = self.relationships[entity_name]
        
        # Attack if:
        # - Trust is very low (< -30) AND
        # - Fear is not too high (< 70) AND
        # - They attacked us multiple times
        return (rel.trust < -30 and 
                rel.fear < 70 and 
                rel.times_attacked_by >= 2)
    
    def should_avoid(self, entity_name: str) -> bool:
        """Determine if NPC should avoid entity."""
        if entity_name not in self.relationships:
            return False
        
        rel = self.relationships[entity_name]
        
        # Avoid if:
        # - Fear is high (> 50) OR
        # - Trust is low and they're much stronger (dealt lots of damage)
        return (rel.fear > 50 or 
                (rel.trust < -20 and rel.total_damage_received > 15))


# Example usage functions
def example_combat_scenario():
    """Example: Player attacks NPC multiple times."""
    memory = EnhancedMemoryStore(npc_id="Professor G")
    
    # Player attacks once
    memory.add_combat_event(CombatEvent(
        event_type="attacked_by",
        entity_name="Steve",
        entity_type="player",
        damage=3.0,
        weapon="wooden_sword"
    ))
    
    print("After 1 attack:")
    print(memory.get_relationship_summary("Steve"))
    print(f"Should attack? {memory.should_be_aggressive('Steve')}")
    print()
    
    # Player attacks twice more
    for i in range(2):
        memory.add_combat_event(CombatEvent(
            event_type="attacked_by",
            entity_name="Steve",
            entity_type="player",
            damage=4.0,
            weapon="stone_sword"
        ))
    
    print("After 3 attacks:")
    print(memory.get_relationship_summary("Steve"))
    print(f"Should attack? {memory.should_be_aggressive('Steve')}")
    print(f"Should avoid? {memory.should_avoid('Steve')}")
    print()
    print(memory.get_context_summary())


def example_social_scenario():
    """Example: Player gives gifts."""
    memory = EnhancedMemoryStore(npc_id="Professor G")
    
    # Player gives diamond
    memory.add_social_event(SocialEvent(
        event_type="gift_received",
        entity_name="Alex",
        item="diamond"
    ))
    
    # Player gives more gifts
    memory.add_social_event(SocialEvent(
        event_type="gift_received",
        entity_name="Alex",
        item="gold_ingot"
    ))
    
    print("After 2 gifts:")
    print(memory.get_relationship_summary("Alex"))
    print()
    print(memory.get_context_summary())


if __name__ == "__main__":
    print("=== Combat Scenario ===")
    example_combat_scenario()
    print("\n" + "="*50 + "\n")
    print("=== Social Scenario ===")
    example_social_scenario()