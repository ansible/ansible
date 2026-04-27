from __future__ import annotations as _annotations

import collections.abc as _c
import typing as _t


class SequenceProxy[T](_c.Sequence[T]):
    """A read-only sequence proxy."""

    # DTFIX5: needs unit test coverage

    __slots__ = ('__value',)

    def __init__(self, value: _c.Sequence[T]) -> None:
        self.__value = value

    @_t.overload
    def __getitem__(self, index: int) -> T: ...

    @_t.overload
    def __getitem__(self, index: slice) -> _c.Sequence[T]: ...

    def __getitem__(self, index: int | slice) -> T | _c.Sequence[T]:
        if isinstance(index, slice):
            return self.__class__(self.__value[index])

        return self.__value[index]

    def __len__(self) -> int:
        return len(self.__value)

    def __contains__(self, item: object) -> bool:
        return item in self.__value

    def __iter__(self) -> _t.Iterator[T]:
        yield from self.__value

    def __reversed__(self) -> _c.Iterator[T]:
        return reversed(self.__value)

    def index(self, *args) -> int:
        return self.__value.index(*args)

    def count(self, value: object) -> int:
        return self.__value.count(value)
