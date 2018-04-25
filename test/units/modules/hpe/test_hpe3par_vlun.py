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
from ansible.modules.storage.hpe import hpe3par_vlun as vlun
from ansible.module_utils.basic import AnsibleModule as ansible
import unittest

class TestHpe3parVlun(unittest.TestCase):

    PARAMS_FOR_PRESENT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'export_volume_to_host' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}

    fields = {
        "state": {
            "required": True,
            "choices": [
                'export_volume_to_host',
                'unexport_volume_to_host',
                'export_volumeset_to_host',
                'unexport_volumeset_to_host',
                'export_volume_to_hostset',
                'unexport_volume_to_hostset',
                'export_volumeset_to_hostset',
                'unexport_volumeset_to_hostset'],
            "type": 'str'},
        "storage_system_ip": {
            "required": True,
            "type": "str"},
        "storage_system_name": {
            "type": "str"},
        "storage_system_username": {
            "required": True,
            "type": "str",
            "no_log": True},
        "storage_system_password": {
            "required": True,
            "type": "str",
            "no_log": True},
        "volume_name": {
            "required": False,
            "type": "str"},
        "volume_set_name": {
            "required": False,
            "type": "str"},
        "lunid": {
            "type": "int"},
        "autolun": {
            "type": "bool",
            "default": False},
        "host_name": {
            "type": "str"},
        "host_set_name": {
            "required": False,
            "type": "str"},
        "node_val": {
            "type": "int"},
        "slot": {
            "type": "int"},
        "card_port": {
            "type": "int"}
    }

    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    def test_module_args(self, mock_module, mock_client):
        """
        hpe3par vlun - test module arguments
        """

        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        vlun.main()
        mock_module.assert_called_with(
            argument_spec=self.fields)

    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volume_to_host')
    def test_main_exit_functionality_success_without_issue_attr_dict(self, mock_export_volume_to_host, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volume_to_host.return_value = (True, True, "Created VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.unexport_volume_to_host')
    def test_main_exit_unexport_volume_to_host(self, mock_unexport_volume_to_host,mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'unexport_volume_to_host' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_unexport_volume_to_host.return_value = (True, True, "Deleted VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volume_to_hostset')
    def test_main_exit_export_volume_to_hostset(self, mock_export_volume_to_hostset, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'export_volume_to_hostset' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volume_to_hostset.return_value = (True, True, "Created VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.unexport_volume_to_hostset')
    def test_main_exit_unexport_volume_to_hostset(self, mock_unexport_volume_to_hostset, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'unexport_volume_to_hostset' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_unexport_volume_to_hostset.return_value = (True, True, "Deleted VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volumeset_to_host')
    def test_main_exit_export_volumeset_to_host(self, mock_export_volumeset_to_host, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'export_volumeset_to_host' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volumeset_to_host.return_value = (True, True, "Created VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.unexport_volumeset_to_host')
    def test_main_exit_unexport_volumeset_to_host(self, mock_unexport_volumeset_to_host, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'unexport_volumeset_to_host' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_unexport_volumeset_to_host.return_value = (True, True, "Deleted VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volumeset_to_hostset')
    def test_main_exit_export_volumeset_to_hostset(self, mock_export_volumeset_to_hostset, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'export_volumeset_to_hostset' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volumeset_to_hostset.return_value = (True, True, "Created VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.unexport_volumeset_to_hostset')
    def test_main_exit_unexport_volumeset_to_hostset(self, mock_unexport_volumeset_to_hostset, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        PARAMS_FOR_UNEXPORT = {'storage_system_ip':'192.168.0.1', 'storage_system_name':'3PAR', 'storage_system_username':'USER',
                           'storage_system_password':'PASS', 'state':'unexport_volumeset_to_hostset' ,'volume_name':'test_vol_name', 'volume_set_name':'test_volset_name', 'lunid':12,'autolun':True,'host_name':'test_host_name','host_set_name':'test_hostset_name','node_val':3,'slot':2,'card_port':1}
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = PARAMS_FOR_UNEXPORT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_unexport_volumeset_to_hostset.return_value = (True, True, "Deleted VLUN successfully.", {})
        vlun.main()
        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Deleted VLUN successfully.")
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volume_to_host')
    def test_main_exit_functionality_success_with_issue_attr_dict(self, mock_export_volume_to_host, mock_module, mock_client):
        """
        hpe3par vlun - success check
        """
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volume_to_host.return_value = (True, True, "Created VLUN successfully", {"dummy":"dummy"})
        vlun.main()

        # AnsibleModule.exit_json should be called
        instance.exit_json.assert_called_with(
                changed=True, msg="Created VLUN successfully",issue={"dummy":"dummy"})
        # AnsibleModule.fail_json should not be called
        self.assertEqual(instance.fail_json.call_count, 0)
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.AnsibleModule')
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.export_volume_to_host')
    def test_main_exit_functionality_fail(self, mock_export_volume_to_host, mock_module, mock_client):
        """
        hpe3par vlun - exit fail check
        """
        # This creates a instance of the AnsibleModule mock.
        mock_module.params = self.PARAMS_FOR_PRESENT
        mock_module.return_value = mock_module
        instance = mock_module.return_value
        mock_export_volume_to_host.return_value = (False, False, "VLUN creation failed", {"dummy":"dummy"})
        vlun.main()

        # AnsibleModule.exit_json should not be activated
        self.assertEqual(instance.exit_json.call_count, 0)
        # AnsibleModule.fail_json should be called
        instance.fail_json.assert_called_with(msg="VLUN creation failed")

#export
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volume_tohost_with_host_andport_empty(self, mock_client):
        """
        hpe3par vlun - export volume to host
        """
        result = vlun.export_volume_to_host(mock_client,"user","password","test_volume_name",1,None,None,None,None,True)

        self.assertEqual(result, (
            False,
            False,
            "Attribute host_name or port positions or both need to be specified to create a vlun",
            {}))

#export volume to host
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volume_tohost_with_port_empty(self, mock_client):
        """
        hpe3par vlun - export volume to host
        """
        result = vlun.export_volume_to_host(mock_client,"user","password","test_volume_name",1,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Node, Slot and Port need to be specified to create a vlun',
            {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_vlun_already_present(self, mock_client):
        """
        hpe3par vlun - export volume to host
        """
        result = vlun.export_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1,True)
        self.assertEqual(result, (True, False, "VLUN already present", {}))

    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volume_to_host_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volume to host
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.export_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1,True)
        self.assertEqual(result, (False, False, "VLUN creation failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volume_to_host_sucess_(self, mock_client):
        """
        hpe3par vlun - export volume to host
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.export_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1,True)
        self.assertEqual(result, (True, True, "Created VLUN successfully.", {}))

#unexport volume to host
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volume_to_host_with_port_empty(self, mock_client):
        """
        hpe3par vlun - unexport volume to host
        """
        result = vlun.unexport_volume_to_host(mock_client,"user","password","test_volume_name",None,None,2,3,None)

        self.assertEqual(result, (
            False,
            False,
            'Node, Slot and Port or host name need to be specified to unexport a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_host_exception_in_login(self, mock_client):
        """
        hpe3par vlun - unexport volume to host
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1)
        self.assertEqual(result, (False, False, "VLUN deletion failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_host_with_nonexistent_vlun(self, mock_client):
        """
        hpe3par vlun - unexport volume to host
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1)
        self.assertEqual(result, (True, False, "VLUN does not exist", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_host_sucess_(self, mock_client):
        """
        hpe3par vlun - unexport volume to host
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1)
        self.assertEqual(result, (True, True, "Deleted VLUN successfully.", {}))

#export volume to hostset
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volume_to_hostset_with_empty_volume(self, mock_client):
        """
        hpe3par vlun - export volume to hostset
        """
        result = vlun.export_volume_to_hostset(mock_client,"user","password",None,None,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute volume name is required for vlun creation',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volume_to_hostset_with_empty_hostset(self, mock_client):
        """
        hpe3par vlun - export volume to hostset
        """
        result = vlun.export_volume_to_hostset(mock_client,"user","password","volume_name",1,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute hostset_name is required to export a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volume_to_hostset_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volume to hostset
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.export_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1,True)
        self.assertEqual(result, (False, False, "VLUN creation failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volume_to_hostset_with_existent_vlun(self, mock_client):
        """
        hpe3par vlun - export volume to hostset
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.export_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1,False)
        self.assertEqual(result, (True, False, "VLUN already present", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volume_to_hostset_sucess_(self, mock_client):
        """
        hpe3par vlun - export volume to hostset
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.export_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1,True)
        self.assertEqual(result, (True, True, "Created VLUN successfully.", {}))

#unexport volume to hostset
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volume_to_hostset_with_port_empty(self, mock_client):
        """
        hpe3par vlun - unexport volume to hostset
        """
        result = vlun.unexport_volume_to_hostset(mock_client,"user","password","test_volume_name",1,None,2,3,None)

        self.assertEqual(result, (
            False,
            False,
            'Node, Slot and Port or host name need to be specified to unexport a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volume_to_hostset_empty(self, mock_client):
        """
        hpe3par vlun - unexport volume to hostset
        """
        result = vlun.unexport_volume_to_hostset(mock_client,"user","password","test_volume_name",1,None,2,3,1)

        self.assertEqual(result, (
            False,
            False,
            'Attribute hostset_name is required to unexport a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_hostset_exception_in_login(self, mock_client):
        """
        hpe3par vlun - unexport volume to hostset
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1)
        self.assertEqual(result, (False, False, "VLUN deletion failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_hostset_with_nonexistent_vlun(self, mock_client):
        """
        hpe3par vlun - unexport volume to host
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1)
        self.assertEqual(result, (True, False, "VLUN does not exist", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volume_to_hostset_sucess_(self, mock_client):
        """
        hpe3par vlun - unexport volume to hostset
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.unexport_volume_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1)
        self.assertEqual(result, (True, True, "Deleted VLUN successfully.", {}))

#export volumeset to host
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_host_with_empty_volumeset(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        result = vlun.export_volumeset_to_host(mock_client,"user","password",None,None,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute volumeset name is required for vlun creation',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_host_with_empty_host(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        result = vlun.export_volumeset_to_host(mock_client,"user","password","volumeset_name",1,None,None,None,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute host_name or port positions or both need to be specified to create a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_host_with_empty_host_and_port(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        result = vlun.export_volumeset_to_host(mock_client,"user","password","volumeset_name",1,None,None,None,2,True)

        self.assertEqual(result, (
            False,
            False,
            'All port positions (node,slot,cardport) are required to create a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volumeset_to_host_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,"test_hostsetname",2,3,1,True)
        self.assertEqual(result, (False, False, "VLUN creation failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_host_with_existent_vlun(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,"test_hostsetname",2,3,1,False)
        self.assertEqual(result, (True, False, "VLUN already present", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volumeset_to_host_sucess(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_host(mock_client,"user","password","test_volume_name",1,"test_hostname",2,3,1,True)
        self.assertEqual(result, (True, True, "Created VLUN successfully.", {}))

#unexport volumeset to host
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volumeset_to_host_with_port_empty(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to host
        """
        result = vlun.unexport_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,None,2,3,None)

        self.assertEqual(result, (
            False,
            False,
            'Node, Slot and Port or host name need to be specified to unexport a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volumeset_to_host_empty(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to host
        """
        result = vlun.unexport_volumeset_to_host(mock_client,"user","password",None,1,'host_name',None,2,3)

        self.assertEqual(result, (
            False,
            False,
            'Attribute volume_set_name is required to unexport a vlun',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volumeset_to_host_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volumeset to host
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,"test_hostsetname",2,3,1)
        self.assertEqual(result, (False, False, "VLUN deletion failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volumeset_to_host_with_nonexistent_vlun(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to host
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,"test_hostname",2,3,1)
        self.assertEqual(result, (True, False, "VLUN does not exist", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volumeset_to_host_sucess_(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to host
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_host(mock_client,"user","password","test_volumeset_name",1,"test_hostname",2,3,1)
#export volumeset to hostsetset
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_hostset_with_empty_volumeset(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        result = vlun.export_volumeset_to_hostset(mock_client,"user","password",None,None,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute volumeset name is required for vlun creation',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_hostset_with_empty_hostset(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        result = vlun.export_volumeset_to_hostset(mock_client,"user","password","volume_set_name",1,None,2,3,None,True)

        self.assertEqual(result, (
            False,
            False,
            'Attribute hostset name is required for vlun creation',
            {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volumeset_to_hostset_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,"test_hostsetsetname",2,3,1,True)
        self.assertEqual(result, (False, False, "VLUN creation failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_export_volumeset_to_hostset_with_existent_vlun(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,"test_hostsetsetname",2,3,1,False)
        self.assertEqual(result, (True, False, "VLUN already present", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_export_volumeset_to_hostset_sucess(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.export_volumeset_to_hostset(mock_client,"user","password","test_volume_name",1,"test_hostsetname",2,3,1,True)
        self.assertEqual(result, (True, True, "Created VLUN successfully.", {}))
#unexport volumeset to hostset
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volumeset_to_hostset_with_port_empty(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to host
        """
        result = vlun.unexport_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,None,2,3,None)

        self.assertEqual(result, (
            False,
            False,
            'Node, Slot and Port or host set name need to be specified to unexport a vlun',{}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volumeset_to_hostset_with_empty_volumeset_and_hostset(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to hostset
        """
        result = vlun.unexport_volumeset_to_hostset(mock_client,"user","password",None,1,None,2,3,2)

        self.assertEqual(result, (
            False,
            False,
            'Attribute hostset_name and volumeset_name is required to unexport a vlun',{}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client')
    def test_unexport_volumeset_to_hostset_exception_in_login(self, mock_client):
        """
        hpe3par vlun - export volumeset to hostset
        """
        mock_client.login.side_effect = Exception("Failed to login!")
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,"test_hostsetsetname",2,3,1)
        self.assertEqual(result, (False, False, "VLUN deletion failed | Failed to login!", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volumeset_to_hostset_with_nonexistent_vlun(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to hostset
        """
        mock_client.vlunExists.return_value = False
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,"test_hostsetname",2,3,1)
        self.assertEqual(result, (True, False, "VLUN does not exist", {}))
    @mock.patch('ansible.modules.storage.hpe.hpe3par_vlun.client.HPE3ParClient')
    def test_unexport_volumeset_to_hostset_sucess_(self, mock_client):
        """
        hpe3par vlun - unexport volumeset to hostset
        """
        mock_client.vlunExists.return_value = True
        mock_client.return_value = mock_client
        result = vlun.unexport_volumeset_to_hostset(mock_client,"user","password","test_volumeset_name",1,"test_hostsetname",2,3,1)
if __name__ == '__main__':
    unittest.main(exit=False)
