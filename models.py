from dataclasses import dataclass, field


class ParserError(Exception):
    def __init__(self,line_num:int, message:str):
        self.line_num = line_num
        self.message = message
    def __str__(self) -> str:
        return f"ParserError at line {self.line_num}: {self.message}"



@dataclass
class HUB:
    name: str
    x: int
    y: int
    h_type: str
    meta_dict: dict[str, str | int]
    links: list[str] = field(default_factory=list)

    def __post_init__(self) ->None:
        self.zone_type = self.meta_dict.get('zone', 'normal')
        self.max_drones = int(self.meta_dict.get('max_drones', 1))
        self.color  = self.meta_dict.get('color',None)
        self.links_capacity: dict[str,int] = {}


@dataclass
class ParseResult:
    nb_drones: int
    hubs: dict[str, HUB]
    start: HUB
    end: HUB