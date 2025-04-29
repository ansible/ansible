from __future__ import annotations

import collections.abc as c


class CustomMapping(c.Mapping):
    """Minimally functional Mapping implementation for testing."""
    def __init__(self, data: dict) -> None:
        self._data = data

    def __getitem__(self, __key):
        return self._data[__key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f'{type(self).__name__}({self._data!r})'


class CustomSequence(c.Sequence):
    """Minimally functional Sequence implementation for testing."""
    def __init__(self, data: list) -> None:
        self._data = data

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f'{type(self).__name__}({self._data!r})'

    def __eq__(self, other):
        return self._data == other


class CustomInt(int): ...


class CustomFloat(float): ...


class CustomStr(str): ...
