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
from ansible.modules.storage.hpe import hpe3par_volumeset as volumeset
from mock import MagicMock
from ansible.module_utils.basic import AnsibleModule as ansible
import unittest

class TestHpe3parvolumeset(unittest.TestCase):
       
    PARAMS_FOR_PRESENT = {'state':'present','storage_system_username':'USER','storage_system_ip':'192.168.0.1','storage_system_password':'PASS', 'volumeset_name':'volumeset','domain':'domain', 'setmembers':'new'}

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'add_volumes', 'remove_volumes'],
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
        "volumeset_name": {
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
 
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par volumeset - test module arguments
        """
       
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        volumeset.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.create_volumeset')
    def test_main_exit_functionality_success_without_issue_attr_dict(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "Created volumeset host successfully.", {})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created volumeset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
  
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.create_volumeset')
    def test_main_exit_functionality_success_with_issue_attr_dict(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "Created volumeset host successfully.", {"dummy":"dummy"})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created volumeset host successfully.",issue={"dummy":"dummy"})
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.create_volumeset')
    def test_main_exit_functionality_fail(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - exit fail check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (False, False, "volumeset creation failed.", {"dummy":"dummy"})
        volumeset.main()
        
        # AnsibleModule.exit_json should not be activated
        self.assertEqual(instance.exit_json.call_count, 0) 
        # AnsibleModule.fail_json should be called
        instance.fail_json.assert_called_with(msg='volumeset creation failed.') 
       
#Create volumeset
      
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_create_volumeset_username_empty(self, mock_client):
        """
        hpe3par volumeset - create a volumeset
        """  
        result = volumeset.create_volumeset(mock_client,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "volumeset create failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_create_volumeset_hostname_empty(self, mock_client):
        """
        hpe3par volumeset - create a volumeset
        """  
        result = volumeset.create_volumeset(mock_client,"user","pass",None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "volumeset create failed. volumeset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_create_volumeset_create_already_present(self, mock_client):
        """
        hpe3par volumeset - create a volumeset
        """  
        result = volumeset.create_volumeset(mock_client,"user","pass","host",None,None)    
        self.assertEqual(result, (True, False, "volumeset already present", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_create_volumeset_create_exception_in_login(self, mock_client):
        """
        hpe3par volumeset - create a volumeset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = volumeset.create_volumeset(mock_client,"user","password",'vs_name',None,None) 
        self.assertEqual(result, (False, False, "volumeset creation failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_create_volumeset_create_sucess_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.volumeSetExists.return_value = False
        mock_client.return_value = mock_client
        result = volumeset.create_volumeset(mock_client,"user","password","hostname","domain",["member1"])
        self.assertEqual(result, (True, True, "Created volumeset hostname successfully.", {}))

            
# Delete volumeset   

      
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_delete_volumeset_username_empty(self, mock_client):
        """
        hpe3par volumeset - delete a volumeset
        """  
        result = volumeset.delete_volumeset(mock_client,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "volumeset delete failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_delete_volumeset_hostname_empty(self, mock_client):
        """
        hpe3par volumeset - delete a volumeset
        """  
        result = volumeset.delete_volumeset(mock_client,"user","pass",None)
        
        self.assertEqual(result, (
            False,
            False,
            "volumeset delete failed. volumeset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_delete_volumeset_create_already_present(self, mock_client):
        """
        hpe3par volumeset - delete a volumeset
        """  
        mock_client.volumeSetExists.return_value = False
        mock_client.return_value = mock_client        
        result = volumeset.delete_volumeset(mock_client,"user","pass","host")    
        self.assertEqual(result, (True, False, "volumeset does not exist", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_delete_volumeset_create_exception_in_login(self, mock_client):
        """
        hpe3par volumeset - delete a volumeset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = volumeset.delete_volumeset(mock_client,"user","password","hostname") 
        self.assertEqual(result, (False, False, "volumeset delete failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_delete_volumeset_create_sucess_login(self, mock_client):
        """
        hpe3par flash cache - create a flash cache
        """  
        mock_client.volumeSetExists.return_value = True
        mock_client.return_value = mock_client
        result = volumeset.delete_volumeset(mock_client,"user","password","hostname")
        self.assertEqual(result, (True, True, "Deleted volumeset hostname successfully.", {}))  

     
# Add volume to volumeset.

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_add_volume_to_volumeset_volumeset_username_empty(self, mock_client):
        """
        hpe3par volumeset - Add volumes to a volumeset
        """  
        result = volumeset.add_volumes(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Add volume to volumeset failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_add_volume_to_volumeset_volumeset_hostname_empty(self, mock_client):
        """
        hpe3par volumeset - Add volumes to a volumeset
        """  
        result = volumeset.add_volumes(mock_client,"user","pass",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Add volume to volumeset failed. Volumeset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_add_volume_to_volumeset_volumeset_setmembers_empty(self, mock_client):
        """
        hpe3par volumeset - Add volumes to a volumeset
        """  
        result = volumeset.add_volumes(mock_client,"user","pass","volumeset",None)
        
        self.assertEqual(result, (
            False,
            False,
            "Add volume to volumeset failed. Setmembers is null",
            {}))        
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_add_volume_to_volumeset_volumeset_create_sucess_login(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        result = volumeset.add_volumes(mock_client,"user","pass","host",["members"])    
        self.assertEqual(result, (True, True, 'Added volumes successfully.', {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_add_volume_to_volumeset_volumeset_create_exception_in_login(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = volumeset.add_volumes(mock_client,"user","password","host",["members"]) 
        self.assertEqual(result, (False, False, "Add volumes to volumeset failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_add_volume_to_volumeset_volumeset_doesnt_exists(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        mock_client.volumeSetExists.return_value = False
        mock_client.return_value = mock_client
        result = volumeset.add_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (False, False, "Volumeset does not exist", {}))
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_add_volume_to_volumeset_No_new_members_to_add_to_the_Host_set(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        mock_client.getVolumeSet.return_value.setmembers = ["member1"]
        mock_client.return_value = mock_client
        result = volumeset.add_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "No new members to add to the Volume set hostname#. Nothing to do.", {}))                     

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_add_volume_to_volumeset_No_new_members_to_add_to_the_Host_set_login(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        mock_client.getVolumeSet.return_value.setmembers = []
        mock_client.return_value = mock_client
        result = volumeset.add_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Added volumes successfully.', {}))
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_add_volume_to_volumeset_No_new_members_to_add_to_the_Host_set_login_setmembers_none(self, mock_client):
        """
        hpe3par volumeset - add volume to a volumeset
        """  
        mock_client.getVolumeSet.return_value.setmembers = None
        mock_client.return_value = mock_client
        result = volumeset.add_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Added volumes successfully.', {}))        

 
# Remove hosts from volumeset.

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_remove_host_from_volumeset_volumeset_username_empty(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        result = volumeset.remove_volumes(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_remove_host_from_volumeset_volumeset_hostname_empty(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        result = volumeset.remove_volumes(mock_client,"user","pass",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Volumeset name is null",
            {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_remove_host_from_volumeset_volumeset_setmembers_empty(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        result = volumeset.remove_volumes(mock_client,"user","pass","volumeset",None)
        
        self.assertEqual(result, (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Setmembers is null",
            {}))        
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    def test_remove_host_from_volumeset_volumeset_create_sucess_login(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        mock_client.volumesetExists.return_value = True
        mock_client.getVolumeSet.return_value.setmembers = ["members"]
        mock_client.return_value = mock_client        
        result = volumeset.remove_volumes(mock_client,"user","pass","host",["members"])    
        self.assertEqual(result, (True, True, 'Removed volumes successfully.', {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_remove_host_from_volumeset_volumeset_create_exception_in_login(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = volumeset.remove_volumes(mock_client,"user","password","host",["members"]) 
        self.assertEqual(result, (False, False, "Remove volumes from volumeset failed | Failed to login!", {}))        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_remove_host_from_volumeset_volumeset_doesnt_exists(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        mock_client.volumeSetExists.return_value = False
        mock_client.return_value = mock_client        
        result = volumeset.remove_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "Volumeset does not exist", {}))
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_remove_host_from_volumeset_No_new_members_to_remove_from_the_Host_set(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        mock_client.getVolumeSet.return_value.setmembers = []
        mock_client.return_value = mock_client
        result = volumeset.remove_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, False, "No members to remove to the Volume set hostname. Nothing to do.", {}))
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client.HPE3ParClient')
    def test_remove_host_from_volumeset_No_new_members_to_remove_from_the_Host_set_setmembers_none(self, mock_client):
        """
        hpe3par volumeset - remove volume from a volumeset
        """  
        mock_client.getVolumeSet.return_value.setmembers = None
        mock_client.return_value = mock_client
        result = volumeset.remove_volumes(mock_client,"user","password","hostname",["member1"])
        self.assertEqual(result, (True, True, 'Removed volumes successfully.', {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.create_volumeset')
    def test_main_exit_functionality_success_without_issue_attr_dict_present(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "present"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "Created volumeset host successfully.", {})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created volumeset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        
                  
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.delete_volumeset')
    def test_main_exit_functionality_success_without_issue_attr_dict_present(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "absent"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "Deleted volumeset host successfully.", {})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted volumeset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        

    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.add_volumes')
    def test_main_exit_functionality_success_without_issue_attr_dict_add_volumes(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "add_volumes"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "add_volumes volumeset host successfully.", {})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="add_volumes volumeset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_volumeset.remove_volumes')
    def test_main_exit_functionality_success_without_issue_attr_dict_remove_volumes(self, mock_volumeset, mock_module, mock_client):
        """
        hpe3par volumeset - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "remove_volumes"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_volumeset.return_value = (True, True, "remove_volumes volumeset host successfully.", {})
        volumeset.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="remove_volumes volumeset host successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        
              
if __name__ == '__main__':
    unittest.main(exit=False)     
