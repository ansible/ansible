from __future__ import annotations

import botocore


def test_constraints():
    assert botocore.__version__ == '1.13.50'
