# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import errno
from itertools import product
from io import BytesIO

import pytest

from ansible.module_utils._text import to_native


class OpenBytesIO(BytesIO):
    """BytesIO with dummy close() method

    So that you can inspect the content after close() was called.
    """

    def close(self):
        pass


@pytest.fixture
def mock_os(mocker):
    def mock_os_read(fd, nbytes):
        return os._cmd_out[fd].read(nbytes)

    def mock_os_chdir(path):
        if path == '/inaccessible':
            raise OSError(errno.EPERM, "Permission denied: '/inaccessible'")

    def mock_os_abspath(path):
        if path.startswith('/'):
            return path
        else:
            return os.getcwd.return_value + '/' + path

    os = mocker.patch('ansible.module_utils.basic.os')
    os._cmd_out = {
        # os.read() is returning 'bytes', not strings
        mocker.sentinel.stdout: BytesIO(),
        mocker.sentinel.stderr: BytesIO(),
    }

    os.path.expandvars.side_effect = lambda x: x
    os.path.expanduser.side_effect = lambda x: x
    os.environ = {'PATH': '/bin'}
    os.getcwd.return_value = '/home/foo'
    os.path.isdir.return_value = True
    os.chdir.side_effect = mock_os_chdir
    os.read.side_effect = mock_os_read
    os.path.abspath.side_effect = mock_os_abspath

    yield os


@pytest.fixture
def mock_subprocess(mocker):
    def mock_select(rlist, wlist, xlist, timeout=1):
        return (rlist, [], [])

    fake_select = mocker.patch('ansible.module_utils.basic.select')
    fake_select.select.side_effect = mock_select

    subprocess = mocker.patch('ansible.module_utils.basic.subprocess')
    cmd = mocker.MagicMock()
    cmd.returncode = 0
    cmd.stdin = OpenBytesIO()
    cmd.stdout.fileno.return_value = mocker.sentinel.stdout
    cmd.stderr.fileno.return_value = mocker.sentinel.stderr
    subprocess.Popen.return_value = cmd

    yield subprocess


@pytest.fixture()
def rc_am(mocker, am, mock_os, mock_subprocess):
    am.fail_json = mocker.MagicMock(side_effect=SystemExit)
    am._os = mock_os
    am._subprocess = mock_subprocess
    yield am


class TestRunCommandArgs:
    # Format is command as passed to run_command, command to Popen as list, command to Popen as string
    ARGS_DATA = (
                (['/bin/ls', 'a', 'b', 'c'], ['/bin/ls', 'a', 'b', 'c'], '/bin/ls a b c'),
                ('/bin/ls a " b" "c "', ['/bin/ls', 'a', ' b', 'c '], '/bin/ls a " b" "c "'),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('cmd, expected, shell, stdin',
                             ((arg, cmd_str if sh else cmd_lst, sh, {})
                              for (arg, cmd_lst, cmd_str), sh in product(ARGS_DATA, (True, False))),
                             indirect=['stdin'])
    def test_args(self, cmd, expected, shell, rc_am):
        rc_am.run_command(cmd, use_unsafe_shell=shell)
        assert rc_am._subprocess.Popen.called
        args, kwargs = rc_am._subprocess.Popen.call_args
        assert args == (expected, )
        assert kwargs['shell'] == shell

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_tuple_as_args(self, rc_am):
        with pytest.raises(SystemExit):
            rc_am.run_command(('ls', '/'))
        assert rc_am.fail_json.called


class TestRunCommandCwd:
    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_cwd(self, mocker, rc_am):
        rc_am._os.getcwd.return_value = '/old'
        rc_am.run_command('/bin/ls', cwd='/new')
        assert rc_am._os.chdir.mock_calls == [mocker.call('/new'), mocker.call('/old'), ]

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_cwd_relative_path(self, mocker, rc_am):
        rc_am._os.getcwd.return_value = '/old'
        rc_am.run_command('/bin/ls', cwd='sub-dir')
        assert rc_am._os.chdir.mock_calls == [mocker.call('/old/sub-dir'), mocker.call('/old'), ]

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_cwd_not_a_dir(self, mocker, rc_am):
        rc_am._os.getcwd.return_value = '/old'
        rc_am._os.path.isdir.side_effect = lambda d: d != '/not-a-dir'
        rc_am.run_command('/bin/ls', cwd='/not-a-dir')
        assert rc_am._os.chdir.mock_calls == [mocker.call('/old'), ]

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_cwd_inaccessible(self, rc_am):
        with pytest.raises(SystemExit):
            rc_am.run_command('/bin/ls', cwd='/inaccessible')
        assert rc_am.fail_json.called
        args, kwargs = rc_am.fail_json.call_args
        assert kwargs['rc'] == errno.EPERM


class TestRunCommandPrompt:
    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_prompt_bad_regex(self, rc_am):
        with pytest.raises(SystemExit):
            rc_am.run_command('foo', prompt_regex='[pP)assword:')
        assert rc_am.fail_json.called

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_prompt_no_match(self, mocker, rc_am):
        rc_am._os._cmd_out[mocker.sentinel.stdout] = BytesIO(b'hello')
        (rc, _, _) = rc_am.run_command('foo', prompt_regex='[pP]assword:')
        assert rc == 0

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_prompt_match_wo_data(self, mocker, rc_am):
        rc_am._os._cmd_out[mocker.sentinel.stdout] = BytesIO(b'Authentication required!\nEnter password: ')
        (rc, _, _) = rc_am.run_command('foo', prompt_regex=r'[pP]assword:', data=None)
        assert rc == 257


class TestRunCommandRc:
    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_check_rc_false(self, rc_am):
        rc_am._subprocess.Popen.return_value.returncode = 1
        (rc, _, _) = rc_am.run_command('/bin/false', check_rc=False)
        assert rc == 1

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_check_rc_true(self, rc_am):
        rc_am._subprocess.Popen.return_value.returncode = 1
        with pytest.raises(SystemExit):
            rc_am.run_command('/bin/false', check_rc=True)
        assert rc_am.fail_json.called
        args, kwargs = rc_am.fail_json.call_args
        assert kwargs['rc'] == 1


class TestRunCommandOutput:
    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_text_stdin(self, rc_am):
        (rc, stdout, stderr) = rc_am.run_command('/bin/foo', data='hello world')
        assert rc_am._subprocess.Popen.return_value.stdin.getvalue() == b'hello world\n'

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_ascii_stdout(self, mocker, rc_am):
        rc_am._os._cmd_out[mocker.sentinel.stdout] = BytesIO(b'hello')
        (rc, stdout, stderr) = rc_am.run_command('/bin/cat hello.txt')
        assert rc == 0
        # module_utils function.  On py3 it returns text and py2 it returns
        # bytes because it's returning native strings
        assert stdout == 'hello'

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_utf8_output(self, mocker, rc_am):
        rc_am._os._cmd_out[mocker.sentinel.stdout] = BytesIO(u'Žarn§'.encode('utf-8'))
        rc_am._os._cmd_out[mocker.sentinel.stderr] = BytesIO(u'لرئيسية'.encode('utf-8'))
        (rc, stdout, stderr) = rc_am.run_command('/bin/something_ugly')
        assert rc == 0
        # module_utils function.  On py3 it returns text and py2 it returns
        # bytes because it's returning native strings
        assert stdout == to_native(u'Žarn§')
        assert stderr == to_native(u'لرئيسية')
