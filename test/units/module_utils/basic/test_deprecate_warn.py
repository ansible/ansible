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

import json
import sys

from ansible.compat.tests import unittest
from units.mock.procenv import swap_stdin_and_argv, swap_stdout

import ansible.module_utils.basic


class TestAnsibleModuleWarnDeprecate(unittest.TestCase):
    """Test the AnsibleModule Warn Method"""

    def test_warn(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        with swap_stdin_and_argv(stdin_data=args):
            with swap_stdout():

                ansible.module_utils.basic._ANSIBLE_ARGS = None
                am = ansible.module_utils.basic.AnsibleModule(
                    argument_spec = dict(),
                )
                am._name = 'unittest'

                am.warn('warning1')

                with self.assertRaises(SystemExit):
                    am.exit_json(warnings=['warning2'])
                self.assertEquals(json.loads(sys.stdout.getvalue())['warnings'], ['warning1', 'warning2'])

    def test_deprecate(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        with swap_stdin_and_argv(stdin_data=args):
            with swap_stdout():

                ansible.module_utils.basic._ANSIBLE_ARGS = None
                am = ansible.module_utils.basic.AnsibleModule(
                    argument_spec = dict(),
                )
                am._name = 'unittest'

                am.deprecate('deprecation1')
                am.deprecate('deprecation2', '2.3')

                with self.assertRaises(SystemExit):
                    am.exit_json(deprecations=['deprecation3', ('deprecation4', '2.4')])
                output = json.loads(sys.stdout.getvalue())
                self.assertTrue('warnings' not in output or output['warnings'] == [])
                self.assertEquals(output['deprecations'], [
                    {u'msg': u'deprecation1', u'version': None},
                    {u'msg': u'deprecation2', u'version': '2.3'},
                    {u'msg': u'deprecation3', u'version': None},
                    {u'msg': u'deprecation4', u'version': '2.4'},
                ])

    def test_deprecate_without_list(self):
        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
        with swap_stdin_and_argv(stdin_data=args):
            with swap_stdout():

                ansible.module_utils.basic._ANSIBLE_ARGS = None
                am = ansible.module_utils.basic.AnsibleModule(
                    argument_spec = dict(),
                )
                am._name = 'unittest'

                with self.assertRaises(SystemExit):
                    am.exit_json(deprecations='Simple deprecation warning')
                output = json.loads(sys.stdout.getvalue())
                self.assertTrue('warnings' not in output or output['warnings'] == [])
                self.assertEquals(output['deprecations'], [
                    {u'msg': u'Simple deprecation warning', u'version': None},
                ])
