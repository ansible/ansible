"""Tests for validate-modules regexes."""
from __future__ import annotations

import pathlib
import sys
from unittest import mock

import pytest


@pytest.fixture(autouse=True, scope='session')
def validate_modules() -> None:
    """Make validate_modules available on sys.path for unit testing."""
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / 'lib/ansible_test/_util/controller/sanity/validate-modules'))

    # Mock out voluptuous to facilitate testing without it, since tests aren't covering anything that uses it.

    sys.modules['voluptuous'] = voluptuous = mock.MagicMock()
    sys.modules['voluptuous.humanize'] = voluptuous.humanize = mock.MagicMock()

    # Mock out antsibull_docs_parser to facilitate testing without it, since tests aren't covering anything that uses it.

    sys.modules['antsibull_docs_parser'] = antsibull_docs_parser = mock.MagicMock()
    sys.modules['antsibull_docs_parser.parser'] = antsibull_docs_parser.parser = mock.MagicMock()
