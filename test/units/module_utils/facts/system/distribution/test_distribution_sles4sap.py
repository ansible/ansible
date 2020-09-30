# -*- coding: utf-8 -*-
# Copyright: (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.facts.system.distribution import DistributionFiles


@pytest.mark.parametrize('realpath', ('SUSE_SLES_SAP.prod', 'SLES_SAP.prod'))
def test_distribution_sles4sap_suse_sles_sap(mock_module, mocker, realpath):
    mocker.patch('os.path.islink', return_value=True)
    mocker.patch('os.path.realpath', return_value='/etc/products.d/' + realpath)

    test_input = {
        'name': 'SUSE',
        'path': '',
        'data': 'suse',
        'collected_facts': None,
    }

    test_result = (
        True,
        {
            'distribution': 'SLES_SAP',
        }
    )

    distribution = DistributionFiles(module=mock_module())
    assert test_result == distribution.parse_distribution_file_SUSE(**test_input)
