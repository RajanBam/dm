"""Unit tests for all three problem implementations.

Run with:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from src.delivery_routes import (
    DeliveryRoutePlanner,
    Location,
    NearestNeighbourSolver,
    RouteGraph,
    TwoOptOptimiser,
)
from src.recommendation_engine import (
    Book,
    RecommendationEngine,
    User,
    jaccard_similarity,
)
from src.resource_allocation import (
    FCFSScheduler,
    PriorityScheduler,
    Process,
    ResourcePool,
    RoundRobinScheduler,
    ShortestJobFirstScheduler,
)


class TestDeliveryRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.locations = [
            Location("Depot", 0, 0), Location("A", 0, 3),
            Location("B", 4, 3), Location("C", 4, 0),
        ]  # a unit-ish square: optimal loop length is the perimeter.

    def test_graph_distance_is_symmetric(self) -> None:
        g = RouteGraph(self.locations)
        a, b = self.locations[0], self.locations[2]
        self.assertAlmostEqual(g.distance(a, b), g.distance(b, a))

    def test_graph_rejects_duplicate_names(self) -> None:
        with self.assertRaises(ValueError):
            RouteGraph([Location("X", 0, 0), Location("X", 1, 1)])

    def test_nearest_neighbour_visits_all_once(self) -> None:
        g = RouteGraph(self.locations)
        tour = NearestNeighbourSolver(g).solve(self.locations[0])
        self.assertEqual(len(tour), len(self.locations))
        self.assertEqual(set(tour), set(self.locations))
        self.assertEqual(tour[0], self.locations[0])

    def test_two_opt_never_worsens_tour(self) -> None:
        g = RouteGraph(self.locations)
        nn = NearestNeighbourSolver(g).solve(self.locations[0])
        opt = TwoOptOptimiser(g).improve(nn)
        self.assertLessEqual(g.tour_length(opt), g.tour_length(nn) + 1e-9)

    def test_planner_finds_square_perimeter(self) -> None:
        planner = DeliveryRoutePlanner(self.locations)
        _, length = planner.plan("Depot")
        self.assertAlmostEqual(length, 14.0, places=6)  # 3+4+3+4

    def test_unknown_depot_raises(self) -> None:
        planner = DeliveryRoutePlanner(self.locations)
        with self.assertRaises(KeyError):
            planner.plan("Nowhere")


class TestResourceAllocation(unittest.TestCase):
    def setUp(self) -> None:
        self.workload = [
            Process("P1", 0, 7, 2), Process("P2", 2, 4, 1),
            Process("P3", 4, 1, 3), Process("P4", 5, 4, 2),
        ]
        self.pool = ResourcePool(1)

    def test_process_rejects_non_positive_burst(self) -> None:
        with self.assertRaises(ValueError):
            Process("X", 0, 0)

    def test_resource_pool_enforces_capacity(self) -> None:
        pool = ResourcePool(1)
        pool.acquire()
        with self.assertRaises(RuntimeError):
            pool.acquire()
        pool.release()
        self.assertEqual(pool.available, 1)

    def test_fcfs_runs_in_arrival_order(self) -> None:
        result = FCFSScheduler(self.pool).run_and_report(self.workload)
        self.assertEqual(result.order, ["P1", "P2", "P3", "P4"])

    def test_sjf_beats_fcfs_on_waiting_time(self) -> None:
        fcfs = FCFSScheduler(self.pool).run_and_report(self.workload)
        sjf = ShortestJobFirstScheduler(self.pool).run_and_report(self.workload)
        self.assertLessEqual(sjf.avg_waiting, fcfs.avg_waiting)

    def test_priority_runs_highest_priority_when_available(self) -> None:
        result = PriorityScheduler(self.pool).run_and_report(self.workload)
        # P1 starts at t=0 (only one present); P2 (priority 1) next.
        self.assertEqual(result.order[0], "P1")
        self.assertEqual(result.order[1], "P2")

    def test_all_policies_complete_every_process(self) -> None:
        for scheduler in [
            FCFSScheduler(self.pool),
            ShortestJobFirstScheduler(self.pool),
            PriorityScheduler(self.pool),
            RoundRobinScheduler(self.pool, quantum=2),
        ]:
            result = scheduler.run_and_report(self.workload)
            self.assertCountEqual(result.order, ["P1", "P2", "P3", "P4"])

    def test_total_service_time_conserved(self) -> None:
        # Round Robin must still give each process its full burst.
        rr = RoundRobinScheduler(self.pool, quantum=2)
        completed = rr.run([Process(p.pid, p.arrival, p.burst, p.priority)
                            for p in self.workload])
        for p in completed:
            self.assertTrue(p.is_complete)


class TestRecommendationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RecommendationEngine()
        for book in [Book(f"b{i}", f"Book {i}") for i in range(1, 7)]:
            self.engine.add_book(book)
        reading = {
            "Ann": ["b1", "b2", "b3"], "Ben": ["b1", "b2", "b4"],
            "Cara": ["b3", "b4", "b6"], "Dev": ["b1", "b3", "b4"],
        }
        for uid, books in reading.items():
            for bid in books:
                self.engine.record_reading(uid, bid)

    def test_jaccard_basic_values(self) -> None:
        self.assertEqual(jaccard_similarity({1, 2}, {1, 2}), 1.0)
        self.assertEqual(jaccard_similarity({1, 2}, {3, 4}), 0.0)
        self.assertAlmostEqual(jaccard_similarity({1, 2, 3}, {2, 3, 4}), 0.5)

    def test_jaccard_empty_sets(self) -> None:
        self.assertEqual(jaccard_similarity(set(), set()), 0.0)

    def test_user_read_is_a_set(self) -> None:
        user = User("u1")
        user.record("b1")
        user.record("b1")
        self.assertEqual(user.read, {"b1"})

    def test_recording_unknown_book_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.engine.record_reading("Ann", "does-not-exist")

    def test_recommendations_exclude_already_read(self) -> None:
        recs = self.engine.recommend("Dev", limit=5)
        titles = {book.book_id for book, _ in recs}
        self.assertNotIn("b1", titles)
        self.assertNotIn("b3", titles)
        self.assertNotIn("b4", titles)

    def test_recommendation_scores_descend(self) -> None:
        recs = self.engine.recommend("Dev", limit=5)
        scores = [score for _, score in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_unknown_user_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.engine.recommend("Nobody")


if __name__ == "__main__":
    unittest.main(verbosity=2)
