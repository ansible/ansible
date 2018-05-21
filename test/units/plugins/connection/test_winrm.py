# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from io import StringIO
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader


class TestConnectionWinRM(object):

    OPTIONS_DATA = (
        # default options
        (
            {},
            {'_extras': {}},
            {},
            {
                '_kerb_managed': False,
                '_kinit_cmd': 'kinit',
                '_winrm_connection_timeout': None,
                '_winrm_host': None,
                '_winrm_kwargs': {'username': None, 'password': ''},
                '_winrm_pass': '',
                '_winrm_path': '/wsman',
                '_winrm_port': 5986,
                '_winrm_scheme': 'https',
                '_winrm_transport': ['ssl'],
                '_winrm_user': None
            }
        ),
        # http through port
        (
            {},
            {'_extras': {}, 'ansible_port': 5985},
            {},
            {
                '_winrm_kwargs': {'username': None, 'password': ''},
                '_winrm_port': 5985,
                '_winrm_scheme': 'http',
                '_winrm_transport': ['plaintext'],
            }
        ),
        # kerberos user
        (
            {},
            {'_extras': {}, 'ansible_user': 'user@domain.com'},
            {},
            {
                '_kerb_managed': False,
                '_kinit_cmd': 'kinit',
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': ''},
                '_winrm_pass': '',
                '_winrm_transport': ['kerberos', 'ssl'],
                '_winrm_user': 'user@domain.com'
            }
        ),
        # kerberos user with managed ticket (implicit)
        (
            {'password': 'pass'},
            {'_extras': {}, 'ansible_user': 'user@domain.com'},
            {},
            {
                '_kerb_managed': True,
                '_kinit_cmd': 'kinit',
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': 'pass'},
                '_winrm_pass': 'pass',
                '_winrm_transport': ['kerberos', 'ssl'],
                '_winrm_user': 'user@domain.com'
            }
        ),
        # kerb with managed ticket (explicit)
        (
            {'password': 'pass'},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'managed'},
            {},
            {
                '_kerb_managed': True,
            }
        ),
        # kerb with unmanaged ticket (explicit))
        (
            {'password': 'pass'},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'manual'},
            {},
            {
                '_kerb_managed': False,
            }
        ),
        # transport override (single)
        (
            {},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_transport': 'ntlm'},
            {},
            {
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': ''},
                '_winrm_pass': '',
                '_winrm_transport': ['ntlm'],
            }
        ),
        # transport override (list)
        (
            {},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_transport': ['ntlm', 'certificate']},
            {},
            {
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': ''},
                '_winrm_pass': '',
                '_winrm_transport': ['ntlm', 'certificate'],
            }
        ),
        # winrm extras
        (
            {},
            {'_extras': {'ansible_winrm_server_cert_validation': 'ignore',
                         'ansible_winrm_service': 'WSMAN'}},
            {},
            {
                '_winrm_kwargs': {'username': None, 'password': '',
                                  'server_cert_validation': 'ignore',
                                  'service': 'WSMAN'},
            }
        ),
        # direct override
        (
            {},
            {'_extras': {}, 'ansible_winrm_connection_timeout': 5},
            {'connection_timeout': 10},
            {
                '_winrm_connection_timeout': 10,
            }
        ),
        # user comes from option not play context
        (
            {'username': 'user1'},
            {'_extras': {}, 'ansible_user': 'user2'},
            {},
            {
                '_winrm_user': 'user2',
                '_winrm_kwargs': {'username': 'user2', 'password': ''}
            }
        )
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('play, options, direct, expected',
                             ((p, o, d, e) for p, o, d, e in OPTIONS_DATA))
    def test_set_options(self, play, options, direct, expected):
        pc = PlayContext()
        for attr, value in play.items():
            setattr(pc, attr, value)

        new_stdin = StringIO()
        conn = connection_loader.get('winrm', pc, new_stdin)
        conn.set_options(var_options=options, direct=direct)

        for attr, expected in expected.items():
            actual = getattr(conn, attr)
            assert actual == expected, \
                "winrm attr '%s', actual '%s' != expected '%s'"\
                % (attr, actual, expected)
