# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import pytest

from io import StringIO

from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes
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
                '_winrm_host': 'inventory_hostname',
                '_winrm_kwargs': {'username': None, 'password': ''},
                '_winrm_pass': '',
                '_winrm_path': '/wsman',
                '_winrm_port': 5986,
                '_winrm_scheme': 'https',
                '_winrm_transport': ['ssl'],
                '_winrm_user': None
            },
            False
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
            },
            False
        ),
        # kerberos user with kerb present
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
            },
            True
        ),
        # kerberos user without kerb present
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
                '_winrm_transport': ['ssl'],
                '_winrm_user': 'user@domain.com'
            },
            False
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
            },
            True
        ),
        # kerb with managed ticket (explicit)
        (
            {'password': 'pass'},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'managed'},
            {},
            {
                '_kerb_managed': True,
            },
            True
        ),
        # kerb with unmanaged ticket (explicit))
        (
            {'password': 'pass'},
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'manual'},
            {},
            {
                '_kerb_managed': False,
            },
            True
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
            },
            False
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
            },
            False
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
            },
            False
        ),
        # direct override
        (
            {},
            {'_extras': {}, 'ansible_winrm_connection_timeout': 5},
            {'connection_timeout': 10},
            {
                '_winrm_connection_timeout': 10,
            },
            False
        ),
        # user comes from option not play context
        (
            {'username': 'user1'},
            {'_extras': {}, 'ansible_user': 'user2'},
            {},
            {
                '_winrm_user': 'user2',
                '_winrm_kwargs': {'username': 'user2', 'password': ''}
            },
            False
        )
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('play, options, direct, expected, kerb',
                             ((p, o, d, e, k) for p, o, d, e, k in OPTIONS_DATA))
    def test_set_options(self, play, options, direct, expected, kerb):
        if kerb:
            kerberos_mock = MagicMock()
            modules = {'kerberos': kerberos_mock}
        else:
            modules = {'kerberos': None}

        module_patcher = patch.dict(sys.modules, modules)
        module_patcher.start()

        pc = PlayContext()
        for attr, value in play.items():
            setattr(pc, attr, value)

        new_stdin = StringIO()

        # ensure we get a fresh connection plugin by clearing the cache
        connection_loader._module_cache = {}
        conn = connection_loader.get('winrm', pc, new_stdin)
        conn.set_options(var_options=options, direct=direct)

        for attr, expected in expected.items():
            actual = getattr(conn, attr)
            assert actual == expected, \
                "winrm attr '%s', actual '%s' != expected '%s'"\
                % (attr, actual, expected)

        module_patcher.stop()


