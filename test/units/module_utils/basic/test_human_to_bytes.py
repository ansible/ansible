# -*- coding: utf-8 -*-
# Copyright: (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.basic import AnsibleModule


DATA = [
    ("4KB", False, 4096),
    ("4KB", None, 4096),
    ("4Kb", True, 4096),
]

WO_ISBITS_DATA = [
    ("4KB", 4096),
]

EXCEPTION_DATA = [
    ("4Kb", False),
    ("4KB", True),
]


@pytest.mark.usefixtures("stdin")
@pytest.mark.parametrize('input, isbits, expected', DATA)
def test_validator_function(input, isbits, expected):
    am = AnsibleModule(argument_spec=dict())
    assert am.human_to_bytes(input, isbits=isbits) == expected


@pytest.mark.usefixtures("stdin")
@pytest.mark.parametrize('input, expected', WO_ISBITS_DATA)
def test_validator_functio(input, expected):
    am = AnsibleModule(argument_spec=dict())
    assert am.human_to_bytes(input) == expected


@pytest.mark.usefixtures("stdin")
@pytest.mark.parametrize('input, isbits', EXCEPTION_DATA)
def test_validator_functions(input, isbits):
    am = AnsibleModule(argument_spec=dict())
    with pytest.raises(ValueError):
        am.human_to_bytes(input, isbits=isbits)
