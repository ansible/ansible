from __future__ import annotations

from ast import literal_eval


class FilterModule(object):
    """Python literal eval filter."""

    def filters(self):
        return {
            "python_literal_eval": literal_eval,
        }
