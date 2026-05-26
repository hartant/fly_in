from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Drone:
    id: int
    current_zone: str
    path: list[str] = field(default_factory=list)
    arrived: bool = False
    in_transit: bool = False
    transit_destination: str | None = None

    def next_zone(self) -> str | None:
        try:

            idx = self.path.index(self.current_zone)
        except ValueError:
            return None


        idx += 1 
        if idx >= len(self.path):
            return None
        
        return self.path[idx]