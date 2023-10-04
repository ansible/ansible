from __future__ import annotations

from .....plugins.module_utils.my_util import hello


def test_hello():
    assert hello('Ansibull') == 'Hello Ansibull'
