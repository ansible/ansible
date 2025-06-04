from __future__ import annotations

import pytest

from ansible.template import Templar


@pytest.fixture
def templar():
    return Templar()
