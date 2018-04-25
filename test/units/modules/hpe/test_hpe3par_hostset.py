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
from ansible.modules.storage.hpe import hpe3par_hostset as hostset
from mock import MagicMock
from ansible.module_utils.basic import AnsibleModule as ansible
import unittest

class TestHpe3parhostset(unittest.TestCase):
       
    PARAMS_FOR_PRESENT = {'state':'present','storage_system_username':'USER','storage_system_name':'3PAR','storage_system_ip':'192.168.0.1','storage_system_password':'PASS', 'hostset_name':'hostset',
                           'domain':'domain', 'setmembers':'new'}

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'add_hosts', 'remove_hosts'],
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
        "hostset_name": {
            "required": True,
            "type": "str"
        },
        "domain": {
            "type": "str"
        },
        "setmembers": {
            "type": "list"
        }
    }
 
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par host set - test module arguments
        """
       
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        hostset.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.create_hostset')
    def test_main_exit_functionality_success_without_issue_attr_dict(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "Created hostset host successfully.", {})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created hostset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
  
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.create_hostset')
    def test_main_exit_functionality_success_with_issue_attr_dict(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "Created hostset host successfully.", {"dummy":"dummy"})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created hostset host successfully.",issue={"dummy":"dummy"})
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.create_hostset')
    def test_main_exit_functionality_fail(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - exit fail check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (False, False, "hostset creation failed.", {"dummy":"dummy"})
        hostset.main()
        
        # AnsibleModule.exit_json should not be activated
        self.assertEqual(instance.exit_json.call_count, 0) 
        # AnsibleModule.fail_json should be called
        instance.fail_json.assert_called_with(msg='hostset creation failed.') 
        
#Create hostset
      
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_create_hostset_username_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.create_hostset(mock_client,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Hostset create failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_create_hostset_hostname_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.create_hostset(mock_client,"user","pass",None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Hostset create failed. Hostset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_create_hostset_create_already_present(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.create_hostset(mock_client,"user","pass","host",None,None)    
        self.assertEqual(result, (True, False, "Hostset already present", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_create_hostset_create_exception_in_login(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = hostset.create_hostset(mock_client,"user","password",'hostset_name',None,None) 
        self.assertEqual(result, (False, False, "Hostset creation failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_create_hostset_create_sucess_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.hostSetExists.return_value = False
        mock_client.return_value = mock_client
        result = hostset.create_hostset(mock_client,"user","password","hostname","domain",["member1"])
        self.assertEqual(result, (True, True, "Created Hostset hostname successfully.", {}))
               
# Delete hostset   

      
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_delete_hostset_username_empty(self, mock_client):
        """
        hpe3par hostset - delete a hostset
        """  
        result = hostset.delete_hostset(mock_client,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Hostset delete failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_delete_hostset_hostname_empty(self, mock_client):
        """
        hpe3par hostset - delete a hostset
        """  
        result = hostset.delete_hostset(mock_client,"user","pass",None)
        
        self.assertEqual(result, (
            False,
            False,
            "Hostset delete failed. Hostset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_delete_hostset_create_already_present(self, mock_client):
        """
        hpe3par hostset - delete a hostset
        """  
        mock_client.hostSetExists.return_value = False
        mock_client.return_value = mock_client        
        result = hostset.delete_hostset(mock_client,"user","pass","host")    
        self.assertEqual(result, (True, False, "Hostset does not exist", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_delete_hostset_create_exception_in_login(self, mock_client):
        """
        hpe3par hostset - delete a hostset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = hostset.delete_hostset(mock_client,"user","password","hostname") 
        self.assertEqual(result, (False, False, "Hostset delete failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_delete_hostset_create_sucess_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.hostSetExists.return_value = True
        mock_client.return_value = mock_client
        result = hostset.delete_hostset(mock_client,"user","password","hostname")
        self.assertEqual(result, (True, True, "Deleted Hostset hostname successfully.", {}))  
        
# Add hosts to hostset.

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_add_host_to_hostset_hostset_username_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.add_hosts(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Add host to hostset failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_add_host_to_hostset_hostset_hostname_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.add_hosts(mock_client,"user","pass",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Add host to hostset failed. Hostset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_add_host_to_hostset_hostset_setmembers_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.add_hosts(mock_client,"user","pass","hostset",None)
        
        self.assertEqual(result, (
            False,
            False,
            "setmembers delete failed. Setmembers is null",
            {}))        
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_add_host_to_hostset_hostset_create_sucess_login(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.add_hosts(mock_client,"user","pass","host",["members"])    
        self.assertEqual(result, (True, True, 'Added hosts successfully.', {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_add_host_to_hostset_hostset_create_exception_in_login(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = hostset.add_hosts(mock_client,"user","password","host",["members"]) 
        self.assertEqual(result, (False, False, "Add hosts to hostset failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_add_host_to_hostset_hostset_doesnt_exists(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.hostSetExists.return_value = False
        mock_client.return_value = mock_client
        result = hostset.add_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (False, False, "Hostset does not exist", {}))
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_add_host_to_hostset_No_new_members_to_add_to_the_Host_set(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.getHostSet.return_value.setmembers = ["member1"]
        mock_client.return_value = mock_client
        result = hostset.add_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "No new members to add to the Host set hostname. Nothing to do.", {}))                     

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_add_host_to_hostset_No_new_members_to_add_to_the_Host_set_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.getHostSet.return_value.setmembers = []
        mock_client.return_value = mock_client
        result = hostset.add_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Added hosts successfully.', {}))
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_add_host_to_hostset_No_new_members_to_add_to_the_Host_set_login_setmembers_none(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.getHostSet.return_value.setmembers = None
        mock_client.return_value = mock_client
        result = hostset.add_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Added hosts successfully.', {}))        
        
# Remove hosts from hostset.

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_remove_host_from_hostset_hostset_username_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.remove_hosts(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Remove host from hostset failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_remove_host_from_hostset_hostset_hostname_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.remove_hosts(mock_client,"user","pass",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Remove host from hostset failed. Hostset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_remove_host_from_hostset_hostset_setmembers_empty(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        result = hostset.remove_hosts(mock_client,"user","pass","hostset",None)
        
        self.assertEqual(result, (
            False,
            False,
            "setmembers delete failed. Setmembers is null",
            {}))        
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    def test_remove_host_from_hostset_hostset_create_sucess_login(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        mock_client.hostSetExists.return_value = True
        mock_client.getHostSet.return_value.setmembers = ["members"]
        mock_client.return_value = mock_client        
        result = hostset.remove_hosts(mock_client,"user","pass","host",["members"])    
        self.assertEqual(result, (True, True, 'Removed hosts successfully.', {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_remove_host_from_hostset_hostset_create_exception_in_login(self, mock_client):
        """
        hpe3par hostset - create a hostset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = hostset.remove_hosts(mock_client,"user","password","host",["members"]) 
        self.assertEqual(result, (False, False, "Remove hosts from hostset failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_remove_host_from_hostset_hostset_doesnt_exists(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.hostSetExists.return_value = False
        mock_client.return_value = mock_client        
        result = hostset.remove_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "Hostset does not exist", {}))
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_remove_host_from_hostset_No_new_members_to_remove_from_the_Host_set(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.getHostSet.return_value.setmembers = []
        mock_client.return_value = mock_client
        result = hostset.remove_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "No members to remove to the Host set hostname. Nothing to do.", {}))
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client.HPE3ParClient')
    def test_remove_host_from_hostset_No_new_members_to_remove_from_the_Host_set_setmembers_none(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.getHostSet.return_value.setmembers = None
        mock_client.return_value = mock_client
        result = hostset.remove_hosts(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Removed hosts successfully.', {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.create_hostset')
    def test_main_exit_functionality_success_without_issue_attr_dict_present(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "present"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "Created hostset host successfully.", {})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created hostset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        
                  
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.delete_hostset')
    def test_main_exit_functionality_success_without_issue_attr_dict_present(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "absent"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "Deleted hostset host successfully.", {})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted hostset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.add_hosts')
    def test_main_exit_functionality_success_without_issue_attr_dict_add_hosts(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "add_hosts"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "add_hosts hostset host successfully.", {})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="add_hosts hostset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_hostset.remove_hosts')
    def test_main_exit_functionality_success_without_issue_attr_dict_remove_hosts(self, mock_hostset, mock_module, mock_client):
        """
        hpe3par hostset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "remove_hosts"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_hostset.return_value = (True, True, "remove_hosts hostset host successfully.", {})
        hostset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="remove_hosts hostset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        
              
if __name__ == '__main__':
    unittest.main(exit=False)     
