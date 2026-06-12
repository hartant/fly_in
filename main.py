from parsing import fileparse
from graph import Graph
from simulator import Simulator
import sys

try:
    result = fileparse("map.txt")
    graph = Graph(result.hubs)
    sim = Simulator(result, graph)
    sim.run()
except SystemExit:
    print("\nSimulation interrupted by user")
    sys.exit(0)