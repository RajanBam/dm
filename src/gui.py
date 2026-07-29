"""
Graphical front-end for all three problems.

A single Tkinter application (Python standard library only, so it runs anywhere
Python is installed) with one tab per problem. Each tab takes input, runs the
relevant algorithm from ``src`` and visualises the result on a native
``Canvas`` -- a route map for Problem 1 and bar charts for Problems 2 and 5.

Run with:  python -m src.gui      (or:  python src/gui.py)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple

from src.delivery_routes import DeliveryRoutePlanner, Location
from src.resource_allocation import (
    FCFSScheduler,
    PriorityScheduler,
    Process,
    ResourcePool,
    RoundRobinScheduler,
    Scheduler,
    ShortestJobFirstScheduler,
)
from src.recommendation_engine import Book, RecommendationEngine

# Greyscale palette so the demonstrator matches the black-and-white report.
PALETTE = ["#2b2b2b", "#5a5a5a", "#808080", "#a6a6a6", "#c9c9c9", "#e0e0e0"]


def _draw_bar_chart(
    canvas: tk.Canvas,
    labels: List[str],
    values: List[float],
    title: str,
    value_fmt: str = "{:.2f}",
) -> None:
    """Render a simple vertical bar chart on a Tk canvas (no dependencies)."""
    canvas.delete("all")
    canvas.update_idletasks()
    width = int(canvas["width"])
    height = int(canvas["height"])
    margin_l, margin_r, margin_t, margin_b = 45, 20, 40, 55

    canvas.create_text(width / 2, 20, text=title, font=("TkDefaultFont", 11, "bold"))
    if not values:
        return

    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    max_val = max(values) or 1.0

    # Axes.
    canvas.create_line(margin_l, margin_t, margin_l, height - margin_b, fill="#888")
    canvas.create_line(
        margin_l, height - margin_b, width - margin_r, height - margin_b, fill="#888"
    )

    n = len(values)
    slot = plot_w / n
    bar_w = slot * 0.6
    for i, (label, value) in enumerate(zip(labels, values)):
        x0 = margin_l + i * slot + (slot - bar_w) / 2
        x1 = x0 + bar_w
        bar_h = (value / max_val) * plot_h
        y1 = height - margin_b
        y0 = y1 - bar_h
        colour = PALETTE[i % len(PALETTE)]
        canvas.create_rectangle(x0, y0, x1, y1, fill=colour, outline="")
        canvas.create_text(
            (x0 + x1) / 2, y0 - 10, text=value_fmt.format(value),
            font=("TkDefaultFont", 8),
        )
        canvas.create_text(
            (x0 + x1) / 2, y1 + 14, text=label, font=("TkDefaultFont", 8),
            width=slot,
        )


class DeliveryTab(ttk.Frame):
    """Tab for Problem 1 - delivery route optimisation."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=10)
        self._locations = [
            Location("Depot", 0, 0), Location("Alpha", 2, 6),
            Location("Bravo", 5, 2), Location("Charlie", 6, 6),
            Location("Delta", 8, 3), Location("Echo", 1, 3),
            Location("Foxtrot", 7, 8),
        ]
        ttk.Label(
            self, text="Nearest-Neighbour + 2-opt tour from the Depot",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w")
        ttk.Button(self, text="Plan optimised route", command=self._run).pack(
            anchor="w", pady=6
        )
        self._canvas = tk.Canvas(self, width=520, height=320, bg="white",
                                 highlightthickness=1, highlightbackground="#ccc")
        self._canvas.pack()
        self._info = ttk.Label(self, text="", justify="left")
        self._info.pack(anchor="w", pady=6)
        self._run()

    def _run(self) -> None:
        planner = DeliveryRoutePlanner(self._locations)
        _, nn_len = planner.initial_plan("Depot")
        tour, opt_len = planner.plan("Depot")
        self._draw_route(tour)
        saved = (nn_len - opt_len) / nn_len * 100 if nn_len else 0
        self._info.config(
            text=(f"Nearest-Neighbour length: {nn_len:.2f}    "
                  f"Optimised (2-opt): {opt_len:.2f}    "
                  f"Saving: {saved:.1f}%")
        )

    def _draw_route(self, tour: List[Location]) -> None:
        c = self._canvas
        c.delete("all")
        c.create_text(260, 16, text="Optimised delivery tour",
                      font=("TkDefaultFont", 11, "bold"))
        xs = [loc.x for loc in self._locations]
        ys = [loc.y for loc in self._locations]
        pad = 40
        w, h = 520, 320
        sx = (w - 2 * pad) / (max(xs) - min(xs) or 1)
        sy = (h - 2 * pad - 20) / (max(ys) - min(ys) or 1)

        def px(loc: Location) -> Tuple[float, float]:
            return (pad + (loc.x - min(xs)) * sx,
                    h - pad - (loc.y - min(ys)) * sy)

        closed = tour + [tour[0]]
        for a, b in zip(closed, closed[1:]):
            x0, y0 = px(a)
            x1, y1 = px(b)
            c.create_line(x0, y0, x1, y1, fill="#000000", width=2, arrow=tk.LAST)
        for loc in self._locations:
            x, y = px(loc)
            is_depot = loc.name == "Depot"
            fill = "#000000" if is_depot else "#ffffff"
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=fill,
                          outline="#000000", width=2)
            c.create_text(x, y - 14, text=loc.name, font=("TkDefaultFont", 8))


