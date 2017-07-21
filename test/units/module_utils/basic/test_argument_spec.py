# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division)
__metaclass__ = type

import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock
from units.mock.procenv import swap_stdin_and_argv, swap_stdout
from ansible.module_utils import basic


class TestCallableTypeValidation(unittest.TestCase):
    def setUp(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS=dict(arg="42")))
        self.stdin_swap_ctx = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap_ctx.__enter__()

        # since we can't use context managers and "with" without overriding run(), call them directly
        self.stdout_swap_ctx = swap_stdout()
        self.fake_stream = self.stdout_swap_ctx.__enter__()

        basic._ANSIBLE_ARGS = None

    def tearDown(self):
        # since we can't use context managers and "with" without overriding run(), call them directly to clean up
        self.stdin_swap_ctx.__exit__(None, None, None)
        self.stdout_swap_ctx.__exit__(None, None, None)

    def test_validate_success(self):
        mock_validator = MagicMock(return_value=42)
        m = basic.AnsibleModule(argument_spec=dict(
            arg=dict(type=mock_validator)
        ))

        self.assertTrue(mock_validator.called)
        self.assertEqual(m.params['arg'], 42)
        self.assertEqual(type(m.params['arg']), int)

    def test_validate_fail(self):
        mock_validator = MagicMock(side_effect=TypeError("bad conversion"))
        with self.assertRaises(SystemExit) as ecm:
            m = basic.AnsibleModule(argument_spec=dict(
                arg=dict(type=mock_validator)
            ))

        self.assertIn("bad conversion", json.loads(self.fake_stream.getvalue())['msg'])
