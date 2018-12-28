#!/usr/bin/python
# coding=utf-8
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import logging
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_brasrui_bind_sourcepoolgroups_destinationpools_config
version_added: "2.6"
short_description: Specifies the name of a source IP address pool group and the destination IP address pool.
description:
    - Specifies the name of a source IP address pool group and the destination IP address pool.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    remoteBackupProfileName:
        description:
            - Remote backup profile name.
        required: false
    poolGroupName:
        description:
            - The source pool group name.
        required: false
    targetPoolName:
        description:
            - The target pool name.
        required: false
    nodeId:
        description:
            - Node id.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the nodeId cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasrui_bind_sourcepoolgroups_destinationpools_config test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
        host: "{{ inventory_hostname }}"
        port: "{{ ansible_ssh_port }}"
        username: "{{ ansible_user }}"
        password: "{{ ansible_ssh_pass }}"
        transport: cli

    tasks:

    - name: "Specifies the name of a source IP address pool group and the destination IP address pool, the operation type is 'create'."
      ne_brasrui_bind_sourcepoolgroups_destinationpools_config:
        remoteBackupProfileName='nameTest1'
        poolGroupName='nameTest2'
        targetPoolName='nameTest3'
        nodeId='1'
        operation='create'
        provider: "{{ cli }}"

    - name: "Specifies the name of a source IP address pool group and the destination IP address pool, the operation type is 'delete'."
      ne_brasrui_bind_sourcepoolgroups_destinationpools_config:
        remoteBackupProfileName='nameTest1'
        poolGroupName='nameTest2'
        targetPoolName='nameTest3'
        nodeId='1'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Specifies the name of a source IP address pool group and the destination IP address pool, the operation type is 'get'."
      ne_brasrui_bind_sourcepoolgroups_destinationpools_config:
        remoteBackupProfileName='nameTest1'
        poolGroupName='nameTest2'
        targetPoolName='nameTest3'
        nodeId='1'
        operation='get'
        provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "remoteBackupProfileName": "nameTest1",
        "poolGroupName": "nameTest2",
        "targetPoolName": "nameTest3",
        "nodeId": 1,
        "operation": "create",
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "sourceGroupDestinaPools": [
            {
                "remoteBackupProfileName": "nameTest1",
                "poolGroupName": "nameTest2",
                "targetPoolName": "nameTest3",
                "nodeId": 1
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "sourceGroupDestinaPools": [
            {
                "remoteBackupProfileName": "nameTest1",
                "poolGroupName": "nameTest2",
                "targetPoolName": "nameTest3",
                "nodeId": 1
            }
        ]
    }
'''


REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CONFIG_HEAD = """
    <config>
      <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
        <remoteBackupProfiles>
          <remoteBackupProfile>
"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CONFIG_TAIL = """
          </remoteBackupProfile>
        </remoteBackupProfiles>
      </brasrui>
    </config>
"""

SOURCEGROUPDESTINAPOOLS_START = """
            <sourceGroupDestinaPools>"""

SOURCEGROUPDESTINAPOOL_START = """
              <sourceGroupDestinaPool>"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CREATE = """
              <sourceGroupDestinaPool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_DELETE = """
              <sourceGroupDestinaPool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_MERGE = """
              <sourceGroupDestinaPool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SOURCEGROUPDESTINAPOOL_END = """
              </sourceGroupDestinaPool>"""

SOURCEGROUPDESTINAPOOLS_END = """
            </sourceGroupDestinaPools>"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_GET_HEAD = """
  <filter type="subtree">
    <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
      <remoteBackupProfiles>
        <remoteBackupProfile>"""

REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_GET_TAIL = """
        </remoteBackupProfile>
      </remoteBackupProfiles>
    </brasrui>
  </filter>"""

REMOTEBACKUPPROFILENAME = """
                <remoteBackupProfileName>%s</remoteBackupProfileName>"""

POOLGROUPNAME = """
                <poolGroupName>%s</poolGroupName>"""

TARGETPOOLNAME = """
                <targetPoolName>%s</targetPoolName>"""

NODEID = """
                <nodeId>%s</nodeId>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

        # module input info
        self.remoteBackupProfileName = self.module.params['remoteBackupProfileName']
        self.poolGroupName = self.module.params['poolGroupName']
        self.targetPoolName = self.module.params['targetPoolName']
        self.nodeId = self.module.params['nodeId']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.remoteBackupProfileName is not None:
            self.proposed["remoteBackupProfileName"] = self.remoteBackupProfileName
        if self.poolGroupName is not None:
            self.proposed["poolGroupName"] = self.poolGroupName
        if self.targetPoolName is not None:
            self.proposed["targetPoolName"] = self.targetPoolName
        if self.nodeId is not None:
            self.proposed["nodeId"] = self.nodeId
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        """get config rpc string"""
        cfg_str = ''
        self.changed = True
        cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CONFIG_HEAD
        if self.remoteBackupProfileName is not None:
            cfg_str += REMOTEBACKUPPROFILENAME % self.remoteBackupProfileName

        cfg_str += SOURCEGROUPDESTINAPOOLS_START
        if self.operation == 'create':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CREATE
        if self.operation == 'merge':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_MERGE
        if self.operation == 'delete':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_DELETE

        if self.poolGroupName is not None:
            cfg_str += POOLGROUPNAME % self.poolGroupName
        if self.targetPoolName is not None:
            cfg_str += TARGETPOOLNAME % self.targetPoolName
        if self.nodeId is not None:
            cfg_str += NODEID % self.nodeId

        cfg_str += SOURCEGROUPDESTINAPOOL_END
        cfg_str += SOURCEGROUPDESTINAPOOLS_END
        cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_GET_HEAD

        if self.remoteBackupProfileName is not None:
            cfg_str += REMOTEBACKUPPROFILENAME % self.remoteBackupProfileName
        cfg_str += SOURCEGROUPDESTINAPOOLS_START
        cfg_str += SOURCEGROUPDESTINAPOOL_START
        if self.poolGroupName is not None:
            cfg_str += POOLGROUPNAME % self.poolGroupName
        if self.targetPoolName is not None:
            cfg_str += TARGETPOOLNAME % self.targetPoolName
        cfg_str += SOURCEGROUPDESTINAPOOL_END
        cfg_str += SOURCEGROUPDESTINAPOOLS_END

        cfg_str += REMOTEBACKUPPROFILES_SOURCEGROUPDESTINAPOOLS_GET_TAIL

        if self.operation == 'get':
            if self.nodeId is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasrui/remoteBackupProfiles/remoteBackupProfile")
        attributes_Info["sourceGroupDestinaPools"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["remoteBackupProfileName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "sourceGroupDestinaPools/sourceGroupDestinaPool")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["poolGroupName",
                                                   "targetPoolName",
                                                   "nodeId"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["sourceGroupDestinaPools"].append(
                            container_2_info_Table)

        if len(attributes_Info["sourceGroupDestinaPools"]) == 0:
            attributes_Info.clear()
        return attributes_Info

    def run(self):
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        if self.operation != 'get':
            self.create_set_delete_process()
            self.end_state = self.get_info_process()
            self.results['end_state'] = self.end_state

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.module.exit_json(**self.results)


def main():
    """ main module """
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    argument_spec = dict(
        remoteBackupProfileName=dict(required=False, type='str'),
        poolGroupName=dict(required=False, type='str'),
        targetPoolName=dict(required=False, type='str'),
        nodeId=dict(required=False, type='int'),
        operation=dict(
            required=True,
            choices=[
                'create',
                'delete',
                'merge',
                'get']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
