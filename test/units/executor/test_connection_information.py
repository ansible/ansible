# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pwd
import os

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.connection_info import ConnectionInformation

from units.mock.loader import DictDataLoader

class TestConnectionInformation(unittest.TestCase):

    def setUp(self):
        self._parser = CLI.base_parser(
            runas_opts   = True,
            meta_opts    = True,
            runtask_opts = True,
            vault_opts   = True,
            async_opts   = True,
            connect_opts = True,
            subset_opts  = True,
            check_opts   = True,
            diff_opts    = True,
        )

    def tearDown(self):
        pass

    def test_connection_info(self):
        (options, args) = self._parser.parse_args(['-vv', '--check'])
        conn_info = ConnectionInformation(options=options)
        self.assertEqual(conn_info.connection, 'smart')
        self.assertEqual(conn_info.remote_addr, None)
        self.assertEqual(conn_info.remote_user, pwd.getpwuid(os.geteuid())[0])
        self.assertEqual(conn_info.password, '')
        self.assertEqual(conn_info.port, None)
        self.assertEqual(conn_info.private_key_file, C.DEFAULT_PRIVATE_KEY_FILE)
        self.assertEqual(conn_info.timeout, C.DEFAULT_TIMEOUT)
        self.assertEqual(conn_info.shell, None)
        self.assertEqual(conn_info.verbosity, 2)
        self.assertEqual(conn_info.check_mode, True)
        self.assertEqual(conn_info.no_log, False)

        mock_play = MagicMock()
        mock_play.connection    = 'mock'
        mock_play.remote_user   = 'mock'
        mock_play.port          = 1234
        mock_play.become        = True
        mock_play.become_method = 'mock'
        mock_play.become_user   = 'mockroot'
        mock_play.no_log        = True
        mock_play.environment   = dict(mock='mockenv')

        conn_info = ConnectionInformation(play=mock_play, options=options)
        self.assertEqual(conn_info.connection, 'mock')
        self.assertEqual(conn_info.remote_user, 'mock')
        self.assertEqual(conn_info.password, '')
        self.assertEqual(conn_info.port, 1234)
        self.assertEqual(conn_info.no_log, True)
        self.assertEqual(conn_info.environment, dict(mock="mockenv"))
        self.assertEqual(conn_info.become, True)
        self.assertEqual(conn_info.become_method, "mock")
        self.assertEqual(conn_info.become_user, "mockroot")

        mock_task = MagicMock()
        mock_task.connection    = 'mocktask'
        mock_task.remote_user   = 'mocktask'
        mock_task.become        = True
        mock_task.become_method = 'mocktask'
        mock_task.become_user   = 'mocktaskroot'
        mock_task.become_pass   = 'mocktaskpass'
        mock_task.no_log        = False
        mock_task.environment   = dict(mock='mocktaskenv')

        mock_host = MagicMock()
        mock_host.get_vars.return_value = dict(
            ansible_connection = 'mock_inventory',
            ansible_ssh_port = 4321,
        )

        conn_info = ConnectionInformation(play=mock_play, options=options)
        conn_info = conn_info.set_task_and_host_override(task=mock_task, host=mock_host)
        self.assertEqual(conn_info.connection, 'mock_inventory')
        self.assertEqual(conn_info.remote_user, 'mocktask')
        self.assertEqual(conn_info.port, 4321)
        self.assertEqual(conn_info.no_log, False)
        self.assertEqual(conn_info.environment, dict(mock="mocktaskenv"))
        self.assertEqual(conn_info.become, True)
        self.assertEqual(conn_info.become_method, "mocktask")
        self.assertEqual(conn_info.become_user, "mocktaskroot")
        self.assertEqual(conn_info.become_pass, "mocktaskpass")

    def test_connection_info_make_become_cmd(self):
        (options, args) = self._parser.parse_args([])
        conn_info = ConnectionInformation(options=options)

        default_cmd = "/bin/foo"
        default_exe = "/bin/bash"
        sudo_exe    = C.DEFAULT_SUDO_EXE
        sudo_flags  = C.DEFAULT_SUDO_FLAGS
        su_exe      = C.DEFAULT_SU_EXE
        su_flags    = C.DEFAULT_SU_FLAGS
        pbrun_exe   = 'pbrun'
        pbrun_flags = ''

        (cmd, prompt, key) = conn_info.make_become_cmd(cmd=default_cmd, executable=default_exe)
        self.assertEqual(cmd, default_cmd)

        conn_info.become = True
        conn_info.become_user = 'foo'

        conn_info.become_method = 'sudo'
        (cmd, prompt, key) = conn_info.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -c '%s -k && %s %s -S -p "%s" -u %s %s -c '"'"'echo %s; %s'"'"''""" % (default_exe, sudo_exe, sudo_exe, sudo_flags, prompt, conn_info.become_user, default_exe, key, default_cmd))

        conn_info.become_method = 'su'
        (cmd, prompt, key) = conn_info.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -c '%s  %s -c "%s -c '"'"'echo %s; %s'"'"'"'""" % (default_exe, su_exe, conn_info.become_user, default_exe, key, default_cmd))

        conn_info.become_method = 'pbrun'
        (cmd, prompt, key) = conn_info.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -c '%s -b -l %s -u %s '"'"'echo %s; %s'"'"''""" % (default_exe, pbrun_exe, pbrun_flags, conn_info.become_user, key, default_cmd))

        conn_info.become_method = 'pfexec'
        (cmd, prompt, key) = conn_info.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -c '%s %s "'"'"'echo %s; %s'"'"'"'""" % (default_exe, pbrun_exe, pbrun_flags, key, default_cmd))

        conn_info.become_method = 'bad'
        self.assertRaises(AnsibleError, conn_info.make_become_cmd, cmd=default_cmd, executable="/bin/bash")

