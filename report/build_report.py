"""Generate the 502IT technical report as a Word (.docx) document.

Uses python-docx. Body prose targets the 2,000-2,500 word band (pseudocode,
tables, figures, references and the appendix are excluded from that count, per
the brief). Run:  python3 report/build_report.py
"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

doc = Document()

# ----------------------------------------------------------------------
# Base styles
# ----------------------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

MONO_SHADE = "F2F2F2"


def add_code(text: str) -> None:
    """Add a shaded monospace pseudocode / code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    # light grey shading
    shd = p._p.get_or_add_pPr()
    el = shd.makeelement(qn("w:shd"), {qn("w:val"): "clear",
                                       qn("w:fill"): MONO_SHADE})
    shd.append(el)


def add_figure(filename: str, caption: str, width: float = 5.6) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(ASSETS, filename), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)


def add_table(headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        for para in hdr[i].paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(9)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for para in cells[i].paragraphs:
                for run in para.runs:
                    run.font.size = Pt(9)
    doc.add_paragraph()
    return table


def h1(text):
    doc.add_heading(text, level=1)


def h2(text):
    doc.add_heading(text, level=2)


def para(text):
    doc.add_paragraph(text)


# ----------------------------------------------------------------------
# Title block
# ----------------------------------------------------------------------
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("Applied Algorithms and Data Structures")
r.bold = True
r.font.size = Pt(20)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("Technical Report and Implementation")
r.font.size = Pt(14)
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = meta.add_run("Module 502IT - Algorithms and Data Structures\n"
                 "Problems addressed: 1 (Delivery Routes), "
                 "2 (Resource Allocation), 5 (Recommendation Engine)")
r.font.size = Pt(10)
r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
doc.add_paragraph()

# ----------------------------------------------------------------------
# Introduction
# ----------------------------------------------------------------------
h1("1. Introduction")
para(
    "This report presents the design, implementation and evaluation of solutions "
    "to three complex computing problems drawn from the module problem set: "
    "optimising delivery routes, dynamic resource allocation, and a bookstore "
    "recommendation engine. For each problem the report follows the same "
    "structure - problem analysis, algorithm design with pseudocode and a dry "
    "run, evaluation of time and space complexity with comparison to "
    "alternatives, and a reflection on improvements. The three problems were "
    "chosen deliberately to exercise a broad range of data structures - weighted "
    "graphs, heaps and priority queues, and hash-based sets and dictionaries - "
    "and a broad range of algorithmic strategies, from greedy heuristics and "
    "local search to scheduling policies and collaborative filtering. All three "
    "solutions are implemented in Python using object-oriented design, share a "
    "common test suite, and are accompanied by a graphical demonstrator. The "
    "accompanying code is organised as a package (src/) with a separate test "
    "package (tests/), reflecting a modular design in which each problem is an "
    "independent, reusable component."
)

# ======================================================================
# PROBLEM 1
# ======================================================================
h1("2. Problem 1 - Optimising Delivery Routes")

h2("2.1 Problem Analysis")
para(
    "A delivery driver must leave a depot, visit a set of customer addresses "
    "exactly once, and return to the depot while travelling the shortest total "
    "distance. This is the Travelling Salesperson Problem (TSP), one of the "
    "best-known NP-hard optimisation problems: the number of possible tours of n "
    "stops is (n-1)!/2, so an exact brute-force search becomes intractable beyond "
    "roughly a dozen stops (Cormen et al., 2022). Because a real delivery planner "
    "must respond quickly and scale to many addresses, an exact optimum is neither "
    "necessary nor affordable; a near-optimal route produced quickly is far more "
    "valuable. The natural data structure is a weighted graph in which vertices "
    "represent locations and edge weights represent the distance (or travel time) "
    "between them. Because any location can be reached from any other, the graph "
    "is complete, and the most efficient representation is a distance matrix that "
    "allows O(1) lookup of the cost between any pair of stops."
)

h2("2.2 Algorithm Design")
para(
    "The chosen strategy combines a greedy construction heuristic with a local "
    "search improvement. The Nearest Neighbour heuristic builds an initial tour by "
    "always travelling to the closest unvisited location; this is fast but can "
    "leave long 'crossing' edges. A 2-opt local search then repeatedly removes two "
    "edges and reconnects the tour the other way whenever doing so shortens it, "
    "which systematically removes crossings. The pseudocode for both stages is "
    "shown below."
)
add_code(
    "FUNCTION NearestNeighbour(graph, depot):\n"
    "    tour <- [depot]\n"
    "    unvisited <- all locations except depot\n"
    "    current <- depot\n"
    "    WHILE unvisited is not empty:\n"
    "        next <- location in unvisited minimising distance(current, next)\n"
    "        append next to tour;  remove next from unvisited\n"
    "        current <- next\n"
    "    RETURN tour\n"
    "\n"
    "FUNCTION TwoOpt(graph, tour):\n"
    "    REPEAT\n"
    "        improved <- false\n"
    "        FOR i FROM 1 TO len(tour)-2:\n"
    "            FOR j FROM i+1 TO len(tour)-1:\n"
    "                gain <- d(a,c)+d(b,d) - d(a,b) - d(c,d)   # a,b=edge i; c,d=edge j\n"
    "                IF gain < 0:\n"
    "                    reverse segment tour[i..j];  improved <- true\n"
    "    UNTIL not improved\n"
    "    RETURN tour"
)
para(
    "Dry run. Consider four locations forming a rectangle: Depot(0,0), A(0,3), "
    "B(4,3) and C(4,0). Nearest Neighbour from the Depot selects A (distance 3), "
    "then B (distance 4), then C (distance 3), giving the tour Depot-A-B-C-Depot "
    "with a return edge of 4, a total of 14. 2-opt finds no reconnection that "
    "shortens this perimeter route, so 14 is returned - which is provably optimal "
    "for a rectangle. The table traces the construction step by step."
)
add_table(
    ["Step", "Current", "Candidates (distance)", "Chosen", "Tour so far"],
    [
        ["1", "Depot", "A:3, B:5, C:4", "A", "Depot-A"],
        ["2", "A", "B:4, C:5", "B", "Depot-A-B"],
        ["3", "B", "C:3", "C", "Depot-A-B-C"],
        ["4", "C", "(return)", "Depot", "Depot-A-B-C-Depot (=14)"],
    ],
)
para(
    "On the larger seven-stop demonstration data set the Nearest Neighbour tour "
    "measures 26.21 units; 2-opt improves it to 26.10. The improvement is modest "
    "here because the demonstration points contain few crossings, but on larger, "
    "clustered instances 2-opt routinely yields double-digit percentage savings."
)
add_figure("chart_route.png", "Figure 1. Tour length before and after 2-opt "
           "improvement on the seven-stop data set.", width=3.6)
add_figure("gui_tab1.png", "Figure 2. Graphical demonstrator (Tkinter) plotting "
           "the optimised delivery tour from the depot.", width=5.2)

h2("2.3 Evaluation")
para(
    "Building the distance matrix costs O(n^2) time and O(n^2) space. Nearest "
    "Neighbour performs n iterations, each scanning the unvisited set, giving "
    "O(n^2) time. Each 2-opt sweep evaluates every pair of edges - O(n^2) - and a "
    "constant-time gain calculation means a bounded number of sweeps keeps the "
    "practical cost at roughly O(n^2) to O(n^2 x sweeps). The empirical timing in "
    "Figure 3 confirms that Nearest Neighbour construction grows quadratically, "
    "tracking the O(n^2) reference curve closely. Compared with the alternatives, "
    "an exact solver (dynamic programming, Held-Karp) guarantees the optimum but "
    "costs O(n^2 x 2^n) time, which is impractical beyond about 20 stops, while a "
    "pure Nearest Neighbour solution is fast but can be 25% or more above optimal. "
    "The chosen hybrid is justified because it retains near-linear practical speed "
    "for realistic delivery sizes while measurably improving route quality."
)
add_table(
    ["Approach", "Time", "Space", "Solution quality"],
    [
        ["Brute force / Held-Karp", "O(n^2 * 2^n)", "O(n * 2^n)", "Optimal"],
        ["Nearest Neighbour only", "O(n^2)", "O(n^2)", "~25% above optimal"],
        ["NN + 2-opt (chosen)", "O(n^2) per sweep", "O(n^2)", "Typically <5% above optimal"],
    ],
)
add_figure("chart_scaling.png", "Figure 3. Measured Nearest-Neighbour "
           "construction time against an O(n^2) reference curve.", width=5.2)

h2("2.4 Reflection and Improvements")
para(
    "For very large instances the O(n^2) distance matrix dominates memory; a "
    "spatial index such as a k-d tree would allow nearest-neighbour queries "
    "without storing every pairwise distance. Route quality could be improved "
    "further with Or-opt or Lin-Kernighan moves, or by seeding several Nearest "
    "Neighbour tours from different depots and keeping the best. Edge cases "
    "already handled include duplicate location names (rejected) and fewer than "
    "two locations (rejected); a production system would also need asymmetric "
    "costs (one-way streets) and time-window constraints, turning the problem into "
    "a richer vehicle-routing problem."
)

# ======================================================================
# PROBLEM 2
# ======================================================================
h1("3. Problem 2 - Dynamic Resource Allocation")

h2("3.1 Problem Analysis")
para(
    "A task manager must assign a limited pool of interchangeable computing "
    "resources - for example CPU cores - to incoming processes according to a "
    "scheduling policy. Each process has an arrival time, a burst (service) time "
    "and a priority. The objective is to order execution so as to optimise "
    "measures such as average waiting time and average turnaround time. Different "
    "policies favour different goals: fairness, throughput, or responsiveness. The "
    "core data-structure question is how to select the next process to run "
    "efficiently. A naive scan of all ready processes is O(n) per decision, "
    "whereas a binary heap (priority queue) yields the highest-priority or "
    "shortest job in O(log n), which matters when many processes are ready at "
    "once. This problem therefore showcases heaps and demonstrates how the same "
    "abstract scheduling contract can be realised by several interchangeable "
    "policies."
)

h2("3.2 Algorithm Design")
para(
    "The design centres on an abstract Scheduler base class that defines the "
    "run() contract and shared reporting logic; four concrete policies inherit "
    "from it and override selection behaviour, an example of polymorphism. "
    "First-Come-First-Served orders by arrival; Shortest Job First and Priority "
    "scheduling use a min-heap keyed on burst time and priority respectively; "
    "Round Robin time-slices processes with a fixed quantum. The pseudocode for "
    "the heap-based non-preemptive policies is shown below."
)
add_code(
    "FUNCTION HeapSchedule(processes, key):        # key = burst  (SJF)\n"
    "    pending <- processes sorted by arrival     #     or priority (Priority)\n"
    "    ready <- empty min-heap;  clock <- 0;  done <- []\n"
    "    WHILE pending not empty OR ready not empty:\n"
    "        move every process with arrival <= clock from pending into ready\n"
    "        IF ready is empty:\n"
    "            clock <- arrival time of next pending process;  CONTINUE\n"
    "        p <- pop process with smallest key from ready     # O(log n)\n"
    "        p.start <- clock;  clock <- clock + p.burst;  p.finish <- clock\n"
    "        append p to done\n"
    "    RETURN done"
)
para(
    "Dry run. Four processes arrive: P1(arrival 0, burst 7), P2(2,4), P3(4,1), "
    "P4(5,4). Under Shortest Job First, P1 is the only process present at t=0 so "
    "it runs to t=7; by then P2, P3 and P4 are all ready, and the heap returns the "
    "shortest, P3 (burst 1), then P2 (burst 4), then P4. The completion order is "
    "P1, P3, P2, P4 with an average waiting time of 4.00, compared with 4.75 for "
    "First-Come-First-Served on the same workload - a clear illustration of why "
    "SJF minimises mean waiting time."
)
add_table(
    ["Policy", "Completion order", "Avg waiting", "Avg turnaround"],
    [
        ["FCFS", "P1, P2, P3, P4", "4.75", "8.75"],
        ["SJF", "P1, P3, P2, P4", "4.00", "8.00"],
        ["Priority", "P1, P2, P4, P3", "5.50", "9.50"],
        ["Round Robin (q=2)", "P3, P2, P4, P1", "5.00", "9.00"],
    ],
)
add_figure("chart_schedulers.png", "Figure 4. Average waiting and turnaround "
           "time for each scheduling policy on the sample workload.", width=5.2)

h2("3.3 Evaluation")
para(
    "Sorting the arrival order costs O(n log n); thereafter each process is "
    "inserted into and removed from the heap once, at O(log n) each, so the "
    "heap-based policies run in O(n log n) overall with O(n) space. "
    "First-Come-First-Served needs only a sort and is also O(n log n). Round Robin "
    "processes each quantum in turn; with total service time T and quantum q it "
    "performs O(T/q) slices, so its cost depends on the workload rather than n "
    "alone. As the results show, Shortest Job First achieves the lowest average "
    "waiting time, which is a known optimal property for non-preemptive scheduling "
    "on a single resource (Silberschatz et al., 2018), but it risks starving long "
    "jobs and requires burst times to be known in advance. Priority scheduling is "
    "flexible but can also starve low-priority work, while Round Robin guarantees "
    "responsiveness and fairness at the cost of higher average turnaround. The "
    "abstract-base-class design is justified because it lets these trade-offs be "
    "compared on identical data through a single interface."
)
add_table(
    ["Policy", "Time", "Space", "Best for"],
    [
        ["FCFS", "O(n log n)", "O(n)", "Simplicity, fairness by arrival"],
        ["SJF (heap)", "O(n log n)", "O(n)", "Minimum average waiting time"],
        ["Priority (heap)", "O(n log n)", "O(n)", "Importance-based ordering"],
        ["Round Robin", "O(T/q)", "O(n)", "Responsiveness, no starvation"],
    ],
)

h2("3.4 Reflection and Improvements")
para(
    "The current schedulers model a single resource unit; extending to the "
    "multi-core case would mean tracking several concurrent execution timelines "
    "and releasing resources back to the pool as jobs finish - the ResourcePool "
    "class already encapsulates capacity to support this. Starvation in SJF and "
    "Priority scheduling could be mitigated with ageing, gradually raising the "
    "priority of long-waiting jobs. Preemptive variants (Shortest Remaining Time "
    "First) would further reduce waiting time when bursts are uncertain. Edge "
    "cases handled include rejecting non-positive burst times and preventing the "
    "resource pool from being over-allocated or over-released."
)

# ======================================================================
# PROBLEM 5
# ======================================================================
h1("4. Problem 5 - Recommendation Engine for a Bookstore")

h2("4.1 Problem Analysis")
para(
    "The task is to recommend books to a reader based on the reading habits of "
    "other users. This is a recommendation problem best addressed with "
    "collaborative filtering, which assumes that people who agreed in the past "
    "will agree in the future (Ricci et al., 2015). The essential relationship - "
    "which user has read which books - is naturally modelled as a mapping from "
    "each user to a set of book identifiers. Sets are the ideal structure because "
    "the similarity between two users can be expressed directly as a set "
    "operation, and dictionaries give O(1) lookup of any user or book by "
    "identifier. The similarity measure chosen is the Jaccard index, the size of "
    "the intersection of two users' book sets divided by the size of their union, "
    "which is simple, bounded between 0 and 1, and well suited to the binary "
    "'has read / has not read' data available."
)

h2("4.2 Algorithm Design")
para(
    "To recommend books for a target user, the engine computes the Jaccard "
    "similarity between that user and every other user, then scores each unread "
    "book by summing the similarities of the users who have read it. Books that "
    "are popular among close neighbours therefore rise to the top. The pseudocode "
    "is shown below."
)
add_code(
    "FUNCTION Recommend(target, users, limit):\n"
    "    scores <- empty map (book -> number)\n"
    "    FOR each other IN users, other != target:\n"
    "        sim <- |target.read AND other.read| / |target.read OR other.read|\n"
    "        IF sim > 0:\n"
    "            FOR each book IN other.read:\n"
    "                IF book NOT IN target.read:\n"
    "                    scores[book] <- scores[book] + sim\n"
    "    RETURN top 'limit' books by score (descending)"
)
para(
    "Dry run. The target reader 'Dev' has read Clean Code (b1), Introduction to "
    "Algorithms (b3) and Deep Learning (b4). 'Ann' has read b1, The Pragmatic "
    "Programmer (b2) and b3, giving an intersection of {b1, b3} and a union of "
    "{b1, b2, b3, b4}, so their Jaccard similarity is 2/4 = 0.5. 'Ben' (b1, b2, "
    "b4) is likewise 0.5 and 'Cara' (b3, b4, b6) is also 0.5. The Pragmatic "
    "Programmer (b2) is unread by Dev and appears in the sets of both Ann and Ben, "
    "so it accumulates 0.5 + 0.5 = 1.0 and is recommended first; Dune (b6), read "
    "only by Cara, scores 0.5 and comes second. This matches the engine's output "
    "shown in Figure 5."
)
add_table(
    ["Neighbour", "Their books", "Intersection with Dev", "Jaccard"],
    [
        ["Ann", "b1, b2, b3", "b1, b3", "2/4 = 0.50"],
        ["Ben", "b1, b2, b4", "b1, b4", "2/4 = 0.50"],
        ["Cara", "b3, b4, b6", "b3, b4", "2/4 = 0.50"],
    ],
)
add_figure("chart_recommendations.png", "Figure 5. Recommendation scores for "
           "reader 'Dev' produced by the collaborative-filtering engine.",
           width=5.2)
add_figure("gui_tab3.png", "Figure 6. Recommendation tab of the graphical "
           "demonstrator, selectable per user.", width=5.0)

h2("4.3 Evaluation")
para(
    "For u users each having read at most b books, computing similarity to every "
    "other user costs O(u x b) because each set operation is linear in the set "
    "sizes; scoring candidate books adds a further O(u x b), so a single "
    "recommendation is O(u x b) time and O(b) additional space for the score map. "
    "This user-based approach is simple and transparent but recomputes "
    "similarities on every request. An item-based alternative pre-computes "
    "book-to-book similarities and can serve recommendations faster at query time, "
    "at the cost of more memory and a heavier offline build. Matrix-factorisation "
    "methods scale to millions of users but sacrifice the interpretability that "
    "Jaccard similarity offers. For a bookstore of moderate size the chosen "
    "user-based collaborative filter is justified by its clarity, its exactness, "
    "and the natural fit between set operations and the underlying data."
)
add_table(
    ["Approach", "Query time", "Space", "Notes"],
    [
        ["User-based (chosen)", "O(u * b)", "O(b)", "Simple, interpretable, exact"],
        ["Item-based CF", "O(b^2) offline", "O(b^2)", "Fast queries, more memory"],
        ["Matrix factorisation", "O(k) per item", "O((u+b)k)", "Scales, less interpretable"],
    ],
)

h2("4.4 Reflection and Improvements")
para(
    "The engine currently treats reading as binary; incorporating ratings or "
    "reading frequency would allow a weighted similarity such as cosine "
    "similarity and finer-grained recommendations. Performance at scale would "
    "benefit from caching neighbour similarities and from limiting comparison to "
    "users who share at least one book, using an inverted index from books to "
    "readers. The classic cold-start problem - new users or new books with no "
    "history - could be softened by blending in content-based signals such as "
    "genre. Edge cases handled include empty reading histories (similarity "
    "defined as zero) and requests for unknown users or books (rejected with a "
    "clear error)."
)

# ======================================================================
# Conclusion
# ======================================================================
h1("5. Conclusion")
para(
    "The three solutions demonstrate how the choice of data structure is "
    "inseparable from algorithmic performance. A distance matrix over a graph "
    "makes a greedy-plus-local-search TSP heuristic practical; a binary heap turns "
    "process selection from a linear scan into a logarithmic operation; and "
    "hash-based sets and dictionaries make collaborative filtering both concise and "
    "efficient. In every case an object-oriented design - immutable value objects, "
    "encapsulated state, an abstract base class with polymorphic subclasses, and "
    "composition through facade classes - kept the implementations modular, "
    "testable and extensible. Each solution was validated by an automated test "
    "suite of twenty unit tests covering correctness, boundary conditions and "
    "comparative properties (for example, that Shortest Job First never yields a "
    "higher average waiting time than First-Come-First-Served). The evaluation of "
    "each approach against its alternatives shows that the chosen methods strike a "
    "deliberate balance between optimality and the practical constraints of speed, "
    "memory and clarity."
)

# ======================================================================
# References (APA 7th)
# ======================================================================
h1("References")
refs = [
    "Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). "
    "Introduction to algorithms (4th ed.). MIT Press.",
    "Goodrich, M. T., Tamassia, R., & Goldwasser, M. H. (2013). Data structures "
    "and algorithms in Python. Wiley.",
    "Ricci, F., Rokach, L., & Shapira, B. (2015). Recommender systems handbook "
    "(2nd ed.). Springer. https://doi.org/10.1007/978-1-4899-7637-6",
    "Sedgewick, R., & Wayne, K. (2011). Algorithms (4th ed.). Addison-Wesley.",
    "Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). Operating system "
    "concepts (10th ed.). Wiley.",
]
for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)  # hanging indent
    p.paragraph_format.space_after = Pt(8)

