"""Pure-Python Aho-Corasick automaton covering only the API surface area we use.

``iter_long`` implements leftmost-longest, non-overlapping matching to match the
C extension. For every registered word of length >= 2 it produces exactly the
matches the C library does; the two diverge only for length-1 words (see
``iter_long``), so callers that need parity must enforce a minimum word length.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

# Module-level "kind" constants, mimicking the C extension (``ahocorasick.EMPTY``).
EMPTY = 0
TRIE = 1
AHOCORASICK = 2


# deprecated: description='switch to a proper dataclass' python_version='3.9'
class _ACNode:
    """A single trie/automaton state

    Uses a bare class with manual __slots__ because using default values
    breaks a __slots__ declaration on a dataclass."""

    __slots__ = ("children", "fail", "depth", "is_word", "value", "word_node")

    def __init__(self, depth: int = 0) -> None:
        self.children: dict[str, _ACNode] = {}
        self.fail: _ACNode | None = None
        self.depth = depth
        self.is_word = False
        self.value: object = None
        # Node ending the longest word that ends here (self or an inherited suffix;
        # None if none). Its .depth is the word length, .value what iter_long yields.
        self.word_node: _ACNode | None = None


# deprecated: description='add slots=True' python_version='3.9'
@dataclass(frozen=True)
class _Candidate:
    """A best-so-far, uncommitted ``iter_long`` match."""

    __slots__ = ("start", "end", "value")

    start: int
    end: int
    value: object


class Automaton:
    """Minimal drop-in for C extension ``ahocorasick.Automaton``"""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """The constructor ignores the C extension's ``value_type``/``key_type`` args."""
        self._root = _ACNode()
        self._word_count = 0
        self.kind = EMPTY

    def add_word(self, word: str, value: object = None) -> bool:
        """Register ``word`` with ``value`` (echoed back by ``iter_long``).

        Returns ``True`` if newly added; re-adding overwrites the value. Resets
        ``kind`` to ``TRIE``, invalidating any built automaton.
        """
        if not isinstance(word, str):
            raise TypeError("string expected")
        if not word:
            return False

        node = self._root
        for ch in word:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = _ACNode(depth=node.depth + 1)
                node.children[ch] = nxt
            node = nxt

        node.value = value
        is_new = not node.is_word
        node.is_word = True
        if is_new:
            self._word_count += 1

        self.kind = TRIE
        return is_new

    def exists(self, word: str) -> bool:
        """Return ``True`` if ``word`` is registered."""
        if not isinstance(word, str):
            raise TypeError("string expected")
        node = self._root
        for ch in word:
            node = node.children.get(ch)
            if node is None:
                return False
        return node.is_word

    __contains__ = exists

    def make_automaton(self) -> None:
        """Compute the Aho-Corasick fail links and per-state ``word_node``.

        A breadth-first pass wires each fail link, then sets each state's
        ``word_node`` (longest word ending there) from itself or its fail link.
        """
        root = self._root
        root.fail = root

        queue: deque[_ACNode] = deque()
        for child in root.children.values():
            child.fail = root
            queue.append(child)

        while queue:
            node = queue.popleft()
            if node.is_word:
                node.word_node = node
            elif node.fail is not root:
                node.word_node = node.fail.word_node  # inherit via the fail link

            for ch, child in node.children.items():
                fail_node = node.fail
                while ch not in fail_node.children and fail_node is not root:
                    fail_node = fail_node.fail
                child.fail = fail_node.children.get(ch, root)
                if child.fail is child:  # degenerate self-loop guard
                    child.fail = root
                queue.append(child)

        self.kind = AHOCORASICK if self._word_count else EMPTY

    def iter_long(self, string: str) -> Iterable[tuple[int, object]]:
        """Yield ``(end_index, value)`` for leftmost-longest, non-overlapping matches.

        Diverges from the C extension only for length-1 words: {"a", "aaa"} on "aa"
        yields [(0, 1)] with python vs [(0, 1), (1, 1)] with C.

        ``end_index`` is the final character's index; ``value`` is what was
        stored for the word via ``add_word``. Invariants (do not "simplify" away):

        1. Fail links are followed only while seeking, never while extending.
        2. On commit, resume at ``end + 1`` to re-scan the probe overshoot while
           staying non-overlapping.
        3. ``start <= candidate.start`` (not ``==``): the candidate state may sit
           deeper than its word, so extending can surface a longer word starting
           before ``candidate.start``; a shorter suffix is ignored.
        """
        if not isinstance(string, str):
            raise TypeError("string required")

        root = self._root
        state = root
        i = 0

        candidate: _Candidate | None = None

        while i < len(string):
            ch = string[i]

            if (nxt := state.children.get(ch)) is not None:
                # Descend the goto edge; record a match if at least as leftward (invariant 3).
                state = nxt
                if (w := state.word_node) is not None:
                    start = i - w.depth + 1
                    if candidate is None or start <= candidate.start:
                        candidate = _Candidate(start, i, w.value)
                i += 1
            elif candidate is not None:
                # Extending dead-ends: commit and resume past its end (invariant 2).
                yield candidate.end, candidate.value
                i = candidate.end + 1
                state = root
                candidate = None
            elif state is root:
                i += 1  # seeking, no edge at the un-seeded root: skip this char
            else:
                state = state.fail  # seeking: follow one fail link, re-try goto next iter

        if candidate is not None:  # input ended with a match still candidate
            yield candidate.end, candidate.value
