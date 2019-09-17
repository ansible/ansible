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


from ansible.modules.net_tools.nios import nios_ptr_record
from ansible.module_utils.net_tools.nios import api
from units.compat.mock import patch, MagicMock, Mock
from .test_nios_module import TestNiosModule, load_fixture


class TestNiosPTRRecordModule(TestNiosModule):

    module = nios_ptr_record

    def setUp(self):

        super(TestNiosPTRRecordModule, self).setUp()
        self.module = MagicMock(name='ansible.modules.net_tools.nios.nios_ptr_record.WapiModule')
        self.module.check_mode = False
        self.module.params = {'provider': None}

        self.mock_wapi = patch('ansible.modules.net_tools.nios.nios_ptr_record.WapiModule')
        self.exec_command = self.mock_wapi.start()
        self.mock_wapi_run = patch('ansible.modules.net_tools.nios.nios_ptr_record.WapiModule.run')
        self.mock_wapi_run.start()

        self.load_config = self.mock_wapi_run.start()

    def tearDown(self):
        super(TestNiosPTRRecordModule, self).tearDown()
        self.mock_wapi.stop()

    def _get_wapi(self, test_object):
        wapi = api.WapiModule(self.module)
        wapi.get_object = Mock(name='get_object', return_value=test_object)
        wapi.create_object = Mock(name='create_object')
        wapi.update_object = Mock(name='update_object')
        wapi.delete_object = Mock(name='delete_object')
        return wapi

    def load_fixtures(self, commands=None):
        self.exec_command.return_value = (0, load_fixture('nios_result.txt').strip(), None)
        self.load_config.return_value = dict(diff=None, session='session')

    def test_nios_ptr_record_create(self):
        self.module.params = {'provider': None, 'state': 'present', 'ptrdname': 'ansible.test.com',
                              'ipv4addr': '10.36.241.14', 'comment': None, 'extattrs': None, 'view': 'default'}

        test_object = None
        test_spec = {
            "ipv4addr": {"ib_req": True},
            "ptrdname": {"ib_req": True},
            "comment": {},
            "extattrs": {},
            "view": {"ib_req": True}
        }

        wapi = self._get_wapi(test_object)
        print("WAPI: ", wapi)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.create_object.assert_called_once_with('testobject', {'ipv4addr': '10.36.241.14', 'ptrdname': 'ansible.test.com', 'view': 'default'})

    def test_nios_ptr_record_remove(self):
        self.module.params = {'provider': None, 'state': 'absent', 'ptrdname': 'ansible.test.com',
                              'ipv4addr': '10.36.241.14', 'comment': None, 'extattrs': None, 'view': 'default'}

        ref = "record:ptr/ZG5zLm5ldHdvcmtfdmlldyQw:14.241.36.10.in-addr.arpa/default"

        test_object = [{
            "comment": "test comment",
            "_ref": ref,
            "ptrdname": "ansible.test.com",
            "ipv4addr": "10.36.241.14",
            "view": "default",
            "extattrs": {'Site': {'value': 'test'}}
        }]

        test_spec = {
            "ipv4addr": {"ib_req": True},
            "ptrdname": {"ib_req": True},
            "comment": {},
            "extattrs": {},
            "view": {"ib_req": True}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)
        self.assertTrue(res['changed'])
        wapi.delete_object.assert_called_once_with(ref)

    def test_nios_ptr_record_update_comment(self):
        self.module.params = {'provider': None, 'state': 'present', 'ptrdname': 'ansible.test.com',
                              'ipv4addr': '10.36.241.14', 'comment': 'updated comment', 'extattrs': None, 'view': 'default'}

        test_object = [
            {
                "comment": "test comment",
                "_ref": "record:ptr/ZG5zLm5ldHdvcmtfdmlldyQw:14.241.36.10.in-addr.arpa/default",
                "ptrdname": "ansible.test.com",
                "ipv4addr": "10.36.241.14",
                "extattrs": {},
                "view": "default"
            }
        ]

        test_spec = {
            "ipv4addr": {"ib_req": True},
            "ptrdname": {"ib_req": True},
            "comment": {},
            "extattrs": {},
            "view": {"ib_req": True}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.called_once_with(test_object)

    def test_nios_ptr_record_update_record_ptrdname(self):
        self.module.params = {'provider': None, 'state': 'present', 'ptrdname': 'ansible.test.org',
                              'ipv4addr': '10.36.241.14', 'comment': 'comment', 'extattrs': None, 'view': 'default'}

        test_object = [
            {
                "comment": "test comment",
                "_ref": "record:ptr/ZG5zLm5ldHdvcmtfdmlldyQw:14.241.36.10.in-addr.arpa/default",
                "ptrdname": "ansible.test.com",
                "ipv4addr": "10.36.241.14",
                "extattrs": {},
                "view": "default"
            }
        ]

        test_spec = {
            "ipv4addr": {"ib_req": True},
            "ptrdname": {"ib_req": True},
            "comment": {},
            "extattrs": {},
            "view": {"ib_req": True}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.called_once_with(test_object)

    def test_nios_ptr6_record_create(self):
        self.module.params = {'provider': None, 'state': 'present', 'ptrdname': 'ansible6.test.com',
                              'ipv6addr': '2002:8ac3:802d:1242:20d:60ff:fe38:6d16', 'comment': None, 'extattrs': None, 'view': 'default'}

        test_object = None
        test_spec = {"ipv6addr": {"ib_req": True},
                     "ptrdname": {"ib_req": True},
                     "comment": {},
                     "extattrs": {},
                     "view": {"ib_req": True}}

        wapi = self._get_wapi(test_object)
        print("WAPI: ", wapi)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.create_object.assert_called_once_with('testobject', {'ipv6addr': '2002:8ac3:802d:1242:20d:60ff:fe38:6d16',
                                                                  'ptrdname': 'ansible6.test.com', 'view': 'default'})
