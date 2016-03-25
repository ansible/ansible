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
from io import BytesIO

from ansible.compat.tests import unittest

from ansible.module_utils import basic
from ansible.module_utils.basic import heuristic_log_sanitize
from ansible.module_utils.basic import return_values, remove_values

empty_invocation = {u'module_args': {}}

@unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
class TestAnsibleModuleExitJson(unittest.TestCase):

    def setUp(self):
        self.COMPLEX_ARGS = basic.MODULE_COMPLEX_ARGS
        basic.MODULE_COMPLEX_ARGS = '{}'

        self.old_stdout = sys.stdout
        self.fake_stream = BytesIO()
        sys.stdout = self.fake_stream

        self.module = basic.AnsibleModule(argument_spec=dict())

    def tearDown(self):
        basic.MODULE_COMPLEX_ARGS = self.COMPLEX_ARGS
        sys.stdout = self.old_stdout

    def test_exit_json_no_args_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.exit_json()
        if isinstance(ctx.exception, int):
            # Python2.6... why does sys.exit behave this way?
            self.assertEquals(ctx.exception, 0)
        else:
            self.assertEquals(ctx.exception.code, 0)
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(changed=False, invocation=empty_invocation))

    def test_exit_json_args_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            self.module.exit_json(msg='message')
        if isinstance(ctx.exception, int):
            # Python2.6... why does sys.exit behave this way?
            self.assertEquals(ctx.exception, 0)
        else:
            self.assertEquals(ctx.exception.code, 0)
        return_val = json.loads(self.fake_stream.getvalue())
        self.assertEquals(return_val, dict(msg="message", changed=False, invocation=empty_invocation))

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

@unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
class TestAnsibleModuleExitValuesRemoved(unittest.TestCase):
    OMIT = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
    dataset = (
            (dict(username='person', password='$ecret k3y'),
                dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                    not_secret='following the leader', msg='here'),
                dict(one=1, pwd=OMIT, url='https://username:password12345@foo.com/login/',
                    not_secret='following the leader', changed=False, msg='here',
                    invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
                ),
            (dict(username='person', password='password12345'),
                dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                    not_secret='following the leader', msg='here'),
                dict(one=1, pwd='$ecret k3y', url='https://username:********@foo.com/login/',
                    not_secret='following the leader', changed=False, msg='here',
                    invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
                ),
            (dict(username='person', password='$ecret k3y'),
                dict(one=1, pwd='$ecret k3y', url='https://username:$ecret k3y@foo.com/login/',
                    not_secret='following the leader', msg='here'),
                dict(one=1, pwd=OMIT, url='https://username:********@foo.com/login/',
                    not_secret='following the leader', changed=False, msg='here',
                    invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
                ),
            )

    def setUp(self):
        self.COMPLEX_ARGS = basic.MODULE_COMPLEX_ARGS
        self.old_stdout = sys.stdout

    def tearDown(self):
        basic.MODULE_COMPLEX_ARGS = self.COMPLEX_ARGS
        sys.stdout = self.old_stdout

    def test_exit_json_removes_values(self):
        self.maxDiff = None
        for args, return_val, expected in self.dataset:
            sys.stdout = BytesIO()
            basic.MODULE_COMPLEX_ARGS = json.dumps(args)
            module = basic.AnsibleModule(
                argument_spec = dict(
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
            del expected['changed']
            expected['failed'] = True
            sys.stdout = BytesIO()
            basic.MODULE_COMPLEX_ARGS = json.dumps(args)
            module = basic.AnsibleModule(
                argument_spec = dict(
                    username=dict(),
                    password=dict(no_log=True),
                    token=dict(no_log=True),
                    ),
                )
            with self.assertRaises(SystemExit) as ctx:
                self.assertEquals(module.fail_json(**return_val), expected)
            self.assertEquals(json.loads(sys.stdout.getvalue()), expected)
