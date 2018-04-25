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
from ansible.modules.storage.hpe import hpe3par_online_clone
from ansible.module_utils.basic import AnsibleModule

class TestHpe3parOnlineClone(unittest.TestCase):

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'resync'],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_name": {
            "required": False,
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
        "clone_name": {
            "required": True,
            "type": "str"
        },
        "base_volume_name": {
            "required": False,
            "type": "str"
        },
        "dest_cpg": {
            "required": False,
            "type": "str",
        },
        "tpvv": {
            "required": False,
            "type": "bool",
        },
        "tdvv": {
            "required": False,
            "type": "bool",
        },
        "snap_cpg": {
            "required": False,
            "type": "str",
        },
        "compression": {
            "required": False,
            "type": "bool",
        }
    }

    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par online clone - test module arguments
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'clone_name':'test_clone',
            'base_volume_name':'base_volume',
            'dest_cpg': 'dest_cpg',
            'tpvv': False,
            'tdvv': False,
            'snap_cpg': 'snap_cpg',
            'compression': False,
            'state': 'present'
        }

        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        hpe3par_online_clone.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.create_online_clone')
    def test_main_exit_present(self, mock_create_online_clone, mock_module, mock_client):
        """
        hpe3par online clone - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'clone_name':'test_clone',
            'base_volume_name':'base_volume',
            'dest_cpg': 'dest_cpg',
            'tpvv': False,
            'tdvv': False,
            'snap_cpg': 'snap_cpg',
            'compression': False,
            'state': 'present'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_create_online_clone.return_value = (True, True, "Created Online clone successfully.", {})
        hpe3par_online_clone.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created Online clone successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.delete_clone')
    def test_main_exit_absent(self, mock_delete_clone, mock_module, mock_client):
        """
        hpe3par online clone - success check
        """
        PARAMS_FOR_ABSENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'clone_name':'test_clone',
            'base_volume_name':'base_volume',
            'dest_cpg': None,
            'tpvv': False,
            'tdvv': False,
            'snap_cpg': 'snap_cpg',
            'compression': False,
            'state': 'absent'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_ABSENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_delete_clone.return_value = (True, True, "Deleted Online clone successfully.", {})
        hpe3par_online_clone.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted Online clone successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.resync_clone')
    def test_main_exit_resync(self, mock_resync_clone, mock_module, mock_client):
        """
        hpe3par online clone - success check
        """
        PARAMS_FOR_RESYNC = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'clone_name':'test_clone',
            'base_volume_name':None,
            'dest_cpg': None,
            'tpvv': False,
            'tdvv': False,
            'snap_cpg': 'snap_cpg',
            'compression': False,
            'state': 'resync'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_RESYNC
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_resync_clone.return_value = (True, True, "Resynced Online clone successfully.", {})
        hpe3par_online_clone.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Resynced Online clone successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client.HPE3ParClient')
    def test_create_online_clone(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = False
        mock_HPE3ParClient.copyVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_online_clone.create_online_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'base_volume',
                            'test_clone',
                            'dest_cpg',
                            False,
                            False,
                            'snap_cpg',
                            False
                        ), (True, True, "Created Online Clone %s successfully." % 'test_clone', {}))

        mock_HPE3ParClient.volumeExists.return_value = True
        self.assertEqual(hpe3par_online_clone.create_online_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'base_volume',
                            'test_clone',
                            'dest_cpg',
                            False,
                            False,
                            'snap_cpg',
                            False
                        ), (True, False, "Clone already exists / creation in progress. Nothing to do.", {}))
        self.assertEqual(hpe3par_online_clone.create_online_clone(mock_HPE3ParClient,
                            'USER',
                            None,
                            'base_volume',
                            'test_clone',
                            'dest_cpg',
                            False,
                            False,
                            'snap_cpg',
                            False
                        ), (False, False, "Online clone create failed. Storage system username or password is null", {}))
        self.assertEqual(hpe3par_online_clone.create_online_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'base_volume',
                            None,
                            'dest_cpg',
                            False,
                            False,
                            'snap_cpg',
                            False
                        ), (False, False, "Online clone create failed. Clone name is null", {}))
        self.assertEqual(hpe3par_online_clone.create_online_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_clone',
                            'dest_cpg',
                            False,
                            False,
                            'snap_cpg',
                            False
                        ), (False, False, "Online clone create failed. Base volume name is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client.HPE3ParClient')
    def test_delete_clone(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = True
        mock_HPE3ParClient.setSSHOptions.return_value = True
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.offlinePhysicalCopyExists.return_value = False
        mock_HPE3ParClient.onlinePhysicalCopyExists.return_value = False
        mock_HPE3ParClient.deleteVolume.return_value = None
        self.assertEqual(hpe3par_online_clone.delete_clone(mock_HPE3ParClient,
                            '192.168.0.1',
                            'USER',
                            'PASS',
                            'test_clone',
                            'base_volume'
                        ), (True, True, "Deleted Online Clone %s successfully." % 'test_clone', {}))

        mock_HPE3ParClient.offlinePhysicalCopyExists.return_value = True
        self.assertEqual(hpe3par_online_clone.delete_clone(mock_HPE3ParClient,
                            '192.168.0.1',
                            'USER',
                            'PASS',
                            'test_clone',
                            'base_volume'
                        ), (False, False, "Clone/Volume is busy. Cannot be deleted", {}))

        self.assertEqual(hpe3par_online_clone.delete_clone(mock_HPE3ParClient,
                            '192.168.0.1',
                            None,
                            'PASS',
                            'test_clone',
                            'base_volume'
                        ), (False, False, "Online clone delete failed. Storage system username or password is null", {}))
        self.assertEqual(hpe3par_online_clone.delete_clone(mock_HPE3ParClient,
                            '192.168.0.1',
                            'USER',
                            'PASS',
                            None,
                            'base_volume'
                        ), (False, False, "Online clone delete failed. Clone name is null", {}))
        self.assertEqual(hpe3par_online_clone.delete_clone(mock_HPE3ParClient,
                            '192.168.0.1',
                            'USER',
                            'PASS',
                            'test_clone',
                            None
                        ), (False, False, "Online clone delete failed. Base volume name is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_online_clone.client.HPE3ParClient')
    def test_resync_clone(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = True
        self.assertEqual(hpe3par_online_clone.resync_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_clone'
                        ), (True, True, "Resync-ed Online Clone %s successfully." % 'test_clone', {}))
        self.assertEqual(hpe3par_online_clone.resync_clone(mock_HPE3ParClient,
                            None,
                            'PASS',
                            'test_clone'
                        ), (False, False, "Online clone resync failed. Storage system username or password is null", {}))
        self.assertEqual(hpe3par_online_clone.resync_clone(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None
                        ), (False, False, "Online clone resync failed. Clone name is null", {}))

if __name__ == '__main__':
    unittest.main(exit=False)
