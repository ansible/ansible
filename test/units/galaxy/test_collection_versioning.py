# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for collection version requirement matching."""

from __future__ import annotations

import pytest

from ansible.galaxy.dependency_resolution.versioning import meets_requirements


@pytest.mark.parametrize(
    ('requirements', 'expected'),
    (
        ('>=1.0.0,<2.0.0', True),
        ('>=1.0.0, <2.0.0', True),
        ('>= 1.0.0, < 2.0.0', True),
        ('= 1.5.0', True),
        ('== 1.5.0', True),
        ('!= 1.5.0', False),
        ('> 1.5.0', False),
        ('<= 1.4.0', False),
        ('1.5.0 ', True),
        ('* ', True),
    ),
)
def test_meets_requirements_allows_whitespace(requirements: str, expected: bool) -> None:
    assert meets_requirements('1.5.0', requirements) is expected
