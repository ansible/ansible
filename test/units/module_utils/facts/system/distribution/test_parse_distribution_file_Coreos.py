# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from units.compat.mock import Mock
from ansible.module_utils.facts.system.distribution import DistributionFiles
from . distribution_data import DISTRIBUTION_FILE_DATA


def mock_module():
    mock_module = Mock()
    mock_module.params = {'gather_subset': ['all'],
                          'gather_timeout': 5,
                          'filter': '*'}
    mock_module.get_bin_path = Mock(return_value=None)
    return mock_module


def test_parse_distribution_file_coreos():
    test_input = {
        'name': 'Coreos',
        'data': DISTRIBUTION_FILE_DATA['coreos'],
        'path': '/etc/os-release',
        'collected_facts': None,
    }

    result = (
        True,
        {
            'distribution': 'Coreos',
            'distribution_major_version': '1911',
            'distribution_release': 'rhyolite',
            'distribution_version': '1911.5.0'
        }
    )

    distribution = DistributionFiles(module=mock_module())
    assert result == distribution.parse_distribution_file_Coreos(**test_input)


def test_parse_distribution_file_coreos_no_match():
    # Test against data from other distributions that use same file path to
    # ensure we do not get an incorrect match.

    scenarios = [
        {
            'case': {
                'name': 'ClearLinux',
                'data': DISTRIBUTION_FILE_DATA['clearlinux'],
                'path': '/etc/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
        {
            'case': {
                'name': 'ClearLinux',
                'data': DISTRIBUTION_FILE_DATA['linuxmint'],
                'path': '/etc/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
        {
            'case': {
                'name': 'Debian',
                'data': DISTRIBUTION_FILE_DATA['debian9'],
                'path': '/etc/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
    ]

    distribution = DistributionFiles(module=mock_module())
    for scenario in scenarios:
        assert scenario['result'] == distribution.parse_distribution_file_Coreos(**scenario['case'])
