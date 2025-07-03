from __future__ import annotations

import collections.abc as c


def raise_exceptions(exceptions: c.Sequence[BaseException]) -> None:
    """
    Raise a chain of exceptions from the given exception list.
    Exceptions will be raised starting from the end of the list.
    """
    if len(exceptions) > 1:
        try:
            raise_exceptions(exceptions[1:])
        except Exception as ex:
            raise exceptions[0] from ex

    raise exceptions[0]
