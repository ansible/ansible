# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.utils.version import SemanticVersion


EQ = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '1.0.0-beta', False),
    ('1.0.0-beta2+build1', '1.0.0-beta.2+build.1', False),
    ('1.0.0-beta+build', '1.0.0-beta+build', True),
]

NE = [
    ('1.0.0', '1.0.0', False),
    ('1.0.0', '1.0.0-beta', True),
    ('1.0.0-beta2+build1', '1.0.0-beta.2+build.1', True),
    ('1.0.0-beta+build', '1.0.0-beta+build', False),
]

LT = [
    ('1.0.0', '2.0.0', True),
    ('1.0.0-beta', '2.0.0-alpha', True),
    ('1.0.0-alpha', '1.0.0', True),
    ('1.0.0-beta', '1.0.0-alpha3', False),
    ('1.0.0+foo', '1.0.0-alpha', False),
    ('1.0.0-beta.1', '1.0.0-beta.a', True),
]

GT = [
    ('1.0.0', '2.0.0', False),
    ('1.0.0-beta', '2.0.0-alpha', False),
    ('1.0.0-alpha', '1.0.0', False),
    ('1.0.0-beta', '1.0.0-alpha3', True),
    ('1.0.0+foo', '1.0.0-alpha', True),
    ('1.0.0-beta.1', '1.0.0-beta.a', False),
]

LE = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '2.0.0', True),
]

GE = [
    ('1.0.0', '1.0.0', True),
    ('1.0.0', '2.0.0', False),
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