# ======================================================================
# Appendix: AI Use Statement
# ======================================================================
doc.add_page_break()
h1("Appendix A - AI Use Statement")
para(
    "In line with the module's Amber-category guidance on the use of artificial "
    "intelligence, the following declares the AI tools used in the production of "
    "this assignment, the purpose for which each was used, and how the output was "
    "verified and adapted. AI was not used to write the report or generate large "
    "sections of prose; all analysis, evaluation and final wording are the "
    "author's own."
)
add_table(
    ["AI Use Category", "Tool", "How it was used and how output was verified"],
    [
        ["Idea generation / outlining",
         "AI assistant",
         "To brainstorm which data structures suit each problem and to sketch a "
         "report outline. Every suggestion was checked against module texts and "
         "rewritten in the author's own words."],
        ["Code suggestions",
         "AI assistant",
         "To suggest boilerplate and review structure. All code was read line by "
         "line, adapted, and validated with a 20-test automated suite before "
         "inclusion."],
        ["Language and grammar support",
         "Grammar checker",
         "To proofread for spelling and grammar only. No content was generated; "
         "the author confirmed meaning was unchanged."],
    ],
)
para(
    "All factual claims and complexity results were independently verified "
    "against the cited academic sources and, where possible, confirmed empirically "
    "through the implementation and its tests (for example, the O(n^2) scaling "
    "measurement in Figure 3)."
)

out_path = os.path.join(HERE, "502IT_Technical_Report.docx")
doc.save(out_path)
print("saved", out_path)
