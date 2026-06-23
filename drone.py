from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Drone:
    id: int
    current_zone: str
    path: list[str] = field(default_factory=list)
    path_index: int = 0
    arrived: bool = False
    in_transit: bool = False
    transit_destination: str | None = None
    prev_zone: str | None = None

    def next_zone(self) -> str | None:
        nxt = self.path_index + 1
        if nxt >= len(self.path):
            return None
        return self.path[nxt]
        