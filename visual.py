from __future__ import annotations
import pygame
from models import HUB
from graph import Graph
import math

class Visual:
    def __init__(self, graph:Graph, start:HUB, end:HUB) ->None:
        pygame.init()
        self.screen = pygame.display.set_mode((1750, 800))
        # self.screen = 
        pygame.display.set_caption("Drone Simulator")
        self.graph = graph
        self.start = start
        self.end = end
        self.font = pygame.font.SysFont("monospace", 10)
        self.drone_img = pygame.image.load("drone.png")
        self.drone_img = pygame.transform.scale(self.drone_img, (20, 20))  # كبر أو صغر

    def get_positions(self) -> dict[str, tuple[int, int]]:
        positions = {}
        for name, hub in self.graph.hubs.items():
            px = hub.x * 120 + 150  
            py = hub.y * 120 + 200 
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
          
            self.screen.blit(self.drone_img, (pos[0] + offset_x - 10, pos[1] + offset_y - 10))
         
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(text, (pos[0] - len(name) * 4, pos[1] - 35))
    
    def draw_drones(self, drones: list, positions: dict[str, tuple[int, int]]) -> None:
        drone_colors = [
            (0, 0, 255),   
            (255, 0, 0), 
            (255, 165, 0), 
            (0, 255, 255), 
            (255, 0, 255),
        ]
        for drone in drones:
            if drone.arrived:
                continue

            if drone.in_transit and drone.transit_destination:
                pos1 = positions.get(drone.current_zone)
                pos2 = positions.get(drone.transit_destination)
                if pos1 and pos2:
                    mid_x = (pos1[0] + pos2[0]) // 2
                    mid_y = (pos1[1] + pos2[1]) // 2
                    color = drone_colors[drone.id % len(drone_colors)]
                    pygame.draw.circle(self.screen, color, (mid_x, mid_y), 8)
                    text = self.font.render(f"D{drone.id}", True, (255, 255, 255))
                    self.screen.blit(text, (mid_x - 8, mid_y - 20))
                continue

            pos = positions.get(drone.current_zone)
            if pos is None:
                continue
            color = drone_colors[drone.id % len(drone_colors)]
            offset_angle = (drone.id * 72) % 360
            offset_r = 10
            offset_x = int(math.cos(math.radians(offset_angle)) * offset_r)
            offset_y = int(math.sin(math.radians(offset_angle)) * offset_r)
            pygame.draw.circle(self.screen, color, (pos[0] + offset_x, pos[1] + offset_y), 8)
            self.screen.blit(self.drone_img, (pos[0] + offset_x - 10, pos[1] + offset_y - 10))
            text = self.font.render(f"D{drone.id}", True, (255, 255, 255))
            bg = pygame.Surface((text.get_width() + 4, text.get_height() + 4))
            bg.fill((0, 0, 0))
            self.screen.blit(bg, (pos[0] + offset_x - 10, pos[1] + offset_y - 22))
            self.screen.blit(text, (pos[0] + offset_x - 8, pos[1] + offset_y - 20))
    def draw(self, drones: list, turn: int) -> None:
   
        self.screen.fill((30, 30, 30))
        

        positions = self.get_positions()
        

        self.draw_connections(positions)
        self.draw_zones(positions)
        self.draw_drones(drones, positions)
        

        text = self.font.render(f"Turn: {turn}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        

        pygame.display.flip()
        

        pygame.time.wait(1000)