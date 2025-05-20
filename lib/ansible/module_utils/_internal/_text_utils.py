from __future__ import annotations as _annotations


def concat_message(left: str, right: str) -> str:
    """Normalize `left` by removing trailing punctuation and spaces before appending new punctuation and `right`."""
    return f'{left.rstrip(". ")}: {right}'
