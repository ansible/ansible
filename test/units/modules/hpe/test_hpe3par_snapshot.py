# (C) Copyright 2018 Hewlett Packard Enterprise Development LP
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.  Alternatively, at your
# choice, you may also redistribute it and/or modify it under the terms
# of the Apache License, version 2.0, available at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>

import mock
import unittest
from ansible.modules.storage.hpe import hpe3par_snapshot
from ansible.module_utils.basic import AnsibleModule

class TestHpe3parSnapshot(unittest.TestCase):

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'modify', 'restore_offline', 'restore_online'],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_username": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "storage_system_password": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "snapshot_name": {
            "required": True,
            "type": "str"
        },
        "base_volume_name": {
            "type": "str"
        },
        "read_only": {
            "type": "bool"
        },
        "expiration_time": {
            "type": "int",
        },
        "retention_time": {
            "type": "int"
        },
        "expiration_unit": {
            "type": "str",
            "choices": ['Hours', 'Days'],
            "default": 'Hours'
        },
        "retention_unit": {
            "type": "str",
            "choices": ['Hours', 'Days'],
            "default": 'Hours'
        },
        "expiration_hours": {
            "type": "int",
            "default": 0
        },
        "retention_hours": {
            "type": "int",
            "default": 0
        },
        "priority": {
            "type": "str",
            "choices": ['HIGH', 'MEDIUM', 'LOW'],
        },
        "allow_remote_copy_parent": {
            "type": "bool"
        },
        "new_name": {
            "type": "str"
        },
        "rm_exp_time": {
            "type": "bool"
        }
    }

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par online clone - test module arguments
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':'base_volume',
            'read_only': False,
            'expiration_time': 0,
            'retention_time': 0,
            'expiration_unit': 'Hours',
            'retention_unit': 'Hours',
            'expiration_hours': 0,
            'retention_hours': 0,
            'priority': 'MEDIUM',
            'allow_remote_copy_parent': False,
            'new_name': 'snapshot_new',
            'rm_exp_time': False,
            'state': 'present'
        }

        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        hpe3par_snapshot.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.create_snapshot')
    def test_main_exit_present(self, mock_create_snapshot, mock_module, mock_client):
        """
        hpe3par snapshot - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':'base_volume',
            'read_only': False,
            'expiration_time': 0,
            'retention_time': 0,
            'expiration_unit': 'Hours',
            'retention_unit': 'Hours',
            'expiration_hours': None,
            'retention_hours': None,
            'priority': None,
            'allow_remote_copy_parent': None,
            'new_name': None,
            'rm_exp_time': None,
            'state': 'present'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_create_snapshot.return_value = (True, True, "Created Snapshot successfully.", {})
        hpe3par_snapshot.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created Snapshot successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.delete_snapshot')
    def test_main_exit_absent(self, mock_delete_snapshot, mock_module, mock_client):
        """
        hpe3par snapshot - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':None,
            'read_only': None,
            'expiration_time': None,
            'retention_time': None,
            'expiration_unit': None,
            'retention_unit': None,
            'expiration_hours': None,
            'retention_hours': None,
            'priority': None,
            'allow_remote_copy_parent': None,
            'new_name': None,
            'rm_exp_time': None,
            'state': 'absent'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_delete_snapshot.return_value = (True, True, "Deleted Snapshot test_snapshot successfully.", {})
        hpe3par_snapshot.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted Snapshot test_snapshot successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.modify_snapshot')
    def test_main_exit_modify(self, mock_modify_snapshot, mock_module, mock_client):
        """
        hpe3par snapshot - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':None,
            'read_only': None,
            'expiration_time': None,
            'retention_time': None,
            'expiration_unit': None,
            'retention_unit': None,
            'expiration_hours': 10,
            'retention_hours': 10,
            'priority': None,
            'allow_remote_copy_parent': None,
            'new_name': 'new_snapshot',
            'rm_exp_time': True,
            'state': 'modify'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_modify_snapshot.return_value = (True, True, "Modified Snapshot test_snapshot successfully.", {})
        hpe3par_snapshot.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Modified Snapshot test_snapshot successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.restore_snapshot_offline')
    def test_main_exit_offline_snapshot(self, mock_restore_snapshot_offline, mock_module, mock_client):
        """
        hpe3par snapshot - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':None,
            'read_only': None,
            'expiration_time': None,
            'retention_time': None,
            'expiration_unit': None,
            'retention_unit': None,
            'expiration_hours': None,
            'retention_hours': None,
            'priority': 'MEDIUM',
            'allow_remote_copy_parent': False,
            'new_name': None,
            'rm_exp_time': None,
            'state': 'restore_offline'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_restore_snapshot_offline.return_value = (True, True, "Restored offline snapshot test_snapshot successfully.", {})
        hpe3par_snapshot.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Restored offline snapshot test_snapshot successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.restore_snapshot_online')
    def test_main_exit_online_snapshot(self, mock_restore_snapshot_online, mock_module, mock_client):
        """
        hpe3par snapshot - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'snapshot_name':'test_snapshot',
            'base_volume_name':None,
            'read_only': None,
            'expiration_time': None,
            'retention_time': None,
            'expiration_unit': None,
            'retention_unit': None,
            'expiration_hours': None,
            'retention_hours': None,
            'priority': None,
            'allow_remote_copy_parent': False,
            'new_name': None,
            'rm_exp_time': None,
            'state': 'restore_online'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_restore_snapshot_online.return_value = (True, True, "Restored online snapshot test_snapshot successfully.", {})
        hpe3par_snapshot.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Restored online snapshot test_snapshot successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client.HPE3ParClient')
    def test_create_snapshot(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = False
        mock_HPE3ParClient.createSnapshot.return_value = None
        mock_HPE3ParClient.logout.return_value = None       
        self.assertEqual(hpe3par_snapshot.create_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            'base_volume',
                            False,
                            10,
                            10,
                            'Hours',
                            'Days'
                        ), (True, True, "Created Snapshot %s successfully." % 'test_snapshot', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = True
        self.assertEqual(hpe3par_snapshot.create_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            'base_volume',
                            False,
                            10,
                            10,
                            'Hours',
                            'Days'
                        ), (True, False, "Volume/Snapshot already present", {}))

        self.assertEqual(hpe3par_snapshot.create_snapshot(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_snapshot',
                            'base_volume',
                            False,
                            10,
                            10,
                            'Hours',
                            'Days'
                        ), (False, False, "Snapshot create failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_snapshot.create_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'base_volume',
                            False,
                            10,
                            10,
                            'Hours',
                            'Days'
                        ), (False, False, "Snapshot create failed. Snapshot name is null", {}))

        self.assertEqual(hpe3par_snapshot.create_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            None,
                            False,
                            10,
                            10,
                            'Hours',
                            'Days'
                        ), (False, False, "Snapshot create failed. Base volume name is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client.HPE3ParClient')
    def test_modify_snapshot(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.modifyVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_snapshot.modify_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            'new_snapshot',
                            10,
                            10,
                            True
                        ), (True, True, "Modified Snapshot %s successfully." % 'test_snapshot', {}))
                        
        self.assertEqual(hpe3par_snapshot.modify_snapshot(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_snapshot',
                            'new_snapshot',
                            10,
                            10,
                            True
                        ), (False, False, "Modify snapshot failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_snapshot.modify_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'new_snapshot',
                            10,
                            10,
                            True
                        ), (False, False, "Modify snapshot failed. Snapshot name is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client.HPE3ParClient')
    def test_delete_snapshot(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.deleteVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_snapshot.delete_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot'
                        ), (True, True, "Deleted Snapshot %s successfully." % 'test_snapshot', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = False
        self.assertEqual(hpe3par_snapshot.delete_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot'
                        ), (True, False, "Volume/Snapshot does not exist", {}))

        self.assertEqual(hpe3par_snapshot.delete_snapshot(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_snapshot'
                        ), (False, False, "Snapshot delete failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_snapshot.delete_snapshot(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None
                        ), (False, False, "Snapshot delete failed. Snapshot name is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client.HPE3ParClient')
    def test_restore_snapshot_offline(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.promoteVirtualCopy.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_snapshot.restore_snapshot_offline(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            'MEDIUM',
                            False
                        ), (True, True, "Restored offline snapshot %s successfully." % 'test_snapshot', {}))

        self.assertEqual(hpe3par_snapshot.restore_snapshot_offline(mock_HPE3ParClient,
                            None,
                            'PASS',
                            'test_snapshot',
                            'MEDIUM',
                            False
                        ), (False, False, "Offline snapshot restore failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_snapshot.restore_snapshot_offline(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'MEDIUM',
                            False
                        ), (False, False, "Offline snapshot restore failed. Snapshot name is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_snapshot.client.HPE3ParClient')
    def test_restore_snapshot_online(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.promoteVirtualCopy.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_snapshot.restore_snapshot_online(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_snapshot',
                            False
                        ), (True, True, "Restored online Snapshot %s successfully." % 'test_snapshot', {}))

        self.assertEqual(hpe3par_snapshot.restore_snapshot_online(mock_HPE3ParClient,
                            None,
                            'PASS',
                            'test_snapshot',
                            False
                        ), (False, False, "Online snapshot restore failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_snapshot.restore_snapshot_online(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            False
                        ), (False, False, "Online snapshot restore failed. Snapshot name is null", {}))
                        
if __name__ == '__main__':
    unittest.main(exit=False)
