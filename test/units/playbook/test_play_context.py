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

import os

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.play_context import PlayContext

from units.mock.loader import DictDataLoader

class TestPlayContext(unittest.TestCase):

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
            inventory_opts = True,
        )

    def tearDown(self):
        pass

    def test_play_context(self):
        (options, args) = self._parser.parse_args(['-vv', '--check'])
        play_context = PlayContext(options=options)
        self.assertEqual(play_context.connection, 'smart')
        self.assertEqual(play_context.remote_addr, None)
        self.assertEqual(play_context.remote_user, None)
        self.assertEqual(play_context.password, '')
        self.assertEqual(play_context.port, None)
        self.assertEqual(play_context.private_key_file, C.DEFAULT_PRIVATE_KEY_FILE)
        self.assertEqual(play_context.timeout, C.DEFAULT_TIMEOUT)
        self.assertEqual(play_context.shell, None)
        self.assertEqual(play_context.verbosity, 2)
        self.assertEqual(play_context.check_mode, True)
        self.assertEqual(play_context.no_log, None)

        mock_play = MagicMock()
        mock_play.connection    = 'mock'
        mock_play.remote_user   = 'mock'
        mock_play.port          = 1234
        mock_play.become        = True
        mock_play.become_method = 'mock'
        mock_play.become_user   = 'mockroot'
        mock_play.no_log        = True

        play_context = PlayContext(play=mock_play, options=options)
        self.assertEqual(play_context.connection, 'mock')
        self.assertEqual(play_context.remote_user, 'mock')
        self.assertEqual(play_context.password, '')
        self.assertEqual(play_context.port, 1234)
        self.assertEqual(play_context.become, True)
        self.assertEqual(play_context.become_method, "mock")
        self.assertEqual(play_context.become_user, "mockroot")

        mock_task = MagicMock()
        mock_task.connection    = 'mocktask'
        mock_task.remote_user   = 'mocktask'
        mock_task.no_log        =  mock_play.no_log
        mock_task.become        = True
        mock_task.become_method = 'mocktask'
        mock_task.become_user   = 'mocktaskroot'
        mock_task.become_pass   = 'mocktaskpass'
        mock_task._local_action = False
        mock_task.delegate_to   = None

        all_vars = dict(
            ansible_connection = 'mock_inventory',
            ansible_ssh_port = 4321,
        )

        mock_templar = MagicMock()

        play_context = PlayContext(play=mock_play, options=options)
        play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)
        self.assertEqual(play_context.connection, 'mock_inventory')
        self.assertEqual(play_context.remote_user, 'mocktask')
        self.assertEqual(play_context.port, 4321)
        self.assertEqual(play_context.no_log, True)
        self.assertEqual(play_context.become, True)
        self.assertEqual(play_context.become_method, "mocktask")
        self.assertEqual(play_context.become_user, "mocktaskroot")
        self.assertEqual(play_context.become_pass, "mocktaskpass")

        mock_task.no_log        = False
        play_context = play_context.set_task_and_variable_override(task=mock_task, variables=all_vars, templar=mock_templar)
        self.assertEqual(play_context.no_log, False)

    def test_play_context_make_become_cmd(self):
        (options, args) = self._parser.parse_args([])
        play_context = PlayContext(options=options)

        default_cmd = "/bin/foo"
        default_exe = "/bin/bash"
        sudo_exe    = C.DEFAULT_SUDO_EXE or 'sudo'
        sudo_flags  = C.DEFAULT_SUDO_FLAGS
        su_exe      = C.DEFAULT_SU_EXE or 'su'
        su_flags    = C.DEFAULT_SU_FLAGS or ''
        pbrun_exe   = 'pbrun'
        pbrun_flags = ''
        pfexec_exe   = 'pfexec'
        pfexec_flags = ''
        doas_exe    = 'doas'
        doas_flags  = ' -n  -u foo '

        cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
        self.assertEqual(cmd, default_cmd)

        play_context.become = True
        play_context.become_user = 'foo'

        play_context.become_method = 'sudo'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s %s -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags, play_context.become_user, default_exe, play_context.success_key, default_cmd))
        play_context.become_pass = 'testpass'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
        self.assertEqual(cmd, """%s %s -p "%s" -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags.replace('-n',''), play_context.prompt, play_context.become_user, default_exe, play_context.success_key, default_cmd))

        play_context.become_pass = None

        play_context.become_method = 'su'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s  %s -c '%s -c '"'"'echo %s; %s'"'"''""" % (su_exe, play_context.become_user, default_exe, play_context.success_key, default_cmd))

        play_context.become_method = 'pbrun'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -b %s -u %s 'echo %s; %s'""" % (pbrun_exe, pbrun_flags, play_context.become_user, play_context.success_key, default_cmd))

        play_context.become_method = 'pfexec'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, '''%s %s "'echo %s; %s'"''' % (pfexec_exe, pfexec_flags, play_context.success_key, default_cmd))

        play_context.become_method = 'doas'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s %s echo %s && %s %s env ANSIBLE=true %s""" % (doas_exe, doas_flags, play_context.success_key, doas_exe, doas_flags, default_cmd))

        play_context.become_method = 'bad'
        self.assertRaises(AnsibleError, play_context.make_become_cmd, cmd=default_cmd, executable="/bin/bash")

