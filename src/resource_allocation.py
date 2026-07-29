"""
Problem 2: Dynamic Resource Allocation.

Simulate a task manager that assigns a limited pool of computing resources
(e.g. CPU cores) to incoming processes according to a scheduling policy.
Several classic policies are implemented behind a common interface so they can
be swapped and compared:

    * First-Come-First-Served (FCFS)  - order of arrival.
    * Shortest Job First (SJF)        - shortest burst first (non-preemptive).
    * Priority Scheduling             - highest priority first.
    * Round Robin (RR)                - time-sliced, preemptive rotation.

Object-oriented design
----------------------
* ``Process``      - encapsulates a job's identity, timing and priority, and
                     tracks its own remaining work.
* ``ResourcePool`` - models a fixed number of interchangeable resource units
                     and enforces acquire/release safely.
* ``Scheduler``    - an *abstract base class* defining the scheduling contract.
* The four concrete schedulers *inherit* from ``Scheduler`` and override
  ``_select`` / ``run`` (polymorphism), so ``run_and_report`` works for any of
  them without change.

Heaps (``heapq``) back SJF and Priority scheduling, giving O(log n) selection
of the next process instead of an O(n) scan.
"""

from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Process:
    """A schedulable unit of work.

    ``remaining`` starts equal to ``burst`` and is decremented as the process
    runs, which lets the same object model both preemptive and non-preemptive
    execution. Metrics are filled in by the scheduler.
    """

    pid: str
    arrival: int
    burst: int
    priority: int = 0          # lower number == higher priority
    remaining: int = field(init=False)
    start_time: Optional[int] = field(default=None, init=False)
    finish_time: Optional[int] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.burst <= 0:
            raise ValueError("Burst time must be positive.")
        self.remaining = self.burst

    @property
    def is_complete(self) -> bool:
        return self.remaining == 0

    @property
    def waiting_time(self) -> int:
        """Turnaround minus service time (assumes single resource unit)."""
        if self.finish_time is None:
            raise ValueError("Process has not finished yet.")
        return (self.finish_time - self.arrival) - self.burst

    @property
    def turnaround_time(self) -> int:
        if self.finish_time is None:
            raise ValueError("Process has not finished yet.")
        return self.finish_time - self.arrival


