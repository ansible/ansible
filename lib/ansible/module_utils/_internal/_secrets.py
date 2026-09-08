"""Secret masking registry.

``SecretMasker`` is the public side: it registers secret values (length rules, trimming, de-duplication,
new-secret tracking, locking) and redacts every occurrence of them from strings. Matching is delegated to
a matcher object with a small interface (``add``, ``spans``) so the algorithm can be swapped,
for example for a compiled extension, without touching the registry semantics:

* every occurrence of every secret is found (overlapping included) and the union of the spans is
  redacted, with overlapping and adjacent spans merged into one placeholder, so no character that
  belongs to a secret occurrence is left visible and the number of secrets is not revealed
* secrets of 4-6 characters are masked only at a word boundary (both neighbours non-alphanumeric or
  the string edge); if the longest secret at a position is rejected a shorter one there may still apply

``_AnchoredMatcher`` is an anchored Aho-Corasick implementation with a few optimisations for Ansible:

* the automaton stores only the first ``_ANCHOR_LEN`` characters of each secret; a hit is verified
  against the full secrets registered under that anchor with slice lookups, so memory is bounded by
  distinct prefixes rather than total secret length, and matching never depends on how long secrets are
* before the full comparison, ``_PROBE_LEN`` characters from the middle of the candidate are checked
  against the middles of the registered secrets of that length, so a near-miss costs the probe rather
  than the full length whatever the secret looks like (shared prefixes and suffixes such as PEM
  headers do not help an attacker trying to overload the matching with long secrets that are not present)
* fail/output links are computed lazily per node and cached by epoch, so registering a secret never
  rebuilds anything
"""

from __future__ import annotations

import gc as _gc
import json.encoder as _json_encoder
import typing as _t

from ansible.module_utils._internal._concurrent._fork_safe_lock import ForkSafeLock

# shared frozenset optimization for no secrets found
_emptyfrozenset: frozenset[str] = frozenset()


# If any of these are changed we need to ensure that Ansible.Secrets.cs is updated to match.
_MINIMUM_SECRET_LENGTH = 4  # below this, not registered at all
_MAXIMUM_SHORT_SECRET_LENGTH = 6  # above this, mask unconditionally
_MAXIMUM_SECRET_LENGTH = 65536  # trims to this length as a cap for registration and matching

# _AnchoredMatcher tuning; neither affects results
_ANCHOR_LEN = 8  # chars of each secret held in the automaton; trades memory against false anchor hits
_PROBE_LEN = 8  # chars compared from the middle of a candidate before the full comparison


