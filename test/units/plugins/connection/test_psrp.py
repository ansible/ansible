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

pytest.importorskip("pypsrp")


class TestConnectionWinRM(object):

    OPTIONS_DATA = (
        # default options
        (
            {'_extras': {}},
            {
                '_psrp_auth': 'negotiate',
                '_psrp_cert_validation': True,
                '_psrp_configuration_name': 'Microsoft.PowerShell',
                '_psrp_connection_timeout': 30,
                '_psrp_message_encryption': 'auto',
                '_psrp_host': 'inventory_hostname',
                '_psrp_conn_kwargs': {
                    'server': 'inventory_hostname',
                    'port': 5986,
                    'username': None,
                    'password': '',
                    'ssl': True,
                    'path': 'wsman',
                    'auth': 'negotiate',
                    'cert_validation': True,
                    'connection_timeout': 30,
                    'encryption': 'auto',
                    'proxy': None,
                    'no_proxy': False,
                    'max_envelope_size': 153600,
                    'operation_timeout': 20,
                },
                '_psrp_max_envelope_size': 153600,
                '_psrp_ignore_proxy': False,
                '_psrp_operation_timeout': 20,
                '_psrp_pass': '',
                '_psrp_path': 'wsman',
                '_psrp_port': 5986,
                '_psrp_proxy': None,
                '_psrp_protocol': 'https',
                '_psrp_user': None
            },
        ),
        # ssl=False when port defined to 5985
        (
            {'_extras': {}, 'ansible_port': '5985'},
            {
                '_psrp_port': 5985,
                '_psrp_protocol': 'http'
            },
        ),
        # ssl=True when port defined to not 5985
        (
            {'_extras': {}, 'ansible_port': 1234},
            {
                '_psrp_port': 1234,
                '_psrp_protocol': 'https'
            },
        ),
        # port 5986 when ssl=True
        (
            {'_extras': {}, 'ansible_psrp_protocol': 'https'},
            {
                '_psrp_port': 5986,
                '_psrp_protocol': 'https'
            },
        ),
        # port 5985 when ssl=False
        (
            {'_extras': {}, 'ansible_psrp_protocol': 'http'},
            {
                '_psrp_port': 5985,
                '_psrp_protocol': 'http'
            },
        ),
        # psrp extras
        (
            {'_extras': {'ansible_psrp_negotiate_delegate': True}},
            {
                '_psrp_conn_kwargs': {
                    'server': 'inventory_hostname',
                    'port': 5986,
                    'username': None,
                    'password': '',
                    'ssl': True,
                    'path': 'wsman',
                    'auth': 'negotiate',
                    'cert_validation': True,
                    'connection_timeout': 30,
                    'encryption': 'auto',
                    'proxy': None,
                    'no_proxy': False,
                    'max_envelope_size': 153600,
                    'operation_timeout': 20,
                    'negotiate_delegate': True,

                },
            },
        ),
        # cert validation through string repr of bool
        (
            {'_extras': {}, 'ansible_psrp_cert_validation': 'ignore'},
            {
                '_psrp_cert_validation': False
            },
        ),
        # cert validation path
        (
            {'_extras': {}, 'ansible_psrp_cert_trust_path': '/path/cert.pem'},
            {
                '_psrp_cert_validation': '/path/cert.pem'
            },
        ),
    )

    @pytest.mark.skip(reason="tests are not passing")
    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('options, expected',
                             ((o, e) for o, e in OPTIONS_DATA))
    def test_set_options(self, options, expected):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = connection_loader.get('psrp', pc, new_stdin)
        conn.set_options(var_options=options)
        conn._build_kwargs()

        for attr, expected in expected.items():
            actual = getattr(conn, attr)
            assert actual == expected, \
                "psrp attr '%s', actual '%s' != expected '%s'"\
                % (attr, actual, expected)
