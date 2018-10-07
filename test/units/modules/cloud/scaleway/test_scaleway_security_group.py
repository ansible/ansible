# -*- coding: utf-8 -*-
# Copyright (c) 2018 Pierre-Louis Bonicoli <pierre-louis.bonicoli@libregerbil.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests.mock import patch
from ansible.modules.cloud.scaleway import scaleway_security_group
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic

import pytest
import json


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_without_required_parameters(capfd, mocker):
    """Failure must occurs when all parameters are missing"""
    with pytest.raises(SystemExit):
        scaleway_security_group.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'missing required arguments' in results['msg']


ORGANIZATION = '4baf5549-9fe7-44d4-b4e8-0aed8d78989e'
TESTED_MODULE = scaleway_security_group.__name__
TEST_CASES = [
    [
        # non existent security group => not changed, not failed
        {
            'state': 'absent',
            'region': 'par1',
            'name': 'security_group',
            'description': 'my security group description',
            'organization': ORGANIZATION,
            'stateful': False,
            'api_token': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
        },
        {
            'calls': [
                [
                    {
                        'security_groups': [{
                            'stateful': False,
                            'outbound_default_policy': 'accept',
                            'organization_default': True,
                            'inbound_default_policy': 'accept',
                            'name': 'Default security group',
                            'organization': ORGANIZATION,
                            'enable_default_security': True,
                            'servers': [
                                {
                                    'id': 'e84b015c-7446-4b91-bbf4-6a6d6039cce0',
                                    'name': 'server1'
                                },
                                {
                                    'id': 'a043f90b-7254-4e5a-ad49-3b210077a681',
                                    'name': 'server2'
                                }],
                            'id': '7dbf5501-47e7-49d0-b7c4-c5e35a0fac8f',
                            'description': 'Auto generated security group.'
                        }]
                    },
                    {
                        'url': 'https://cp-par1.scaleway.com/security_groups',
                        'server': 'Tengine',
                        'content-type': 'application/json',
                        'status': 200
                    }
                ],
            ],
            'changed': False,
            'failed': False
        }
    ],
]


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_scaleway_security_group(mocker, capfd, mock_fetch_url, testcase):

    # Workaround for https://github.com/ansible/ansible/pull/45696
    basic.AnsibleModule.ansible_version = '2.8.0'

    with pytest.raises(SystemExit):
        scaleway_security_group.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results.get('changed') == testcase.get('changed')
    assert results.get('failed', False) == testcase.get('failed')
    assert not testcase['calls']  # all calls should have been consumed

    assert mock_fetch_url.call_count == 1