class ResourceTab(ttk.Frame):
    """Tab for Problem 2 - resource allocation policy comparison."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=10)
        self._workload = [
            Process("P1", 0, 7, 2), Process("P2", 2, 4, 1),
            Process("P3", 4, 1, 3), Process("P4", 5, 4, 2),
        ]
        ttk.Label(
            self, text="Average waiting time by scheduling policy",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w")
        ttk.Button(self, text="Compare schedulers", command=self._run).pack(
            anchor="w", pady=6
        )
        self._canvas = tk.Canvas(self, width=520, height=320, bg="white",
                                 highlightthickness=1, highlightbackground="#ccc")
        self._canvas.pack()
        self._info = ttk.Label(self, text="", justify="left")
        self._info.pack(anchor="w", pady=6)
        self._run()

    def _run(self) -> None:
        pool = ResourcePool(1)
        schedulers: List[Scheduler] = [
            FCFSScheduler(pool),
            ShortestJobFirstScheduler(pool),
            PriorityScheduler(pool),
            RoundRobinScheduler(pool, quantum=2),
        ]
        labels, waits, lines = [], [], []
        for s in schedulers:
            r = s.run_and_report(self._workload)
            labels.append(s.name)
            waits.append(r.avg_waiting)
            lines.append(f"{s.name}: order {'-'.join(r.order)}, "
                         f"avg wait {r.avg_waiting:.2f}")
        _draw_bar_chart(self._canvas, labels, waits,
                        "Average waiting time (lower is better)")
        self._info.config(text="\n".join(lines))


class RecommendationTab(ttk.Frame):
    """Tab for Problem 5 - book recommendations."""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, padding=10)
        self._engine = self._build_engine()
        ttk.Label(
            self, text="Recommendation strength for reader 'Dev'",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(anchor="w", pady=6)
        ttk.Label(row, text="User:").pack(side="left")
        self._user = tk.StringVar(value="Dev")
        ttk.Combobox(row, textvariable=self._user, width=10,
                     values=["Ann", "Ben", "Cara", "Dev", "Ella"],
                     state="readonly").pack(side="left", padx=6)
        ttk.Button(row, text="Recommend", command=self._run).pack(side="left")
        self._canvas = tk.Canvas(self, width=520, height=320, bg="white",
                                 highlightthickness=1, highlightbackground="#ccc")
        self._canvas.pack()
        self._info = ttk.Label(self, text="", justify="left")
        self._info.pack(anchor="w", pady=6)
        self._run()

    @staticmethod
    def _build_engine() -> RecommendationEngine:
        engine = RecommendationEngine()
        for book in [
            Book("b1", "Clean Code"), Book("b2", "Pragmatic Programmer"),
            Book("b3", "Intro to Algorithms"), Book("b4", "Deep Learning"),
            Book("b5", "The Hobbit"), Book("b6", "Dune"),
        ]:
            engine.add_book(book)
        reading = {
            "Ann": ["b1", "b2", "b3"], "Ben": ["b1", "b2", "b4"],
            "Cara": ["b3", "b4", "b6"], "Dev": ["b1", "b3", "b4"],
            "Ella": ["b5", "b6"],
        }
        for uid, books in reading.items():
            for bid in books:
                engine.record_reading(uid, bid)
        return engine

    def _run(self) -> None:
        user = self._user.get()
        try:
            recs = self._engine.recommend(user, limit=5)
        except KeyError as exc:
            messagebox.showerror("Error", str(exc))
            return
        labels = [book.title for book, _ in recs]
        scores = [score for _, score in recs]
        _draw_bar_chart(self._canvas, labels, scores,
                        f"Recommendation score for '{user}'")
        sims = self._engine.similar_users(user)
        self._info.config(
            text="Most similar readers: "
                 + ", ".join(f"{u} ({s:.2f})" for u, s in sims[:3])
        )


class ApplicationWindow(tk.Tk):
    """Top-level window hosting the three problem tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.title("502IT - Algorithms & Data Structures Demonstrator")
        self.geometry("580x470")
        self._apply_greyscale_theme()
        notebook = ttk.Notebook(self)
        notebook.add(DeliveryTab(notebook), text="1. Delivery Routes")
        notebook.add(ResourceTab(notebook), text="2. Resource Allocation")
        notebook.add(RecommendationTab(notebook), text="3. Recommendations")
        notebook.pack(fill="both", expand=True)

    def _apply_greyscale_theme(self) -> None:
        """Force a neutral grey theme so the UI matches the B/W report."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            return
        self.configure(bg="#f2f2f2")
        style.configure(".", background="#f2f2f2", foreground="#000000")
        style.configure("TFrame", background="#f2f2f2")
        style.configure("TLabel", background="#f2f2f2", foreground="#000000")
        style.configure("TButton", background="#d9d9d9", foreground="#000000")
        style.configure("TNotebook", background="#f2f2f2")
        style.configure("TNotebook.Tab", background="#d9d9d9",
                        foreground="#000000")
        style.map("TNotebook.Tab",
                  background=[("selected", "#ffffff")],
                  foreground=[("selected", "#000000")])


def main() -> None:
    ApplicationWindow().mainloop()


if __name__ == "__main__":
    main()
