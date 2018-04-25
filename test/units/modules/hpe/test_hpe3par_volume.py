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
from ansible.modules.storage.hpe import hpe3par_volume
from ansible.module_utils.basic import AnsibleModule

class TestHpe3parSnapshot(unittest.TestCase):

    fields = {
        "state": {
            "required": True,
            "choices": ['present',
                        'absent',
                        'modify',
                        'grow',
                        'grow_to_size',
                        'change_snap_cpg',
                        'change_user_cpg',
                        'convert_type',
                        'set_snap_cpg'
                       ],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_name": {
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
        "volume_name": {
            "required": True,
            "type": "str"
        },
        "cpg": {
            "type": "str",
            "default": None
        },
        "size": {
            "type": "float",
            "default": None
        },
        "size_unit": {
            "choices": ['MiB', 'GiB', 'TiB'],
            "type": 'str',
            "default": 'MiB'
        },
        "snap_cpg": {
            "type": "str"
        },
        "wait_for_task_to_end": {
            "type": "bool",
            "default": False
        },
        "new_name": {
            "type": "str",
        },
        "expiration_hours": {
            "type": "int",
            "default": 0
        },
        "retention_hours": {
            "type": "int",
            "default": 0
        },
        "ss_spc_alloc_warning_pct": {
            "type": "int",
            "default": 0
        },
        "ss_spc_alloc_limit_pct": {
            "type": "int",
            "default": 0
        },
        "usr_spc_alloc_warning_pct": {
            "required": False,
            "type": "int",
            "default": 0
        },
        "usr_spc_alloc_limit_pct": {
            "type": "int",
            "default": 0
        },
        "rm_ss_spc_alloc_warning": {
            "type": "bool",
            "default": False
        },
        "rm_usr_spc_alloc_warning": {
            "type": "bool",
            "default": False
        },
        "rm_exp_time": {
            "type": "bool",
            "default": False
        },
        "rm_usr_spc_alloc_limit": {
            "type": "bool",
            "default": False
        },
        "rm_ss_spc_alloc_limit": {
            "type": "bool",
            "default": False
        },
        "compression": {
            "type": "bool",
            "default": False
        },
        "type": {
            "choices": ['thin', 'thin_dedupe', 'full'],
            "type": "str",
        },
        "keep_vv": {
            "type": "str",
        }
    }
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par online clone - test module arguments
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':'test_cpg',
            'size': 1.0,
            'size_unit': 'GiB',
            'snap_cpg': 'test_snap_cpg',
            'wait_for_task_to_end': False,
            'new_name': 'new_volume',
            'expiration_hours': 0,
            'retention_hours': 0,
            'ss_spc_alloc_warning_pct': 0,
            'ss_spc_alloc_limit_pct': 0,
            'usr_spc_alloc_warning_pct': '0',
            'usr_spc_alloc_limit_pct': 0,
            'rm_ss_spc_alloc_warning': False,
            'rm_usr_spc_alloc_warning': False,
            'rm_exp_time': False,
            'rm_usr_spc_alloc_limit': False,
            'rm_ss_spc_alloc_limit': False,
            'compression': True,
            'type': 'thin',
            'keep_vv': 'keep_vv',
            'state': 'present'
        }

        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        hpe3par_volume.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.delete_volume')
    def test_main_exit_absent(self, mock_delete_volume, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':None,
            'size': None,
            'size_unit': None,
            'snap_cpg': None,
            'wait_for_task_to_end': None,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': False,
            'type': 'thin',
            'keep_vv': None,
            'state': 'absent'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_delete_volume.return_value = (True, True, "Deleted volume successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted volume successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.modify_volume')
    def test_main_exit_modify(self, mock_modify_volume, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':None,
            'size': None,
            'size_unit': None,
            'snap_cpg': None,
            'wait_for_task_to_end': None,
            'new_name': 'new_volume',
            'expiration_hours': 10,
            'retention_hours': 100,
            'ss_spc_alloc_warning_pct': 0,
            'ss_spc_alloc_limit_pct': 0,
            'usr_spc_alloc_warning_pct': 0,
            'usr_spc_alloc_limit_pct': 0,
            'rm_ss_spc_alloc_warning': False,
            'rm_usr_spc_alloc_warning': False,
            'rm_exp_time': False,
            'rm_usr_spc_alloc_limit': False,
            'rm_ss_spc_alloc_limit': False,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'modify'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_modify_volume.return_value = (True, True, "Modified volume successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Modified volume successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.grow')
    def test_main_exit_grow(self, mock_grow, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg': None ,
            'size': 1.0,
            'size_unit': 'GiB',
            'snap_cpg': None,
            'wait_for_task_to_end': None,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'grow'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_grow.return_value = (True, True, "Volume grown successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Volume grown successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.grow_to_size')
    def test_main_exit_grow_to_size(self, mock_grow_to_size, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg': None ,
            'size': 1.0,
            'size_unit': 'GiB',
            'snap_cpg': None,
            'wait_for_task_to_end': None,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'grow_to_size'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_grow_to_size.return_value = (True, True, "Volume grown to size successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Volume grown to size successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.change_snap_cpg')
    def test_main_exit_change_snap_cpg(self, mock_change_snap_cpg, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':None,
            'size': None,
            'size_unit': None,
            'snap_cpg': 'test_snap_cpg',
            'wait_for_task_to_end': True,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'change_snap_cpg'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_change_snap_cpg.return_value = (True, True, "Changed snap CPG successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Changed snap CPG successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.change_user_cpg')
    def test_main_exit_change_user_cpg(self, mock_change_user_cpg, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':'test_cpg',
            'size': None,
            'size_unit': None,
            'snap_cpg': None,
            'wait_for_task_to_end': True,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'change_user_cpg'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_change_user_cpg.return_value = (True, True, "Changed user CPG successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Changed user CPG successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.convert_type')
    def test_main_exit_convert_type(self, mock_convert_type, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':'test_cpg',
            'size': None,
            'size_unit': None,
            'snap_cpg': None,
            'wait_for_task_to_end': True,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': True,
            'type': 'full',
            'keep_vv': 'keep_vv',
            'state': 'convert_type'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_convert_type.return_value = (True, True, "Converted type successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Converted type successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.modify_volume')
    def test_main_exit_set_snap_cpg(self, mock_modify_volume, mock_module, mock_client):
        """
        hpe3par volume - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR',
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'volume_name':'test_volume',
            'cpg':None,
            'size': None,
            'size_unit': None,
            'snap_cpg': 'snap_cpg',
            'wait_for_task_to_end': None,
            'new_name': None,
            'expiration_hours': None,
            'retention_hours': None,
            'ss_spc_alloc_warning_pct': None,
            'ss_spc_alloc_limit_pct': None,
            'usr_spc_alloc_warning_pct': None,
            'usr_spc_alloc_limit_pct': None,
            'rm_ss_spc_alloc_warning': None,
            'rm_usr_spc_alloc_warning': None,
            'rm_exp_time': None,
            'rm_usr_spc_alloc_limit': None,
            'rm_ss_spc_alloc_limit': None,
            'compression': None,
            'type': None,
            'keep_vv': None,
            'state': 'set_snap_cpg'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_modify_volume.return_value = (True, True, "Set snap CPG successfully.", {})
        hpe3par_volume.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Set snap CPG successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_create_snapshot(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = False
        mock_HPE3ParClient.createVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None       
        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            2,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (True, True, "Created volume %s successfully." % 'test_volume', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = True
        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            2,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (True, False, "Volume already present", {}))

        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            'test_cpg',
                            2,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (False, False, "Volume creation failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_cpg',
                            2,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (False, False, "Volume creation failed. Volume name is null", {}))

        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            2,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (False, False, "Volume creation failed. Cpg is null", {}))
                        
        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            None,
                            'GiB',
                            'thin',
                            True,
                            'snap_cpg'
                        ), (False, False, "Volume creation failed. Volume size is null", {}))
                        
        self.assertEqual(hpe3par_volume.create_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            2,
                            None,
                            'thin',
                            True,
                            'snap_cpg'
                        ), (False, False, "Volume creation failed. Volume size_unit is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_delete_snapshot(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.createVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None 
        self.assertEqual(hpe3par_volume.delete_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume'
                        ), (True, True, "Deleted volume %s successfully." % 'test_volume', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = False
        self.assertEqual(hpe3par_volume.delete_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume'
                        ), (True, False, "Volume does not exist", {}))
                        
        self.assertEqual(hpe3par_volume.delete_volume(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume'
                        ), (False, False, "Volume delete failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_volume.delete_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None
                        ), (False, False, "Volume delete failed. Volume name is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_grow(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.growVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_volume.grow(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            'GiB'
                        ), (True, True, "Grown volume %s by %s %s successfully." % ('test_volume', 2, 'GiB'), {}))
                        
        self.assertEqual(hpe3par_volume.grow(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            2,
                            'GiB'
                        ), (False, False, "Grow volume failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_volume.grow(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            2,
                            'GiB'
                        ), (False, False, "Grow volume failed. Volume name is null", {}))
                        
        self.assertEqual(hpe3par_volume.grow(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            'GiB'
                        ), (False, False, "Grow volume failed. Volume size is null", {}))

        self.assertEqual(hpe3par_volume.grow(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            None
                        ), (False, False, "Grow volume failed. Volume size_unit is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_grow_to_size(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.growVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        mock_HPE3ParClient.getVolume.return_value.size_mib = 1024
        print mock_HPE3ParClient.getVolume.return_value.size_mib
        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            'GiB'
                        ), (True, True, "Grown volume %s to %s %s successfully." % ('test_volume', 2, 'GiB'), {}))
                    
        mock_HPE3ParClient.getVolume.return_value.size_mib = 2048
        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            'GiB'
                        ), (True, False, "Volume size already >= %s %s" % (2, 'GiB'), {}))

        mock_HPE3ParClient.volumeExists.return_value = False
        mock_HPE3ParClient.getVolume.return_value.size_mib = 1024
        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            'GiB'
                        ), (False, False, "Volume does not exist", {}))
                        
        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            2,
                            'GiB'
                        ), (False, False, "Grow_to_size volume failed. Storage system username or password is null", {}))


        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            2,
                            'GiB'
                        ), (False, False, "Grow_to_size volume failed. Volume name is null", {}))
                        
        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            'GiB'
                        ), (False, False, "Grow_to_size volume failed. Volume size is null", {}))

        self.assertEqual(hpe3par_volume.grow_to_size(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            2,
                            None
                        ), (False, False, "Grow_to_size volume failed. Volume size_unit is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_convert_type(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.tuneVolume.return_value.task_id = 1
        mock_HPE3ParClient.waitForTaskToEnd.return_value = True
        mock_HPE3ParClient.logout.return_value = None
        mock_HPE3ParClient.getVolume.return_value.provisioning_type = 2
        mock_HPE3ParClient.Task.return_value.task_id = 1
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (True, True, "Provisioning type changed to %s successfully." % 'full', {}))
                        
        mock_HPE3ParClient.getVolume.return_value.provisioning_type = 1
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (True, False, "Provisioning type already set to %s" % 'full', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = False
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (False, False, "Volume does not exist", {}))

        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            'test_cpg',
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (False, False, "Convert volume type failed. Storage system username or password is null", {}))
                        
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_cpg',
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (False, False, "Convert volume type failed. Volume name is null", {}))
                        
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            'full',
                            True,
                            'keep_vv',
                            True
                        ), (False, False, "Convert volume type failed. Snap CPG is null", {}))
                        
        self.assertEqual(hpe3par_volume.convert_type(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            None,
                            True,
                            'keep_vv',
                            True
                        ), (False, False, "Convert volume type failed. Volume type is null", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_change_snap_cpg(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.tuneVolume.return_value.task_id = 1
        mock_HPE3ParClient.waitForTaskToEnd.return_value = True
        mock_HPE3ParClient.logout.return_value = None
        mock_HPE3ParClient.getVolume.return_value.snap_cpg = 'original_cpg'
        mock_HPE3ParClient.Task.return_value.task_id = 1
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (True, True, "Changed snap CPG to %s successfully." % 'test_cpg', {}))
                        
        mock_HPE3ParClient.getVolume.return_value.snap_cpg = 'test_cpg'
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (True, False, "Snap CPG already set to %s" % 'test_cpg', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = False
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (False, False, "Volume does not exist", {}))\
                        
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            'test_cpg',
                            True
                        ), (False, False, "Change snap CPG failed. Storage system username or password is null", {}))
                        
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_cpg',
                            True
                        ), (False, False, "Change snap CPG failed. Volume name is null", {}))
                        
        self.assertEqual(hpe3par_volume.change_snap_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            True
                        ), (False, False, "Change snap CPG failed. Snap CPG is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_change_user_cpg(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.volumeExists.return_value = True
        mock_HPE3ParClient.tuneVolume.return_value.task_id = 1
        mock_HPE3ParClient.waitForTaskToEnd.return_value = True
        mock_HPE3ParClient.logout.return_value = None
        mock_HPE3ParClient.getVolume.return_value.user_cpg = 'original_cpg'
        mock_HPE3ParClient.Task.return_value.task_id = 1
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (True, True, "Changed user CPG to %s successfully." % 'test_cpg', {}))
                        
        mock_HPE3ParClient.getVolume.return_value.user_cpg = 'test_cpg'
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (True, False, "user CPG already set to %s" % 'test_cpg', {}))
                        
        mock_HPE3ParClient.volumeExists.return_value = False
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'test_cpg',
                            True
                        ), (False, False, "Volume does not exist", {}))\
                        
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            'test_cpg',
                            True
                        ), (False, False, "Change user CPG failed. Storage system username or password is null", {}))
                        
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_cpg',
                            True
                        ), (False, False, "Change user CPG failed. Volume name is null", {}))
                        
        self.assertEqual(hpe3par_volume.change_user_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            None,
                            True
                        ), (False, False, "Change user CPG failed. Snap CPG is null", {}))
                        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volume.client.HPE3ParClient')
    def test_modify_volume(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = None
        mock_HPE3ParClient.modifyVolume.return_value = None
        mock_HPE3ParClient.logout.return_value = None
        self.assertEqual(hpe3par_volume.modify_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_volume',
                            'new_volume_name',
                            10,
                            100,
                            0,
                            0,
                            0,
                            0,
                            False,
                            False,
                            False,
                            False,
                            False,
                            'test_cpg',
                            'snap_cpg'
                        ), (True, True, "Modified Volume %s successfully." % 'test_volume', {}))
                        
        self.assertEqual(hpe3par_volume.modify_volume(mock_HPE3ParClient,
                            'USER',
                            None,
                            'test_volume',
                            'new_volume_name',
                            10,
                            100,
                            0,
                            0,
                            0,
                            0,
                            False,
                            False,
                            False,
                            False,
                            False,
                            'test_cpg',
                            'snap_cpg'
                        ), (False, False, "Modify volume type failed. Storage system username or password is null", {}))

        self.assertEqual(hpe3par_volume.modify_volume(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'new_volume_name',
                            10,
                            100,
                            0,
                            0,
                            0,
                            0,
                            False,
                            False,
                            False,
                            False,
                            False,
                            'test_cpg',
                            'snap_cpg'
                        ), (False, False, "Modify volume type failed. Volume name is null", {}))
                        
    def test_convert_to_binary_multiple(self):
        self.assertEqual(hpe3par_volume.convert_to_binary_multiple(1, 'MiB'), 1)
        self.assertEqual(hpe3par_volume.convert_to_binary_multiple(1, 'GiB'), 1024)
        self.assertEqual(hpe3par_volume.convert_to_binary_multiple(1, 'TiB'), 1024 * 1024)
    
    def get_volume_type(self):
        self.assertEqual(hpe3par_volume.get_volume_type('thin'), ['TPVV', 1])
        self.assertEqual(hpe3par_volume.get_volume_type('thin_dedupe'), ['TDVV', 3])
        self.assertEqual(hpe3par_volume.get_volume_type('full'), ['FPVV', 2])
                        
if __name__ == '__main__':
    unittest.main(exit=False)


