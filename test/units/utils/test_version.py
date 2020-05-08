# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from distutils.version import LooseVersion, StrictVersion

import pytest

from ansible.utils.version import _Alpha, _Numeric, SemanticVersion


EQ = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '1.0.0-beta', False),
    ('1.0.0-beta2+build1', '1.0.0-beta.2+build.1', False),
    ('1.0.0-beta+build', '1.0.0-beta+build', True),
    ('1.0.0-beta+build1', '1.0.0-beta+build2', True),
    ('1.0.0-beta+a', '1.0.0-alpha+bar', False),
]

NE = [
    ('1.0.0', '1.0.0', False),
    ('1.0.0', '1.0.0-beta', True),
    ('1.0.0-beta2+build1', '1.0.0-beta.2+build.1', True),
    ('1.0.0-beta+build', '1.0.0-beta+build', False),
    ('1.0.0-beta+a', '1.0.0-alpha+bar', True),
]

LT = [
    ('1.0.0', '2.0.0', True),
    ('1.0.0-beta', '2.0.0-alpha', True),
    ('1.0.0-alpha', '2.0.0-beta', True),
    ('1.0.0-alpha', '1.0.0', True),
    ('1.0.0-beta', '1.0.0-alpha3', False),
    ('1.0.0+foo', '1.0.0-alpha', False),
    ('1.0.0-beta.1', '1.0.0-beta.a', True),
    ('1.0.0-beta+a', '1.0.0-alpha+bar', False),
]

GT = [
    ('1.0.0', '2.0.0', False),
    ('1.0.0-beta', '2.0.0-alpha', False),
    ('1.0.0-alpha', '2.0.0-beta', False),
    ('1.0.0-alpha', '1.0.0', False),
    ('1.0.0-beta', '1.0.0-alpha3', True),
    ('1.0.0+foo', '1.0.0-alpha', True),
    ('1.0.0-beta.1', '1.0.0-beta.a', False),
    ('1.0.0-beta+a', '1.0.0-alpha+bar', True),
]

LE = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '2.0.0', True),
    ('1.0.0-alpha', '1.0.0-beta', True),
    ('1.0.0-beta', '1.0.0-alpha', False),
]

GE = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '2.0.0', False),
    ('1.0.0-alpha', '1.0.0-beta', False),
    ('1.0.0-beta', '1.0.0-alpha', True),
]

VALID = [
    "0.0.4",
    "1.2.3",
    "10.20.30",
    "1.1.2-prerelease+meta",
    "1.1.2+meta",
    "1.1.2+meta-valid",
    "1.0.0-alpha",
    "1.0.0-beta",
    "1.0.0-alpha.beta",
    "1.0.0-alpha.beta.1",
    "1.0.0-alpha.1",
    "1.0.0-alpha0.valid",
    "1.0.0-alpha.0valid",
    "1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay",
    "1.0.0-rc.1+build.1",
    "2.0.0-rc.1+build.123",
    "1.2.3-beta",
    "10.2.3-DEV-SNAPSHOT",
    "1.2.3-SNAPSHOT-123",
    "1.0.0",
    "2.0.0",
    "1.1.7",
    "2.0.0+build.1848",
    "2.0.1-alpha.1227",
    "1.0.0-alpha+beta",
    "1.2.3----RC-SNAPSHOT.12.9.1--.12+788",
    "1.2.3----R-S.12.9.1--.12+meta",
    "1.2.3----RC-SNAPSHOT.12.9.1--.12",
    "1.0.0+0.build.1-rc.10000aaa-kk-0.1",
    "99999999999999999999999.999999999999999999.99999999999999999",
    "1.0.0-0A.is.legal",
]

