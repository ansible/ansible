# -*- coding: utf-8 -*-
# Copyright (c) 2018–2019, Sviatoslav Sydorenko <webknjaz@redhat.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Test low-level utility functions from ``module_utils.common.collections``."""

from __future__ import annotations

import pytest

from collections.abc import Sequence
from ansible.module_utils.common.collections import ImmutableDict, OrderedSet, is_iterable, is_sequence


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


class TestOrderedSet:
    def test_init_empty(self):
        o = OrderedSet()
        assert len(o) == 0
        assert list(o) == []

    def test_init_with_iterable(self):
        o = OrderedSet(['foo', 'bar', 'baz'])
        assert list(o) == ['foo', 'bar', 'baz']

    def test_init_deduplication(self):
        o = OrderedSet([1, 2, 1, 3, 2, 4])
        assert list(o) == [1, 2, 3, 4]

    def test_repr(self):
        o = OrderedSet([1, 2, 3])
        assert repr(o) == "OrderedSet([1, 2, 3])"

    def test_repr_empty(self):
        o = OrderedSet()
        assert repr(o) == "OrderedSet([])"

    def test_len(self):
        o = OrderedSet([1, 2, 3])
        assert len(o) == 3

    def test_len_empty(self):
        o = OrderedSet()
        assert len(o) == 0

    @pytest.mark.parametrize('value,expected', [
        ('foo', True),
        ('missing', False),
        (1, False),
    ])
    def test_contains(self, value, expected):
        o = OrderedSet(['foo', 'bar', 'baz'])
        assert (value in o) == expected

    def test_iter_preserves_order(self):
        expected = ['foo', 'bar', 'baz']
        o = OrderedSet(expected)
        assert list(o) == expected

    def test_add(self):
        o = OrderedSet()
        o.add('foo')
        assert 'foo' in o
        assert list(o) == ['foo']

    def test_add_duplicate(self):
        o = OrderedSet(['foo', 'bar'])
        o.add('foo')
        assert list(o) == ['foo', 'bar']

    def test_discard_existing(self):
        o = OrderedSet(['foo', 'bar', 'baz'])
        o.discard('bar')
        assert list(o) == ['foo', 'baz']

    def test_discard_missing(self):
        o = OrderedSet(['foo', 'bar'])
        o.discard('missing')
        assert list(o) == ['foo', 'bar']

    def test_clear(self):
        o = OrderedSet(['foo', 'bar', 'baz'])
        o.clear()
        assert len(o) == 0
        assert list(o) == []

    def test_copy(self):
        o1 = OrderedSet(['foo', 'bar', 'baz'])
        o2 = o1.copy()
        assert o1 == o2
        assert o1 is not o2

    def test_copy_independence(self):
        o1 = OrderedSet(['foo', 'bar'])
        o2 = o1.copy()
        o2.add('baz')
        assert list(o1) == ['foo', 'bar']
        assert list(o2) == ['foo', 'bar', 'baz']

    def test_eq_same_order(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2, 3])
        assert o1 == o2

    def test_eq_different_order(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([3, 2, 1])
        assert o1 != o2

    def test_eq_different_elements(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2, 4])
        assert o1 != o2

    def test_eq_different_length(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2])
        assert o1 != o2

    @pytest.mark.parametrize('other', [
        set([1, 2, 3]),
        [1, 2, 3],
        {1: 2, 2: 3, 3: 4},
        'abc',
    ])
    def test_eq_with_non_orderedset(self, other):
        o = OrderedSet([1, 2, 3])
        assert (o == other) is False

    def test_difference(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        result = o1 - o2
        assert list(result) == ['foo', 'baz']

    def test_difference_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        result = o1.difference(o2)
        assert list(result) == ['foo', 'baz']

    def test_difference_update(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        o1 -= o2
        assert list(o1) == ['foo', 'baz']

    def test_difference_update_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        o1.difference_update(o2)
        assert list(o1) == ['foo', 'baz']

    def test_intersection(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        result = o1 & o2
        assert list(result) == ['bar', 'qux']

    def test_intersection_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        result = o1.intersection(o2)
        assert list(result) == ['bar', 'qux']

    def test_intersection_update(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        o1 &= o2
        assert list(o1) == ['bar', 'qux']

    def test_intersection_update_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham'])
        o1.intersection_update(o2)
        assert list(o1) == ['bar', 'qux']

    def test_union(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        result = o1 | o2
        assert list(result) == ['foo', 'bar', 'baz', 'qux', 'ham', 'sandwich']

    def test_union_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        result = o1.union(o2)
        assert list(result) == ['foo', 'bar', 'baz', 'qux', 'ham', 'sandwich']

    def test_update(self):
        o1 = OrderedSet(['foo', 'bar'])
        o1 |= ['baz', 'qux']
        assert list(o1) == ['foo', 'bar', 'baz', 'qux']

    def test_update_method(self):
        o1 = OrderedSet(['foo', 'bar'])
        o1.update(['baz', 'qux'])
        assert list(o1) == ['foo', 'bar', 'baz', 'qux']

    def test_symmetric_difference(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        result = o1 ^ o2
        assert list(result) == ['foo', 'baz', 'ham', 'sandwich']

    def test_symmetric_difference_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        result = o1.symmetric_difference(o2)
        assert list(result) == ['foo', 'baz', 'ham', 'sandwich']

    def test_symmetric_difference_update(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        o1 ^= o2
        assert list(o1) == ['foo', 'baz', 'ham', 'sandwich']

    def test_symmetric_difference_update_method(self):
        o1 = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        o2 = OrderedSet(['qux', 'bar', 'ham', 'sandwich'])
        o1.symmetric_difference_update(o2)
        assert list(o1) == ['foo', 'baz', 'ham', 'sandwich']

    def test_issubset_true(self):
        o1 = OrderedSet([1, 2])
        o2 = OrderedSet([1, 2, 3])
        assert o1.issubset(o2)
        assert o1 <= o2

    def test_issubset_different_order(self):
        o1 = OrderedSet([2, 1])
        o2 = OrderedSet([1, 2, 3])
        assert o1.issubset(o2)
        assert o1 <= o2

    def test_issubset_false(self):
        o1 = OrderedSet([1, 2, 4])
        o2 = OrderedSet([1, 2, 3])
        assert not o1.issubset(o2)
        assert not (o1 <= o2)  # pylint: disable=unnecessary-negation

    def test_issubset_equal(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2, 3])
        assert o1.issubset(o2)
        assert o1 <= o2

    def test_issuperset_true(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2])
        assert o1.issuperset(o2)
        assert o1 >= o2

    def test_issuperset_different_order(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([2, 1])
        assert o1.issuperset(o2)
        assert o1 >= o2

    def test_issuperset_false(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2, 4])
        assert not o1.issuperset(o2)
        assert not (o1 >= o2)  # pylint: disable=unnecessary-negation

    def test_issuperset_equal(self):
        o1 = OrderedSet([1, 2, 3])
        o2 = OrderedSet([1, 2, 3])
        assert o1.issuperset(o2)
        assert o1 >= o2

    def test_rand_intersection(self):
        o = OrderedSet(['bar', 'qux'])
        s = {'foo', 'bar', 'baz', 'qux'}
        result = s & o
        assert isinstance(result, OrderedSet)
        assert list(result) == ['bar', 'qux']

    def test_ror_union(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = s | o
        assert isinstance(result, OrderedSet)
        assert list(result) == ['foo', 'bar', 'baz', 'qux', 'ham']

    def test_rsub_difference(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = s - o
        assert isinstance(result, OrderedSet)
        assert list(result) == ['ham']

    def test_rxor_symmetric_difference(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = s ^ o
        assert isinstance(result, OrderedSet)
        assert set(result) == {'foo', 'baz', 'ham'}

    def test_intersection_with_regular_set(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = o & s
        assert list(result) == ['bar', 'qux']

    def test_difference_with_regular_set(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = o - s
        assert list(result) == ['foo', 'baz']

    def test_union_with_regular_set(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = o | s
        assert list(result) == ['foo', 'bar', 'baz', 'qux', 'ham']

    def test_symmetric_difference_with_regular_set(self):
        o = OrderedSet(['foo', 'bar', 'baz', 'qux'])
        s = {'qux', 'bar', 'ham'}
        result = o ^ s
        assert set(result) == {'foo', 'baz', 'ham'}

    def test_union_preserves_left_order_for_duplicates(self):
        o1 = OrderedSet([1, 2, 3, 4])
        o2 = OrderedSet([3, 5, 1, 6])
        result = o1 | o2
        assert list(result) == [1, 2, 3, 4, 5, 6]

    def test_update_with_duplicates(self):
        o = OrderedSet([1, 2, 3])
        o.update([3, 4, 1, 5])
        assert list(o) == [1, 2, 3, 4, 5]
