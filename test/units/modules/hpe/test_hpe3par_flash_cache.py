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
from ansible.modules.storage.hpe import hpe3par_flash_cache as flash_cache
from ansible.module_utils.basic import AnsibleModule as ansible
import unittest

class TestHpe3parFlashCache(unittest.TestCase):
    
    PARAMS_FOR_PRESENT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'size_in_gib':1024, 'mode':1, 'state': 'present'}
    
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
         "size_in_gib": {
             "type": "int"
         },
         "mode": {
             "type": "int"
         }
    }
 
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par flash cache - test module arguments
        """
       
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        flash_cache.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.create_flash_cache')
    def test_main_exit_functionality_success_without_issue_attr_dict(self, mock_create_flash_cache, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_flash_cache.return_value = (True, True, "Created Flash Cache successfully.", {})
        flash_cache.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created Flash Cache successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.create_flash_cache')
    def test_main_exit_functionality_success_with_issue_attr_dict(self, mock_create_flash_cache, mock_module, mock_client):
        """
        hpe3par flash cache - success check 
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_flash_cache.return_value = (True, True, "Created Flash Cache successfully.", {"dummy":"dummy"})
        flash_cache.main()
        
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created Flash Cache successfully.",issue={"dummy":"dummy"})
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        

        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.create_flash_cache')
    def test_main_exit_functionality_fail(self, mock_create_flash_cache, mock_module, mock_client):
        """
        hpe3par flash cache - exit fail check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_flash_cache.return_value = (False, False, "Flash Cache creation failed.", {"dummy":"dummy"})
        flash_cache.main()
        
        # AnsibleModule.exit_json should not be activated
        self.assertEqual(instance.exit_json.call_count, 0) 
        # AnsibleModule.fail_json should be called
        instance.fail_json.assert_called_with(msg='Flash Cache creation failed.')  
 
#Create 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_create_flash_cache_username_empty(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.create_flash_cache(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Flash Cache creation failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_create_flash_cache_size_in_gib_empty(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.create_flash_cache(mock_client,"user","password",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Flash Cache creation failed. Size is null",
            {})) 
  
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_create_flash_cache_create_already_present(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.create_flash_cache(mock_client,"user","password",1024,None)     
        self.assertEqual(result, (True, False, "Flash Cache already present", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client.HPE3ParClient')
    def test_create_flash_cache_create_exception_in_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = flash_cache.create_flash_cache(mock_client,"user","password",1024,None) 
        self.assertEqual(result, (False, False, "Flash Cache creation failed | Failed to login!", {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client.HPE3ParClient')
    def test_create_flash_cache_create_sucess_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.flashCacheExists.return_value = False
        mock_client.return_value = mock_client
        result = flash_cache.create_flash_cache(mock_client,"user","password",1024,None) 
        self.assertEqual(result, (True, True, "Created Flash Cache successfully.", {}))   

#Delete

    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_delete_flash_cache_username_empty(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.delete_flash_cache(mock_client,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Flash Cache deletion failed. Storage system username or password is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_delete_flash_cache_create_absent(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.delete_flash_cache(mock_client,"user","password")     
        self.assertEqual(result, (True, True, "Deleted Flash Cache successfully.", {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client')
    def test_delete_flash_cache_create_present(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        result = flash_cache.delete_flash_cache(mock_client,"user","password")     
        self.assertEqual(result, (True, True, "Deleted Flash Cache successfully.", {}))
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_flash_cache.client.HPE3ParClient')
    def test_delete_flash_cache_create_exception_in_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = flash_cache.delete_flash_cache(mock_client,"user","password") 
        self.assertEqual(result, (False, False, "Flash Cache delete failed | Failed to login!", {}))                     
    
if __name__ == '__main__':
    unittest.main(exit=False)     
