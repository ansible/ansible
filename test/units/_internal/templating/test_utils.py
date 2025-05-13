from __future__ import annotations

import pytest

from ansible._internal._templating._jinja_common import Marker, MarkerError


def test_marker_repr(marker: Marker) -> None:
    with pytest.raises(MarkerError):
        repr(marker)


def test_marker_str(marker: Marker) -> None:
    with pytest.raises(MarkerError):
        str(marker)


def test_marker_getattr(marker: Marker) -> None:
    assert marker.foo is marker


def test_marker_getattr_dunder(marker: Marker) -> None:
    with pytest.raises(AttributeError):
        _unused = marker.__dunder_that_is_not_defined__


def test_marker_getitem(marker: Marker) -> None:
    assert marker['foo'] is marker
