# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.facts.virtual import linux


def test_get_virtual_facts_bhyve(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('ansible.module_utils.facts.virtual.linux.get_file_content', return_value='')
    mocker.patch('ansible.module_utils.facts.virtual.linux.get_file_lines', return_value=[])

    module = mocker.Mock()
    module.run_command.return_value = (0, 'BHYVE\n', '')
    inst = linux.LinuxVirtual(module)

    facts = inst.get_virtual_facts()
    expected = {
        'virtualization_role': 'guest',
        'virtualization_type': 'bhyve',
    }

    assert facts == expected
