from __future__ import annotations
import sys
import math
import pygame
from models import HUB
from graph import Graph

FPS = 144
ANIMATION_DURATION = 2


class Visual:
    def __init__(self, graph: Graph, start: HUB, end: HUB) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        pygame.display.set_caption("Drone Simulator")
        self.graph = graph
        self.start = start
        self.end = end
        self.font = pygame.font.SysFont("monospace", 10)
        self.clock = pygame.time.Clock()

        self.anim_state: dict[int, dict] = {}

    COLOR_NAME_MAP: dict[str, tuple[int, int, int]] = {
        "red":     (220, 50,  50),
        "green":   (50,  200, 50),
        "blue":    (50,  100, 220),
        "yellow":  (240, 220, 30),
        "orange":  (230, 140, 30),
        "purple":  (160, 50,  200),
        "cyan":    (0,   210, 210),
        "lime":    (100, 230, 50),
        "gray":    (130, 130, 130),
        "grey":    (130, 130, 130),
        "white":   (240, 240, 240),
        "black":   (20,  20,  20),
        "magenta": (220, 50,  200),
        "brown":   (160, 100, 50),
        "gold":    (255, 200, 0),
        "pink":    (255, 150, 180),
        "teal":    (0,   150, 150),
    }

    ZONE_TYPE_COLORS: dict[str, tuple[int, int, int]] = {
        "normal":     (200, 200, 200),
        "restricted": (220, 80,  80),
        "priority":   (80,  200, 80),
        "blocked":    (50,  50,  50),
    }

    def resolve_color(
        self, color_str: str | None, zone_type: str
    ) -> tuple[int, int, int]:
        """Resolve a color string from map metadata to an RGB tuple."""
        if color_str:
            name = str(color_str).lower().strip()
            if name in self.COLOR_NAME_MAP:
                return self.COLOR_NAME_MAP[name]
            if name.startswith("#") and len(name) == 7:
                try:
                    r = int(name[1:3], 16)
                    g = int(name[3:5], 16)
                    b = int(name[5:7], 16)
                    return (r, g, b)
                except ValueError:
                    pass
        return self.ZONE_TYPE_COLORS.get(zone_type, (200, 200, 200))

    def get_positions(self) -> dict[str, tuple[int, int]]:
        """Auto-fit all zones to fill ~90% of the window."""
        hubs = list(self.graph.hubs.values())
        if not hubs:
            return {}
        xs = [h.x for h in hubs]
        ys = [h.y for h in hubs]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        win_w, win_h = self.screen.get_size()
        margin_x = 120
        margin_y = 80
        span_x = max_x - min_x or 1
        span_y = max_y - min_y or 1
        scale_x = (win_w - 2 * margin_x) / span_x
        scale_y = (win_h - 2 * margin_y - 40) / span_y
        scale = min(scale_x, scale_y)
        positions = {}
        for name, hub in self.graph.hubs.items():
            px = int((hub.x - min_x) * scale) + margin_x
            py = int((hub.y - min_y) * scale) + margin_y + 40
            positions[name] = (px, py)
        return positions

    def draw_connections(
        self, positions: dict[str, tuple[int, int]]
    ) -> None:
        for name, hub in self.graph.hubs.items():
            for neighbor in hub.links:
                start_pos = positions[name]
                end_pos = positions[neighbor]
                pygame.draw.line(
                    self.screen, (150, 150, 150), start_pos, end_pos, 2
                )

    def draw_zones(self, positions: dict[str, tuple[int, int]]) -> None:
        for name, hub in self.graph.hubs.items():
            pos = positions[name]
            zone_type = str(hub.zone_type)
            if name == self.start.name:
                radius = 35
                color = self.resolve_color(
                    str(hub.color) if hub.color else "green", zone_type
                )
            elif name == self.end.name:
                radius = 35
                color = self.resolve_color(
                    str(hub.color) if hub.color else "yellow", zone_type
                )
            else:
                radius = 22
                color = self.resolve_color(
                    str(hub.color) if hub.color else None, zone_type
                )
            pygame.draw.circle(self.screen, color, pos, radius)

            if name in (self.start.name, self.end.name):
                pygame.draw.circle(
                    self.screen, (255, 255, 255), pos, radius, 3
                )
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(
                text, (pos[0] - len(name) * 3, pos[1] - radius - 12)
            )

    DRONE_COLORS: list[tuple[int, int, int]] = [
        (0,   120, 255), (255, 60,  60),  (255, 165, 0),   (0,   230, 230),
        (220, 0,   220), (0,   200, 80),  (255, 255, 0),   (255, 100, 180),
        (80,  200, 255), (200, 100, 0),   (100, 255, 100), (255, 80,  150),
        (0,   150, 200), (180, 0,   255), (255, 200, 100), (50,  255, 200),
        (255, 150, 50),  (150, 200, 0),   (0,   200, 180), (200, 200, 255),
        (255, 50,  100), (100, 100, 255), (200, 255, 50),  (255, 180, 200),
        (100, 200, 100),
    ]

    def drone_color(self, drone_id: int) -> tuple[int, int, int]:
        return self.DRONE_COLORS[(drone_id - 1) % len(self.DRONE_COLORS)]

    def draw_drones(
        self, drones: list, positions: dict[str, tuple[int, int]]
    ) -> None:

        arrived = [d for d in drones if d.arrived]
        if arrived:
            goal_pos = positions.get(self.end.name)
            if goal_pos:
                n = len(arrived)

                inner_r = 22 if n <= 6 else 30
                for idx, drone in enumerate(arrived):
                    angle = (
                        2 * math.pi * idx / max(n, 1)
                    ) - math.pi / 2
                    spread = min(inner_r, 10 + n * 2)
                    dx = int(math.cos(angle) * spread)
                    dy = int(math.sin(angle) * spread)
                    cx = goal_pos[0] + dx
                    cy = goal_pos[1] + dy
                    color = self.drone_color(drone.id)
                    pygame.draw.circle(self.screen, color, (cx, cy), 5)
                    lbl = self.font.render(f"D{drone.id}", True, color)
                    self.screen.blit(lbl, (cx - 6, cy - 14))

        total_drones = len(drones)
        angle_step = (2 * math.pi) / max(total_drones, 1)

        for drone in drones:
            if drone.arrived:
                continue

            color = self.drone_color(drone.id)
            anim = self.anim_state.get(drone.id)

            fixed_angle = angle_step * (drone.id - 1)
            ox = int(math.cos(fixed_angle) * 12)
            oy = int(math.sin(fixed_angle) * 12)

            if anim:
                p = anim["progress"]
                pos1 = positions.get(anim["from"])
                pos2 = positions.get(anim["to"])
                if pos1 and pos2:
                    cx = int(pos1[0] + (pos2[0] - pos1[0]) * p) + ox
                    cy = int(pos1[1] + (pos2[1] - pos1[1]) * p) + oy
                    pygame.draw.circle(
                        self.screen, (255, 255, 255), (cx, cy), 9
                    )
                    pygame.draw.circle(self.screen, color, (cx, cy), 8)
                    text = self.font.render(
                        f"D{drone.id}", True, (255, 255, 255)
                    )
                    bg = pygame.Surface(
                        (text.get_width() + 4, text.get_height() + 4)
                    )
                    bg.fill((0, 0, 0))
                    self.screen.blit(bg, (cx - 8, cy - 22))
                    self.screen.blit(text, (cx - 6, cy - 20))
            else:
                pos = positions.get(drone.current_zone)
                if pos is None:
                    continue
                cx, cy = pos[0] + ox, pos[1] + oy
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (cx, cy), 9
                )
                pygame.draw.circle(self.screen, color, (cx, cy), 8)
                text = self.font.render(
                    f"D{drone.id}", True, (255, 255, 255)
                )
                bg = pygame.Surface(
                    (text.get_width() + 4, text.get_height() + 4)
                )
                bg.fill((0, 0, 0))
                self.screen.blit(bg, (cx - 8, cy - 22))
                self.screen.blit(text, (cx - 6, cy - 20))

    def animate_moves(
        self,
        drones: list,
        positions: dict[str, tuple[int, int]],
        turn: int,
    ) -> None:
        """Animate all drone moves smoothly over ANIMATION_DURATION sec."""
        self.anim_state = {}
        for drone in drones:
            if drone.prev_zone and drone.prev_zone != drone.current_zone:
                if (drone.prev_zone in positions
                        and drone.current_zone in positions):
                    self.anim_state[drone.id] = {
                        "from": drone.prev_zone,
                        "to": drone.current_zone,
                        "progress": 0.0
                    }

        total_frames = int(FPS * ANIMATION_DURATION)
        for frame in range(total_frames):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

            progress = frame / total_frames

            for drone_id in self.anim_state:
                self.anim_state[drone_id]["progress"] = progress

            self.screen.fill((30, 30, 30))
            self.draw_connections(positions)
            self.draw_zones(positions)
            self.draw_drones(drones, positions)

            text = self.font.render(
                f"Turn: {turn}", True, (255, 255, 255)
            )
            self.screen.blit(text, (10, 10))

            pygame.display.flip()
            self.clock.tick(FPS)

        self.anim_state = {}

    def draw(self, drones: list, turn: int) -> None:
        positions = self.get_positions()
        self.animate_moves(drones, positions, turn)

        self.screen.fill((30, 30, 30))
        self.draw_connections(positions)
        self.draw_zones(positions)
        self.draw_drones(drones, positions)
        text = self.font.render(f"Turn: {turn}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()
        self.clock.tick(FPS)
