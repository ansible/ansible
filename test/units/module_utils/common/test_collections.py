# -*- coding: utf-8 -*-
# Copyright (c) 2018–2019, Sviatoslav Sydorenko <webknjaz@redhat.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Test low-level utility functions from ``module_utils.common.collections``."""

from __future__ import annotations

import pytest

from collections.abc import Sequence
from ansible.module_utils.common.collections import ImmutableDict, is_iterable, is_sequence


class SeqStub:
    """Stub emulating a sequence type.

    >>> from collections.abc import Sequence
    >>> assert issubclass(SeqStub, Sequence)
    >>> assert isinstance(SeqStub(), Sequence)
    """


Sequence.register(SeqStub)


TEST_STRINGS = u'he', u'Україна', u'Česká republika'
TEST_STRINGS = TEST_STRINGS + tuple(s.encode('utf-8') for s in TEST_STRINGS)

TEST_ITEMS_NON_SEQUENCES: tuple = (
    {}, object(), frozenset(),
    4, 0.,
) + TEST_STRINGS

TEST_ITEMS_SEQUENCES: tuple = (
    [], (),
    SeqStub(),
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


@pytest.mark.parametrize(
    'seq',
    ([], (), {}, set(), frozenset()),
)
def test_iterable_positive(seq):
    assert is_iterable(seq)


@pytest.mark.parametrize(
    'seq', (object(), 5, 9.)
)
def test_iterable_negative(seq):
    assert not is_iterable(seq)


@pytest.mark.parametrize('string_input', TEST_STRINGS)
def test_iterable_including_strings(string_input):
    assert is_iterable(string_input, include_strings=True)


@pytest.mark.parametrize('string_input', TEST_STRINGS)
def test_iterable_excluding_strings(string_input):
    assert not is_iterable(string_input, include_strings=False)


class TestImmutableDict:
    def test_scalar(self):
        imdict = ImmutableDict({1: 2})
        assert imdict[1] == 2

    def test_string(self):
        imdict = ImmutableDict({u'café': u'くらとみ'})
        assert imdict[u'café'] == u'くらとみ'

    def test_container(self):
        imdict = ImmutableDict({(1, 2): ['1', '2']})
        assert imdict[(1, 2)] == ['1', '2']

    def test_from_tuples(self):
        imdict = ImmutableDict((('a', 1), ('b', 2)))
        assert frozenset(imdict.items()) == frozenset((('a', 1), ('b', 2)))

    def test_from_kwargs(self):
        imdict = ImmutableDict(a=1, b=2)
        assert frozenset(imdict.items()) == frozenset((('a', 1), ('b', 2)))

    def test_immutable(self):
        imdict = ImmutableDict({1: 2})

        expected_reason = r"^'ImmutableDict' object does not support item assignment$"

        with pytest.raises(TypeError, match=expected_reason):
            imdict[1] = 3

        with pytest.raises(TypeError, match=expected_reason):
            imdict[5] = 3

    def test_hashable(self):
        # ImmutableDict is hashable when all of its values are hashable
        imdict = ImmutableDict({u'café': u'くらとみ'})
        assert hash(imdict)

    def test_nonhashable(self):
        # ImmutableDict is unhashable when one of its values is unhashable
        imdict = ImmutableDict({u'café': u'くらとみ', 1: [1, 2]})

        expected_reason = r"unhashable type: 'list'"

        with pytest.raises(TypeError, match=expected_reason):
            hash(imdict)

    def test_len(self):
        imdict = ImmutableDict({1: 2, 'a': 'b'})
        assert len(imdict) == 2

    def test_repr(self):
        initial_data = {1: 2, 'a': 'b'}
        initial_data_repr = repr(initial_data)
        imdict = ImmutableDict(initial_data)
        actual_repr = repr(imdict)
        expected_repr = "ImmutableDict({0})".format(initial_data_repr)
        assert actual_repr == expected_repr
