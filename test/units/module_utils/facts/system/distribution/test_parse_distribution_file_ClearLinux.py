# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from units.compat.mock import Mock
from ansible.module_utils.facts.system.distribution import DistributionFiles


def mock_module():
    mock_module = Mock()
    mock_module.params = {'gather_subset': ['all'],
                          'gather_timeout': 5,
                          'filter': '*'}
    mock_module.get_bin_path = Mock(return_value=None)
    return mock_module


def test_parse_distribution_file_clear_linux():
    test_input = {
        'name': 'Clearlinux',
        'data': 'NAME="Clear Linux OS"\nVERSION=1\nID=clear-linux-os\nID_LIKE=clear-linux-os\nVERSION_ID=28120\nPRETTY_NAME="Clear Linux OS"\nANSI_COLOR="1;35"'
                '\nHOME_URL="https://clearlinux.org"\nSUPPORT_URL="https://clearlinux.org"\nBUG_REPORT_URL="mailto:dev@lists.clearlinux.org"',
        'path': '/usr/lib/os-release',
        'collected_facts': None,
    }

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


def test_parse_distribution_file_clear_linux_no_match():
    # Test against data from Linux Mint and CoreOS to ensure we do not get a reported
    # match from parse_distribution_file_ClearLinux()

    scenarios = [
        {
            # CoreOS
            'case': {
                'name': 'Clearlinux',
                'data': 'NAME="Container Linux by CoreOS"\nID=coreos\nVERSION=1911.5.0\nVERSION_ID=1911.5.0\nBUILD_ID=2018-12-15-2317\nPRETTY_NAME="Container L'
                        'inux by CoreOS 1911.5.0 (Rhyolite)"\nANSI_COLOR="38;5;75"\nHOME_URL="https://coreos.com/"\nBUG_REPORT_URL="https://issues.coreos.com"'
                        '\nCOREOS_BOARD="amd64-usr"',
                'path': '/usr/lib/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
        {
            # Linux Mint
            'case': {
                'name': 'Clearlinux',
                'data': 'NAME="Linux Mint"\nVERSION="19.1 (Tessa)"\nID=linuxmint\nID_LIKE=ubuntu\nPRETTY_NAME="Linux Mint 19.1"\nVERSION_ID="19.1"\nHOME_URL="h'
                        'ttps://www.linuxmint.com/"\nSUPPORT_URL="https://forums.ubuntu.com/"\nBUG_REPORT_URL="http://linuxmint-troubleshooting-guide.readthedo'
                        'cs.io/en/latest/"\nPRIVACY_POLICY_URL="https://www.linuxmint.com/"\nVERSION_CODENAME=tessa\nUBUNTU_CODENAME=bionic',
                'path': '/usr/lib/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
    ]

    distribution = DistributionFiles(module=mock_module())
    for scenario in scenarios:
        assert scenario['result'] == distribution.parse_distribution_file_ClearLinux(**scenario['case'])