def _sits_at_boundary(value: str, start: int, end: int) -> bool:
    """Return True if the candidate at value[start:end] is at a word boundary."""
    at_beginning = start == 0
    at_end = end == len(value)
    boundary_left = at_beginning or not value[start - 1].isalnum()
    boundary_right = at_end or not value[end].isalnum()
    return boundary_left and boundary_right


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Sort spans and merge any that overlap or touch into one, so one placeholder covers them all."""
    if len(spans) < 2:
        return spans
    spans.sort()
    merged = [spans[0]]
    for start, end in spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            if end > last_end:
                merged[-1] = (last_start, end)
        else:
            merged.append((start, end))
    return merged


def _probe_span(length: int) -> tuple[int, int]:
    """(offset, size) of the probe window inside a secret of ``length``: its middle, where structured
    secrets keep their entropy, clipped to the secret for secrets shorter than the probe."""
    size = min(_PROBE_LEN, length)
    return max(0, length // 2 - size // 2), size


class AnsibleSecretMaskError(Exception):
    """Raised when secret masking fails.

    Deliberately carries no reference to the value being masked so that a masking
    failure can never leak the unmasked value through the exception itself.
    """


class _Node:
    __slots__ = ("children", "depth", "lengths", "fail", "out", "epoch")

    def __init__(self, depth: int, fail: _Node | None = None) -> None:
        self.children: dict[str, _Node] = {}
        self.depth = depth

        # anchor node: full-secret lengths under this anchor, longest first; empty when not an anchor
        self.lengths: tuple[int, ...] = ()

        # longest proper suffix of this node's path that is also a path; the root's is itself, and every
        # other node starts at the root until _link computes the real one
        self.fail: _Node = fail if fail is not None else self
        self.out: _Node | None = None  # nearest anchor node on the fail chain (self if this is an anchor)
        self.epoch = -1  # registry epoch fail/out were computed for


class _AnchoredMatcher:
    """Finds every occurrence of the registered words in a string. Not thread-safe; the owner locks.

    Words must already satisfy the registry rules (minimum length, trimmed, not previously added).
    """

    def __init__(self) -> None:
        self._root = _Node(0)
        self._root.epoch = 0

        # Secrets and probes (middle of secrets) are stored by length for lookup during verification.
        self._by_length: dict[int, set[str]] = {}
        self._probes: dict[int, set[str]] = {}  # per length, the middle _PROBE_LEN chars of every word of that length
        self._epoch = 0

    def add(self, word: str) -> None:
        """Add a word to the matcher. The word must already satisfy the registry rules."""
        self._by_length.setdefault(len(word), set()).add(word)

        word_len = len(word)
        offset, size = _probe_span(word_len)
        self._probes.setdefault(word_len, set()).add(word[offset : offset + size])

        node = self._root
        for depth, char in enumerate(word[:_ANCHOR_LEN], start=1):
            child = node.children.get(char)
            if child is None:
                child = _Node(depth, fail=self._root)
                node.children[char] = child

            node = child

        if word_len not in node.lengths:
            node.lengths = tuple(sorted(node.lengths + (word_len,), reverse=True))

        # new nodes can become better fail targets for existing nodes: drop every cached link
        self._epoch += 1
        self._root.epoch = self._epoch

    def spans(self, value: str, boundary_check: bool) -> list[tuple[int, int]]:
        """Every verified word occurrence in ``value`` as (start, end), unsorted, overlapping allowed.

        With ``boundary_check`` the longest valid word at each start is reported (it covers any shorter
        one) and short words are subject to the boundary rule; without it every word is reported.
        """
        root = self._root
        epoch = self._epoch
        value_len = len(value)
        state = root
        children = root.children
        spans: list[tuple[int, int]] = []
        found: set[tuple[int, int]] = set()
        verify = self._verify
        detect_all = self._detect_all

        index = 0
        while index < value_len:
            char = value[index]
            next_state = children.get(char)
            if next_state is None:
                if state is not root:
                    # no edge for this char, follow fail links until one has it, or give up at root
                    while True:
                        state = state.fail
                        children = state.children
                        next_state = children.get(char)
                        if next_state is not None or state is root:
                            break

                if next_state is None:
                    index += 1
                    continue

            state = next_state
            children = state.children
            if state.epoch != epoch:
                self._link(state, value[index - state.depth + 1 : index + 1])

            # every anchor ending at this index: the state's own, then shorter ones along the fail chain
            anchor = state.out
            while anchor is not None:
                start = index - anchor.depth + 1
                if boundary_check:
                    end = verify(value, start, anchor, True)
                    if end > 0:
                        spans.append((start, end))
                else:
                    detect_all(value, start, anchor, found)

                anchor = anchor.fail.out if anchor.fail is not root else None
            index += 1

        return spans if boundary_check else list(found)

    def _link(self, node: _Node, path: str) -> None:
        """Compute fail/out for ``node`` (the state reached by ``path``) for the current epoch."""
        root = self._root
        epoch = self._epoch
        chain = [root]  # chain[depth] is the node for path[:depth]

        for char in path:
            chain.append(chain[-1].children[char])

        for depth in range(1, len(chain)):
            current = chain[depth]
            if current.epoch == epoch:
                continue

            if depth == 1:
                fail = root
            else:
                # walk the parent's fail chain until a node has an edge for this char (or root)
                fail = chain[depth - 1].fail
                char = path[depth - 1]
                while True:
                    candidate = fail.children.get(char)
                    if candidate is not None and candidate is not current:
                        fail = candidate
                        break
                    if fail is root:
                        break
                    if fail.epoch != epoch:
                        self._link(fail, path[depth - 1 - fail.depth : depth - 1])
                    fail = fail.fail

                if fail.epoch != epoch:
                    self._link(fail, path[depth - fail.depth : depth])

            current.fail = fail
            if current.lengths:
                current.out = current
            elif fail is root:
                current.out = None
            else:
                current.out = fail.out

            current.epoch = epoch

    def _verify(self, value: str, start: int, node: _Node, boundary_check: bool) -> int:
        """End of the longest registered word starting at ``start`` under anchor ``node``, or -1."""
        by_length = self._by_length
        probes = self._probes
        value_len = len(value)

        for length in node.lengths:
            end = start + length
            if end > value_len:
                continue

            offset, size = _probe_span(length)
            if value[start + offset : start + offset + size] not in probes[length]:
                continue

            if value[start:end] in by_length[length]:
                if boundary_check and length <= _MAXIMUM_SHORT_SECRET_LENGTH and not _sits_at_boundary(value, start, end):
                    continue

                return end
        return -1

    def _detect_all(self, value: str, start: int, node: _Node, found: set[tuple[int, int]]) -> None:
        """Detection: record every registered word starting at ``start`` under anchor ``node``."""
        by_length = self._by_length
        probes = self._probes
        value_len = len(value)
        for length in node.lengths:
            end = start + length
            if end > value_len:
                continue

            offset, size = _probe_span(length)
            if value[start + offset : start + offset + size] in probes[length] and value[start:end] in by_length[length]:
                found.add((start, end))


class SecretMasker:
    # Instantiating this permanently registers os.register_at_fork handlers (via
    # ForkSafeLock) that cannot be unregistered, so this is intended to be used as a
    # long-lived singleton (see the shared _secret_masker instance below).
    def __init__(self) -> None:
        self._new_secret_trackers: set[NewSecretTracker] = set()
        self._lock = ForkSafeLock()
        self._matcher = _AnchoredMatcher()

        self._secrets: set[str] = set()  # the registered secrets, as given (trimmed)
        self._forms: set[str] = set()  # every string the matcher knows: secrets and their derived forms
        # JSON-encoded form -> the secret it is the encoding of, for forms that differ from the secret
        self._json_forms: dict[str, str] = {}

    def track_new_secrets(self) -> NewSecretTracker:
        with self._lock:
            self._new_secret_trackers.add(tracker := NewSecretTracker(self))
        return tracker

    def register_secret_text(self, secret: str, /) -> str:
        """Register a secret for masking, returning the registered value."""
        if len(secret) >= _MINIMUM_SECRET_LENGTH:
            self.register_secret_texts((secret,))

        return secret

    def register_secret_texts(self, secrets: _t.Iterable[str], /) -> None:
        """Register every secret in ``secrets`` for masking."""
        with self._lock:
            new = set()
            was_enabled = _gc.isenabled()
            _gc.disable()  # trie construction is dominated by the cyclic GC otherwise
            try:
                for secret in secrets:
                    if len(secret) < _MINIMUM_SECRET_LENGTH:
                        continue

                    # FUTURE: Look into string normalisation \u00e9 vs \u0065\u0301, etc. to avoid
                    # leaking secrets that are equivalent but not identical. Would require logic
                    # on the masking side either to normalise and mutate the input or to register
                    # multiple normalised forms of each secret.
                    trimmed = secret[:_MAXIMUM_SECRET_LENGTH]

                    if self._add(trimmed):
                        new.add(trimmed)

            finally:
                if was_enabled:
                    _gc.enable()

            for tracker in self._new_secret_trackers:
                tracker._new_secrets.update(new)

    def mask_string(self, value: str, /, *, mask_placeholder: str = "$REDACTED$") -> str:
        """Masks any registered secret in the provided string with the provided placeholder. Returns the masked string."""
        if not value:
            return value

        try:
            spans = []
            with self._lock:
                if self._forms:
                    spans = self._matcher.spans(value, boundary_check=True)

            spans = _merge_spans(spans)
            if not spans:
                return value

            parts = []
            value_pos = 0

            for start, end in spans:
                parts.append(value[value_pos:start])
                parts.append(mask_placeholder)
                value_pos = end

            parts.append(value[value_pos:])

            return "".join(parts)
        except Exception:
            # We deliberately do not include the value or original exception
            # to avoid leaking secrets through the exception.
            raise AnsibleSecretMaskError("secret masking failed") from None

    def secrets_in_json(self, value: str) -> frozenset[str]:
        """Return the registered secrets present in a JSON document, as their literal values."""
        if not value:
            return _emptyfrozenset

        spans = None
        with self._lock:
            if self._forms:
                spans = self._matcher.spans(value, boundary_check=False)

        if not spans:
            return _emptyfrozenset

        # Every matched form is either a registered secret or a JSON-encoded form derived from one.
        # If it's a derived form, return the secret it was derived from. The result is a set of the
        # literal secrets the JSON represents and not how they appear in the JSON. The receiver of
        # the secrets can register them which builds the derived forms again internally.
        json_forms = self._json_forms
        return frozenset(json_forms.get(form, form) for form in (value[start:end] for start, end in spans))

    def _add(self, secret: str) -> bool:
        """Register ``secret`` (already length-checked and trimmed) and every form it can appear in.

        Returns False if ``secret`` was already registered. A form shared with another secret (a
        secret that is itself the JSON-escaped form of another) is only handed to the matcher once.
        """
        if secret in self._secrets:
            return False

        self._secrets.add(secret)

        # Majority of the output in Ansible is JSON and we use it when transferring module data to
        # the target. As JSON can escape characters we will also register the JSON encoded form of
        # the secret (without quotes). Both UTF-8 and non-ASCII escaped forms are registered as
        # the legacy module serialization profile does ensure_ascii=True while modern does not. If
        # the secret does not contain any special characters nothing extra is added to the registry.
        # FUTURE: measure the cost of deriving both forms on large registries.
        json_ascii_form = _json_encoder.encode_basestring_ascii(secret)[1:-1]
        secret_forms = {secret, json_ascii_form}
        if secret != json_ascii_form:
            # If the ASCII encoded form differs then we need to check the UTF-8 encoded form as well.
            secret_forms.add(_json_encoder.encode_basestring(secret)[1:-1])

        for form in secret_forms:
            if form != secret:
                self._json_forms[form] = secret

            if form in self._forms:
                continue
            self._forms.add(form)
            self._matcher.add(form)

        return True


class NewSecretTracker:
    """Used to track newly registered secrets once the tracker was registered."""

    def __init__(self, masker: SecretMasker):
        self._new_secrets: set[str] = set()
        self._masker = masker

    def unregister(self):
        with self._masker._lock:
            self._masker._new_secret_trackers.discard(self)

    def flush(self) -> frozenset[str]:
        with self._masker._lock:
            if not self._new_secrets:
                return _emptyfrozenset
            flushed = frozenset(self._new_secrets)
            self._new_secrets = set()
        return flushed


_secret_masker = SecretMasker()  # default shared instance
