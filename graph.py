from __future__ import annotations
from models import HUB

ZONE_COST = {
    "normal":1,
    "restricted":2,
    "priority": 1,
    "blocked": float('inf'),
}

class Graph:
    def __init__(self,hubs:dict[str,HUB])-> None:
        self.hubs =  hubs
    

    def get_neighbors(self, name: str) -> list[HUB]:
        if name not in self.hubs:
            raise KeyError(f"zone '{name}' not found in graph")
        return [self.hubs[n] for n in self.hubs[name].links]

    def get_cost(self, zone_type: str) -> float:
        return ZONE_COST[zone_type]
    
    def is_blocked(self, name: str) -> bool:
        return self.hubs[name].zone_type == "blocked"