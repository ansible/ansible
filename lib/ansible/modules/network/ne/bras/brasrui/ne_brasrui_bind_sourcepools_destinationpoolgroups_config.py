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
module: ne_brasrui_bind_sourcepools_destinationpoolgroups_config
version_added: "2.6"
short_description: Specifies the name of a source IP address pool and the destination IP address pool group.
description:
    - Specifies the name of a source IP address pool and the destination IP address pool group.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    remoteBackupProfileName:
        description:
            - Remote backup profile name.
        required: false
    poolName:
        description:
            - IP pool name.
        required: false
    targetPoolGroupName:
        description:
            - The target pool group name.
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

- name: ne_brasrui_bind_sourcepools_destinationpoolgroups_config test
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

    - name: "Specifies the name of a source IP address pool and the destination IP address pool group, the operation type is 'create'."
      ne_brasrui_bind_sourcepools_destinationpoolgroups_config:
        remoteBackupProfileName='nameTest1'
        poolName='nameTest2'
        targetPoolGroupName='nameTest3'
        nodeId='1'
        operation='create'
        provider: "{{ cli }}"

    - name: "Specifies the name of a source IP address pool and the destination IP address pool group, the operation type is 'delete'."
      ne_brasrui_bind_sourcepools_destinationpoolgroups_config:
        remoteBackupProfileName='nameTest1'
        poolName='nameTest2'
        targetPoolGroupName='nameTest3'
        nodeId='1'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Specifies the name of a source IP address pool and the destination IP address pool group, the operation type is 'get'."
      ne_brasrui_bind_sourcepools_destinationpoolgroups_config:
        remoteBackupProfileName='nameTest1'
        poolName='nameTest2'
        targetPoolGroupName='nameTest3'
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
        "poolName": "nameTest2",
        "targetPoolGroupName": "nameTest3",
        "nodeId": 1,
        "operation": "create",
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "sourcePoolDestinaGroups": [
            {
                "remoteBackupProfileName": "nameTest1",
                "poolName": "nameTest2",
                "targetPoolGroupName": "nameTest3",
                "nodeId": 1
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "sourcePoolDestinaGroups": [
            {
                "remoteBackupProfileName": "nameTest1",
                "poolName": "nameTest2",
                "targetPoolGroupName": "nameTest3",
                "nodeId": 1
            }
        ]
    }
'''


REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CONFIG_HEAD = """
    <config>
      <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
        <remoteBackupProfiles>
          <remoteBackupProfile>
"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CONFIG_TAIL = """
          </remoteBackupProfile>
        </remoteBackupProfiles>
      </brasrui>
    </config>
"""

SOURCEPOOLDESTINAGROUPS_START = """
            <sourcePoolDestinaGroups>"""

SOURCEPOOLDESTINAGROUP_START = """
              <sourcePoolDestinaGroup>"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CREATE = """
              <sourcePoolDestinaGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_DELETE = """
              <sourcePoolDestinaGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_MERGE = """
              <sourcePoolDestinaGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SOURCEPOOLDESTINAGROUP_END = """
              </sourcePoolDestinaGroup>"""

SOURCEPOOLDESTINAGROUPS_END = """
            </sourcePoolDestinaGroups>"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_GET_HEAD = """
  <filter type="subtree">
    <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
      <remoteBackupProfiles>
        <remoteBackupProfile>"""

REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_GET_TAIL = """
        </remoteBackupProfile>
      </remoteBackupProfiles>
    </brasrui>
  </filter>"""

REMOTEBACKUPPROFILENAME = """
                <remoteBackupProfileName>%s</remoteBackupProfileName>"""

POOLNAME = """
                <poolName>%s</poolName>"""

TARGETPOOLGROUPNAME = """
                <targetPoolGroupName>%s</targetPoolGroupName>"""

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
        self.poolName = self.module.params['poolName']
        self.targetPoolGroupName = self.module.params['targetPoolGroupName']
        self.nodeId = self.module.params['nodeId']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.remoteBackupProfileName is not None:
            self.proposed["remoteBackupProfileName"] = self.remoteBackupProfileName
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.targetPoolGroupName is not None:
            self.proposed["targetPoolGroupName"] = self.targetPoolGroupName
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
        cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CONFIG_HEAD
        if self.remoteBackupProfileName is not None:
            cfg_str += REMOTEBACKUPPROFILENAME % self.remoteBackupProfileName

        cfg_str += SOURCEPOOLDESTINAGROUPS_START
        if self.operation == 'create':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CREATE
        if self.operation == 'merge':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_MERGE
        if self.operation == 'delete':
            cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_DELETE

        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName
        if self.targetPoolGroupName is not None:
            cfg_str += TARGETPOOLGROUPNAME % self.targetPoolGroupName
        if self.nodeId is not None:
            cfg_str += NODEID % self.nodeId

        cfg_str += SOURCEPOOLDESTINAGROUP_END
        cfg_str += SOURCEPOOLDESTINAGROUPS_END
        cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_GET_HEAD

        if self.remoteBackupProfileName is not None:
            cfg_str += REMOTEBACKUPPROFILENAME % self.remoteBackupProfileName
        cfg_str += SOURCEPOOLDESTINAGROUPS_START
        cfg_str += SOURCEPOOLDESTINAGROUP_START
        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName
        if self.targetPoolGroupName is not None:
            cfg_str += TARGETPOOLGROUPNAME % self.targetPoolGroupName
        cfg_str += SOURCEPOOLDESTINAGROUP_END
        cfg_str += SOURCEPOOLDESTINAGROUPS_END

        cfg_str += REMOTEBACKUPPROFILES_SOURCEPOOLDESTINAGROUPS_GET_TAIL

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
        attributes_Info["sourcePoolDestinaGroups"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["remoteBackupProfileName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "sourcePoolDestinaGroups/sourcePoolDestinaGroup")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["poolName",
                                                   "targetPoolGroupName",
                                                   "nodeId"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["sourcePoolDestinaGroups"].append(
                            container_2_info_Table)

        if len(attributes_Info["sourcePoolDestinaGroups"]) == 0:
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
        poolName=dict(required=False, type='str'),
        targetPoolGroupName=dict(required=False, type='str'),
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
