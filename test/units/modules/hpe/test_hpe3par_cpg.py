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
from ansible.modules.storage.hpe import hpe3par_cpg
from ansible.module_utils.basic import AnsibleModule

class TestHpe3parCPG(unittest.TestCase):

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent'],
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
        "cpg_name": {
            "required": True,
            "type": "str"
        },
        "domain": {
            "type": "str"
        },
        "growth_increment": {
            "type": "float",
            "default": -1.0
        },
        "growth_increment_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "growth_limit": {
            "type": "float",
            "default": -1.0
        },
        "growth_limit_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "growth_warning": {
            "type": "float",
            "default": -1.0
        },
        "growth_warning_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "raid_type": {
            "required": False,
            "type": "str",
            "choices": ['R0', 'R1', 'R5', 'R6'],
        },
        "set_size": {
            "required": False,
            "type": "int",
            "default": -1
        },
        "high_availability": {
            "type": "str",
            "choices": ['PORT', 'CAGE', 'MAG'],
        },
        "disk_type": {
            "type": "str",
            "choices": ['FC', 'NL', 'SSD'],
        }
    }

    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par CPG - test module arguments
        """
        
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR', 
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'cpg_name':'test_cpg',
            'domain':'test_domain',
            'growth_increment': 32768,
            'growth_increment_unit': 'MiB',
            'growth_limit': 32768,
            'growth_limit_unit': 'MiB',
            'growth_warning': 32768,
            'growth_warning_unit': 'MiB',
            'raid_type': 'R6',
            'set_size': 8,
            'high_availability': 'MAG',
            'disk_type': 'FC',
            'state': 'present'
        }
       
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        hpe3par_cpg.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.create_cpg')
    def test_main_exit_functionality_present_success_without_issue_attr_dict(self, mock_create_cpg, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """
        PARAMS_FOR_PRESENT = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR', 
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'cpg_name':'test_cpg',
            'domain':'test_domain',
            'growth_increment': 32768,
            'growth_increment_unit': 'MiB',
            'growth_limit': 32768,
            'growth_limit_unit': 'MiB',
            'growth_warning': 32768,
            'growth_warning_unit': 'MiB',
            'raid_type': 'R6',
            'set_size': 8,
            'high_availability': 'MAG',
            'disk_type': 'FC',
            'state': 'present'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_cpg.return_value = (True, True, "Created CPG successfully.", {})
        hpe3par_cpg.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created CPG successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.delete_cpg')
    def test_main_exit_functionality_absent_success_without_issue_attr_dict(self, mock_delete_cpg, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        PARAMS_FOR_DELETE = {
            'storage_system_ip':'192.168.0.1',
            'storage_system_name':'3PAR', 
            'storage_system_username':'USER',
            'storage_system_password':'PASS',
            'cpg_name':'test_cpg',
            'domain': None,
            'growth_increment': None,
            'growth_increment_unit': None,
            'growth_limit': None,
            'growth_limit_unit': None,
            'growth_warning': None,
            'growth_warning_unit': None,
            'raid_type': None,
            'set_size': None,
            'high_availability': None,
            'disk_type': None,
            'state': 'absent'
        }
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_DELETE
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_delete_cpg.return_value = (True, True, "Deleted CPG test_cpg successfully.", {})
        hpe3par_cpg.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted CPG test_cpg successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    def test_convert_to_binary_multiple(self):
        self.assertEqual(hpe3par_cpg.convert_to_binary_multiple(1, 'MiB'), 1)
        self.assertEqual(hpe3par_cpg.convert_to_binary_multiple(1, 'GiB'), 1 * 1024)
        self.assertEqual(hpe3par_cpg.convert_to_binary_multiple(1, 'TiB'), 1 * 1024 * 1024)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client.HPE3ParClient')
    def test_cpg_ldlayout_map(self, mock_HPE3ParClient):
        mock_HPE3ParClient.PORT = 1
        mock_HPE3ParClient.RAID_MAP = {'R6': {'raid_value': 1, 'set_sizes': [1]}, 
            'R1': {'raid_value': 2, 'set_sizes': [2, 3, 4]} , 
            'R5': {'raid_value': 3, 'set_sizes': [3, 4, 5, 6, 7, 8, 9]}, 
            'R6': {'raid_value': 4, 'set_sizes': [6, 8, 10, 12, 16]}
        }
        ldlayout_dict={'RAIDType': 'R6', 'HA': 'PORT'}
        self.assertEqual(hpe3par_cpg.cpg_ldlayout_map(ldlayout_dict), {'RAIDType': 4, 'HA': 1})
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client.HPE3ParClient')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg')
    def test_create_cpg(self, mock_hpe3par_cpg, mock_HPE3ParClient):
        mock_hpe3par_cpg.validate_set_size.return_value = None
        mock_hpe3par_cpg.cpg_ldlayout_map.return_value = {'RAIDType': 4, 'HA': 1}
        mock_hpe3par_cpg.convert_to_binary_multiple.return_value = 1000
        
        mock_HPE3ParClient.login.return_value = True
        mock_HPE3ParClient.cpgExists.return_value = False
        mock_HPE3ParClient.FC = 1
        mock_HPE3ParClient.createCPG.return_value = True
        
        self.assertEqual(hpe3par_cpg.create_cpg(mock_HPE3ParClient, 
                            'USER',
                            'PASS',
                            'test_cpg',
                            'test_domain',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            'R6',
                            8,
                            'MAG',
                            'FC'
                        ), (True, True, "Created CPG %s successfully." % 'test_cpg', {}))
                        
        mock_HPE3ParClient.cpgExists.return_value = True
        self.assertEqual(hpe3par_cpg.create_cpg(mock_HPE3ParClient, 
                            'USER',
                            'PASS',
                            'test_cpg',
                            'test_domain',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            'R6',
                            8,
                            'MAG',
                            'FC'
                        ), (True, False, "CPG already present", {}))
        self.assertEqual(hpe3par_cpg.create_cpg(mock_HPE3ParClient,
                            None,
                            'PASS',
                            'test_cpg',
                            'test_domain',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            'R6',
                            8,
                            'MAG',
                            'FC'
                        ), (False, False, "CPG create failed. Storage system username or password is null", {}))
        self.assertEqual(hpe3par_cpg.create_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None,
                            'test_domain',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            32768,
                            'MiB',
                            'R6',
                            8,
                            'MAG',
                            'FC'
                        ), (False, False, "CPG create failed. CPG name is null", {})) 
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_cpg.client.HPE3ParClient')
    def test_delete_cpg(self, mock_HPE3ParClient):
        mock_HPE3ParClient.login.return_value = True
        mock_HPE3ParClient.cpgExists.return_value = True
        mock_HPE3ParClient.FC = 1
        mock_HPE3ParClient.deleteCPG.return_value = True
        
        self.assertEqual(hpe3par_cpg.delete_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_cpg'
                        ), (True, True, "Deleted CPG %s successfully." % 'test_cpg', {}))
                        
        mock_HPE3ParClient.cpgExists.return_value = False

        self.assertEqual(hpe3par_cpg.delete_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            'test_cpg'
                        ), (True, False, "CPG does not exist", {}))
        self.assertEqual(hpe3par_cpg.delete_cpg(mock_HPE3ParClient,
                            None,
                            'PASS',
                            'test_cpg'
                        ), (False, False, "CPG delete failed. Storage system username or password is null", {}))
        self.assertEqual(hpe3par_cpg.delete_cpg(mock_HPE3ParClient,
                            'USER',
                            'PASS',
                            None
                        ), (False, False, "CPG delete failed. CPG name is null", {}))
                        
     
    
if __name__ == '__main__':
    unittest.main(exit=False)  

