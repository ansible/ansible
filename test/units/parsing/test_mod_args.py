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

from ansible.parsing.mod_args import ModuleArgsParser
from ansible.errors import AnsibleParserError

from ansible.compat.tests import unittest

class TestModArgsDwim(unittest.TestCase):

    # TODO: add tests that construct ModuleArgsParser with a task reference
    # TODO: verify the AnsibleError raised on failure knows the task
    #       and the task knows the line numbers

    def setUp(self):
        pass

    def _debug(self, mod, args, to):
        print("RETURNED module = {0}".format(mod))
        print("           args = {0}".format(args))
        print("             to = {0}".format(to))

    def tearDown(self):
        pass

    def test_basic_shell(self):
        m = ModuleArgsParser(dict(shell='echo hi'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'command')
        self.assertEqual(args, dict(
                                _raw_params = 'echo hi',
                                _uses_shell = True,
                        ))
        self.assertIsNone(to)

    def test_basic_command(self):
        m = ModuleArgsParser(dict(command='echo hi'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'command')
        self.assertEqual(args, dict(
                                _raw_params = 'echo hi',
                        ))
        self.assertIsNone(to)

    def test_shell_with_modifiers(self):
        m = ModuleArgsParser(dict(shell='/bin/foo creates=/tmp/baz removes=/tmp/bleep'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'command')
        self.assertEqual(args, dict(
                                creates     = '/tmp/baz',
                                removes     = '/tmp/bleep',
                                _raw_params = '/bin/foo',
                                _uses_shell = True,
                        ))
        self.assertIsNone(to)

    def test_normal_usage(self):
        m = ModuleArgsParser(dict(copy='src=a dest=b'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'copy')
        self.assertEqual(args, dict(src='a', dest='b'))
        self.assertIsNone(to)

    def test_complex_args(self):
        m = ModuleArgsParser(dict(copy=dict(src='a', dest='b')))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'copy')
        self.assertEqual(args, dict(src='a', dest='b'))
        self.assertIsNone(to)

    def test_action_with_complex(self):
        m = ModuleArgsParser(dict(action=dict(module='copy', src='a', dest='b')))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'copy')
        self.assertEqual(args, dict(src='a', dest='b'))
        self.assertIsNone(to)

    def test_action_with_complex_and_complex_args(self):
        m = ModuleArgsParser(dict(action=dict(module='copy', args=dict(src='a', dest='b'))))
        mod, args, to = m.parse()
        self._debug(mod, args, to)
        self.assertEqual(mod, 'copy')
        self.assertEqual(args, dict(src='a', dest='b'))
        self.assertIsNone(to)

    def test_local_action_string(self):
        m = ModuleArgsParser(dict(local_action='copy src=a dest=b'))
        mod, args, delegate_to = m.parse()
        self._debug(mod, args, delegate_to)
        self.assertEqual(mod, 'copy')
        self.assertEqual(args, dict(src='a', dest='b'))
        self.assertIs(delegate_to, 'localhost')

    def test_multiple_actions(self):
        m = ModuleArgsParser(dict(action='shell echo hi', local_action='shell echo hi'))
        self.assertRaises(AnsibleParserError, m.parse)

        m = ModuleArgsParser(dict(action='shell echo hi', shell='echo hi'))
        self.assertRaises(AnsibleParserError, m.parse)

        m = ModuleArgsParser(dict(local_action='shell echo hi', shell='echo hi'))
        self.assertRaises(AnsibleParserError, m.parse)

        m = ModuleArgsParser(dict(ping='data=hi', shell='echo hi'))
        self.assertRaises(AnsibleParserError, m.parse)

