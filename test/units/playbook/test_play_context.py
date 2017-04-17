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
from ansible.compat.six.moves import shlex_quote
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
        self.assertEqual(play_context._attributes['connection'], C.DEFAULT_TRANSPORT)
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
        ksu_exe = 'ksu'
        ksu_flags = ''
        dzdo_exe   = 'dzdo'

        cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
        self.assertEqual(cmd, default_cmd)

        play_context.become = True
        play_context.become_user = 'foo'

        play_context.become_method = 'sudo'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(
            cmd,
            """%s %s -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags, play_context.become_user, default_exe, play_context.success_key, default_cmd)
        )
        play_context.become_pass = 'testpass'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable=default_exe)
        self.assertEqual(
            cmd,
            """%s %s -p "%s" -u %s %s -c 'echo %s; %s'""" % (sudo_exe, sudo_flags.replace('-n',''), play_context.prompt, play_context.become_user, default_exe,
                                                             play_context.success_key, default_cmd)
        )

        play_context.become_pass = None

        play_context.become_method = 'su'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(
            cmd,
            """%s  %s -c '%s -c '"'"'echo %s; %s'"'"''""" % (su_exe, play_context.become_user, default_exe, play_context.success_key, default_cmd)
        )

        play_context.become_method = 'pbrun'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s %s -u %s 'echo %s; %s'""" % (pbrun_exe, pbrun_flags, play_context.become_user, play_context.success_key, default_cmd))

        play_context.become_method = 'pfexec'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, '''%s %s "'echo %s; %s'"''' % (pfexec_exe, pfexec_flags, play_context.success_key, default_cmd))

        play_context.become_method = 'doas'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(
            cmd,
            """%s %s echo %s && %s %s env ANSIBLE=true %s""" % (doas_exe, doas_flags, play_context.success_key, doas_exe, doas_flags, default_cmd)
        )

        play_context.become_method = 'ksu'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(
            cmd,
            """%s %s %s -e %s -c 'echo %s; %s'""" % (ksu_exe, play_context.become_user, ksu_flags, default_exe, play_context.success_key, default_cmd)
        )

        play_context.become_method = 'bad'
        self.assertRaises(AnsibleError, play_context.make_become_cmd, cmd=default_cmd, executable="/bin/bash")

        play_context.become_method = 'dzdo'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(cmd, """%s -u %s %s -c 'echo %s; %s'""" % (dzdo_exe, play_context.become_user, default_exe, play_context.success_key, default_cmd))

        play_context.become_pass = 'testpass'
        play_context.become_method = 'dzdo'
        cmd = play_context.make_become_cmd(cmd=default_cmd, executable="/bin/bash")
        self.assertEqual(
            cmd,
            """%s -p %s -u %s %s -c 'echo %s; %s'""" % (dzdo_exe, shlex_quote(play_context.prompt), play_context.become_user, default_exe,
                                                        play_context.success_key, default_cmd)
        )


class TestTaskAndVariableOverrride(unittest.TestCase):

    inventory_vars = (
        ('preferred_names',
                dict(ansible_connection='local',
                    ansible_user='ansibull',
                    ansible_become_user='ansibull',
                    ansible_become_method='su',
                    ansible_become_pass='ansibullwuzhere',),
                dict(connection='local',
                    remote_user='ansibull',
                    become_user='ansibull',
                    become_method='su',
                    become_pass='ansibullwuzhere',)
            ),
        ('alternate_names',
                dict(ansible_become_password='ansibullwuzhere',),
                dict(become_pass='ansibullwuzhere',)
            ),
        ('deprecated_names',
                dict(ansible_ssh_user='ansibull',
                    ansible_sudo_user='ansibull',
                    ansible_sudo_pass='ansibullwuzhere',),
                dict(remote_user='ansibull',
                    become_method='sudo',
                    become_user='ansibull',
                    become_pass='ansibullwuzhere',)
            ),
        ('deprecated_names2',
                dict(ansible_ssh_user='ansibull',
                    ansible_su_user='ansibull',
                    ansible_su_pass='ansibullwuzhere',),
                dict(remote_user='ansibull',
                    become_method='su',
                    become_user='ansibull',
                    become_pass='ansibullwuzhere',)
            ),
        ('deprecated_alt_names',
                dict(ansible_sudo_password='ansibullwuzhere',),
                dict(become_method='sudo',
                    become_pass='ansibullwuzhere',)
            ),
        ('deprecated_alt_names2',
                dict(ansible_su_password='ansibullwuzhere',),
                dict(become_method='su',
                    become_pass='ansibullwuzhere',)
            ),
        ('deprecated_and_preferred_names',
                dict(ansible_user='ansibull',
                    ansible_ssh_user='badbull',
                    ansible_become_user='ansibull',
                    ansible_sudo_user='badbull',
                    ansible_become_method='su',
                    ansible_become_pass='ansibullwuzhere',
                    ansible_sudo_pass='badbull',
                    ),
                dict(connection='local',
                    remote_user='ansibull',
                    become_user='ansibull',
                    become_method='su',
                    become_pass='ansibullwuzhere',)
            ),
    )

    def setUp(self):
        parser = CLI.base_parser(
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

        (options, args) = parser.parse_args(['-vv', '--check'])

        mock_play = MagicMock()
        mock_play.connection    = 'mock'
        mock_play.remote_user   = 'mock'
        mock_play.port          = 1234
        mock_play.become        = True
        mock_play.become_method = 'mock'
        mock_play.become_user   = 'mockroot'
        mock_play.no_log        = True

        self.play_context = PlayContext(play=mock_play, options=options)

        mock_task = MagicMock()
        mock_task.connection    = mock_play.connection
        mock_task.remote_user   = mock_play.remote_user
        mock_task.no_log        = mock_play.no_log
        mock_task.become        = mock_play.become
        mock_task.become_method = mock_play.becom_method
        mock_task.become_user   = mock_play.become_user
        mock_task.become_pass   = 'mocktaskpass'
        mock_task._local_action = False
        mock_task.delegate_to   = None

        self.mock_task = mock_task

        self.mock_templar = MagicMock()

    def tearDown(self):
        pass

    def _check_vars_overridden(self):
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

    def test_override_magic_variables(self):
        play_context = play_context.set_task_and_variable_override(task=self.mock_task, variables=all_vars, templar=self.mock_templar)

        mock_play.connection    = 'mock'
        mock_play.remote_user   = 'mock'
        mock_play.port          = 1234
        mock_play.become_method = 'mock'
        mock_play.become_user   = 'mockroot'
        mock_task.become_pass   = 'mocktaskpass'
        # Inventory vars override things set from cli vars (--become, -user,
        # etc... [notably, not --extravars])
        for test_name, all_vars, expected in self.inventory_vars:
            yield self._check_vars_overriden, test_name, all_vars, expected
