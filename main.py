from __future__ import annotations
import sys
import pygame
from parsing import fileparse, ParserError
from graph import Graph
from simulator import Simulator


def main() -> None:
    """Entry point — parse args, build graph, run simulation."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    try:
        result = fileparse(sys.argv[1])
        graph = Graph(result.hubs)
        sim = Simulator(result, graph)
        sim.run()
    except ParserError as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()