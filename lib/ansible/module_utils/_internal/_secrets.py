from __future__ import annotations

import typing as _t

from ansible.module_utils._internal._concurrent._fork_safe_lock import ForkSafeLock

try:
    import ahocorasick
except ImportError:
    from ansible.module_utils._internal import _ahocorasick as ahocorasick


_emptyfrozenset: frozenset[str] = frozenset()  # shared frozenset optimization for no secrets found

# If this is ever changed we need to ensure that Ansible.Secrets.cs is updated
# to match.
_MINIMUM_SECRET_LENGTH = 4  # below this, not registered at all
_MAXIMUM_SHORT_SECRET_LENGTH = 6  # above this, mask unconditionally
_MAXIMUM_SECRET_LENGTH = 1024  # secrets longer than this are trimmed to this length before registration


def _is_short_secret(length: int) -> bool:
    return _MINIMUM_SECRET_LENGTH <= length <= _MAXIMUM_SHORT_SECRET_LENGTH


def _sits_at_boundary(value: str, start: int, end: int) -> bool:
    at_beginning = start == 0
    at_end = end == len(value)
    boundary_left = at_beginning or not value[start - 1].isalnum()
    boundary_right = at_end or not value[end].isalnum()
    return boundary_left and boundary_right


class SecretMasker:
    # Instantiating this permanently registers os.register_at_fork handlers (via
    # ForkSafeLock) that cannot be unregistered, so this is intended to be used as a
    # long-lived singleton (see the shared _secret_masker instance below).
    def __init__(self) -> None:
        self._store = ahocorasick.Automaton()
        self._new_secret_trackers: set[NewSecretTracker] = set()
        self._lock = ForkSafeLock()

    def track_new_secrets(self) -> NewSecretTracker:
        with self._lock:
            self._new_secret_trackers.add(st := NewSecretTracker(self))
        return st

    def register_secret_text(self, secret: str) -> str:
        if len(secret) < _MINIMUM_SECRET_LENGTH:
            return secret

        # Overly long secrets are trimmed before registration so only the first
        # _MAXIMUM_SECRET_LENGTH characters are matched and masked.
        trimmed = secret[:_MAXIMUM_SECRET_LENGTH]

        with self._lock:
            if self._store.exists(trimmed):
                return secret

            self._store.add_word(trimmed, len(trimmed))

            for tracker in self._new_secret_trackers:
                tracker._new_secrets.add(trimmed)

            return secret

    def register_secret_texts(self, secrets: _t.Iterable[str]) -> None:
        with self._lock:
            new = set()

            for secret in secrets:
                if len(secret) < _MINIMUM_SECRET_LENGTH:
                    continue
                trimmed = secret[:_MAXIMUM_SECRET_LENGTH]
                if self._store.exists(trimmed):
                    continue
                self._store.add_word(trimmed, len(trimmed))
                new.add(trimmed)

            for tracker in self._new_secret_trackers:
                tracker._new_secrets.update(new)

    def _raw_spans(self, value: str) -> list[tuple[int, int]]:
        """(start, end) positions of every registered secret found in value."""
        with self._lock:
            if self._store.kind == ahocorasick.EMPTY:
                # noop - no secrets registered
                return []
            if self._store.kind != ahocorasick.AHOCORASICK:
                self._store.make_automaton()
            return [(end - length + 1, end + 1) for end, length in self._store.iter_long(value)]

    def _effective_spans(self, value: str) -> list[tuple[int, int]]:
        """Spans to redact: long secrets always, short secrets only when at a word boundary."""
        return [(start, end) for start, end in self._raw_spans(value) if not _is_short_secret(end - start) or _sits_at_boundary(value, start, end)]

    def mask_string(self, value: str, *, mask_placeholder: str = '$REDACTED$') -> str:
        if not value:
            return value

        spans = self._effective_spans(value)

        if not spans:
            return value

        parts = []
        value_pos = 0

        for start, end in spans:
            parts.append(value[value_pos:start])
            parts.append(mask_placeholder)
            value_pos = end

        parts.append(value[value_pos:])

        return ''.join(parts)

    def secrets_in(self, value: str) -> frozenset[str]:
        # Detection, not redaction: report every present secret (even short, non-boundary ones)
        # so child processes learn about them and can mask them if they surface at a boundary there.
        if not value:
            return _emptyfrozenset

        spans = self._raw_spans(value)

        if not spans:
            return _emptyfrozenset

        return frozenset(value[start:end] for start, end in spans)


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
