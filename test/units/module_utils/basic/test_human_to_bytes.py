# -*- coding: utf-8 -*-
# Copyright: (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.basic import AnsibleModule


@pytest.mark.parametrize('value, isbits, expected', [
    ("4KB", False, 4096),
    ("4KB", None, 4096),
    ("4Kb", True, 4096),
])
def test_validator_function(value: str, isbits: bool | None, expected: int) -> None:
    assert AnsibleModule.human_to_bytes(value, isbits=isbits) == expected


@pytest.mark.parametrize('value, expected', [
    ("4KB", 4096),
])
def test_validator_function_default_isbits(value: str, expected: int) -> None:
    assert AnsibleModule.human_to_bytes(value) == expected


@pytest.mark.parametrize('value, isbits', [
    ("4Kb", False),
    ("4KB", True),
])
def test_validator_functions(value: str, isbits: bool) -> None:
    with pytest.raises(ValueError):
        AnsibleModule.human_to_bytes(value, isbits=isbits)
