"""
Problem 5: Recommendation Engine for a Bookstore.

Recommend books to a user based on the reading habits of *similar* users
(user-based collaborative filtering). Similarity between two users is the
Jaccard index of the sets of books they have read:

        J(A, B) = |A intersect B| / |A union B|

Object-oriented design
----------------------
* ``Book``                 - a value object for a catalogue entry.
* ``User``                 - encapsulates a reader and the *set* of book IDs
                             they have read; set membership gives O(1) tests.
* ``RecommendationEngine`` - stores the user/book relationships in
                             dictionaries and produces ranked recommendations.

Sets and dictionaries are the natural structures here: set operations express
Jaccard similarity directly, and dictionaries give O(1) lookup of users and
books by id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class Book:
    """A catalogue entry."""

    book_id: str
    title: str
    genre: str = "General"


@dataclass
class User:
    """A reader and the set of books they have read.

    ``read`` is a ``set`` so repeated purchases collapse naturally and
    membership / intersection / union are efficient.
    """

    user_id: str
    read: Set[str] = field(default_factory=set)

    def record(self, book_id: str) -> None:
        self.read.add(book_id)


def jaccard_similarity(a: Set[str], b: Set[str]) -> float:
    """Jaccard index of two sets; 0.0 when both are empty."""
    if not a and not b:
        return 0.0
    union = len(a | b)
    if union == 0:
        return 0.0
    return len(a & b) / union


class RecommendationEngine:
    """User-based collaborative filtering over a bookstore catalogue.

    Encapsulation: users and books live in private dictionaries. Callers add
    data through methods and receive plain, ranked results, so the storage
    representation can change (e.g. to a database) without breaking clients.
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._books: Dict[str, Book] = {}

    # -- catalogue / data management ------------------------------------
    def add_book(self, book: Book) -> None:
        self._books[book.book_id] = book

    def add_user(self, user_id: str) -> User:
        user = self._users.setdefault(user_id, User(user_id))
        return user

    def record_reading(self, user_id: str, book_id: str) -> None:
        """Record that a user has read/purchased a book."""
        if book_id not in self._books:
            raise KeyError(f"Unknown book: {book_id!r}")
        self.add_user(user_id).record(book_id)

    # -- queries ---------------------------------------------------------
    def similar_users(self, user_id: str) -> List[Tuple[str, float]]:
        """Rank every other user by Jaccard similarity, most similar first."""
        target = self._require_user(user_id)
        scored = [
            (other.user_id, jaccard_similarity(target.read, other.read))
            for other in self._users.values()
            if other.user_id != user_id
        ]
        scored = [pair for pair in scored if pair[1] > 0.0]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored

    def recommend(self, user_id: str, limit: int = 3) -> List[Tuple[Book, float]]:
        """Recommend unread books, scored by summed similarity of readers.

        A candidate book's score is the sum of the similarities of the users
        who read it (and who are similar to the target). This favours books
        that are popular among close neighbours.
        """
        target = self._require_user(user_id)
        neighbours = self.similar_users(user_id)

        scores: Dict[str, float] = {}
        for other_id, sim in neighbours:
            for book_id in self._users[other_id].read:
                if book_id not in target.read:      # only unread books
                    scores[book_id] = scores.get(book_id, 0.0) + sim

        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(self._books[bid], score) for bid, score in ranked[:limit]]

    # -- helpers ---------------------------------------------------------
    def _require_user(self, user_id: str) -> User:
        if user_id not in self._users:
            raise KeyError(f"Unknown user: {user_id!r}")
        return self._users[user_id]


def demo() -> None:
    """Recommend books for a target reader (I/O evidence)."""
    engine = RecommendationEngine()
    catalogue = [
        Book("b1", "Clean Code", "Software"),
        Book("b2", "The Pragmatic Programmer", "Software"),
        Book("b3", "Introduction to Algorithms", "Computer Science"),
        Book("b4", "Deep Learning", "AI"),
        Book("b5", "The Hobbit", "Fantasy"),
        Book("b6", "Dune", "Sci-Fi"),
    ]
    for book in catalogue:
        engine.add_book(book)

    reading = {
        "Ann":   ["b1", "b2", "b3"],
        "Ben":   ["b1", "b2", "b4"],
        "Cara":  ["b3", "b4", "b6"],
        "Dev":   ["b1", "b3", "b4"],   # target reader
        "Ella":  ["b5", "b6"],
    }
    for user_id, books in reading.items():
        for book_id in books:
            engine.record_reading(user_id, book_id)

    print("Problem 5 - Recommendation Engine")
    print("-" * 46)
    print("Most similar users to 'Dev':")
    for uid, sim in engine.similar_users("Dev"):
        print(f"   {uid:<6} similarity = {sim:.2f}")
    print("Recommended books for 'Dev':")
    for book, score in engine.recommend("Dev"):
        print(f"   {book.title:<28} score = {score:.2f}")
    print()


if __name__ == "__main__":
    demo()
