# -*- coding: utf-8 -*-
# Copyright (c), Sviatoslav Sydorenko <ssydoren@redhat.com> 2018
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Test low-level utility functions from ``module_utils.common.collections``."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common._collections_compat import Sequence
from ansible.module_utils.common.collections import is_sequence


class SeqStub:
    """Stub emulating a sequence type.

    >>> from collections.abc import Sequence
    >>> assert issubclass(SeqStub, Sequence)
    >>> assert isinstance(SeqStub(), Sequence)
    """


Sequence.register(SeqStub)


TEST_STRINGS = u'he', u'Україна', u'Česká republika'
TEST_STRINGS = TEST_STRINGS + tuple(s.encode('utf-8') for s in TEST_STRINGS)

TEST_ITEMS_NON_SEQUENCES = (
    {}, object(), frozenset(),
    4, 0.,
) + TEST_STRINGS

TEST_ITEMS_SEQUENCES = (
    [], (),
    SeqStub(),
)
TEST_ITEMS_SEQUENCES = TEST_ITEMS_SEQUENCES + (
    # Iterable effectively containing nested random data:
    TEST_ITEMS_NON_SEQUENCES,
)


@pytest.mark.parametrize('sequence_input', TEST_ITEMS_SEQUENCES)
def test_sequence_positive(sequence_input):
    """Test that non-string item sequences are identified correctly."""
    assert is_sequence(sequence_input)
    assert is_sequence(sequence_input, include_strings=False)


@pytest.mark.parametrize('non_sequence_input', TEST_ITEMS_NON_SEQUENCES)
def test_sequence_negative(non_sequence_input):
    """Test that non-sequences are identified correctly."""
    assert not is_sequence(non_sequence_input)


@pytest.mark.parametrize('string_input', TEST_STRINGS)
def test_sequence_string_types_with_strings(string_input):
    """Test that ``is_sequence`` can separate string and non-string."""
    assert is_sequence(string_input, include_strings=True)


@pytest.mark.parametrize('string_input', TEST_STRINGS)
def test_sequence_string_types_without_strings(string_input):
    """Test that ``is_sequence`` can separate string and non-string."""
    assert not is_sequence(string_input, include_strings=False)
