# (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy

from units.compat import unittest
from units.compat.mock import patch, MagicMock, Mock
from ansible.module_utils.net_tools.nios import api


class TestNiosApi(unittest.TestCase):

    def setUp(self):
        super(TestNiosApi, self).setUp()

        self.module = MagicMock(name='AnsibleModule')
        self.module.check_mode = False
        self.module.params = {'provider': None}

        self.mock_connector = patch('ansible.module_utils.net_tools.nios.api.get_connector')
        self.mock_connector.start()

    def tearDown(self):
        super(TestNiosApi, self).tearDown()

        self.mock_connector.stop()

    def test_get_provider_spec(self):
        provider_options = ['host', 'username', 'password', 'validate_certs', 'silent_ssl_warnings',
                            'http_request_timeout', 'http_pool_connections',
                            'http_pool_maxsize', 'max_retries', 'wapi_version', 'max_results']
        res = api.WapiBase.provider_spec
        self.assertIsNotNone(res)
        self.assertIn('provider', res)
        self.assertIn('options', res['provider'])
        returned_options = res['provider']['options']
        self.assertEqual(sorted(provider_options), sorted(returned_options.keys()))

    def _get_wapi(self, test_object):
        wapi = api.WapiModule(self.module)
        wapi.get_object = Mock(name='get_object', return_value=test_object)
        wapi.create_object = Mock(name='create_object')
        wapi.update_object = Mock(name='update_object')
        wapi.delete_object = Mock(name='delete_object')
        return wapi

    def test_wapi_no_change(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'default',
                              'comment': 'test comment', 'extattrs': None}

        test_object = [
            {
                "comment": "test comment",
                "_ref": "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true",
                "name": self.module._check_type_dict().__getitem__(),
                "extattrs": {}
            }
        ]

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertFalse(res['changed'])

    def test_wapi_change(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'default',
                              'comment': 'updated comment', 'extattrs': None}

        test_object = [
            {
                "comment": "test comment",
                "_ref": "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true",
                "name": "default",
                "extattrs": {}
            }
        ]

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.called_once_with(test_object)

    def test_wapi_change_false(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'default',
                              'comment': 'updated comment', 'extattrs': None, 'fqdn': 'foo'}

        test_object = [
            {
                "comment": "test comment",
                "_ref": "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true",
                "name": "default",
                "extattrs": {}
            }
        ]

        test_spec = {
            "name": {"ib_req": True},
            "fqdn": {"ib_req": True, 'update': False},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.called_once_with(test_object)

    def test_wapi_extattrs_change(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'default',
                              'comment': 'test comment', 'extattrs': {'Site': 'update'}}

        ref = "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true"

        test_object = [{
            "comment": "test comment",
            "_ref": ref,
            "name": "default",
            "extattrs": {'Site': {'value': 'test'}}
        }]

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        kwargs = copy.deepcopy(test_object[0])
        kwargs['extattrs']['Site']['value'] = 'update'
        kwargs['name'] = self.module._check_type_dict().__getitem__()
        del kwargs['_ref']

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.assert_called_once_with(ref, kwargs)

    def test_wapi_extattrs_nochange(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'default',
                              'comment': 'test comment', 'extattrs': {'Site': 'test'}}

        test_object = [{
            "comment": "test comment",
            "_ref": "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:default/true",
            "name": self.module._check_type_dict().__getitem__(),
            "extattrs": {'Site': {'value': 'test'}}
        }]

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertFalse(res['changed'])

    def test_wapi_create(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'ansible',
                              'comment': None, 'extattrs': None}

        test_object = None

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.create_object.assert_called_once_with('testobject', {'name': self.module._check_type_dict().__getitem__()})

    def test_wapi_delete(self):
        self.module.params = {'provider': None, 'state': 'absent', 'name': 'ansible',
                              'comment': None, 'extattrs': None}

        ref = "networkview/ZG5zLm5ldHdvcmtfdmlldyQw:ansible/false"

        test_object = [{
            "comment": "test comment",
            "_ref": ref,
            "name": "ansible",
            "extattrs": {'Site': {'value': 'test'}}
        }]

        test_spec = {
            "name": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.delete_object.assert_called_once_with(ref)

    def test_wapi_strip_network_view(self):
        self.module.params = {'provider': None, 'state': 'present', 'name': 'ansible',
                              'comment': 'updated comment', 'extattrs': None,
                              'network_view': 'default'}

        test_object = [{
            "comment": "test comment",
            "_ref": "view/ZG5zLm5ldHdvcmtfdmlldyQw:ansible/true",
            "name": "ansible",
            "extattrs": {},
            "network_view": "default"
        }]

        test_spec = {
            "name": {"ib_req": True},
            "network_view": {"ib_req": True},
            "comment": {},
            "extattrs": {}
        }

        kwargs = test_object[0].copy()
        ref = kwargs.pop('_ref')
        kwargs['comment'] = 'updated comment'
        kwargs['name'] = self.module._check_type_dict().__getitem__()
        del kwargs['network_view']
        del kwargs['extattrs']

        wapi = self._get_wapi(test_object)
        res = wapi.run('testobject', test_spec)

        self.assertTrue(res['changed'])
        wapi.update_object.assert_called_once_with(ref, kwargs)
