# -*- coding: utf-8 -*-
# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for depresolver dataclass objects."""


import pytest

from ansible.galaxy.dependency_resolution.dataclasses import Requirement


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
        (' != 1.0.0', False),
        (' !=1.0.0', False),
        ('>1.0.0', False),
        ('> 1.0.0', False),
        (' > 1.0.0', False),
        (' >1.0.0', False),
        ('>=1.0.0', False),
        ('>= 1.0.0', False),
        (' >= 1.0.0', False),
        (' >=1.0.0', False),
        ('<1.0.0', False),
        ('< 1.0.0', False),
        (' < 1.0.0', False),
        (' <1.0.0', False),
        ('*', False),
        ('* ', False),
        (' * ', False),
        (' *', False),
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
