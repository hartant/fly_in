from __future__ import annotations
import pygame
import math
from models import HUB
from graph import Graph
 
FPS = 60
ANIMATION_DURATION = 2  # secondes per move (1-2s)
 
class Visual:
    def __init__(self, graph: Graph, start: HUB, end: HUB) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((1750, 800))
        pygame.display.set_caption("Drone Simulator")
        self.graph = graph
        self.start = start
        self.end = end
        self.font = pygame.font.SysFont("monospace", 10)
        self.clock = pygame.time.Clock()
 
        # animation state: drone_id -> {from, to, progress}
        self.anim_state: dict[int, dict] = {}
 
    def get_positions(self) -> dict[str, tuple[int, int]]:
        positions = {}
        for name, hub in self.graph.hubs.items():
            px = hub.x * 100 + 150
            py = hub.y * 100 + 200
            positions[name] = (px, py)
        return positions
 
    def draw_connections(self, positions: dict[str, tuple[int, int]]) -> None:
        for name, hub in self.graph.hubs.items():
            for neighbor in hub.links:
                start_pos = positions[name]
                end_pos = positions[neighbor]
                pygame.draw.line(self.screen, (150, 150, 150), start_pos, end_pos, 2)
 
    def draw_zones(self, positions: dict[str, tuple[int, int]]) -> None:
        colors = {
            "normal":     (200, 200, 200),
            "restricted": (255, 100, 100),
            "priority":   (100, 255, 100),
            "blocked":    (50,  50,  50),
        }
        for name, hub in self.graph.hubs.items():
            pos = positions[name]
            if name == self.start.name:
                color = (0, 255, 0)
            elif name == self.end.name:
                color = (255, 255, 0)
            else:
                color = colors.get(hub.zone_type, (200, 200, 200))
            pygame.draw.circle(self.screen, color, pos, 22)
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(text, (pos[0] - len(name) * 3, pos[1] - 40))
 
    def draw_drone_shape(self, surface, color, x, y, angle_deg):
        """Draw a triangle pointing in direction of travel."""
        angle = math.radians(-angle_deg)
        size = 10
        tip = (x + math.cos(angle) * size, y + math.sin(angle) * size)
        left = (x + math.cos(angle + 2.5) * size * 0.6, y + math.sin(angle + 2.5) * size * 0.6)
        right = (x + math.cos(angle - 2.5) * size * 0.6, y + math.sin(angle - 2.5) * size * 0.6)
        pygame.draw.polygon(surface, color, [tip, left, right])
        pygame.draw.polygon(surface, (255, 255, 255), [tip, left, right], 1)
 
    def draw_drones(self, drones: list, positions: dict[str, tuple[int, int]]) -> None:
        drone_colors = [
            (0, 120, 255),
            (255, 60, 60),
            (255, 165, 0),
            (0, 230, 230),
            (220, 0, 220),
        ]
        for drone in drones:

            if drone.arrived:
                pos = positions.get(self.end.name)
                if pos:
                    text = self.font.render(f"D{drone.id}✓", True, (0, 255, 0))
                    bg = pygame.Surface((text.get_width() + 6, text.get_height() + 6))
                    bg.fill((0, 60, 0))
                    pygame.draw.rect(bg, (0, 255, 0), bg.get_rect(), 1)
                    offset_angle = (drone.id * 72) % 360
                    ox = int(math.cos(math.radians(offset_angle)) * 25)
                    oy = int(math.sin(math.radians(offset_angle)) * 25)
                    self.screen.blit(bg, (pos[0] + ox - 10, pos[1] + oy - 22))
                    self.screen.blit(text, (pos[0] + ox - 8, pos[1] + oy - 20))
                continue
 
            color = drone_colors[drone.id % len(drone_colors)]
            anim = self.anim_state.get(drone.id)
 
            if anim:
                p = anim["progress"]
                pos1 = positions.get(anim["from"])
                pos2 = positions.get(anim["to"])
                if pos1 and pos2:
                    # smooth lerp
                    cx = pos1[0] + (pos2[0] - pos1[0]) * p
                    cy = pos1[1] + (pos2[1] - pos1[1]) * p
                    angle = math.degrees(math.atan2(pos2[1] - pos1[1], pos2[0] - pos1[0]))
                    pygame.draw.circle(self.screen, color, (int(cx), int(cy)), 8)
                    text = self.font.render(f"D{drone.id}", True, (255, 255, 255))
                    bg = pygame.Surface((text.get_width() + 4, text.get_height() + 4))
                    bg.fill((0, 0, 0))
                    self.screen.blit(bg, (int(cx) - 8, int(cy) - 22))
                    self.screen.blit(text, (int(cx) - 6, int(cy) - 20))
            else:
                pos = positions.get(drone.current_zone)
                if pos is None:
                    continue
                offset_angle = (drone.id * 72) % 360
                offset_r = 10
                ox = int(math.cos(math.radians(offset_angle)) * offset_r)
                oy = int(math.sin(math.radians(offset_angle)) * offset_r)
                cx, cy = pos[0] + ox, pos[1] + oy
                pygame.draw.circle(self.screen, color, (cx, cy), 8)
                text = self.font.render(f"D{drone.id}", True, (255, 255, 255))
                bg = pygame.Surface((text.get_width() + 4, text.get_height() + 4))
                bg.fill((0, 100, 0))
                self.screen.blit(bg, (cx - 8, cy - 22))
                self.screen.blit(text, (cx - 6, cy - 20))
 
    def animate_moves(self, drones: list, positions: dict[str, tuple[int, int]], turn: int) -> None:
        """Animate all drone moves smoothly over ANIMATION_DURATION seconds."""
        # CORRECT
        self.anim_state = {}
        for drone in drones:
            if drone.arrived:
                continue
            if drone.prev_zone and drone.prev_zone != drone.current_zone:
                 if drone.prev_zone in positions and drone.current_zone in positions:
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
                    return
 
            progress = frame / total_frames
 
            # update all anim progress
            for drone_id in self.anim_state:
                self.anim_state[drone_id]["progress"] = progress
 
            self.screen.fill((30, 30, 30))
            self.draw_connections(positions)
            self.draw_zones(positions)
            self.draw_drones(drones, positions)
 
            text = self.font.render(f"Turn: {turn}", True, (255, 255, 255))
            self.screen.blit(text, (10, 10))
 
            pygame.display.flip()
            self.clock.tick(FPS)
 
        # finalize: progress = 1.0
        self.anim_state = {}
 
    def draw(self, drones: list, turn: int) -> None:
        positions = self.get_positions()
        self.animate_moves(drones, positions, turn)
 
        # final frame static
        self.screen.fill((30, 30, 30))
        self.draw_connections(positions)
        self.draw_zones(positions)
        self.draw_drones(drones, positions)
        text = self.font.render(f"Turn: {turn}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()
        self.clock.tick(FPS)