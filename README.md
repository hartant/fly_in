*This project has been created as part of the 42 curriculum by mbenamar.*

# Fly-in

## Description

Fly-in is a drone routing simulation system written in Python. The goal is to
move a fleet of drones from a unique start zone to a unique end zone through a
network of connected zones, while respecting strict movement and capacity
constraints, and minimizing the total number of simulation turns.

The network is described in a custom text format (zones, connections, zone
types, capacities, colors). The program parses this format from scratch
(no external graph library is used), builds an internal graph, computes
efficient paths for every drone with a custom Dijkstra-based pathfinding
algorithm, then simulates the movement of all drones turn by turn while
enforcing zone occupancy and connection capacity rules. The simulation is
shown live in a pygame window.

## Instructions

### Requirements
- Python 3.10+
- pygame (installed automatically by `make install`)

### Setup and run

```bash
make install        # creates a venv and installs pygame, mypy, flake8
make run             # runs python3 main.py map.txt
make run MAP=path/to/other_map.txt   # run with a custom map
```

### Other Makefile targets

```bash
make debug           # run the program inside pdb
make lint            # flake8 + mypy (project required flags)
make lint-strict      # flake8 + mypy --strict
make clean            # remove __pycache__, .mypy_cache, .pytest_cache
```

### Manual run

```bash
python3 main.py map.txt
```

Press the window's close button or Ctrl+C at any time to stop the simulation
cleanly.

## Algorithm Explanation

### Parsing

The map file is read line by line with a small set of regular expressions
(`nb_drones:`, `start_hub:`/`end_hub:`/`hub:`, `connection:`). Each line is
validated independently and any malformed line raises a `ParserError` that
carries the line number and a clear message. Zones are stored as `HUB`
dataclass instances inside a dictionary keyed by zone name (`dict[str, HUB]`),
and connections are stored as adjacency lists (`links`) plus a capacity map
(`links_capacity`) on each `HUB`.

### Graph

The `Graph` class is a thin, custom wrapper around the `hubs` dictionary built
by the parser. It exposes three operations used by the rest of the program:
`get_neighbors(name)` (adjacent zones), `get_cost(zone_type)` (turn cost of a
zone type), and `is_blocked(name)`. No external graph library
(`networkx`, `graphlib`, ...) is used; the graph is entirely hand-written on
top of plain Python dictionaries and lists.

### Pathfinding

Paths are computed with a custom Dijkstra implementation (`find_path`) using
Python's `heapq` as a priority queue, where the cost of entering a zone
depends on its type (`normal`=1, `priority`=1, `restricted`=2, `blocked`=infinity).

To distribute drones efficiently across the graph instead of bottlenecking
them on a single corridor, `find_all_paths` repeatedly searches for a path,
computes its throughput (`min(max_drones)` over every intermediate zone), and
then "reserves" that path for that many drones before blocking all of its
intermediate zones and searching again. This produces a set of disjoint paths
(paths that don't share intermediate zones) so that multiple drones can move
truly in parallel without competing for the same zone capacity. Drones are
then assigned to these paths in a round-robin fashion (`paths[i % len(paths)]`)
so the algorithm scales to any number of drones, even more than the number of
distinct paths found.

### Simulation

The `Simulator` runs a turn-based loop. At every turn:
1. The current occupancy of every zone is computed from the drones' current
   positions.
2. Drones that are mid-transit through a `restricted` zone (which takes two
   turns) are advanced first, if the destination zone has room.
3. The remaining drones attempt to move to their next zone, checking both
   zone capacity (`max_drones`) and connection capacity
   (`max_link_capacity`) before moving. A move that would exceed a capacity
   limit is simply skipped for this turn (the drone waits).
4. All moves of the turn are printed on one line, in the format
   `D<id>-<zone>` (or `D<id>-<from>_<to>` while crossing a restricted
   connection).

The simulation stops as soon as every drone has reached the end zone, and an
explicit error is raised at startup if no path exists between start and end
(for example because of blocked zones), instead of looping forever.

### Complexity

- Each Dijkstra search is `O((V + E) log V)`.
- `find_all_paths` runs Dijkstra at most `O(V)` times (each call blocks at
  least one new zone), so building the full path set is bounded by
  `O(V * (V + E) log V)` in the worst case, but in practice stops much
  earlier once enough throughput has been found for all drones.
- Paths are computed **once** at the start of the simulation and then
  reused/cached on each `Drone` object (`drone.path`); they are not
  recomputed every turn. Memory usage is therefore proportional to the
  number of distinct paths found (at most `nb_drones`) plus the size of the
  graph, not to the number of turns.

## Visual Representation

The simulation is displayed live in a resizable pygame window:
- Every zone is drawn as a circle using the `color` specified in the map
  metadata (falling back to a color based on its zone type if none is
  given). The start and end zones are drawn larger with a white outline so
  they are always easy to spot.
- Connections are drawn as lines between zones.
- Each drone is drawn as a small circle with a white outline (so it stays
  visible even on a zone of a similar color) and its id label, and moves
  are animated smoothly from one zone to the next instead of jumping
  instantly, which makes it much easier to follow several drones moving at
  once.
- Drones that have arrived are shown clustered inside the end zone instead
  of disappearing, so the final state of the simulation is still visible.
- The current turn number is displayed in the corner of the window.

This makes it possible to visually verify, at a glance, that capacity and
movement rules are respected (no zone ever shows more drones overlapping than
its `max_drones` allows) without having to read the raw text output.

## Example

Given the bundled `map.txt`:

```
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

Running `python3 main.py map.txt` produces output similar to:

```
D1-corridorA D2-roof1
D1-tunnelB D3-corridorA
D1-goal D2-roof2 D4-corridorA
D3-tunnelB D2-goal D5-corridorA
D3-goal D4-tunnelB
D4-goal D5-tunnelB
D5-goal
```

Each line is one simulation turn; only drones that actually moved that turn
are listed, and the simulation stops once every drone has reached `goal`.

## Resources

- Dijkstra's algorithm -- Wikipedia
- Python `heapq` documentation
- Python `dataclasses` documentation
- pygame documentation
- mypy documentation

### AI usage

An AI assistant (Claude) was used throughout this project as a **debugging
and learning partner**, not as a code generator:
- Explaining Python concepts used in the codebase (`@dataclass`,
  `field(default_factory=...)`, `__post_init__`, `heapq`, generators,
  `dict`/`set` semantics, `continue` vs `break`) with examples based on this
  project's own map files, so every piece of code could be fully understood
  and re-explained rather than copy-pasted.
- Reviewing already-written code (parser, graph, pathfinding, simulator,
  visualizer) to identify concrete bugs -- for example: a duplicate-zone
  cost bug, an incorrect index lookup in `Drone.next_zone`, a disjoint-path
  blocking bug only marking one zone instead of the whole path, a missing
  zone-occupancy initialization at the start of each turn, and several
  visualization bugs (zone colors ignored, drones changing apparent color
  when sharing a zone, arrived drones overlapping at the end zone).
- Helping design and verify test scenarios (single drone, multiple disjoint
  paths, capacity bottlenecks, restricted zones, blocked/unreachable maps)
  used to confirm each fix actually solved the reported problem.

All AI-suggested fixes were reviewed, tested against custom map files, and
re-explained back in order to be fully understood before being kept in the
project.