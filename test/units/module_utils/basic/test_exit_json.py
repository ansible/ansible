# -*- coding: utf-8 -*-
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

import copy
import json
import sys

from ansible.compat.tests import unittest
from ansible.module_utils import basic
from units.mock.procenv import swap_stdin_and_argv, swap_stdout


empty_invocation = {u'module_args': {}}


class TestAnsibleModuleExitJson(unittest.TestCase):
    def setUp(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        self.stdin_swap_ctx = swap_stdin_and_argv(stdin_data=args)
        self.stdin_swap_ctx.__enter__()

        # since we can't use context managers and "with" without overriding run(), call them directly
        self.stdout_swap_ctx = swap_stdout()
        self.fake_stream = self.stdout_swap_ctx.__enter__()

        basic._ANSIBLE_ARGS = None
        self.module = basic.AnsibleModule(argument_spec=dict())

    def tearDown(self):
        # since we can't use context managers and "with" without overriding run(), call them directly to clean up
        self.stdin_swap_ctx.__exit__(None, None, None)
        self.stdout_swap_ctx.__exit__(None, None, None)

    def test_exit_json_no_args_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.exit_json()
        if isinstance(ctx.exception, int):
            # Python2.6... why does sys.exit behave this way?
            self.assertEquals(ctx.exception, 0)
        else:
            self.assertEquals(ctx.exception.code, 0)
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(invocation=empty_invocation))

    def test_exit_json_args_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.exit_json(msg='message')
        if isinstance(ctx.exception, int):
            # Python2.6... why does sys.exit behave this way?
            self.assertEquals(ctx.exception, 0)
        else:
            self.assertEquals(ctx.exception.code, 0)
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(msg="message", invocation=empty_invocation))

    def test_fail_json_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.fail_json(msg='message')
        if isinstance(ctx.exception, int):
            # Python2.6... why does sys.exit behave this way?
            self.assertEquals(ctx.exception, 1)
        else:
            self.assertEquals(ctx.exception.code, 1)
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(msg="message", failed=True, invocation=empty_invocation))

    def test_exit_json_proper_changed(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.exit_json(changed=True, msg='success')
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(changed=True, msg='success', invocation=empty_invocation))


class TestAnsibleModuleExitValuesRemoved(unittest.TestCase):
    OMIT = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
    dataset = (
        (
            dict(username='person', password='$ecret k3y'),
            dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd=OMIT, url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
        (
            dict(username='person', password='password12345'),
            dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd='$ecret k3y', url='https://username:********@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
        (
            dict(username='person', password='$ecret k3y'),
            dict(one=1, pwd='$ecret k3y', url='https://username:$ecret k3y@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd=OMIT, url='https://username:********@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
    )

    def test_exit_json_removes_values(self):
        self.maxDiff = None
        for args, return_val, expected in self.dataset:
            params = dict(ANSIBLE_MODULE_ARGS=args)
            params = json.dumps(params)

            with swap_stdin_and_argv(stdin_data=params):
                with swap_stdout():
                    basic._ANSIBLE_ARGS = None
                    module = basic.AnsibleModule(
                        argument_spec=dict(
                            username=dict(),
                            password=dict(no_log=True),
                            token=dict(no_log=True),
                        ),
                    )
                    with self.assertRaises(SystemExit) as ctx:
                        self.assertEquals(module.exit_json(**return_val), expected)
                    self.assertEquals(json.loads(sys.stdout.getvalue()), expected)

    def test_fail_json_removes_values(self):
        self.maxDiff = None
        for args, return_val, expected in self.dataset:
            expected = copy.deepcopy(expected)
            expected['failed'] = True
            params = dict(ANSIBLE_MODULE_ARGS=args)
            params = json.dumps(params)
            with swap_stdin_and_argv(stdin_data=params):
                with swap_stdout():
                    basic._ANSIBLE_ARGS = None
                    module = basic.AnsibleModule(
                        argument_spec=dict(
                            username=dict(),
                            password=dict(no_log=True),
                            token=dict(no_log=True),
                        ),
                    )
                    with self.assertRaises(SystemExit) as ctx:
                        self.assertEquals(module.fail_json(**return_val), expected)
                    self.assertEquals(json.loads(sys.stdout.getvalue()), expected)
