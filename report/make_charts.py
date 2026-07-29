"""Generate the analytical charts embedded in the technical report.

Produces PNG figures in report/assets/ using matplotlib. These are figures for
the written report (as opposed to the live GUI screenshots).
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.delivery_routes import DeliveryRoutePlanner, Location, NearestNeighbourSolver, RouteGraph
from src.resource_allocation import (
    FCFSScheduler, PriorityScheduler, Process, ResourcePool,
    RoundRobinScheduler, ShortestJobFirstScheduler,
)
from src.recommendation_engine import Book, RecommendationEngine

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

# Black-and-white scheme: grey fills distinguished by hatch patterns and black
# edges, so every figure prints clearly without colour.
GREYS = ["#3d3d3d", "#7a7a7a", "#b0b0b0", "#dcdcdc", "#565656", "#9a9a9a"]
HATCH = ["", "///", "...", "xxx", "\\\\\\", "+++"]
plt.rcParams.update({
    "figure.dpi": 130, "font.size": 10,
    "axes.edgecolor": "black", "axes.labelcolor": "black",
    "text.color": "black", "xtick.color": "black", "ytick.color": "black",
    "font.family": "DejaVu Sans",
})


def chart_scheduler_comparison() -> None:
    workload = [Process("P1", 0, 7, 2), Process("P2", 2, 4, 1),
                Process("P3", 4, 1, 3), Process("P4", 5, 4, 2)]
    pool = ResourcePool(1)
    schedulers = [FCFSScheduler(pool), ShortestJobFirstScheduler(pool),
                  PriorityScheduler(pool), RoundRobinScheduler(pool, 2)]
    names, waits, turns = [], [], []
    for s in schedulers:
        r = s.run_and_report(workload)
        names.append(s.name)
        waits.append(r.avg_waiting)
        turns.append(r.avg_turnaround)

    x = range(len(names))
    width = 0.38
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    b1 = ax.bar([i - width / 2 for i in x], waits, width, label="Avg waiting",
                color=GREYS[2], edgecolor="black", hatch=HATCH[0])
    b2 = ax.bar([i + width / 2 for i in x], turns, width, label="Avg turnaround",
                color=GREYS[0], edgecolor="black", hatch=HATCH[1])
    ax.bar_label(b1, fmt="%.2f", fontsize=8, padding=2)
    ax.bar_label(b2, fmt="%.2f", fontsize=8, padding=2)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel("Time units")
    ax.set_title("Scheduling policy comparison (lower is better)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_schedulers.png"))
    plt.close(fig)


def chart_recommendations() -> None:
    engine = RecommendationEngine()
    for b in [Book("b1", "Clean Code"), Book("b2", "Pragmatic Programmer"),
              Book("b3", "Intro to Algorithms"), Book("b4", "Deep Learning"),
              Book("b5", "The Hobbit"), Book("b6", "Dune")]:
        engine.add_book(b)
    reading = {"Ann": ["b1", "b2", "b3"], "Ben": ["b1", "b2", "b4"],
               "Cara": ["b3", "b4", "b6"], "Dev": ["b1", "b3", "b4"],
               "Ella": ["b5", "b6"]}
    for uid, books in reading.items():
        for bid in books:
            engine.record_reading(uid, bid)
    recs = engine.recommend("Dev", limit=5)
    titles = [book.title for book, _ in recs]
    scores = [s for _, s in recs]

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    bars = ax.barh(titles[::-1], scores[::-1],
                   color=[GREYS[i % len(GREYS)] for i in range(len(scores))],
                   edgecolor="black")
    for bar, h in zip(bars, [HATCH[i % len(HATCH)] for i in range(len(scores))]):
        bar.set_hatch(h)
    ax.bar_label(bars, fmt="%.2f", fontsize=8, padding=3)
    ax.set_xlabel("Recommendation score (sum of neighbour similarity)")
    ax.set_title("Book recommendations for reader 'Dev'")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_recommendations.png"))
    plt.close(fig)


def chart_route_improvement() -> None:
    locations = [Location("Depot", 0, 0), Location("Alpha", 2, 6),
                 Location("Bravo", 5, 2), Location("Charlie", 6, 6),
                 Location("Delta", 8, 3), Location("Echo", 1, 3),
                 Location("Foxtrot", 7, 8)]
    planner = DeliveryRoutePlanner(locations)
    _, nn = planner.initial_plan("Depot")
    _, opt = planner.plan("Depot")
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    bars = ax.bar(["Nearest\nNeighbour", "NN + 2-opt"], [nn, opt],
                  color=[GREYS[2], GREYS[0]], edgecolor="black",
                  hatch="", width=0.6)
    bars[1].set_hatch("///")
    ax.bar_label(bars, fmt="%.2f", fontsize=9)
    ax.set_ylabel("Total tour length (units)")
    ax.set_title("Tour length before / after 2-opt")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_route.png"))
    plt.close(fig)


def chart_scaling() -> None:
    """Empirical runtime of Nearest-Neighbour construction vs n (~O(n^2))."""
    import math
    import random
    sizes = [10, 25, 50, 100, 200, 400]
    measured = []
    for n in sizes:
        locs = [Location(f"L{i}", random.uniform(0, 100), random.uniform(0, 100))
                for i in range(n)]
        graph = RouteGraph(locs)
        solver = NearestNeighbourSolver(graph)
        start = time.perf_counter()
        solver.solve(locs[0])
        measured.append((time.perf_counter() - start) * 1000)

    # Reference O(n^2) curve scaled to the largest measurement.
    ref = [(n * n) for n in sizes]
    scale = measured[-1] / ref[-1]
    ref = [r * scale for r in ref]

    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.plot(sizes, measured, "o-", color="black", label="Measured runtime")
    ax.plot(sizes, ref, "s--", color="#7a7a7a", label="O(n^2) reference")
    ax.set_xlabel("Number of locations (n)")
    ax.set_ylabel("Construction time (ms)")
    ax.set_title("Nearest-Neighbour scaling: measured vs O(n^2)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_scaling.png"))
    plt.close(fig)


def chart_gantt() -> None:
    """Gantt-style execution timelines for FCFS vs SJF on the sample workload."""
    workload = [Process("P1", 0, 7, 2), Process("P2", 2, 4, 1),
                Process("P3", 4, 1, 3), Process("P4", 5, 4, 2)]
    pool = ResourcePool(1)
    policies = [("FCFS", FCFSScheduler(pool)),
                ("SJF", ShortestJobFirstScheduler(pool))]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    hatch_for = {"P1": "", "P2": "///", "P3": "...", "P4": "xxx"}
    grey_for = {"P1": "#b0b0b0", "P2": "#7a7a7a", "P3": "#dcdcdc", "P4": "#565656"}
    for row, (name, sched) in enumerate(policies):
        done = sched.run([Process(p.pid, p.arrival, p.burst, p.priority)
                          for p in workload])
        for p in done:
            ax.barh(row, p.burst, left=p.start_time, height=0.5,
                    color=grey_for[p.pid], edgecolor="black",
                    hatch=hatch_for[p.pid])
            ax.text(p.start_time + p.burst / 2, row, p.pid,
                    va="center", ha="center", fontsize=8)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["FCFS", "SJF"])
    ax.set_xlabel("Time")
    ax.set_title("Execution timeline: FCFS vs Shortest Job First")
    ax.set_xlim(0, 16)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_gantt.png"))
    plt.close(fig)


if __name__ == "__main__":
    chart_scheduler_comparison()
    chart_recommendations()
    chart_route_improvement()
    chart_scaling()
    chart_gantt()
    print("charts written to", OUT)
