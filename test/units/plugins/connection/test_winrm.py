# -*- coding: utf-8 -*-
# (c) 2018, Jordan Borean <jborean@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import typing as t

import pytest

from unittest.mock import MagicMock
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.module_utils.common.text.converters import to_bytes
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader
from ansible.plugins.connection import winrm

pytest.importorskip("winrm")


class TestConnectionWinRM(object):

    OPTIONS_DATA: tuple[tuple[dict[str, t.Any], dict[str, t.Any], dict[str, t.Any], bool], ...] = (
        # default options
        (
            {'_extras': {}},
            {},
            {
                '_kerb_managed': False,
                '_kinit_cmd': 'kinit',
                '_winrm_connection_timeout': None,
                '_winrm_host': 'inventory_hostname',
                '_winrm_kwargs': {'username': None, 'password': None},
                '_winrm_pass': None,
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
            {'_extras': {}, 'ansible_port': 5985},
            {},
            {
                '_winrm_kwargs': {'username': None, 'password': None},
                '_winrm_port': 5985,
                '_winrm_scheme': 'http',
                '_winrm_transport': ['plaintext'],
            },
            False
        ),
        # kerberos user with kerb present
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com'},
            {},
            {
                '_kerb_managed': False,
                '_kinit_cmd': 'kinit',
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': None},
                '_winrm_pass': None,
                '_winrm_transport': ['kerberos', 'ssl'],
                '_winrm_user': 'user@domain.com'
            },
            True
        ),
        # kerberos user without kerb present
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com'},
            {},
            {
                '_kerb_managed': False,
                '_kinit_cmd': 'kinit',
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': None},
                '_winrm_pass': None,
                '_winrm_transport': ['ssl'],
                '_winrm_user': 'user@domain.com'
            },
            False
        ),
        # kerberos user with managed ticket (implicit)
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com'},
            {'remote_password': 'pass'},
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
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'managed'},
            {'password': 'pass'},
            {
                '_kerb_managed': True,
            },
            True
        ),
        # kerb with unmanaged ticket (explicit))
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_kinit_mode': 'manual'},
            {'password': 'pass'},
            {
                '_kerb_managed': False,
            },
            True
        ),
        # transport override (single)
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_transport': 'ntlm'},
            {},
            {
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': None},
                '_winrm_pass': None,
                '_winrm_transport': ['ntlm'],
            },
            False
        ),
        # transport override (list)
        (
            {'_extras': {}, 'ansible_user': 'user@domain.com',
             'ansible_winrm_transport': ['ntlm', 'certificate']},
            {},
            {
                '_winrm_kwargs': {'username': 'user@domain.com',
                                  'password': None},
                '_winrm_pass': None,
                '_winrm_transport': ['ntlm', 'certificate'],
            },
            False
        ),
        # winrm extras
        (
            {'_extras': {'ansible_winrm_server_cert_validation': 'ignore',
                         'ansible_winrm_service': 'WSMAN'}},
            {},
            {
                '_winrm_kwargs': {'username': None, 'password': None,
                                  'server_cert_validation': 'ignore',
                                  'service': 'WSMAN'},
            },
            False
        ),
        # direct override
        (
            {'_extras': {}, 'ansible_winrm_connection_timeout': 5},
            {'connection_timeout': 10},
            {
                '_winrm_connection_timeout': 10,
            },
            False
        ),
        # password as ansible_password
        (
            {'_extras': {}, 'ansible_password': 'pass'},
            {},
            {
                '_winrm_pass': 'pass',
                '_winrm_kwargs': {'username': None, 'password': 'pass'}
            },
            False
        ),
        # password as ansible_winrm_pass
        (
            {'_extras': {}, 'ansible_winrm_pass': 'pass'},
            {},
            {
                '_winrm_pass': 'pass',
                '_winrm_kwargs': {'username': None, 'password': 'pass'}
            },
            False
        ),

        # password as ansible_winrm_password
        (
            {'_extras': {}, 'ansible_winrm_password': 'pass'},
            {},
            {
                '_winrm_pass': 'pass',
                '_winrm_kwargs': {'username': None, 'password': 'pass'}
            },
            False
        ),
    )

    @pytest.mark.parametrize('options, direct, expected, kerb',
                             ((o, d, e, k) for o, d, e, k in OPTIONS_DATA))
    def test_set_options(self, options, direct, expected, kerb):
        winrm.HAVE_KERBEROS = kerb

        pc = PlayContext()

        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options=options, direct=direct)
        conn._build_winrm_kwargs()

        for attr, expected in expected.items():
            actual = getattr(conn, attr)
            assert actual == expected, \
                "winrm attr '%s', actual '%s' != expected '%s'"\
                % (attr, actual, expected)


