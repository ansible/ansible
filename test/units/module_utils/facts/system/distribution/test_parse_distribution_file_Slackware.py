# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import pytest

from ansible.module_utils.facts.system.distribution import DistributionFiles


@pytest.mark.parametrize(
    ('distro_file', 'expected_version'),
    (
        ('Slackware', '14.1'),
        ('SlackwareCurrent', '14.2+'),
    )
)
def test_parse_distribution_file_slackware(mock_module, distro_file, expected_version):
    test_input = {
        'name': 'Slackware',
        'data': open(os.path.join(os.path.dirname(__file__), '../../fixtures/distribution_files', distro_file)).read(),
        'path': '/etc/os-release',
        'collected_facts': None,
    }

    result = (
        True,
        {
            'distribution': 'Slackware',
            'distribution_version': expected_version
        }
    )
    distribution = DistributionFiles(module=mock_module())
    assert result == distribution.parse_distribution_file_Slackware(**test_input)
