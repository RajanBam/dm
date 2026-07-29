"""Command-line entry point that runs all three problem demonstrations.

Usage:
    python main.py            # run every demo
    python main.py 1          # run only Problem 1
    python main.py 2 5        # run Problems 2 and 5
    python main.py --gui      # launch the graphical demonstrator
"""

from __future__ import annotations

import sys

from src import delivery_routes, recommendation_engine, resource_allocation

DEMOS = {
    "1": delivery_routes.demo,
    "2": resource_allocation.demo,
    "5": recommendation_engine.demo,
}


def main(argv: list[str]) -> None:
    if "--gui" in argv:
        from src.gui import main as gui_main
        gui_main()
        return

    selected = [a for a in argv if a in DEMOS] or list(DEMOS)
    print("=" * 46)
    print(" 502IT Algorithms & Data Structures - Demos")
    print("=" * 46 + "\n")
    for key in selected:
        DEMOS[key]()


if __name__ == "__main__":
    main(sys.argv[1:])
