# 502IT — Applied Algorithms and Data Structures

Coursework submission for module **502IT — Algorithms and Data Structures**:
a technical report plus working, object-oriented Python implementations of
three problems from the brief.

**Problems addressed**

| # | Problem | Key data structures | Core algorithms |
|---|---------|---------------------|-----------------|
| 1 | Optimising Delivery Routes | Weighted graph + distance matrix | Nearest Neighbour + 2-opt (TSP heuristics) |
| 2 | Dynamic Resource Allocation | Binary heap / priority queue | FCFS, Shortest Job First, Priority, Round Robin |
| 5 | Recommendation Engine | Hash sets + dictionaries | User-based collaborative filtering (Jaccard) |

## Project layout

```
.
├── main.py                     # CLI entry point (runs the demos / launches GUI)
├── src/
│   ├── delivery_routes.py      # Problem 1
│   ├── resource_allocation.py  # Problem 2
│   ├── recommendation_engine.py# Problem 5
│   └── gui.py                  # Tkinter demonstrator (all three problems)
├── tests/
│   └── test_all.py             # 20 unit tests (unittest)
└── report/
    ├── 502IT_Technical_Report.docx  # the written report
    ├── build_report.py         # regenerates the report
    ├── make_charts.py          # regenerates the analytical charts
    ├── capture_gui.py          # captures GUI screenshots (headless)
    └── assets/                 # figures embedded in the report
```

## Running

The implementations and GUI use **only the Python standard library**, so they
run with any Python 3.10+ install.

```bash
# Run all three problem demonstrations
python main.py

# Run selected problems only
python main.py 1 5

# Launch the graphical demonstrator (needs a display)
python main.py --gui
```

## Testing

```bash
python -m unittest discover -s tests -v
```

All 20 tests cover correctness, boundary conditions (empty/invalid input), and
comparative properties (e.g. Shortest Job First never has a higher average
waiting time than First-Come-First-Served).

## Regenerating the report artefacts

These steps require extra packages (`matplotlib`, `python-docx`, `pillow`) and,
for the GUI screenshots, a display (or `xvfb-run`):

```bash
python report/make_charts.py                                   # charts
xvfb-run -s "-screen 0 640x520x24" python report/capture_gui.py # GUI screenshots
python report/build_report.py                                  # assemble the .docx
```

## Object-oriented design highlights

- **Encapsulation** — `RouteGraph` hides its distance matrix; `ResourcePool`
  guards capacity; `RecommendationEngine` hides its user/book dictionaries.
- **Inheritance & polymorphism** — an abstract `Scheduler` base class with four
  interchangeable policy subclasses.
- **Abstraction & composition** — `DeliveryRoutePlanner` is a facade composing a
  graph and two solvers behind a single `plan()` method.
- **Immutability** — `Location` and `Book` are frozen value objects.
