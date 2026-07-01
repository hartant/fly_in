from __future__ import annotations
import heapq
from models import HUB
from graph import Graph


def find_path(start: HUB, end: HUB, graph: Graph) -> list[str]:
    que: list[tuple[float, list[str]]] = [(0, [start.name])]
    visted: set[str] = set()
    while que:
        cost, path = heapq.heappop(que)
        cur = path[-1]
        if cur == end.name:
            return path
        if cur in visted:
            continue

        visted.add(cur)
        for neighbor in graph.get_neighbors(cur):
            if (not graph.is_blocked(neighbor.name)
                    and neighbor.name not in visted):
                zone_type = str(neighbor.zone_type)
                new_cost = cost + graph.get_cost(zone_type)
                heapq.heappush(que, (new_cost, path + [neighbor.name]))

    return []


def find_path_with_blocked(
    start: HUB, end: HUB, graph: Graph, blocked: set[str]
) -> list[str]:
    que: list[tuple[float, list[str]]] = [(0, [start.name])]
    visted: set[str] = set()
    while que:
        cost, path = heapq.heappop(que)
        cur = path[-1]
        if cur == end.name:
            return path
        if cur in visted:
            continue

        visted.add(cur)
        for neighbor in graph.get_neighbors(cur):
            if graph.is_blocked(neighbor.name):
                continue
            if neighbor.name in visted:
                continue
            if neighbor.name in blocked:
                continue
            zone_type = str(neighbor.zone_type)
            new_cost = cost + graph.get_cost(zone_type)
            heapq.heappush(que, (new_cost, path + [neighbor.name]))

    return []


def find_all_paths(
    start: HUB, end: HUB, graph: Graph, n: int
) -> list[list[str]]:
    paths: list[list[str]] = []
    blocked: set[str] = set()

    while len(paths) < n:
        path = find_path_with_blocked(start, end, graph, blocked)
        if not path:
            break

        if len(path) > 2:
            throughput = float('inf')
            for z in path[1:-1]:
                throughput = min(throughput, graph.hubs[z].max_drones)
        else:
            throughput = n

        for _ in range(min(throughput, n - len(paths))):
            paths.append(path)

        for zone in path[1:-1]:
            blocked.add(zone)

    if not paths:
        paths.append(find_path(start, end, graph))

    return paths
