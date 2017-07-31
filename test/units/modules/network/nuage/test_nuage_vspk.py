# -*- coding: utf-8 -*-

# (c) 2017, Nokia
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

import sys

from nose.plugins.skip import SkipTest
if not(sys.version_info[0] == 2 and sys.version_info[1] >= 7):
    raise SkipTest('Nuage Ansible modules requires Python 2.7')

try:
    from vspk import v5_0 as vsdk
    from bambou.exceptions import BambouHTTPError
    from ansible.modules.network.nuage import nuage_vspk
except ImportError:
    raise SkipTest('Nuage Ansible modules requires the vspk and bambou python libraries')

from ansible.compat.tests.mock import patch
from .nuage_module import AnsibleExitJson, AnsibleFailJson, MockNuageConnection, TestNuageModule, set_module_args, set_module_args_custom_auth

_LOOP_COUNTER = 0


class TestNuageVSPKModule(TestNuageModule):

    def setUp(self):
        super(TestNuageVSPKModule, self).setUp()

        self.patches = []

        def enterprises_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False,
                            callback=None):
            if 'unknown' in filter:
                return []

            result = [vsdk.NUEnterprise(id='enterprise-id', name='test-enterprise')]
            if filter == '' or filter == 'name == "test%"':
                result.append(vsdk.NUEnterprise(id='enterprise-id-2', name='test-enterprise-2'))
            return result

        self.enterprises_get_mock = patch('vspk.v5_0.fetchers.NUEnterprisesFetcher.get', new=enterprises_get)
        self.enterprises_get_mock.start()
        self.patches.append(self.enterprises_get_mock)

        def enterprises_get_first(self, filter=None, order_by=None, group_by=[], query_parameters=None, commit=False, async=False, callback=None):
            if filter == 'name == "test-enterprise-create"' or 'unknown' in filter:
                return None
            return vsdk.NUEnterprise(id='enterprise-id', name='test-enterprise')

        self.enterprises_get_first_mock = patch('vspk.v5_0.fetchers.NUEnterprisesFetcher.get_first', new=enterprises_get_first)
        self.enterprises_get_first_mock.start()
        self.patches.append(self.enterprises_get_first_mock)

        def enterprise_delete(self, response_choice=1, async=False, callback=None):
            pass

        self.enterprise_delete_mock = patch('vspk.v5_0.NUEnterprise.delete', new=enterprise_delete)
        self.enterprise_delete_mock.start()
        self.patches.append(self.enterprise_delete_mock)

        def enterprise_fetch(self, async=False, callback=None):
            self.id = 'enterprise-id'
            self.name = 'test-enterprise'

        self.enterprise_fetch_mock = patch('vspk.v5_0.NUEnterprise.fetch', new=enterprise_fetch)
        self.enterprise_fetch_mock.start()
        self.patches.append(self.enterprise_fetch_mock)

        def enterprise_save(self, response_choice=None, async=False, callback=None):
            self.id = 'enterprise-id'
            self.name = 'test-enterprise-update'

        self.enterprise_save_mock = patch('vspk.v5_0.NUEnterprise.save', new=enterprise_save)
        self.enterprise_save_mock.start()
        self.patches.append(self.enterprise_save_mock)

        def enterprise_create_child(self, nurest_object, response_choice=None, async=False, callback=None, commit=True):
            nurest_object.id = 'user-id-create'
            return nurest_object

        self.enterprise_create_child_mock = patch('vspk.v5_0.NUEnterprise.create_child', new=enterprise_create_child)
        self.enterprise_create_child_mock.start()
        self.patches.append(self.enterprise_create_child_mock)

        def me_create_child(self, nurest_object, response_choice=None, async=False, callback=None, commit=True):
            nurest_object.id = 'enterprise-id-create'
            return nurest_object

        self.me_create_child_mock = patch('vspk.v5_0.NUMe.create_child', new=me_create_child)
        self.me_create_child_mock.start()
        self.patches.append(self.me_create_child_mock)

        def user_fetch(self, async=False, callback=None):
            self.id = 'user-id'
            self.first_name = 'John'
            self.last_name = 'Doe'
            self.email = 'john.doe@localhost'
            self.user_name = 'johndoe'
            self.password = ''

        self.user_fetch_mock = patch('vspk.v5_0.NUUser.fetch', new=user_fetch)
        self.user_fetch_mock.start()
        self.patches.append(self.user_fetch_mock)

        def user_save(self, response_choice=None, async=False, callback=None):
            self.id = 'user-id'
            self.first_name = 'John'
            self.last_name = 'Doe'
            self.email = 'john.doe@localhost'
            self.user_name = 'johndoe'
            self.password = ''

        self.user_save_mock = patch('vspk.v5_0.NUUser.save', new=user_save)
        self.user_save_mock.start()
        self.patches.append(self.user_save_mock)

        def groups_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False,
                       callback=None):
            return []

        self.groups_get_mock = patch('vspk.v5_0.fetchers.NUGroupsFetcher.get', new=groups_get)
        self.groups_get_mock.start()
        self.patches.append(self.groups_get_mock)

        def group_fetch(self, async=False, callback=None):
            self.id = 'group-id'
            self.name = 'group'

        self.group_fetch_mock = patch('vspk.v5_0.NUGroup.fetch', new=group_fetch)
        self.group_fetch_mock.start()
        self.patches.append(self.group_fetch_mock)

        def group_assign(self, objects, nurest_object_type, async=False, callback=None, commit=True):
            self.id = 'group-id'
            self.name = 'group'

        self.group_assign_mock = patch('vspk.v5_0.NUGroup.assign', new=group_assign)
        self.group_assign_mock.start()
        self.patches.append(self.group_assign_mock)

        def job_fetch(self, async=False, callback=None):
            global _LOOP_COUNTER
            self.id = 'job-id'
            self.command = 'EXPORT'
            self.status = 'RUNNING'
            if _LOOP_COUNTER > 1:
                self.status = 'SUCCESS'
            _LOOP_COUNTER += 1

        self.job_fetch_mock = patch('vspk.v5_0.NUJob.fetch', new=job_fetch)
        self.job_fetch_mock.start()
        self.patches.append(self.job_fetch_mock)

    def tearDown(self):
        super(TestNuageVSPKModule, self).tearDown()
        for patch in self.patches:
            patch.stop()

    def test_certificate_auth(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'state': 'present',
                'properties': {
                    'name': 'test-enterprise'
                }
            },
            auth={
                'api_username': 'csproot',
                'api_certificate': '/dummy/location/certificate.pem',
                'api_key': '/dummy/location/key.pem',
                'api_enterprise': 'csp',
                'api_url': 'https://localhost:8443',
                'api_version': 'v5_0'
            }
        )

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_command_find_by_property(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'find',
            'properties': {
                'name': 'test-enterprise'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_command_find_by_filter(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'find',
            'match_filter': 'name == "test%"'
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 2)
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')
        self.assertEqual(result['entities'][1]['name'], 'test-enterprise-2')

    def test_command_find_by_id(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'command': 'find'
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_command_find_all(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'find'
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 2)
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')
        self.assertEqual(result['entities'][1]['name'], 'test-enterprise-2')

    def test_command_change_password(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'enterprise-id',
            'parent_type': 'Enterprise',
            'command': 'change_password',
            'properties': {
                'password': 'test'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(result['id'], 'user-id')
        self.assertEqual(result['entities'][0]['firstName'], 'John')
        self.assertEqual(result['entities'][0]['lastName'], 'Doe')
        self.assertEqual(result['entities'][0]['email'], 'john.doe@localhost')
        self.assertEqual(result['entities'][0]['userName'], 'johndoe')
        self.assertEqual(result['entities'][0]['password'], '')

    def test_command_wait_for_job(self):
        set_module_args(args={
            'id': 'job-id',
            'type': 'Job',
            'command': 'wait_for_job',
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(result['id'], 'job-id')
        self.assertEqual(result['entities'][0]['command'], 'EXPORT')
        self.assertEqual(result['entities'][0]['status'], 'SUCCESS')

    def test_command_get_csp_enterprise(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'get_csp_enterprise'
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_state_present_existing(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'id': 'enterprise-id',
                'name': 'test-enterprise'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_state_present_existing_filter(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'match_filter': 'name == "test-enterprise"'
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise')

    def test_state_present_create(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id-create')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise-create')

    def test_state_present_update(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-update'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'enterprise-id')
        self.assertEqual(result['entities'][0]['name'], 'test-enterprise-update')

    def test_state_present_member_existing(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'present'
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return [vsdk.NUUser(id='user-id'), vsdk.NUUser(id='user-id-2')]

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])

    def test_state_present_member_missing(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'present'
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return []

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['id'], 'user-id')

    def test_state_present_children_update(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise'
            },
            'children': [
                {
                    'id': 'user-id',
                    'type': 'User',
                    'match_filter': 'userName == "johndoe"',
                    'properties': {
                        'user_name': 'johndoe-changed'
                    }
                }
            ]
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertEqual(result['changed'], True)
        self.assertEqual(len(result['entities']), 2)

    def test_state_present_children_create(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            },
            'children': [
                {
                    'type': 'User',
                    'properties': {
                        'user_name': 'johndoe-new'
                    }
                }
            ]
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return []

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['changed'])
        self.assertEqual(len(result['entities']), 2)

    def test_state_present_children_member_missing(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'unkown-test-enterprise'
            },
            'children': [
                {
                    'type': 'Group',
                    'properties': {
                        'name': 'unknown-group'
                    },
                    'children': [
                        {
                            'id': 'user-id',
                            'type': 'User'
                        }
                    ]
                }
            ]
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return []

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['changed'])
        self.assertEqual(len(result['entities']), 3)

    def test_state_absent(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'absent',
            'properties': {
                'name': 'test-enterprise'
            }
        })

        with self.assertRaises(AnsibleExitJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['changed'])

    def test_state_absent_member(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'absent'
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return [vsdk.NUUser(id='user-id')]

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['changed'])

    def test_exception_session(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'command': 'find'
        })

        def failed_session_start(self):
            raise BambouHTTPError(MockNuageConnection(status_code='401', reason='Unauthorized', errors={}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUVSDSession.start', new=failed_session_start):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unable to connect to the API URL with given username, password and enterprise: [HTTP 401(Unauthorized)] {}')

    def test_exception_find_parent(self):
        set_module_args(args={
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'command': 'find'
        })

        def group_failed_fetch(self, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUGroup.fetch', group_failed_fetch):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Failed to fetch the specified parent: [HTTP 404(Not Found)] {'description': 'Entity not found'}")

    def test_exception_find_entities_id(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'command': 'find'
        })

        def enterprise_failed_fetch(self, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUEnterprise.fetch', enterprise_failed_fetch):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Failed to fetch the specified entity by ID: [HTTP 404(Not Found)] {'description': 'Entity not found'}")

    def test_excption_find_entities_property(self):
        set_module_args(args={
            'type': 'Enterprise',
            'match_filter': 'name == "enterprise-id"',
            'command': 'find'
        })

        def enterprises_failed_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False,
                                   callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.fetchers.NUEnterprisesFetcher.get', enterprises_failed_get):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unable to find matching entries')

    def test_exception_find_entity_id(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'state': 'present'
        })

        def enterprise_failed_fetch(self, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUEnterprise.fetch', enterprise_failed_fetch):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Failed to fetch the specified entity by ID: [HTTP 404(Not Found)] {'description': 'Entity not found'}")

    def test_exception_find_entity_property(self):
        set_module_args(args={
            'type': 'Enterprise',
            'match_filter': 'name == "enterprise-id"',
            'state': 'absent'
        })

        def enterprises_failed_get_first(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True,
                                         async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleExitJson) as exc:
            with patch('vspk.v5_0.fetchers.NUEnterprisesFetcher.get_first', enterprises_failed_get_first):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertFalse(result['changed'])

    def test_exception_get_csp_enterprise(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'get_csp_enterprise'
        })

        def enterprise_failed_fetch(self, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='404', reason='Not Found', errors={'description': 'Entity not found'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUEnterprise.fetch', enterprise_failed_fetch):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to fetch CSP enterprise: [HTTP 404(Not Found)] {'description': 'Entity not found'}")

    def test_exception_assign_member(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'present'
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return []

        def group_assign(self, objects, nurest_object_type, async=False, callback=None, commit=True):
            raise BambouHTTPError(MockNuageConnection(status_code='500', reason='Server exception', errors={'description': 'Unable to assign member'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                with patch('vspk.v5_0.NUGroup.assign', new=group_assign):
                    nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to assign entity as a member: [HTTP 500(Server exception)] {'description': 'Unable to assign member'}")

    def test_exception_unassign_member(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'absent'
        })

        def users_get(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False, callback=None):
            return [vsdk.NUUser(id='user-id'), vsdk.NUUser(id='user-id-2')]

        def group_assign(self, objects, nurest_object_type, async=False, callback=None, commit=True):
            raise BambouHTTPError(MockNuageConnection(status_code='500', reason='Server exception', errors={'description': 'Unable to remove member'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get', users_get):
                with patch('vspk.v5_0.NUGroup.assign', new=group_assign):
                    nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to remove entity as a member: [HTTP 500(Server exception)] {'description': 'Unable to remove member'}")

    def test_exception_create_entity(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            }
        })

        def me_create_child(self, nurest_object, response_choice=None, async=False, callback=None, commit=True):
            raise BambouHTTPError(MockNuageConnection(status_code='500', reason='Server exception', errors={'description': 'Unable to create entity'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUMe.create_child', me_create_child):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to create entity: [HTTP 500(Server exception)] {'description': 'Unable to create entity'}")

    def test_exception_save_entity(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'new-enterprise-name'
            }
        })

        def enterprise_save(self, response_choice=None, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='500', reason='Server exception', errors={'description': 'Unable to save entity'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUEnterprise.save', enterprise_save):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to update entity: [HTTP 500(Server exception)] {'description': 'Unable to save entity'}")

    def test_exception_delete_entity(self):
        set_module_args(args={
            'id': 'enterprise-id',
            'type': 'Enterprise',
            'state': 'absent'
        })

        def enterprise_delete(self, response_choice=1, async=False, callback=None):
            raise BambouHTTPError(MockNuageConnection(status_code='500', reason='Server exception', errors={'description': 'Unable to delete entity'}))

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUEnterprise.delete', enterprise_delete):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Unable to delete entity: [HTTP 500(Server exception)] {'description': 'Unable to delete entity'}")

    def test_exception_wait_for_job(self):
        set_module_args(args={
            'id': 'job-id',
            'type': 'Job',
            'command': 'wait_for_job'
        })

        def job_fetch(self, async=False, callback=None):
            global _LOOP_COUNTER
            self.id = 'job-id'
            self.command = 'EXPORT'
            self.status = 'RUNNING'
            if _LOOP_COUNTER > 1:
                self.status = 'ERROR'
            _LOOP_COUNTER += 1

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.NUJob.fetch', new=job_fetch):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "Job ended in an error")

    def test_fail_auth(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_username': 'csproot',
                'api_enterprise': 'csp',
                'api_url': 'https://localhost:8443',
                'api_version': 'v5_0'
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Missing api_password or api_certificate and api_key parameter in auth')

    def test_fail_version(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_username': 'csproot',
                'api_password': 'csproot',
                'api_enterprise': 'csp',
                'api_url': 'https://localhost:8443',
                'api_version': 'v1_0'
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'vspk is required for this module, or the API version specified does not exist.')

    def test_fail_type(self):
        set_module_args(args={
            'type': 'Unknown',
            'command': 'find'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unrecognised type specified')

    def test_fail_parent_type(self):
        set_module_args(args={
            'type': 'User',
            'parent_id': 'unkown-id',
            'parent_type': 'Unknown',
            'command': 'find'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unrecognised parent type specified')

    def test_fail_parent_child(self):
        set_module_args(args={
            'type': 'Enterprise',
            'parent_id': 'user-id',
            'parent_type': 'User',
            'command': 'find'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Specified parent is not a valid parent for the specified type')

    def test_fail_no_parent(self):
        set_module_args(args={
            'type': 'Group',
            'command': 'find'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'No parent specified and root object is not a parent for the type')

    def test_fail_present_member(self):
        set_module_args(args={
            'type': 'User',
            'match_filter': 'name == "test-user"',
            'parent_id': 'group-id',
            'parent_type': 'Group',
            'state': 'present'
        })

        def users_get_first(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False,
                            callback=None):
            return None

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get_first', users_get_first):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Trying to assign an entity that does not exist', result)

    def test_fail_change_password(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'command': 'change_password',
            'properties': {}
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'command is change_password but the following are missing: password property')

    def test_fail_change_password_non_user(self):
        set_module_args(args={
            'id': 'group-id',
            'type': 'Group',
            'command': 'change_password',
            'properties': {
                'password': 'new-password'
            }
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Entity does not have a password property')

    def test_fail_command_find(self):
        set_module_args(args={
            'type': 'Enterprise',
            'command': 'find',
            'properties': {
                'id': 'unknown-enterprise-id',
                'name': 'unkown-enterprise'
            }
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unable to find matching entries')

    def test_fail_children_type(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            },
            'children': [
                {
                    'properties': {
                        'user_name': 'johndoe-new'
                    }
                }
            ]
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Child type unspecified')

    def test_fail_children_mandatory(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            },
            'children': [
                {
                    'type': 'User'
                }
            ]
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Child ID or properties unspecified')

    def test_fail_children_unknown(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'properties': {
                'name': 'test-enterprise-create'
            },
            'children': [
                {
                    'id': 'unkown-id',
                    'type': 'Unkown'
                }
            ]
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unrecognised child type specified')

    def test_fail_children_parent(self):
        set_module_args(args={
            'id': 'group-id',
            'type': 'Group',
            'state': 'present',
            'children': [
                {
                    'type': 'User',
                    'properties': {
                        'name': 'test-user'
                    }
                }
            ]
        })

        def users_get_first(self, filter=None, order_by=None, group_by=[], page=None, page_size=None, query_parameters=None, commit=True, async=False,
                            callback=None):
            return None

        with self.assertRaises(AnsibleFailJson) as exc:
            with patch('vspk.v5_0.fetchers.NUUsersFetcher.get_first', users_get_first):
                nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Trying to assign a child that does not exist')

    def test_fail_children_fetcher(self):
        set_module_args(args={
            'id': 'group-id',
            'type': 'Group',
            'state': 'present',
            'children': [
                {
                    'type': 'Enterprise',
                    'properties': {
                        'name': 'test-enterprise'
                    }
                }
            ]
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Unable to find a fetcher for child, and no ID specified.')

    def test_fail_has_changed(self):
        set_module_args(args={
            'id': 'user-id',
            'type': 'User',
            'state': 'present',
            'properties': {
                'user_name': 'changed-user',
                'fake': 'invalid-property',
                'password': 'hidden-property'
            }
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'Property fake is not valid for this type of entity')

    def test_input_auth_username(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_password': 'csproot',
                'api_enterprise': 'csp',
                'api_url': 'https://localhost:8443',
                'api_version': 'v5_0'
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'missing required arguments: api_username')

    def test_input_auth_enterprise(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_username': 'csproot',
                'api_password': 'csproot',
                'api_url': 'https://localhost:8443',
                'api_version': 'v5_0'
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'missing required arguments: api_enterprise')

    def test_input_auth_url(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_username': 'csproot',
                'api_password': 'csproot',
                'api_enterprise': 'csp',
                'api_version': 'v5_0'
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'missing required arguments: api_url')

    def test_input_auth_version(self):
        set_module_args_custom_auth(
            args={
                'type': 'Enterprise',
                'command': 'find'
            },
            auth={
                'api_username': 'csproot',
                'api_password': 'csproot',
                'api_enterprise': 'csp',
                'api_url': 'https://localhost:8443',
            }
        )

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], 'missing required arguments: api_version')

    def test_input_exclusive(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
            'command': 'find'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "parameters are mutually exclusive: ['command', 'state']")

    def test_input_require_both_parent_id(self):
        set_module_args(args={
            'type': 'User',
            'command': 'find',
            'parent_type': 'Enterprise'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "parameters are required together: ['parent_id', 'parent_type']")

    def test_input_require_both_parent_type(self):
        set_module_args(args={
            'type': 'User',
            'command': 'find',
            'parent_id': 'enterprise-id'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "parameters are required together: ['parent_id', 'parent_type']")

    def test_input_require_on_off(self):
        set_module_args(args={
            'type': 'Enterprise'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "one of the following is required: command,state")

    def test_input_require_if_present(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'present',
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "state is present but the following are missing: id,properties,match_filter")

    def test_input_require_if_absent(self):
        set_module_args(args={
            'type': 'Enterprise',
            'state': 'absent',
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "state is absent but the following are missing: id,properties,match_filter")

    def test_input_require_if_change_password_id(self):
        set_module_args(args={
            'type': 'User',
            'command': 'change_password',
            'properties': {
                'password': 'dummy-password'
            }
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "command is change_password but the following are missing: id")

    def test_input_require_if_change_password_properties(self):
        set_module_args(args={
            'type': 'User',
            'command': 'change_password',
            'id': 'user-id'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "command is change_password but the following are missing: properties")

    def test_input_require_if_wait_for_job_id(self):
        set_module_args(args={
            'type': 'Job',
            'command': 'wait_for_job'
        })

        with self.assertRaises(AnsibleFailJson) as exc:
            nuage_vspk.main()

        result = exc.exception.args[0]

        self.assertTrue(result['failed'])
        self.assertEqual(result['msg'], "command is wait_for_job but the following are missing: id")
