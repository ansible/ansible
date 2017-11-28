# (c) 2016 Red Hat Inc.
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
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.modules.network.cnos.cnos_restapi as cnos_restapi


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


class TestCnosRestModule(unittest.TestCase):

    def execute_module(self, failed=False, changed=False, defaults=False):

        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

    def failed(self):
        def fail_json(*args, **kwargs):
            kwargs['failed'] = True
            raise AnsibleFailJson(kwargs)

        with patch.object(basic.AnsibleModule, 'fail_json', fail_json):
            with self.assertRaises(AnsibleFailJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        def exit_json(*args, **kwargs):
            if 'changed' not in kwargs:
                kwargs['changed'] = False
            raise AnsibleExitJson(kwargs)

        with patch.object(basic.AnsibleModule, 'exit_json', exit_json):
            with self.assertRaises(AnsibleExitJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result


class TestCnosRestapiModule(TestCnosRestModule):

    module = cnos_restapi

    def test_cnos_restapi_unreachable(self):        
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='https', urlpath='/nos/api/cfg/vlan',
                             method='GET'))
        result = self.execute_module(failed=True)

    @patch('ansible.modules.network.lenovo.cnos_restapi.RestModule')
    def test_cnos_restapi_success(self, RestModule):
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='https', urlpath='/nos/api/cfg/vlan',
                             method='GET'))
        instance = RestModule.return_value
        instance.loginurl.return_value = 1
        instance.cb_method.return_value = 1, "good"
        result = self.execute_module(changed=True)

    @patch('ansible.modules.network.lenovo.cnos_restapi.RestModule')
    def test_cnos_restapi_failed_at_login(self, RestModule):
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='https', urlpath='/nos/api/cfg/vlan',
                             method='GET'))
        instance = RestModule.return_value
        instance.loginurl.return_value = 0
        result = self.execute_module(failed=True)

    @patch('ansible.modules.network.lenovo.cnos_restapi.RestModule')
    def test_cnos_restapi_failed_at_cbmethod(self, RestModule):
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='https', urlpath='/nos/api/cfg/vlan',
                             method='GET'))
        instance = RestModule.return_value
        instance.loginurl.return_value = 1
        instance.cb_method.return_value = 0, "bad"
        result = self.execute_module(failed=True)

    @patch('ansible.modules.network.lenovo.cnos_restapi.RestModule')
    def test_cnos_restapi_failed_incorrect_method(self, RestModule):
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='https', urlpath='/nos/api/cfg/vlan',
                             method='GT'))
        instance = RestModule.return_value
        instance.loginurl.return_value = 1
        instance.cb_method.return_value = 0, "bad"
        result = self.execute_module(failed=True)

    @patch('ansible.modules.network.lenovo.cnos_restapi.RestModule')
    def test_cnos_restapi_failed_incorrect_transport(self, RestModule):
        set_module_args(dict(outputfile='myfile', host='10.240.176.2',
                             username='admin', password='admin',
                             transport='tps', urlpath='/nos/api/cfg/vlan',
                             method='GET'))
        instance = RestModule.return_value
        instance.loginurl.return_value = 1
        instance.cb_method.return_value = 0, "bad"
        result = self.execute_module(failed=True)