INVALID = [
    "1",
    "1.2",
    "1.2.3-0123",
    "1.2.3-0123.0123",
    "1.1.2+.123",
    "+invalid",
    "-invalid",
    "-invalid+invalid",
    "-invalid.01",
    "alpha",
    "alpha.beta",
    "alpha.beta.1",
    "alpha.1",
    "alpha+beta",
    "alpha_beta",
    "alpha.",
    "alpha..",
    "beta",
    "1.0.0-alpha_beta",
    "-alpha.",
    "1.0.0-alpha..",
    "1.0.0-alpha..1",
    "1.0.0-alpha...1",
    "1.0.0-alpha....1",
    "1.0.0-alpha.....1",
    "1.0.0-alpha......1",
    "1.0.0-alpha.......1",
    "01.1.1",
    "1.01.1",
    "1.1.01",
    "1.2",
    "1.2.3.DEV",
    "1.2-SNAPSHOT",
    "1.2.31.2.3----RC-SNAPSHOT.12.09.1--..12+788",
    "1.2-RC-SNAPSHOT",
    "-1.0.3-gamma+b7718",
    "+justmeta",
    "9.8.7+meta+meta",
    "9.8.7-whatever+meta+meta",
]

PRERELEASE = [
    ('1.0.0-alpha', True),
    ('1.0.0-alpha.1', True),
    ('1.0.0-0.3.7', True),
    ('1.0.0-x.7.z.92', True),
    ('0.1.2', False),
    ('0.1.2+bob', False),
    ('1.0.0', False),
]

STABLE = [
    ('1.0.0-alpha', False),
    ('1.0.0-alpha.1', False),
    ('1.0.0-0.3.7', False),
    ('1.0.0-x.7.z.92', False),
    ('0.1.2', False),
    ('0.1.2+bob', False),
    ('1.0.0', True),
    ('1.0.0+bob', True),
]

LOOSE_VERSION = [
    (LooseVersion('1'), SemanticVersion('1.0.0')),
    (LooseVersion('1-alpha'), SemanticVersion('1.0.0-alpha')),
    (LooseVersion('1.0.0-alpha+build'), SemanticVersion('1.0.0-alpha+build')),
]

LOOSE_VERSION_INVALID = [
    LooseVersion('1.a.3'),
    LooseVersion(),
    'bar',
    StrictVersion('1.2.3'),
]


def test_semanticversion_none():
    assert SemanticVersion().major is None


@pytest.mark.parametrize('left,right,expected', EQ)
def test_eq(left, right, expected):
    assert (SemanticVersion(left) == SemanticVersion(right)) is expected


@pytest.mark.parametrize('left,right,expected', NE)
def test_ne(left, right, expected):
    assert (SemanticVersion(left) != SemanticVersion(right)) is expected


@pytest.mark.parametrize('left,right,expected', LT)
def test_lt(left, right, expected):
    assert (SemanticVersion(left) < SemanticVersion(right)) is expected


@pytest.mark.parametrize('left,right,expected', LE)
def test_le(left, right, expected):
    assert (SemanticVersion(left) <= SemanticVersion(right)) is expected


@pytest.mark.parametrize('left,right,expected', GT)
def test_gt(left, right, expected):
    assert (SemanticVersion(left) > SemanticVersion(right)) is expected


@pytest.mark.parametrize('left,right,expected', GE)
def test_ge(left, right, expected):
    assert (SemanticVersion(left) >= SemanticVersion(right)) is expected


@pytest.mark.parametrize('value', VALID)
def test_valid(value):
    SemanticVersion(value)


@pytest.mark.parametrize('value', INVALID)
def test_invalid(value):
    pytest.raises(ValueError, SemanticVersion, value)


def test_example_precedence():
    # https://semver.org/#spec-item-11
    sv = SemanticVersion
    assert sv('1.0.0') < sv('2.0.0') < sv('2.1.0') < sv('2.1.1')
    assert sv('1.0.0-alpha') < sv('1.0.0')
    assert sv('1.0.0-alpha') < sv('1.0.0-alpha.1') < sv('1.0.0-alpha.beta')
    assert sv('1.0.0-beta') < sv('1.0.0-beta.2') < sv('1.0.0-beta.11') < sv('1.0.0-rc.1') < sv('1.0.0')


@pytest.mark.parametrize('value,expected', PRERELEASE)
def test_prerelease(value, expected):
    assert SemanticVersion(value).is_prerelease is expected


@pytest.mark.parametrize('value,expected', STABLE)
def test_stable(value, expected):
    assert SemanticVersion(value).is_stable is expected


@pytest.mark.parametrize('value,expected', LOOSE_VERSION)
def test_from_loose_version(value, expected):
    assert SemanticVersion.from_loose_version(value) == expected


