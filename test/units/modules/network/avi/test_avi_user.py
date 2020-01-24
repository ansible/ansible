import os
import json
from units.compat import unittest
from units.compat.mock import Mock
from units.modules.utils import set_module_args
from ansible.modules.network.avi import avi_user

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
with open(fixture_path + '/avi_user.json') as json_file:
    data = json.load(json_file)


class TestAviUser(unittest.TestCase):

    def test_create_user(self):
        set_module_args({
            "avi_credentials": {
                "controller": "192.0.2.13",
                "username": "username",
                "password": "fakepassword",
                "api_version": "18.2.5"
            },
            "state": "present",
            "name": "testuser",
            "obj_username": "testuser",
            "obj_password": "test123",
            "email": "test@abc.com",
            "access": [
                {
                    "role_ref": "/api/role?name=Tenant-Admin",
                    "tenant_ref": "/api/tenant?name=Test-Admin",
                    "all_tenants": False
                }
            ],
            "user_profile_ref": "/api/useraccountprofile?name=Default-User-Account-Profile",
            "is_active": True,
            "is_superuser": True,
            "default_tenant_ref": "/api/tenant?name=admin"
        })
        avi_user.avi_ansible_api = Mock(return_value=data['mock_create_res'])
        response = avi_user.main()
        assert response['changed']

    def test_put_on_user(self):
        set_module_args({
            "avi_credentials": {
                "controller": "192.0.2.13",
                "username": "username",
                "password": "fakepassword",
                "api_version": "18.2.5"
            },
            "state": "present",
            "avi_api_update_method": "put",
            "name": "testuser",
            "obj_username": "testuser",
            "obj_password": "test123",
            "email": "newemail@abc.com",
            "access": [{
                "role_ref": "/api/role?name=Tenant-Admin",
                "tenant_ref": "/api/tenant?name=Test-Admin",
                "all_tenants": False
            }],
            "user_profile_ref": "/api/useraccountprofile?name=Default-User-Account-Profile",
            "is_active": True,
            "is_superuser": True,
            "default_tenant_ref": "/api/tenant?name=admin"
        })
        avi_user.avi_ansible_api = Mock(return_value=data['mock_put_res'])
        response = avi_user.main()
        assert response['changed']
        assert response['obj']
        assert response['old_obj']

    def test_delete_user(self):
        set_module_args({
            "avi_credentials": {
                "controller": "192.0.2.13",
                "username": "username",
                "password": "fakepassword",
                "api_version": "18.2.5"

            },
            "name": "testuser",
            "obj_username": "testuser",
            "obj_password": "test123",
            "email": "test@abc.com",
            "access": [{
                "role_ref": "/api/role?name=Tenant-Admin",
                "tenant_ref": "/api/tenant?name=Test-Admin",
                "all_tenants": False
            }],
            "user_profile_ref": "/api/useraccountprofile?name=Default-User-Account-Profile",
            "is_active": True,
            "is_superuser": True,
            "default_tenant_ref": "/api/tenant?name=admin"
        })
        avi_user.avi_ansible_api = Mock(return_value=data['mock_del_res'])
        response = avi_user.main()
        assert response['changed']
        assert not response['obj']
        assert response['old_obj']
