# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
import sys

from io import StringIO
from unittest.mock import MagicMock

from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader


@pytest.fixture(autouse=True)
def psrp_connection():
    """Imports the psrp connection plugin with a mocked pypsrp module for testing"""

    # Take a snapshot of sys.modules before we manipulate it
    orig_modules = sys.modules.copy()
    try:
        sys.modules["pypsrp.complex_objects"] = MagicMock()
        sys.modules["pypsrp.exceptions"] = MagicMock()
        sys.modules["pypsrp.host"] = MagicMock()
        sys.modules["pypsrp.powershell"] = MagicMock()
        sys.modules["pypsrp.shell"] = MagicMock()
        sys.modules["pypsrp.wsman"] = MagicMock()
        sys.modules["requests.exceptions"] = MagicMock()

        from ansible.plugins.connection import psrp

        # Take a copy of the original import state vars before we set to an ok import
        orig_has_psrp = psrp.HAS_PYPSRP
        orig_psrp_imp_err = psrp.PYPSRP_IMP_ERR

        yield psrp

        psrp.HAS_PYPSRP = orig_has_psrp
        psrp.PYPSRP_IMP_ERR = orig_psrp_imp_err
    finally:
        # Restore sys.modules back to our pre-shenanigans
        sys.modules = orig_modules


class TestConnectionPSRP(object):

    OPTIONS_DATA = (
        # default options
        (
            {},
            {
                '_psrp_auth': 'negotiate',
                '_psrp_configuration_name': 'Microsoft.PowerShell',
                '_psrp_host': 'inventory_hostname',
                '_psrp_conn_kwargs': {
                    'server': 'inventory_hostname',
                    'port': 5986,
                    'username': None,
                    'password': None,
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
                    'certificate_key_pem': None,
                    'certificate_pem': None,
                    'credssp_auth_mechanism': 'auto',
                    'credssp_disable_tlsv1_2': False,
                    'credssp_minimum_version': 2,
                    'negotiate_delegate': None,
                    'negotiate_hostname_override': None,
                    'negotiate_send_cbt': True,
                    'negotiate_service': 'WSMAN',
                    'read_timeout': 30,
                    'reconnection_backoff': 2.0,
                    'reconnection_retries': 0,
                },
                '_psrp_port': 5986,
                '_psrp_user': None
            },
        ),
        # ssl=False when port defined to 5985
        (
            {'ansible_port': '5985'},
            {
                '_psrp_port': 5985,
                '_psrp_conn_kwargs': {'ssl': False},
            },
        ),
        # ssl=True when port defined to not 5985
        (
            {'ansible_port': 1234},
            {
                '_psrp_port': 1234,
                '_psrp_conn_kwargs': {'ssl': True},
            },
        ),
        # port 5986 when ssl=True
        (
            {'ansible_psrp_protocol': 'https'},
            {
                '_psrp_port': 5986,
                '_psrp_conn_kwargs': {'ssl': True},
            },
        ),
        # port 5985 when ssl=False
        (
            {'ansible_psrp_protocol': 'http'},
            {
                '_psrp_port': 5985,
                '_psrp_conn_kwargs': {'ssl': False},
            },
        ),
        # psrp extras
        (
            {'ansible_psrp_mock_test1': True},
            {
                '_psrp_conn_kwargs': {
                    'server': 'inventory_hostname',
                    'port': 5986,
                    'username': None,
                    'password': None,
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
                    'certificate_key_pem': None,
                    'certificate_pem': None,
                    'credssp_auth_mechanism': 'auto',
                    'credssp_disable_tlsv1_2': False,
                    'credssp_minimum_version': 2,
                    'negotiate_delegate': None,
                    'negotiate_hostname_override': None,
                    'negotiate_send_cbt': True,
                    'negotiate_service': 'WSMAN',
                    'read_timeout': 30,
                    'reconnection_backoff': 2.0,
                    'reconnection_retries': 0,
                },
            },
        ),
        # cert validation through string repr of bool
        (
            {'ansible_psrp_cert_validation': 'ignore'},
            {
                '_psrp_conn_kwargs': {'cert_validation': False},
            },
        ),
        # cert validation path
        (
            {'ansible_psrp_cert_trust_path': '/path/cert.pem'},
            {
                '_psrp_conn_kwargs': {'cert_validation': '/path/cert.pem'},
            },
        ),
        # ignore proxy boolean value
        (
            {'ansible_psrp_ignore_proxy': 'true'},
            {
                '_psrp_conn_kwargs': {'no_proxy': True},
            }
        ),
        # ignore proxy false-ish value
        (
            {'ansible_psrp_ignore_proxy': 'n'},
            {
                '_psrp_conn_kwargs': {'no_proxy': False},
            }
        ),
        # ignore proxy true-ish value
        (
            {'ansible_psrp_ignore_proxy': 'y'},
            {
                '_psrp_conn_kwargs': {'no_proxy': True},
            }
        ),
    )

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

            if attr == '_psrp_conn_kwargs':
                for k, v in expected.items():
                    actual_v = actual[k]
                    assert actual_v == v, \
                        f"psrp Protocol kwarg '{k}', actual '{actual_v}' != expected '{v}'"

            else:
                assert actual == expected, \
                    "psrp attr '%s', actual '%s' != expected '%s'"\
                    % (attr, actual, expected)
