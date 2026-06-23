from models import HUB
from graph import Graph

h1 = HUB("start", 0, 0, "hub", {"zone": "normal"})
h2 = HUB("goal", 5, 5, "hub", {"zone": "priority"})
h1.links.append("goal")
h2.links.append("start")

graph = Graph({"start": h1, "goal": h2})

print(graph.get_neighbors("start"))   # khass yban [HUB(name="goal"...)]
print(graph.get_cost("restricted"))   # khass yban 2
print(graph.is_blocked("start"))      # khass yban False