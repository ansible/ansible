from __future__ import annotations

from .....plugins.modules.hello import say_hello


def test_say_hello():
    assert say_hello('Ansibull') == dict(message='Hello Ansibull')
