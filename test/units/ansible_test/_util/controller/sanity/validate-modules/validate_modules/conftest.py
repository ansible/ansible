from __future__ import annotations


import pytest
import sys

from pathlib import Path


@pytest.fixture(autouse=True, scope='session')
def inject_ansible_test_validate_modules() -> None:
    """Make ansible_test's validate-modules available on `sys.path` for unit testing ansible-test."""
    test_lib = (
        Path(__file__).parent / ".." / ".." / ".." / ".." / ".." / ".." / ".."
        / "lib" / "ansible_test" / "_util" / "controller" / "sanity" / "validate-modules"
    )
    sys.path.insert(0, str(test_lib))
