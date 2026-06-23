from __future__ import annotations
from models import ParseResult, HUB
from graph import Graph
from drone import Drone
from pathfinding import find_path, find_all_paths
from visual import Visual
import pygame
import sys

class Simulator:
    def __init__(self, result : ParseResult, graph : Graph) -> None:
        self.result = result
        self.graph  = graph
        self.end =  result.end
        self.visual = Visual(graph, result.start, result.end)

        self.drones =  [Drone(id = i , current_zone= result.start.name ) for i  in range(1 , result.nb_drones + 1 )  ]
        paths = find_all_paths(result.start, result.end, graph, result.nb_drones)
        for i, drone in enumerate(self.drones):
            drone.path = paths[i % len(paths)]
    

    def run(self) -> None:
        turn = 0 
        while not all(drone.arrived for drone in self.drones):
            turn += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

            zone_occupancy: dict[str, int] = {}
            conn_usage: dict[tuple[str, str], int] = {}
            moves: list[str] = []
            moved_this_turn: set[int] = set()

            for dr in self.drones:
                if not dr.arrived and not dr.in_transit:
                    zone_occupancy[dr.current_zone] = zone_occupancy.get(dr.current_zone, 0) + 1


            for dr in self.drones:
                if not dr.in_transit:
                    continue

                dest = dr.transit_destination
                if dest is None:
                    continue
                
                current = zone_occupancy.get(dest, 0)
                max_cap = self.graph.hubs[dest].max_drones

                if current >= max_cap:
                    continue


                zone_occupancy[dest] = zone_occupancy.get(dest, 0) + 1
                dr.prev_zone = dr.current_zone 
                dr.current_zone = dest
                dr.in_transit = False
                dr.transit_destination = None

                if dest == self.end.name:
                    dr.arrived = True

                moved_this_turn.add(dr.id)
                moves.append(f"D{dr.id}-{dest}")
                

            for dr in self.drones:
                if dr.arrived or dr.in_transit or dr.id in moved_this_turn:
                    continue
                
                nxt = dr.next_zone()
                if nxt is None:
                    continue

                current_in_zone = zone_occupancy.get(nxt, 0)
                max_cap = self.graph.hubs[nxt].max_drones

                if current_in_zone >= max_cap:
                    continue

                conn = tuple(sorted([dr.current_zone, nxt]))
                current_on_conn = conn_usage.get(conn, 0)
                max_conn = self.graph.hubs[dr.current_zone].links_capacity.get(nxt, 1)

                if current_on_conn >= max_conn:
                    continue


                if dr.current_zone in zone_occupancy and zone_occupancy[dr.current_zone] > 0:
                    zone_occupancy[dr.current_zone] -= 1

                zone_occupancy[nxt] = zone_occupancy.get(nxt, 0) + 1
                conn_usage[conn] = conn_usage.get(conn, 0) + 1

                if self.graph.hubs[nxt].zone_type == "restricted":
                    dr.in_transit = True
                    dr.transit_destination = nxt

                    old_zone = dr.current_zone
                    dr.prev_zone = dr.current_zone
                    dr.current_zone = nxt
                    dr.path_index += 1 
                    moves.append(f"D{dr.id}-{old_zone}_{nxt}") 
                else:
                    dr.prev_zone = dr.current_zone
                    dr.current_zone = nxt
                    dr.path_index += 1
                    
                    if nxt == self.end.name:
                        dr.arrived = True
                    moves.append(f"D{dr.id}-{nxt}")

            if moves:
                print(" ".join(moves))
            
            self.visual.draw(self.drones, turn)