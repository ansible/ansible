# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import glob
import json
import os
import pytest

from ansible.module_utils.facts.virtual import linux


TESTSETS = []

for datafile in glob.glob(os.path.join(os.path.dirname(__file__), 'fixtures/linux/*.json')):
    with open(os.path.join(os.path.dirname(__file__), '%s' % datafile)) as f:
        TESTSETS.append(json.loads(f.read()))

@pytest.mark.parametrize(
    "testcase",
    TESTSETS,
    ids=lambda x: x.get('description'))
def test_linux_virtualization_facts(mocker, testcase):
    def mock_path_exists(fname):
        return (fname in testcase.get('files', {}) and \
                testcase['files'][fname] is not None) or \
                fname in testcase.get('paths', [])

    def mock_access(fname, mode):
        return mock_path_exists(fname)

    def mock_get_file_content(fname, default=None, strip=True):
        data = default
        if fname in testcase.get('files', {}):
            # for debugging
            print('faked %s for %s' % (fname, testcase['description']))
            data = testcase['files'][fname].strip()
        if strip and data is not None:
            data = data.strip()
        return data

    def mock_get_bin_path(fname):
        return fname if fname in testcase.get('binaries', []) else None

    def mock_run_command(command):
        if command not in testcase.get('commands', {}):
            # If the command doesn't exist in our fixture, assume it won't work.
            return (1, '', '')
        res = testcase['commands'][command]
        return (res['rc'], res['stdout'], res['stderr'])

    mocker.patch('os.path.exists', mock_path_exists)
    mocker.patch('os.access', mock_access)
    mocker.patch('ansible.module_utils.facts.virtual.linux.get_file_content', mock_get_file_content)
    # Make it so we can use get_file_lines without patching.
    mocker.patch('ansible.module_utils.facts.utils.get_file_content', mock_get_file_content)

    module = mocker.Mock()
    module.get_bin_path = mock_get_bin_path
    module.run_command = mock_run_command

    # We use lists in the JSON, but we need to compare against sets
    if 'virtualization_tech_host' in testcase['result']:
        testcase['result']['virtualization_tech_host'] = \
            set(testcase['result']['virtualization_tech_host'])

    if 'virtualization_tech_guest' in testcase['result']:
        testcase['result']['virtualization_tech_guest'] = \
            set(testcase['result']['virtualization_tech_guest'])

    inst = linux.LinuxVirtual(module)
    facts = inst.get_virtual_facts()
    assert facts == testcase['result']


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
        'virtualization_tech_host': set(),
        'virtualization_type': 'bhyve',
        'virtualization_tech_guest': set(['bhyve']),
    }

    assert facts == expected
