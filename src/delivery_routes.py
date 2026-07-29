"""
Problem 1: Optimising Delivery Routes.

A delivery driver must start at a depot, visit a set of customer addresses
exactly once, and return to the depot while travelling the shortest total
distance. This is the classic Travelling Salesperson Problem (TSP), which is
NP-hard, so we solve it with a two-stage heuristic:

    1. Nearest Neighbour  -> builds a quick, "good enough" starting tour.
    2. 2-opt improvement  -> repeatedly un-crosses the tour to shorten it.

Object-oriented design
----------------------
* ``Location``          - an immutable value object holding a labelled point.
* ``RouteGraph``        - models locations and the (Euclidean) paths between
                          them, caching a symmetric distance matrix.
* ``NearestNeighbourSolver`` - constructs an initial tour greedily.
* ``TwoOptOptimiser``   - improves an existing tour by local search.
* ``DeliveryRoutePlanner`` - a facade that wires the pieces together and
                          exposes a single ``plan`` method.

The distance metric is deliberately isolated inside ``RouteGraph`` so the same
solvers work for road-network distances, travel times, or any other metric
simply by substituting the graph.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Location:
    """An immutable, labelled point on a 2-D plane.

    Coordinates are treated as abstract map units (e.g. grid references);
    the planner never assumes a particular unit, only that distances are
    comparable.
    """

    name: str
    x: float
    y: float


class RouteGraph:
    """A complete weighted graph over a set of delivery locations.

    Encapsulation: the distance matrix is a private implementation detail.
    Callers ask ``distance(a, b)`` or ``tour_length(...)`` and never touch the
    underlying storage, so the metric can change without affecting solvers.
    """

    def __init__(self, locations: Sequence[Location]) -> None:
        if len(locations) < 2:
            raise ValueError("A route needs at least two locations.")
        self._locations: List[Location] = list(locations)
        self._index: Dict[str, int] = {
            loc.name: i for i, loc in enumerate(self._locations)
        }
        if len(self._index) != len(self._locations):
            raise ValueError("Location names must be unique.")
        self._matrix: List[List[float]] = self._build_matrix()

    def _build_matrix(self) -> List[List[float]]:
        """Pre-compute a symmetric distance matrix once, in O(n^2)."""
        n = len(self._locations)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d = self._euclidean(self._locations[i], self._locations[j])
                matrix[i][j] = matrix[j][i] = d
        return matrix

    @staticmethod
    def _euclidean(a: Location, b: Location) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    @property
    def locations(self) -> Tuple[Location, ...]:
        return tuple(self._locations)

    @property
    def size(self) -> int:
        return len(self._locations)

    def distance(self, a: Location, b: Location) -> float:
        """Return the cached distance between two locations in O(1)."""
        return self._matrix[self._index[a.name]][self._index[b.name]]

    def tour_length(self, tour: Sequence[Location]) -> float:
        """Total distance of a closed tour that returns to its start."""
        total = 0.0
        for i in range(len(tour)):
            total += self.distance(tour[i], tour[(i + 1) % len(tour)])
        return total


class NearestNeighbourSolver:
    """Greedy construction heuristic for an initial TSP tour.

    From the depot, repeatedly hop to the closest not-yet-visited location.
    Runs in O(n^2): for each of the n stops we scan the unvisited set.
    """

    def __init__(self, graph: RouteGraph) -> None:
        self._graph = graph

    def solve(self, depot: Location) -> List[Location]:
        unvisited = [loc for loc in self._graph.locations if loc != depot]
        tour = [depot]
        current = depot
        while unvisited:
            nearest = min(unvisited, key=lambda loc: self._graph.distance(current, loc))
            tour.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        return tour


class TwoOptOptimiser:
    """Local-search improvement that removes route crossings.

    2-opt takes two edges of the tour, reverses the segment between them, and
    keeps the change if it shortens the total distance. It repeats full sweeps
    until no swap helps. Each sweep is O(n^2); the number of sweeps is small in
    practice, giving a strong quality/speed trade-off.
    """

    def __init__(self, graph: RouteGraph) -> None:
        self._graph = graph

    def improve(self, tour: List[Location]) -> List[Location]:
        best = tour[:]
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best) - 1):
                for j in range(i + 1, len(best)):
                    if self._swap_gain(best, i, j) < -1e-12:
                        best[i:j + 1] = reversed(best[i:j + 1])
                        improved = True
        return best

    def _swap_gain(self, tour: List[Location], i: int, j: int) -> float:
        """Change in length if edges (i-1,i) and (j,j+1) are reconnected.

        Only four distances are needed, so evaluating a candidate swap is O(1).
        """
        n = len(tour)
        a, b = tour[i - 1], tour[i]
        c, d = tour[j], tour[(j + 1) % n]
        before = self._graph.distance(a, b) + self._graph.distance(c, d)
        after = self._graph.distance(a, c) + self._graph.distance(b, d)
        return after - before


class DeliveryRoutePlanner:
    """Facade that produces an optimised delivery route.

    Composition over inheritance: the planner *owns* a graph and the two
    solvers, exposing a single high-level operation to the rest of the system.
    """

    def __init__(self, locations: Sequence[Location]) -> None:
        self._graph = RouteGraph(locations)
        self._constructor = NearestNeighbourSolver(self._graph)
        self._optimiser = TwoOptOptimiser(self._graph)

    def plan(self, depot_name: str) -> Tuple[List[Location], float]:
        """Return an optimised closed tour and its length.

        Raises ``KeyError`` (via lookup) if the depot name is unknown.
        """
        depot = self._location_by_name(depot_name)
        initial = self._constructor.solve(depot)
        optimised = self._optimiser.improve(initial)
        return optimised, self._graph.tour_length(optimised)

    def initial_plan(self, depot_name: str) -> Tuple[List[Location], float]:
        """Nearest-Neighbour tour only, for before/after comparison."""
        depot = self._location_by_name(depot_name)
        tour = self._constructor.solve(depot)
        return tour, self._graph.tour_length(tour)

    def _location_by_name(self, name: str) -> Location:
        for loc in self._graph.locations:
            if loc.name == name:
                return loc
        raise KeyError(f"Unknown location: {name!r}")


def demo() -> None:
    """Demonstrate the planner on a small set of addresses (I/O evidence)."""
    locations = [
        Location("Depot", 0, 0),
        Location("Alpha", 2, 6),
        Location("Bravo", 5, 2),
        Location("Charlie", 6, 6),
        Location("Delta", 8, 3),
        Location("Echo", 1, 3),
        Location("Foxtrot", 7, 8),
    ]
    planner = DeliveryRoutePlanner(locations)

    nn_tour, nn_len = planner.initial_plan("Depot")
    opt_tour, opt_len = planner.plan("Depot")

    print("Problem 1 - Optimising Delivery Routes")
    print("-" * 46)
    print("Nearest Neighbour tour:")
    print("   " + " -> ".join(loc.name for loc in nn_tour) + " -> Depot")
    print(f"   length = {nn_len:.2f} units")
    print("After 2-opt improvement:")
    print("   " + " -> ".join(loc.name for loc in opt_tour) + " -> Depot")
    print(f"   length = {opt_len:.2f} units")
    saved = (nn_len - opt_len) / nn_len * 100 if nn_len else 0.0
    print(f"Improvement: {saved:.1f}% shorter\n")


if __name__ == "__main__":
    demo()
