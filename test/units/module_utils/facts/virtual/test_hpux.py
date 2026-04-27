# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.module_utils.facts.virtual.hpux import HPUXVirtual


class MockVirtualSysctl(HPUXVirtual):
    def __init__(self, module):
        self.module = module


def mock_path_exists_vecheck(filename):
    return filename in ("/usr/sbin/vecheck",)


def mock_path_exists_hpvminfo(filename):
    return filename in ("/opt/hpvm/bin/hpvminfo",)


def mock_path_exists_parstatus(filename):
    return filename in ("/usr/sbin/parstatus",)


@pytest.mark.parametrize(
    ("mock_method", "expected_type", "mock_output", "expected_guest"),
    [
        pytest.param(
            mock_path_exists_vecheck,
            "guest",
            "",
            "HP vPar",
            id="HP vPar",
        ),
        pytest.param(
            mock_path_exists_hpvminfo,
            "guest",
            "Running HPVM vPar",
            "HPVM vPar",
            id="HPVM vPar",
        ),
        pytest.param(
            mock_path_exists_hpvminfo,
            "guest",
            "Running HPVM guest",
            "HPVM IVM",
            id="HPVM IVM",
        ),
        pytest.param(
            mock_path_exists_hpvminfo,
            "host",
            "Running HPVM host",
            "HPVM",
            id="HPVM",
        ),
        pytest.param(
            mock_path_exists_parstatus,
            "guest",
            "",
            "HP nPar",
            id="HP nPar",
        ),
    ],
)
def test_get_virtual_facts_hpvpar(mocker, mock_method, expected_type, mock_output, expected_guest):
    mocker.patch("os.path.exists", side_effect=mock_method)
    module = mocker.Mock()
    module.run_command.return_value = (0, mock_output, "")
    mixin = MockVirtualSysctl(module=module)
    guest_facts = mixin.get_virtual_facts()
    expected = {
        "virtualization_role": expected_guest,
        "virtualization_tech_guest": set([expected_guest]),
        "virtualization_tech_host": set(),
        "virtualization_type": expected_type,
    }

    assert guest_facts == expected
