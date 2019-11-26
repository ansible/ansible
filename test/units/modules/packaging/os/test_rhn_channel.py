# -*- coding: utf-8 -*-
# Copyright (c) 2017 Pierre-Louis Bonicoli <pierre-louis@libregerbil.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.modules.packaging.os import rhn_channel

import pytest


pytestmark = pytest.mark.usefixtures('patch_ansible_module')


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
def test_without_required_parameters(capfd):
    with pytest.raises(SystemExit):
        rhn_channel.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'missing required arguments' in results['msg']


TESTED_MODULE = rhn_channel.__name__
TEST_CASES = [
    [
        # add channel already added, check that result isn't changed
        {
            'name': 'rhel-x86_64-server-6',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.listUserSystems',
                 [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
                ('channel.software.listSystemChannels',
                 [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
                ('auth.logout', [1]),
            ],
            'changed': False,
            'msg': 'Channel rhel-x86_64-server-6 already exists',
        }
    ],
    [
        # add channel, check that result is changed
        {
            'name': 'rhel-x86_64-server-6-debuginfo',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.listUserSystems',
                 [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
                ('channel.software.listSystemChannels',
                 [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
                ('channel.software.listSystemChannels',
                 [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
                ('system.setChildChannels', [1]),
                ('auth.logout', [1]),
            ],
            'changed': True,
            'msg': 'Channel rhel-x86_64-server-6-debuginfo added',
        }
    ],
    [
        # remove inexistent channel, check that result isn't changed
        {
            'name': 'rhel-x86_64-server-6-debuginfo',
            'state': 'absent',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.listUserSystems',
                 [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
                ('channel.software.listSystemChannels',
                 [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
                ('auth.logout', [1]),
            ],
            'changed': False,
            'msg': 'Not subscribed to channel rhel-x86_64-server-6-debuginfo.',
        }
    ],
    [
        # remove channel, check that result is changed
        {
            'name': 'rhel-x86_64-server-6-debuginfo',
            'state': 'absent',
            'sysname': 'server01',
            'url': 'https://rhn.redhat.com/rpc/api',
            'user': 'user',
            'password': 'pass',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.listUserSystems',
                 [[{'last_checkin': '2017-08-06 19:49:52.0', 'id': '0123456789', 'name': 'server01'}]]),
                ('channel.software.listSystemChannels', [[
                    {'channel_name': 'RHEL Server Debuginfo (v.6 for x86_64)', 'channel_label': 'rhel-x86_64-server-6-debuginfo'},
                    {'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}
                ]]),
                ('channel.software.listSystemChannels', [[
                    {'channel_name': 'RHEL Server Debuginfo (v.6 for x86_64)', 'channel_label': 'rhel-x86_64-server-6-debuginfo'},
                    {'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}
                ]]),
                ('system.setChildChannels', [1]),
                ('auth.logout', [1]),
            ],
            'changed': True,
            'msg': 'Channel rhel-x86_64-server-6-debuginfo removed'
        }
    ]
]


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, indirect=['patch_ansible_module'])
def test_rhn_channel(capfd, mocker, testcase, mock_request):
    """Check 'msg' and 'changed' results"""

    with pytest.raises(SystemExit):
        rhn_channel.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['changed'] == testcase['changed']
    assert results['msg'] == testcase['msg']
    assert not testcase['calls']  # all calls should have been consumed