class TestWinRMKerbAuth(object):

    @pytest.mark.parametrize('options, expected', [
        [{"_extras": {}},
         (["kinit", "user@domain"],)],
        [{"_extras": {}, 'ansible_winrm_kinit_cmd': 'kinit2'},
         (["kinit2", "user@domain"],)],
        [{"_extras": {'ansible_winrm_kerberos_delegation': True}},
         (["kinit", "-f", "user@domain"],)],
        [{"_extras": {}, 'ansible_winrm_kinit_args': '-f -p'},
         (["kinit", "-f", "-p", "user@domain"],)],
        [{"_extras": {}, 'ansible_winrm_kerberos_delegation': True, 'ansible_winrm_kinit_args': '-p'},
         (["kinit", "-p", "user@domain"],)]
    ])
    def test_kinit_success_subprocess(self, monkeypatch, options, expected):
        def mock_communicate(input=None, timeout=None):
            return b"", b""

        mock_popen = MagicMock()
        mock_popen.return_value.communicate = mock_communicate
        mock_popen.return_value.returncode = 0
        monkeypatch.setattr("subprocess.Popen", mock_popen)

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options=options)
        conn._build_winrm_kwargs()

        conn._kerb_auth("user@domain", "pass")
        mock_calls = mock_popen.mock_calls
        assert len(mock_calls) == 1
        assert mock_calls[0][1] == expected
        actual_env = mock_calls[0][2]['env']
        assert sorted(list(actual_env.keys())) == ['KRB5CCNAME', 'PATH']
        assert actual_env['KRB5CCNAME'].startswith("FILE:/")
        assert actual_env['PATH'] == os.environ['PATH']

    def test_kinit_with_missing_executable_subprocess(self, monkeypatch):
        expected_err = "[Errno 2] No such file or directory: " \
                       "'/fake/kinit': '/fake/kinit'"
        mock_popen = MagicMock(side_effect=OSError(expected_err))

        monkeypatch.setattr("subprocess.Popen", mock_popen)

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        options = {"_extras": {}, "ansible_winrm_kinit_cmd": "/fake/kinit"}
        conn.set_options(var_options=options)
        conn._build_winrm_kwargs()

        with pytest.raises(AnsibleConnectionFailure) as err:
            conn._kerb_auth("user@domain", "pass")
        assert str(err.value) == "Kerberos auth failure when calling " \
                                 "kinit cmd '/fake/kinit': %s" % expected_err

    def test_kinit_error_subprocess(self, monkeypatch):
        expected_err = "kinit: krb5_parse_name: " \
                       "Configuration file does not specify default realm"

        def mock_communicate(input=None, timeout=None):
            return b"", to_bytes(expected_err)

        mock_popen = MagicMock()
        mock_popen.return_value.communicate = mock_communicate
        mock_popen.return_value.returncode = 1
        monkeypatch.setattr("subprocess.Popen", mock_popen)

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"_extras": {}})
        conn._build_winrm_kwargs()

        with pytest.raises(AnsibleConnectionFailure) as err:
            conn._kerb_auth("invaliduser", "pass")

        assert str(err.value) == \
            "Kerberos auth failure for principal invaliduser: %s" % (expected_err)

    def test_kinit_error_pass_in_output_subprocess(self, monkeypatch):
        def mock_communicate(input=None, timeout=None):
            return b"", b"Error with kinit\n" + input

        mock_popen = MagicMock()
        mock_popen.return_value.communicate = mock_communicate
        mock_popen.return_value.returncode = 1
        monkeypatch.setattr("subprocess.Popen", mock_popen)

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"_extras": {}})
        conn._build_winrm_kwargs()

        with pytest.raises(AnsibleConnectionFailure) as err:
            conn._kerb_auth("username", "password")
        assert str(err.value) == \
            "Kerberos auth failure for principal username: " \
            "Error with kinit\n<redacted>"

    def test_exec_command_with_timeout(self, monkeypatch):
        requests_exc = pytest.importorskip("requests.exceptions")

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)

        mock_proto = MagicMock()
        mock_proto.run_command.side_effect = requests_exc.Timeout("msg")

        conn._connected = True
        conn._winrm_host = 'hostname'

        monkeypatch.setattr(conn, "_winrm_connect", lambda: mock_proto)

        with pytest.raises(AnsibleConnectionFailure) as e:
            conn.exec_command('cmd', in_data=None, sudoable=True)

        assert str(e.value) == "winrm connection error: msg"

    def test_exec_command_get_output_timeout(self, monkeypatch):
        requests_exc = pytest.importorskip("requests.exceptions")

        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)

        mock_proto = MagicMock()
        mock_proto.run_command.return_value = "command_id"
        mock_proto.send_message.side_effect = requests_exc.Timeout("msg")

        conn._connected = True
        conn._winrm_host = 'hostname'

        monkeypatch.setattr(conn, "_winrm_connect", lambda: mock_proto)

        with pytest.raises(AnsibleConnectionFailure) as e:
            conn.exec_command('cmd', in_data=None, sudoable=True)

        assert str(e.value) == "winrm connection error: msg"

    def test_connect_failure_auth_401(self, monkeypatch):
        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"ansible_winrm_transport": "basic", "_extras": {}})

        mock_proto = MagicMock()
        mock_proto.open_shell.side_effect = ValueError("Custom exc Code 401")

        mock_proto_init = MagicMock()
        mock_proto_init.return_value = mock_proto
        monkeypatch.setattr(winrm, "Protocol", mock_proto_init)

        with pytest.raises(AnsibleConnectionFailure, match="the specified credentials were rejected by the server"):
            conn.exec_command('cmd', in_data=None, sudoable=True)

    def test_connect_failure_other_exception(self, monkeypatch):
        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"ansible_winrm_transport": "basic", "_extras": {}})

        mock_proto = MagicMock()
        mock_proto.open_shell.side_effect = ValueError("Custom exc")

        mock_proto_init = MagicMock()
        mock_proto_init.return_value = mock_proto
        monkeypatch.setattr(winrm, "Protocol", mock_proto_init)

        with pytest.raises(AnsibleConnectionFailure, match="basic: Custom exc"):
            conn.exec_command('cmd', in_data=None, sudoable=True)

    def test_connect_failure_operation_timed_out(self, monkeypatch):
        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"ansible_winrm_transport": "basic", "_extras": {}})

        mock_proto = MagicMock()
        mock_proto.open_shell.side_effect = ValueError("Custom exc Operation timed out")

        mock_proto_init = MagicMock()
        mock_proto_init.return_value = mock_proto
        monkeypatch.setattr(winrm, "Protocol", mock_proto_init)

        with pytest.raises(AnsibleError, match="the connection attempt timed out"):
            conn.exec_command('cmd', in_data=None, sudoable=True)

    def test_connect_no_transport(self):
        pc = PlayContext()
        conn = connection_loader.get('winrm', pc)
        conn.set_options(var_options={"_extras": {}})
        conn._build_winrm_kwargs()
        conn._winrm_transport = []

        with pytest.raises(AnsibleError, match="No transport found for WinRM connection"):
            conn._winrm_connect()
