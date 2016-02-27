# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import errno
import sys
import time
from io import BytesIO

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, MagicMock, Mock, patch, sentinel

from ansible.module_utils import basic
from ansible.module_utils.basic import AnsibleModule

class OpenBytesIO(BytesIO):
    """BytesIO with dummy close() method

    So that you can inspect the content after close() was called.
    """

    def close(self):
        pass


@unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
class TestAnsibleModuleRunCommand(unittest.TestCase):

    def setUp(self):

        self.cmd_out = {
            # os.read() is returning 'bytes', not strings
            sentinel.stdout: BytesIO(),
            sentinel.stderr: BytesIO(),
        }

        def mock_os_read(fd, nbytes):
            return self.cmd_out[fd].read(nbytes)

        def mock_select(rlist, wlist, xlist, timeout=1):
            return (rlist, [], [])

        def mock_os_chdir(path):
            if path == '/inaccessible':
                raise OSError(errno.EPERM, "Permission denied: '/inaccessible'")

        basic.MODULE_COMPLEX_ARGS = '{}'
        self.module = AnsibleModule(argument_spec=dict())
        self.module.fail_json = MagicMock(side_effect=SystemExit)

        self.os = patch('ansible.module_utils.basic.os').start()
        self.os.path.expandvars.side_effect = lambda x: x
        self.os.path.expanduser.side_effect = lambda x: x
        self.os.environ = {'PATH': '/bin'}
        self.os.getcwd.return_value = '/home/foo'
        self.os.path.isdir.return_value = True
        self.os.chdir.side_effect = mock_os_chdir
        self.os.read.side_effect = mock_os_read

        self.subprocess = patch('ansible.module_utils.basic.subprocess').start()
        self.cmd = Mock()
        self.cmd.returncode = 0
        self.cmd.stdin = OpenBytesIO()
        self.cmd.stdout.fileno.return_value = sentinel.stdout
        self.cmd.stderr.fileno.return_value = sentinel.stderr
        self.subprocess.Popen.return_value = self.cmd

        self.select = patch('ansible.module_utils.basic.select').start()
        self.select.select.side_effect = mock_select

        self.addCleanup(patch.stopall)

    def test_list_as_args(self):
        self.module.run_command(['/bin/ls', 'a', ' b', 'c '])
        self.assertTrue(self.subprocess.Popen.called)
        args, kwargs = self.subprocess.Popen.call_args
        self.assertEqual(args, (['/bin/ls', 'a', ' b', 'c '], ))
        self.assertEqual(kwargs['shell'], False)

    def test_str_as_args(self):
        self.module.run_command('/bin/ls a " b" "c "')
        self.assertTrue(self.subprocess.Popen.called)
        args, kwargs = self.subprocess.Popen.call_args
        self.assertEqual(args, (['/bin/ls', 'a', ' b', 'c '], ))
        self.assertEqual(kwargs['shell'], False)

    def test_tuple_as_args(self):
        self.assertRaises(SystemExit, self.module.run_command, ('ls', '/'))
        self.assertTrue(self.module.fail_json.called)

    def test_unsafe_shell(self):
        self.module.run_command('ls a " b" "c "', use_unsafe_shell=True)
        self.assertTrue(self.subprocess.Popen.called)
        args, kwargs = self.subprocess.Popen.call_args
        self.assertEqual(args, ('ls a " b" "c "', ))
        self.assertEqual(kwargs['shell'], True)

    def test_cwd(self):
        self.os.getcwd.return_value = '/old'
        self.module.run_command('/bin/ls', cwd='/new')
        self.assertEqual(self.os.chdir.mock_calls,
                         [call('/new'), call('/old'), ])

    def test_cwd_not_a_dir(self):
        self.os.getcwd.return_value = '/old'
        self.os.path.isdir.side_effect = lambda d: d != '/not-a-dir'
        self.module.run_command('/bin/ls', cwd='/not-a-dir')
        self.assertEqual(self.os.chdir.mock_calls, [call('/old'), ])

    def test_cwd_inaccessible(self):
        self.assertRaises(SystemExit, self.module.run_command, '/bin/ls', cwd='/inaccessible')
        self.assertTrue(self.module.fail_json.called)
        args, kwargs = self.module.fail_json.call_args
        self.assertEqual(kwargs['rc'], errno.EPERM)

    def test_prompt_bad_regex(self):
        self.assertRaises(SystemExit, self.module.run_command, 'foo', prompt_regex='[pP)assword:')
        self.assertTrue(self.module.fail_json.called)

    def test_prompt_no_match(self):
        self.cmd_out[sentinel.stdout] = BytesIO(b'hello')
        (rc, _, _) = self.module.run_command('foo', prompt_regex='[pP]assword:')
        self.assertEqual(rc, 0)

    def test_prompt_match_wo_data(self):
        self.cmd_out[sentinel.stdout] = BytesIO(b'Authentication required!\nEnter password: ')
        (rc, _, _) = self.module.run_command('foo', prompt_regex=r'[pP]assword:', data=None)
        self.assertEqual(rc, 257)

    def test_check_rc_false(self):
        self.cmd.returncode = 1
        (rc, _, _) = self.module.run_command('/bin/false', check_rc=False)
        self.assertEqual(rc, 1)

    def test_check_rc_true(self):
        self.cmd.returncode = 1
        self.assertRaises(SystemExit, self.module.run_command, '/bin/false', check_rc=True)
        self.assertTrue(self.module.fail_json.called)
        args, kwargs = self.module.fail_json.call_args
        self.assertEqual(kwargs['rc'], 1)

    def test_text_stdin(self):
        (rc, stdout, stderr) = self.module.run_command('/bin/foo', data='hello world')
        self.assertEqual(self.cmd.stdin.getvalue(), 'hello world\n')

    def test_ascii_stdout(self):
        self.cmd_out[sentinel.stdout] = BytesIO(b'hello')
        (rc, stdout, stderr) = self.module.run_command('/bin/cat hello.txt')
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, 'hello')

    def test_utf8_output(self):
        self.cmd_out[sentinel.stdout] = BytesIO(u'Žarn§'.encode('utf-8'))
        self.cmd_out[sentinel.stderr] = BytesIO(u'لرئيسية'.encode('utf-8'))
        (rc, stdout, stderr) = self.module.run_command('/bin/something_ugly')
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.decode('utf-8'), u'Žarn§')
        self.assertEqual(stderr.decode('utf-8'), u'لرئيسية')

