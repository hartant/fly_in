from parsing import fileparse
from graph import Graph
from simulator import Simulator

result = fileparse("map.txt")
graph = Graph(result.hubs)
sim = Simulator(result, graph)
sim.run()