#
# (c) 2019 Extreme Networks Inc.
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
#
from __future__ import (absolute_import, division, print_function)
import json
import re
from units.compat.mock import patch
from ansible.modules.network.exos import exos_vlan
from units.modules.utils import set_module_args
from ansible.module_utils.six import assertCountEqual
from .exos_module import TestExosModule, load_fixture
__metaclass__ = type


class TestExosVlanModule(TestExosModule):
    module = exos_vlan

    def setUp(self):
        super(TestExosVlanModule, self).setUp()
        self._patch_send_requests = patch(
            'ansible.modules.network.exos.exos_vlan.send_requests'
        )
        self._patch_check_declarative_intent_params = patch(
            'ansible.modules.network.exos.exos_vlan.check_declarative_intent_params')
        self._send_requests = self._patch_send_requests.start()
        self._check_declarative_intent_params = self._patch_check_declarative_intent_params.start()

    def tearDown(self):
        super(TestExosVlanModule, self).tearDown()
        self._patch_send_requests.stop()
        self._patch_check_declarative_intent_params.stop()

    def load_fixtures(self, commands=None):
        config_file = 'get_all_vlans'
        self._send_requests.return_value = [load_fixture(config_file)]

    def make_vlan_result(self, changed, *args):
        requests = []
        result = {}
        for each in args:
            request = {}
            vlan_id, name, method = each

            if method == 'POST':
                path = '/rest/restconf/data/openconfig-vlan:vlans/'
            else:
                path = '/rest/restconf/data/openconfig-vlan:vlans/vlan=' + str(vlan_id)

            if method != 'DELETE':
                vlan_body = {'openconfig-vlan:vlan': [{
                    'config': {
                        'vlan-id': None,
                        'status': 'ACTIVE',
                        'tpid': 'oc-vlan-types:TPID_0x8100',
                        'name': None
                    }
                }]}
                vlan_config = vlan_body['openconfig-vlan:vlan'][0]['config']
                vlan_config['vlan-id'] = vlan_id
                vlan_config['name'] = name
                request['data'] = vlan_body
            request['method'] = method
            request['path'] = path
            requests.append(request)
        result['requests'] = requests
        result['changed'] = changed
        return result

    def test_exos_vlan_invalid_parameter(self, *args, **kwargs):
        set_module_args(
            dict(
                vlan=100,
                name='ansible_100',
                state='present'
            )
        )
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.py|basic.pyc)\) module: '
            'vlan Supported parameters include: aggregate, delay, '
            'interfaces, name, purge, state, vlan_id',
            result['msg']
        ), 'Result did not match expected output. Got: %s' % result['msg'])

    def test_exos_vlan_id_with_name(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=400,
            name='ansible_400'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result, self.make_vlan_result(True, (400, 'ansible_400', 'POST')))

    def test_update_vlan_name(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=100,
            name='changed_name',
            state='present'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result, self.make_vlan_result(True, (100, 'changed_name', 'PATCH'))
        )

    def test_exos_vlan_delete(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=200,
            state='absent'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result, self.make_vlan_result(True, (200, None, 'DELETE'))
        )

    def test_exos_vlan_state_absent_nonexistant_vlan(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=400,
            state='absent'
        ))
        result = self.execute_module()
        self.assertEqual(
            result, {'requests': [],
                     'changed': False})

    def test_exos_vlan_state_present_existant_vlan(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=100,
            state='present'))
        result = self.execute_module()
        self.assertEqual(
            result, {'requests': [],
                     'changed': False})

    def test_exos_vlan_aggregate(self, *args, **kwargs):
        set_module_args(
            dict(
                aggregate=list([
                    dict(vlan_id=400, name='ansible_400'),
                    dict(vlan_id=500, name='ansible_500')
                ]),
                state='present'
            )
        )
        result = self.execute_module(changed=True)
        assertCountEqual(
            self,
            result['requests'],
            self.make_vlan_result(True, (500, 'ansible_500', 'POST'),
                                  (400, 'ansible_400', 'POST'))['requests']
        )

    def test_exos_vlan_purge(self, *args, **kwargs):
        set_module_args(
            dict(
                aggregate=list([
                    dict(vlan_id=400, name='ansible_400'),
                    dict(vlan_id=500, name='ansible_500')
                ]),
                state='present',
                purge=True
            )
        )
        result = self.execute_module(changed=True)
        assertCountEqual(
            self,
            result['requests'],
            self.make_vlan_result(True, (500, 'ansible_500', 'POST'),
                                  (400, 'ansible_400', 'POST'),
                                  (100, None, 'DELETE'),
                                  (300, None, 'DELETE'),
                                  (200, None, 'DELETE'))['requests']
        )

    def test_exos_vlan_interfaces(self, *args, **kwargs):
        set_module_args(
            dict(
                vlan_id=100,
                name='ansible_100',
                interfaces=['1', '2', '3']
            )
        )
        result = self.execute_module(changed=True)
        if_base_path = '/rest/restconf/data/openconfig-interfaces:interfaces/interface='
        if_vlan_path = '/openconfig--if-ethernet:ethernet/openconfig-vlan:switched-vlan/'
        assertCountEqual(
            self,
            result['requests'],
            [
                {
                    'data': {
                        'openconfig-vlan:switched-vlan': {
                            'config': {
                                'access-vlan': 100,
                                'interface-mode': 'ACCESS'
                            }
                        }
                    },
                    'method': 'PATCH',
                    'path': if_base_path + '1' + if_vlan_path
                },
                {
                    'data': {
                        'openconfig-vlan:switched-vlan': {
                            'config': {
                                'access-vlan': 100,
                                'interface-mode': 'ACCESS'
                            }
                        }
                    },
                    'method': 'PATCH',
                    'path': if_base_path + '2' + if_vlan_path
                },
                {
                    'data': {
                        'openconfig-vlan:switched-vlan': {
                            'config': {
                                'access-vlan': 100,
                                'interface-mode': 'ACCESS'
                            }
                        }
                    },
                    'method': 'PATCH',
                    'path': if_base_path + '3' + if_vlan_path
                }
            ]
        )
