# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.errors import AnsibleParserError
from ansible.parsing.mod_args import ModuleArgsParser


class TestModArgsDwim:

    # TODO: add tests that construct ModuleArgsParser with a task reference
    # TODO: verify the AnsibleError raised on failure knows the task
    #       and the task knows the line numbers

    INVALID_MULTIPLE_ACTIONS = (
        ({'action': 'shell echo hi', 'local_action': 'shell echo hi'}, "action and local_action are mutually exclusive"),
        ({'action': 'shell echo hi', 'shell': 'echo hi'}, "conflicting action statements: shell, shell"),
        ({'local_action': 'shell echo hi', 'shell': 'echo hi'}, "conflicting action statements: shell, shell"),
    )

    def _debug(self, mod, args, to):
        print("RETURNED module = {0}".format(mod))
        print("           args = {0}".format(args))
        print("             to = {0}".format(to))

    def test_basic_shell(self):
        m = ModuleArgsParser(dict(shell='echo hi'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod == 'shell'
        assert args == dict(
            _raw_params='echo hi',
        )
        assert to is None

    def test_basic_command(self):
        m = ModuleArgsParser(dict(command='echo hi'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod == 'command'
        assert args == dict(
            _raw_params='echo hi',
        )
        assert to is None

    def test_shell_with_modifiers(self):
        m = ModuleArgsParser(dict(shell='/bin/foo creates=/tmp/baz removes=/tmp/bleep'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod == 'shell'
        assert args == dict(
            creates='/tmp/baz',
            removes='/tmp/bleep',
            _raw_params='/bin/foo',
        )
        assert to is None

    def test_normal_usage(self):
        m = ModuleArgsParser(dict(copy='src=a dest=b'))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod, 'copy'
        assert args, dict(src='a', dest='b')
        assert to is None

    def test_complex_args(self):
        m = ModuleArgsParser(dict(copy=dict(src='a', dest='b')))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod, 'copy'
        assert args, dict(src='a', dest='b')
        assert to is None

    def test_action_with_complex(self):
        m = ModuleArgsParser(dict(action=dict(module='copy', src='a', dest='b')))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_action_with_complex_and_complex_args(self):
        m = ModuleArgsParser(dict(action=dict(module='copy', args=dict(src='a', dest='b'))))
        mod, args, to = m.parse()
        self._debug(mod, args, to)

        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert to is None

    def test_local_action_string(self):
        m = ModuleArgsParser(dict(local_action='copy src=a dest=b'))
        mod, args, delegate_to = m.parse()
        self._debug(mod, args, delegate_to)

        assert mod == 'copy'
        assert args == dict(src='a', dest='b')
        assert delegate_to == 'localhost'

    @pytest.mark.parametrize("args_dict, msg", INVALID_MULTIPLE_ACTIONS)
    def test_multiple_actions(self, args_dict, msg):
        m = ModuleArgsParser(args_dict)
        with pytest.raises(AnsibleParserError) as err:
            m.parse()

        assert err.value.args[0] == msg

    def test_multiple_actions(self):
        args_dict = {'ping': 'data=hi', 'shell': 'echo hi'}
        m = ModuleArgsParser(args_dict)
        with pytest.raises(AnsibleParserError) as err:
            m.parse()

        assert err.value.args[0].startswith("conflicting action statements: ")
        conflicts = set(err.value.args[0][len("conflicting action statements: "):].split(', '))
        assert conflicts == set(('ping', 'shell'))
