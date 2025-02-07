# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for depresolver dataclass objects."""


from __future__ import annotations

import pytest

from ansible.galaxy.dependency_resolution.dataclasses import Requirement


NO_LEADING_WHITESPACES = pytest.mark.xfail(
    reason='Does not yet support leading whitespaces',
    strict=True,
)


@pytest.mark.parametrize(
    ('collection_version_spec', 'expected_is_pinned_outcome'),
    (
        ('1.2.3-dev4', True),
        (' 1.2.3-dev4', True),
        ('=1.2.3', True),
        ('= 1.2.3', True),
        (' = 1.2.3', True),
        (' =1.2.3', True),
        ('==1.2.3', True),
        ('== 1.2.3', True),
        (' == 1.2.3', True),
        (' ==1.2.3', True),
        ('!=1.0.0', False),
        ('!= 1.0.0', False),
        pytest.param(' != 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' !=1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('>1.0.0', False),
        ('> 1.0.0', False),
        pytest.param(' > 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' >1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('>=1.0.0', False),
        ('>= 1.0.0', False),
        pytest.param(' >= 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' >=1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('<1.0.0', False),
        ('< 1.0.0', False),
        pytest.param(' < 1.0.0', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' <1.0.0', False, marks=NO_LEADING_WHITESPACES),
        ('*', False),
        ('* ', False),
        pytest.param(' * ', False, marks=NO_LEADING_WHITESPACES),
        pytest.param(' *', False, marks=NO_LEADING_WHITESPACES),
        ('=1.2.3,!=1.2.3rc5', True),
    ),
)
def test_requirement_is_pinned_logic(
        collection_version_spec: str,
        expected_is_pinned_outcome: bool,
) -> None:
    """Test how Requirement's is_pinned property detects pinned spec."""
    assert Requirement(
        'namespace.collection', collection_version_spec,
        None, None, None,
    ).is_pinned is expected_is_pinned_outcome