@pytest.mark.parametrize('value', LOOSE_VERSION_INVALID)
def test_from_loose_version_invalid(value):
    pytest.raises((AttributeError, ValueError), SemanticVersion.from_loose_version, value)


def test_comparison_with_string():
    assert SemanticVersion('1.0.0') > '0.1.0'


def test_alpha():
    assert _Alpha('a') == _Alpha('a')
    assert _Alpha('a') == 'a'
    assert _Alpha('a') != _Alpha('b')
    assert _Alpha('a') != 1
    assert _Alpha('a') < _Alpha('b')
    assert _Alpha('a') < 'c'
    assert _Alpha('a') > _Numeric(1)
    with pytest.raises(ValueError):
        _Alpha('a') < None
    assert _Alpha('a') <= _Alpha('a')
    assert _Alpha('a') <= _Alpha('b')
    assert _Alpha('b') >= _Alpha('a')
    assert _Alpha('b') >= _Alpha('b')

    # The following 3*6 tests check that all comparison operators perform
    # as expected. DO NOT remove any of them, or reformulate them (to remove
    # the explicit `not`)!

    assert _Alpha('a') == _Alpha('a')
    assert not _Alpha('a') != _Alpha('a')  # pylint: disable=unneeded-not
    assert not _Alpha('a') < _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('a') <= _Alpha('a')
    assert not _Alpha('a') > _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('a') >= _Alpha('a')

    assert not _Alpha('a') == _Alpha('b')  # pylint: disable=unneeded-not
    assert _Alpha('a') != _Alpha('b')
    assert _Alpha('a') < _Alpha('b')
    assert _Alpha('a') <= _Alpha('b')
    assert not _Alpha('a') > _Alpha('b')  # pylint: disable=unneeded-not
    assert not _Alpha('a') >= _Alpha('b')  # pylint: disable=unneeded-not

    assert not _Alpha('b') == _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('b') != _Alpha('a')
    assert not _Alpha('b') < _Alpha('a')  # pylint: disable=unneeded-not
    assert not _Alpha('b') <= _Alpha('a')  # pylint: disable=unneeded-not
    assert _Alpha('b') > _Alpha('a')
    assert _Alpha('b') >= _Alpha('a')


def test_numeric():
    assert _Numeric(1) == _Numeric(1)
    assert _Numeric(1) == 1
    assert _Numeric(1) != _Numeric(2)
    assert _Numeric(1) != 'a'
    assert _Numeric(1) < _Numeric(2)
    assert _Numeric(1) < 3
    assert _Numeric(1) < _Alpha('b')
    with pytest.raises(ValueError):
        _Numeric(1) < None
    assert _Numeric(1) <= _Numeric(1)
    assert _Numeric(1) <= _Numeric(2)
    assert _Numeric(2) >= _Numeric(1)
    assert _Numeric(2) >= _Numeric(2)

    # The following 3*6 tests check that all comparison operators perform
    # as expected. DO NOT remove any of them, or reformulate them (to remove
    # the explicit `not`)!

    assert _Numeric(1) == _Numeric(1)
    assert not _Numeric(1) != _Numeric(1)  # pylint: disable=unneeded-not
    assert not _Numeric(1) < _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(1) <= _Numeric(1)
    assert not _Numeric(1) > _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(1) >= _Numeric(1)

    assert not _Numeric(1) == _Numeric(2)  # pylint: disable=unneeded-not
    assert _Numeric(1) != _Numeric(2)
    assert _Numeric(1) < _Numeric(2)
    assert _Numeric(1) <= _Numeric(2)
    assert not _Numeric(1) > _Numeric(2)  # pylint: disable=unneeded-not
    assert not _Numeric(1) >= _Numeric(2)  # pylint: disable=unneeded-not

    assert not _Numeric(2) == _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(2) != _Numeric(1)
    assert not _Numeric(2) < _Numeric(1)  # pylint: disable=unneeded-not
    assert not _Numeric(2) <= _Numeric(1)  # pylint: disable=unneeded-not
    assert _Numeric(2) > _Numeric(1)
    assert _Numeric(2) >= _Numeric(1)
