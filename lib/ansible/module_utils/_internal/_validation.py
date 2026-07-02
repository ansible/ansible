from __future__ import annotations

import keyword


def validate_collection_name(collection_name: object, name: str = 'collection_name') -> None:
    """Validate a collection name."""
    if not isinstance(collection_name, str):
        raise TypeError(f"{name} must be {str} instead of {type(collection_name)}")

    parts = collection_name.split('.')

    if len(parts) != 2 or not all(part.isidentifier() and not keyword.iskeyword(part) for part in parts):
        raise ValueError(f"{name} must consist of two non-keyword identifiers separated by '.'")