class ResourcePool:
    """A fixed pool of interchangeable resource units (e.g. CPU cores).

    Encapsulates availability so schedulers cannot over-allocate: ``acquire``
    fails loudly when the pool is exhausted and ``release`` guards against
    returning more units than exist.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("Resource pool needs at least one unit.")
        self._capacity = capacity
        self._in_use = 0

    @property
    def available(self) -> int:
        return self._capacity - self._in_use

    def acquire(self) -> None:
        if self.available <= 0:
            raise RuntimeError("No resource units available.")
        self._in_use += 1

    def release(self) -> None:
        if self._in_use <= 0:
            raise RuntimeError("Releasing a unit that was never acquired.")
        self._in_use -= 1


@dataclass
class ScheduleResult:
    """Immutable-ish summary of a completed simulation."""

    order: List[str]
    avg_waiting: float
    avg_turnaround: float


class Scheduler(ABC):
    """Abstract scheduling policy.

    Sub-classes implement ``run`` to produce the execution order and completion
    times. ``run_and_report`` is shared behaviour that computes averages, so
    callers treat every policy identically (polymorphism).
    """

    name: str = "Abstract"

    def __init__(self, resources: ResourcePool) -> None:
        self._resources = resources

    @abstractmethod
    def run(self, processes: List[Process]) -> List[Process]:
        """Execute the policy and return processes in completion order."""

    def run_and_report(self, processes: List[Process]) -> ScheduleResult:
        completed = self.run([self._clone(p) for p in processes])
        n = len(completed)
        avg_wait = sum(p.waiting_time for p in completed) / n
        avg_turn = sum(p.turnaround_time for p in completed) / n
        return ScheduleResult(
            order=[p.pid for p in completed],
            avg_waiting=avg_wait,
            avg_turnaround=avg_turn,
        )

    @staticmethod
    def _clone(p: Process) -> Process:
        """Fresh copy so repeated runs never see mutated state."""
        return Process(p.pid, p.arrival, p.burst, p.priority)


class FCFSScheduler(Scheduler):
    """First-Come-First-Served: run to completion in arrival order."""

    name = "FCFS"

    def run(self, processes: List[Process]) -> List[Process]:
        clock = 0
        completed: List[Process] = []
        for p in sorted(processes, key=lambda x: (x.arrival, x.pid)):
            clock = max(clock, p.arrival)
            p.start_time = clock
            clock += p.burst
            p.finish_time = clock
            completed.append(p)
        return completed


class ShortestJobFirstScheduler(Scheduler):
    """Non-preemptive SJF using a min-heap keyed on burst time."""

    name = "SJF"

    def run(self, processes: List[Process]) -> List[Process]:
        pending = sorted(processes, key=lambda x: x.arrival)
        ready: List[tuple] = []
        completed: List[Process] = []
        clock = 0
        i = 0
        while i < len(pending) or ready:
            while i < len(pending) and pending[i].arrival <= clock:
                p = pending[i]
                heapq.heappush(ready, (p.burst, p.pid, p))
                i += 1
            if not ready:
                clock = pending[i].arrival  # fast-forward to next arrival
                continue
            _, _, p = heapq.heappop(ready)
            p.start_time = clock
            clock += p.burst
            p.finish_time = clock
            completed.append(p)
        return completed


class PriorityScheduler(Scheduler):
    """Non-preemptive priority scheduling (lower number = higher priority)."""

    name = "Priority"

    def run(self, processes: List[Process]) -> List[Process]:
        pending = sorted(processes, key=lambda x: x.arrival)
        ready: List[tuple] = []
        completed: List[Process] = []
        clock = 0
        i = 0
        while i < len(pending) or ready:
            while i < len(pending) and pending[i].arrival <= clock:
                p = pending[i]
                heapq.heappush(ready, (p.priority, p.pid, p))
                i += 1
            if not ready:
                clock = pending[i].arrival
                continue
            _, _, p = heapq.heappop(ready)
            p.start_time = clock
            clock += p.burst
            p.finish_time = clock
            completed.append(p)
        return completed


class RoundRobinScheduler(Scheduler):
    """Preemptive Round Robin with a fixed time quantum."""

    name = "Round Robin"

    def __init__(self, resources: ResourcePool, quantum: int = 2) -> None:
        super().__init__(resources)
        if quantum < 1:
            raise ValueError("Quantum must be at least 1.")
        self._quantum = quantum

    def run(self, processes: List[Process]) -> List[Process]:
        pending = sorted(processes, key=lambda x: x.arrival)
        queue: List[Process] = []
        completed: List[Process] = []
        clock = 0
        i = 0
        while i < len(pending) or queue:
            while i < len(pending) and pending[i].arrival <= clock:
                queue.append(pending[i])
                i += 1
            if not queue:
                clock = pending[i].arrival
                continue
            p = queue.pop(0)
            if p.start_time is None:
                p.start_time = clock
            slice_time = min(self._quantum, p.remaining)
            clock += slice_time
            p.remaining -= slice_time
            # Admit any processes that arrived during this slice before requeue.
            while i < len(pending) and pending[i].arrival <= clock:
                queue.append(pending[i])
                i += 1
            if p.is_complete:
                p.finish_time = clock
                completed.append(p)
            else:
                queue.append(p)
        return completed


def demo() -> None:
    """Compare all four policies on the same workload (I/O evidence)."""
    workload = [
        Process("P1", arrival=0, burst=7, priority=2),
        Process("P2", arrival=2, burst=4, priority=1),
        Process("P3", arrival=4, burst=1, priority=3),
        Process("P4", arrival=5, burst=4, priority=2),
    ]
    pool = ResourcePool(capacity=1)
    schedulers: List[Scheduler] = [
        FCFSScheduler(pool),
        ShortestJobFirstScheduler(pool),
        PriorityScheduler(pool),
        RoundRobinScheduler(pool, quantum=2),
    ]

    print("Problem 2 - Dynamic Resource Allocation")
    print("-" * 46)
    print(f"{'Policy':<14}{'Order':<22}{'Wait':>6}{'Turn':>7}")
    for s in schedulers:
        r = s.run_and_report(workload)
        order = ",".join(r.order)
        print(f"{s.name:<14}{order:<22}{r.avg_waiting:>6.2f}{r.avg_turnaround:>7.2f}")
    print()


if __name__ == "__main__":
    demo()