class TestWinRMKerbAuth(object):

    DATA = (
        # default
        ({"_extras": {}}, (["kinit", "user@domain"],), False),
        ({"_extras": {}}, ("kinit", ["user@domain"],), True),

        # override kinit path from options
        ({"_extras": {}, 'ansible_winrm_kinit_cmd': 'kinit2'},
         (["kinit2", "user@domain"],), False),
        ({"_extras": {}, 'ansible_winrm_kinit_cmd': 'kinit2'},
         ("kinit2", ["user@domain"],), True),

        # we expect the -f flag when delegation is set
        ({"_extras": {'ansible_winrm_kerberos_delegation': True}},
         (["kinit", "-f", "user@domain"],), False),
        ({"_extras": {'ansible_winrm_kerberos_delegation': True}},
         ("kinit", ["-f", "user@domain"],), True),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('options, expected, pexpect',
                             ((o, e, p) for o, e, p in DATA))
    def test_kinit_success(self, options, expected, pexpect):
        def mock_popen_communicate(input=None, timeout=None):
            return b"", b""

        mock_pexpect = None
        if pexpect:
            mock_pexpect = MagicMock()
            mock_pexpect.spawn.return_value.exitstatus = 0

        mock_subprocess = MagicMock()
        mock_subprocess.Popen.return_value.communicate = mock_popen_communicate
        mock_subprocess.Popen.return_value.returncode = 0

        modules = {
            'pexpect': mock_pexpect,
            'subprocess': mock_subprocess,
        }

        with patch.dict(sys.modules, modules):
            pc = PlayContext()
            new_stdin = StringIO()

            connection_loader._module_cache = {}
            conn = connection_loader.get('winrm', pc, new_stdin)
            conn.set_options(var_options=options)

            conn._kerb_auth("user@domain", "pass")
            if pexpect:
                assert len(mock_pexpect.method_calls) == 1
                assert mock_pexpect.method_calls[0][1] == expected
                actual_env = mock_pexpect.method_calls[0][2]['env']
            else:
                assert len(mock_subprocess.method_calls) == 1
                assert mock_subprocess.method_calls[0][1] == expected
                actual_env = mock_subprocess.method_calls[0][2]['env']

            assert list(actual_env.keys()) == ['KRB5CCNAME']
            assert actual_env['KRB5CCNAME'].startswith("FILE:/")

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('use_pexpect', (False, True),)
    def test_kinit_with_missing_executable(self, use_pexpect):
        expected_err = "[Errno 2] No such file or directory: " \
                       "'/fake/kinit': '/fake/kinit'"
        mock_subprocess = MagicMock()
        mock_subprocess.Popen = MagicMock(side_effect=OSError(expected_err))

        mock_pexpect = None
        if use_pexpect:
            expected_err = "The command was not found or was not " \
                           "executable: /fake/kinit"

            mock_pexpect = MagicMock()
            mock_pexpect.ExceptionPexpect = Exception
            mock_pexpect.spawn = MagicMock(side_effect=Exception(expected_err))

        modules = {
            'pexpect': mock_pexpect,
            'subprocess': mock_subprocess,
        }

        with patch.dict(sys.modules, modules):
            pc = PlayContext()
            new_stdin = StringIO()

            connection_loader._module_cache = {}
            conn = connection_loader.get('winrm', pc, new_stdin)
            options = {"_extras": {}, "ansible_winrm_kinit_cmd": "/fake/kinit"}
            conn.set_options(var_options=options)

            with pytest.raises(AnsibleConnectionFailure) as err:
                conn._kerb_auth("user@domain", "pass")
            assert str(err.value) == "Kerberos auth failure when calling " \
                                     "kinit cmd '/fake/kinit': %s" % expected_err

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('use_pexpect', (False, True),)
    def test_kinit_error(self, use_pexpect):
        mechanism = "subprocess"
        expected_err = "kinit: krb5_parse_name: " \
                       "Configuration file does not specify default realm"

        def mock_popen_communicate(input=None, timeout=None):
            return b"", to_bytes(expected_err)

        mock_subprocess = MagicMock()
        mock_subprocess.Popen.return_value.communicate = mock_popen_communicate
        mock_subprocess.Popen.return_value.returncode = 1

        mock_pexpect = None
        if use_pexpect:
            mechanism = "pexpect"
            expected_err = "Configuration file does not specify default realm"

            mock_pexpect = MagicMock()
            mock_pexpect.spawn.return_value.expect = MagicMock(side_effect=OSError)
            mock_pexpect.spawn.return_value.read.return_value = to_bytes(expected_err)
            mock_pexpect.spawn.return_value.exitstatus = 1

        modules = {
            'pexpect': mock_pexpect,
            'subprocess': mock_subprocess,
        }

        with patch.dict(sys.modules, modules):
            pc = PlayContext()
            new_stdin = StringIO()

            connection_loader._module_cache = {}
            conn = connection_loader.get('winrm', pc, new_stdin)
            conn.set_options(var_options={"_extras": {}})

            with pytest.raises(AnsibleConnectionFailure) as err:
                conn._kerb_auth("invaliduser", "pass")

            assert str(err.value) == "Kerberos auth failure for principal " \
                                     "invaliduser with %s: %s" % (mechanism, expected_err)
