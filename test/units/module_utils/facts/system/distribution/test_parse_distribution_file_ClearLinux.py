# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import pytest

from ansible.module_utils.facts.system.distribution import DistributionFiles


@pytest.fixture
def test_input():
    return {
        'name': 'Clearlinux',
        'path': '/usr/lib/os-release',
        'collected_facts': None,
    }


def test_parse_distribution_file_clear_linux(mock_module, test_input):
    test_input['data'] = open(os.path.join(os.path.dirname(__file__), '../../fixtures/distribution_files/ClearLinux')).read()

    result = (
        True,
        {
            'distribution': 'Clear Linux OS',
            'distribution_major_version': '28120',
            'distribution_release': 'clear-linux-os',
            'distribution_version': '28120'
        }
    )

    distribution = DistributionFiles(module=mock_module())
    assert result == distribution.parse_distribution_file_ClearLinux(**test_input)


@pytest.mark.parametrize('distro_file', ('CoreOS', 'LinuxMint'))
def test_parse_distribution_file_clear_linux_no_match(mock_module, distro_file, test_input):
    """
    Test against data from Linux Mint and CoreOS to ensure we do not get a reported
    match from parse_distribution_file_ClearLinux()
    """
    test_input['data'] = open(os.path.join(os.path.dirname(__file__), '../../fixtures/distribution_files', distro_file)).read()

    result = (False, {})

    distribution = DistributionFiles(module=mock_module())
    assert result == distribution.parse_distribution_file_ClearLinux(**test_input)
