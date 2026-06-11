from parsing import fileparse
from graph import Graph
from simulator import Simulator

result = fileparse("map.txt")
graph = Graph(result.hubs)
# print([f"{y.name} => {y.links}" for _, y in result.hubs.items()])
sim = Simulator(result, graph)
sim.run()