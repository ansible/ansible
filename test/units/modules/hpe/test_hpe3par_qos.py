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
from ansible.modules.storage.hpe import hpe3par_qos as qos
from ansible.module_utils.basic import AnsibleModule as ansible
import unittest

class TestHpe3parQos(unittest.TestCase):
    
    PARAMS_FOR_PRESENT = {'storage_system_ip':'192.168.0.1','storage_system_username':'USER',
                           'storage_system_password':'PASS', 'qos_target_name':'target', 'type':'vvset', 'state': 'present',
                           'priority':'LOW', 'bwmin_goal_kb':1, 'bwmax_limit_kb':1, 'iomin_goal':1, 'iomax_limit':1, 'bwmin_goal_op':'ZERO',
                           'bwmax_limit_op':'ZERO', 'iomin_goal_op':'ZERO', 'iomax_limit_op':'ZERO', 'latency_goal':1, 'default_latency':False,
                           'enable':False, 'latency_goal_usecs':1}    
    
    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'modify'],
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
        "qos_target_name": {
            "required": True,
            "type": "str"
        },
        "type": {
            "choices": ['vvset', 'sys'],
            "type": "str"
        },
        "priority": {
            "choices": ['LOW', 'NORMAL', 'HIGH'],
            "default": 'LOW',
            "type": "str"
        },
        "bwmin_goal_kb": {
            "type": "int",
            "default": -1
        },
        "bwmax_limit_kb": {
            "type": "int",
            "default": -1
        },
        "iomin_goal": {
            "type": "int",
            "default": -1
        },
        "iomax_limit": {
            "type": "int",
            "default": -1
        },
        "bwmin_goal_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "bwmax_limit_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "iomin_goal_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "iomax_limit_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "latency_goal": {
            "type": "int"
        },
        "default_latency": {
            "type": "bool",
            "default": False
        },
        "enable": {
            "type": "bool",
            "default": False
        },
        "latency_goal_usecs": {
            "type": "int"
        }
    }
     
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par flash cache - test module arguments
        """
       
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        qos.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)
  
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.create_qos_rule')
    def test_main_exit_functionality_success_without_issue_attr_dict(self, mock_create_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_qos_rule.return_value = (True, True, "Created QOS successfully.", {})
        qos.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created QOS successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.create_qos_rule')
    def test_main_exit_functionality_success_with_issue_attr_dict(self, mock_create_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - success check 
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_qos_rule.return_value = (True, True, "Created QOS successfully.", {"dummy":"dummy"})
        qos.main()
        
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created QOS successfully.",issue={"dummy":"dummy"})
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)        

        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.create_qos_rule')
    def test_main_exit_functionality_fail(self, mock_create_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - exit fail check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_qos_rule.return_value = (False, False, "QOS creation failed.", {"dummy":"dummy"})
        qos.main()
        
        # AnsibleModule.exit_json should not be activated
        self.assertEqual(instance.exit_json.call_count, 0) 
        # AnsibleModule.fail_json should be called
        instance.fail_json.assert_called_with(msg='QOS creation failed.')  

#Create 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_create_qos_rule_username_empty(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        result = qos.create_qos_rule(mock_client,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS creation failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_create_qos_rule_size_in_gib_empty(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        result = qos.create_qos_rule(mock_client,"user","password",None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS creation failed. qos_target_name is null",
            {})) 
  
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_create_qos_rule_create_already_present(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        result = qos.create_qos_rule(mock_client,"user","password",'qos_tgt',None,None,None,None,None,None,None,None,None,None,None,None,None,None)     
        self.assertEqual(result, (True, False, "QoS already present", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_create_qos_rule_create_exception_in_login(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = qos.create_qos_rule(mock_client,"user","password",'qos_tgt_name',None,None,None,None,None,None,None,None,None,None,None,None,None,None) 
        self.assertEqual(result, (False, False, "QoS creation failed | Failed to login!", {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_create_qos_rule_create_sucess_login(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        mock_client.qosRuleExists.return_value = False
        mock_client.return_value = mock_client
        result = qos.create_qos_rule(mock_client,"user","password",'qos_tgt_name','vvset',None,None,None,None,None,None,None,None,None,None,None,None,None) 
        self.assertEqual(result, (True, True, "Created QoS successfully.", {})) 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_create_qos_rule_create_sucess_login_latency_goal_latency_goal_usecs(self, mock_client):
        """
        hpe3par qos - create a qos rule
        """  
        mock_client.qosRuleExists.return_value = False
        mock_client.return_value = mock_client
        result = qos.create_qos_rule(mock_client,"user","password",'qos_tgt_name',None,None,None,None,None,None,None,None,None,None,20,None,None,10) 
        self.assertEqual(result, (False, False, 'Attributes latency_goal and latency_goal_usecs cannot be given at the same time for qos rules creation', {}))         

#Delete 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_delete_qos_rule_username_empty(self, mock_client):
        """
        hpe3par qos - delete a qos rule
        """  
        result = qos.delete_qos_rule(mock_client,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS deletion failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_delete_qos_rule_size_in_gib_empty(self, mock_client):
        """
        hpe3par qos - delete a qos rule
        """  
        result = qos.delete_qos_rule(mock_client,"user","password",None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS deletion failed. qos_target_name is null",
            {})) 
  
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_delete_qos_rule_create_already_present(self, mock_client):
        """
        hpe3par qos - delete a qos rule
        """ 
        mock_client.qosRuleExists.return_value = False
        mock_client.return_value = mock_client         
        result = qos.delete_qos_rule(mock_client,"user","password",'qos_tgt_name',None)     
        self.assertEqual(result, (True, False, "QoS does not exist", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_delete_qos_rule_create_exception_in_login(self, mock_client):
        """
        hpe3par qos - delete a qos rule
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = qos.delete_qos_rule(mock_client,"user","password",'qos_tgt_name',None) 
        self.assertEqual(result, (False, False, "QoS delete failed | Failed to login!", {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_delete_qos_rule_create_sucess_login(self, mock_client):
        """
        hpe3par qos - delete a qos rule
        """  
        mock_client.qosRuleExists.return_value = True
        mock_client.return_value = mock_client
        result = qos.delete_qos_rule(mock_client,"user","password",'qos_tgt_name',None) 
        self.assertEqual(result, (True, True, "Deleted QoS successfully.", {})) 

#Modify 
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_modify_qos_rule_username_empty(self, mock_client):
        """
        hpe3par qos - modify a qos rule
        """  
        result = qos.modify_qos_rule(mock_client,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS modification failed. Storage system username or password is null",
            {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_modify_qos_rule_size_in_gib_empty(self, mock_client):
        """
        hpe3par qos - modify a qos rule
        """  
        result = qos.modify_qos_rule(mock_client,"user","password",None,None,None,None,None,None,None,None,None,None,None,None,None,None,None)
        
        self.assertEqual(result, (
            False,
            False,
            "QoS modification failed. qos_target_name is null",
            {})) 
  
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    def test_modify_qos_rule_create_already_present(self, mock_client):
        """
        hpe3par qos - modify a qos rule
        """  
        result = qos.modify_qos_rule(mock_client,"user","password",'qos_tgt_name',None,None,None,None,None,None,None,None,None,None,None,None,None,None)     
        self.assertEqual(result, (True, True, "Modified QoS successfully.", {}))                            
    
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_modify_qos_rule_create_exception_in_login(self, mock_client):
        """
        hpe3par qos - modify a qos rule
        """  
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = qos.modify_qos_rule(mock_client,"user","password",'qos_tgt_name',None,None,None,None,None,None,None,None,None,None,None,None,None,None) 
        self.assertEqual(result, (False, False, "QoS modification failed | Failed to login!", {})) 

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client.HPE3ParClient')
    def test_modify_qos_rule_create_sucess_login(self, mock_client):
        """
        hpe3par qos - modify a qos rule
        """  
        mock_client.qosRuleExists.return_value = False
        mock_client.return_value = mock_client
        result = qos.modify_qos_rule(mock_client,"user","password",'qos_tgt_name',None,None,None,None,None,None,None,None,None,None,None,None,None,None) 
        self.assertEqual(result, (True, True, "Modified QoS successfully.", {})) 

    def test_construct_qos_rules_map_priority(self):
        """
        hpe3par qos - construct_qos_rules
        """  
        result = qos.construct_qos_rules_map(None,None,None,None,None,None,None,None,'LOW',None,None,None,None)   
        self.assertEqual(result['priority'], 1) 
    
    def test_construct_qos_rules_map_bwMinGoalOP(self):
        """
        hpe3par qos - construct_qos_rules
        """  
        result = qos.construct_qos_rules_map(None,None,None,None,None,None,None,None,'LOW','ZERO',None,None,None)
        self.assertEqual(result['bwMinGoalOP'], 1) 
    
    def test_construct_qos_rules_map_bwMaxLimitOP(self):
        """
        hpe3par qos - construct_qos_rules
        """  
        result = qos.construct_qos_rules_map(None,None,None,None,None,None,None,None,'LOW','ZERO','ZERO',None,None)   
        self.assertEqual(result['bwMaxLimitOP'], 1) 
    
    def test_construct_qos_rules_map_iomin_goal_op(self):
        """
        hpe3par qos - construct_qos_rules
        """  
        result = qos.construct_qos_rules_map(None,None,None,None,None,None,None,None,'LOW','ZERO','ZERO','ZERO',None)   
        self.assertEqual(result['ioMinGoalOP'], 1) 

    def test_construct_qos_rules_map_iomax_limit_op(self):
        """
        hpe3par qos - construct_qos_rules
        """  
        result = qos.construct_qos_rules_map(None,None,None,None,None,None,None,None,'LOW','ZERO','ZERO','ZERO','ZERO')   
        self.assertEqual(result['ioMaxLimitOP'], 1) 
 
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.create_qos_rule')
    def test_main_exit_functionality_success_without_issue_attr_dict_present(self, mock_create_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "present"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_create_qos_rule.return_value = (True, True, "Created QOS successfully.", {})
        qos.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created QOS successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
        
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.delete_qos_rule')
    def test_main_exit_functionality_success_without_issue_attr_dict_absent(self, mock_delete_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "absent"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_delete_qos_rule.return_value = (True, True, "Created QOS successfully.", {})
        qos.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created QOS successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)               

    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_qos.modify_qos_rule')
    def test_main_exit_functionality_success_without_issue_attr_dict_modify(self, mock_modify_qos_rule, mock_module, mock_client):
        """
        hpe3par flash cache - success check
        """  
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.params["state"] = "modify"
        mock_module.return_value = mock_module    
        instance = mock_module.return_value
        mock_modify_qos_rule.return_value = (True, True, "Created QOS successfully.", {})
        qos.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created QOS successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)    
    
if __name__ == '__main__':
    unittest.main(exit=False)     
