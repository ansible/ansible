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
module: ne_radius_radiusserver_rdsserveripv4s_config
version_added: "2.6"
short_description: A set of servers in a group.
description:
    - A set of servers in a group.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name,Range Supported [a-z][A-Z][0-9] and [.,_,-].
        required: false
    serverType:
        description:
            - Type of Radius Server.
        required: false
        choices: ['Authentication', 'Accounting']
    serverIPAddress:
        description:
            - IPv4 address of configured server.
        required: false
    serverPort:
        description:
            - Configured server port for a particular server.
        required: false
    serverMode:
        description:
            - To configure primary or secondary server.
        required: false
        choices: ['Secondary-server', 'Primary-server']
    sourceInterfaceName:
        description:
            - To configure source interface name.
        required: false
    sharedKey:
        description:
            - To configure shared-key value for a particular server.
        required: false
    vpnName:
        description:
            - Set VPN instance.
        required: false
    sourceAddress:
        description:
            - To configure source address.
        required: false
    weight:
        description:
            - Set the weight.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the serverMode and sourceInterfaceName and  sharedKey and sourceAddress and weight cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_radius_radiusserver_rdsserveripv4s_config test
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

    - name: "Sets the server attribute in a RADIUS server group, the operation type is 'create'."
      ne_radius_radiusserver_rdsserveripv4s_config:
        groupName='nametest'
        serverType='Accounting'
        serverIPAddress='1.1.1.1'
        serverPort='18'
        operation='create'
        provider: "{{ cli }}"

    - name: "Sets the server attribute in a RADIUS server group, the operation type is 'delete'."
      ne_radius_radiusserver_rdsserveripv4s_config:
        groupName='nametest'
        serverType='Accounting'
        serverIPAddress='1.1.1.1'
        serverPort='18'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Sets the server attribute in a RADIUS server group, the operation type is 'get'."
      ne_radius_radiusserver_rdsserveripv4s_config:
        groupName='nametest'
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
        "groupName": "nametest",
        "operation": "create",
        "serverIPAddress": "1.1.1.1",
        "serverPort": "20",
        "serverType": "Accounting"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "rdsServerIPV4s": [
            {
                "groupName": "nametest",
                "isCurrentServer": "true",
                "serverCurrentState": "Up",
                "serverIPAddress": "1.1.1.1",
                "serverMode": "Primary-server",
                "serverPort": "20",
                "serverType": "Authentication",
                "vpnName": "_public_",
                "weight": "0"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "rdsServerIPV4s": [
            {
                "groupName": "nametest",
                "isCurrentServer": "true",
                "serverCurrentState": "Up",
                "serverIPAddress": "1.1.1.1",
                "serverMode": "Primary-server",
                "serverPort": "20",
                "serverType": "Authentication",
                "vpnName": "_public_",
                "weight": "0"
            },
            {
                "groupName": "nametest",
                "isCurrentServer": "true",
                "serverCurrentState": "Up",
                "serverIPAddress": "1.1.1.1",
                "serverMode": "Primary-server",
                "serverPort": "20",
                "serverType": "Accounting",
                "vpnName": "_public_",
                "weight": "0"
            }
        ]
    }
'''


RDSSERVERIPV4S_CONFIG_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
        <rdsTemplates>
          <rdsTemplate>
"""

RDSSERVERIPV4S_CONFIG_TAIL = """
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

RDSSERVERIPV4S_START = """
            <rdsServerIPV4s>"""

RDSSERVERIPV4_START = """
              <rdsServerIPV4>"""

RDSSERVERIPV4S_CREATE = """
              <rdsServerIPV4 nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RDSSERVERIPV4S_DELETE = """
              <rdsServerIPV4 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RDSSERVERIPV4S_MERGE = """
              <rdsServerIPV4 nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RDSSERVERIPV4_END = """
              </rdsServerIPV4>"""

RDSSERVERIPV4S_END = """
            </rdsServerIPV4s>"""

RDSSERVERIPV4S_GET_HEAD = """
  <filter type="subtree">
    <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <rdsTemplates>
        <rdsTemplate>"""

RDSSERVERIPV4S_GET_TAIL = """
        </rdsTemplate>
      </rdsTemplates>
    </radius>
  </filter>"""

GROUPNAME = """
                <groupName>%s</groupName>"""

SERVERTYPE = """
                <serverType>%s</serverType>"""

SERVERIPADDRESS = """
                <serverIPAddress>%s</serverIPAddress>"""

SERVERPORT = """
                <serverPort>%s</serverPort>"""

SERVERMODE = """
                <serverMode>%s</serverMode>"""

SOURCEINTERFACENAME = """
                <sourceInterfaceName>%s</sourceInterfaceName>"""

SHAREDKEY = """
                <sharedKey>%s</sharedKey>"""

VPNNAME = """
                <vpnName>%s</vpnName>"""

VPNNAME_INVALID = """
                <vpnName>_public_</vpnName>"""

SOURCEADDRESS = """
                <sourceAddress>%s</sourceAddress>"""

WEIGHT = """
                <weight>%s</weight>"""


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
        self.groupName = self.module.params['groupName']
        self.serverType = self.module.params['serverType']
        self.serverIPAddress = self.module.params['serverIPAddress']
        self.serverPort = self.module.params['serverPort']
        self.serverMode = self.module.params['serverMode']
        self.sourceInterfaceName = self.module.params['sourceInterfaceName']
        self.sharedKey = self.module.params['sharedKey']
        self.vpnName = self.module.params['vpnName']
        self.sourceAddress = self.module.params['sourceAddress']
        self.weight = self.module.params['weight']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.serverType is not None:
            self.proposed["serverType"] = self.serverType
        if self.serverIPAddress is not None:
            self.proposed["serverIPAddress"] = self.serverIPAddress
        if self.serverPort is not None:
            self.proposed["serverPort"] = self.serverPort
        if self.serverMode is not None:
            self.proposed["serverMode"] = self.serverMode
        if self.sourceInterfaceName is not None:
            self.proposed["sourceInterfaceName"] = self.sourceInterfaceName
        if self.sharedKey is not None:
            self.proposed["sharedKey"] = self.sharedKey
        if self.vpnName is not None:
            self.proposed["vpnName"] = self.vpnName
        if self.sourceAddress is not None:
            self.proposed["sourceAddress"] = self.sourceAddress
        if self.weight is not None:
            self.proposed["weight"] = self.weight
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
        cfg_str += RDSSERVERIPV4S_CONFIG_HEAD
        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName

        cfg_str += RDSSERVERIPV4S_START
        if self.operation == 'create':
            cfg_str += RDSSERVERIPV4S_CREATE
        if self.operation == 'merge':
            cfg_str += RDSSERVERIPV4S_MERGE
        if self.operation == 'delete':
            cfg_str += RDSSERVERIPV4S_DELETE

        if self.serverType is not None:
            cfg_str += SERVERTYPE % self.serverType
        if self.serverIPAddress is not None:
            cfg_str += SERVERIPADDRESS % self.serverIPAddress
        if self.serverPort is not None:
            cfg_str += SERVERPORT % self.serverPort
        if self.serverMode is not None:
            cfg_str += SERVERMODE % self.serverMode
        if self.sourceInterfaceName is not None:
            cfg_str += SOURCEINTERFACENAME % self.sourceInterfaceName
        if self.sharedKey is not None:
            cfg_str += SHAREDKEY % self.sharedKey
        if self.vpnName is not None:
            cfg_str += VPNNAME % self.vpnName
        else:
            cfg_str += VPNNAME_INVALID
        if self.sourceAddress is not None:
            cfg_str += SOURCEADDRESS % self.sourceAddress
        if self.weight is not None:
            cfg_str += WEIGHT % self.weight

        cfg_str += RDSSERVERIPV4_END
        cfg_str += RDSSERVERIPV4S_END
        cfg_str += RDSSERVERIPV4S_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += RDSSERVERIPV4S_GET_HEAD

        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName
        cfg_str += RDSSERVERIPV4S_START
        cfg_str += RDSSERVERIPV4_START
        if self.serverType is not None:
            cfg_str += SERVERTYPE % self.serverType
        if self.serverIPAddress is not None:
            cfg_str += SERVERIPADDRESS % self.serverIPAddress
        if self.serverPort is not None:
            cfg_str += SERVERPORT % self.serverPort
        if self.vpnName is not None:
            cfg_str += VPNNAME % self.vpnName
        cfg_str += RDSSERVERIPV4_END
        cfg_str += RDSSERVERIPV4S_END

        cfg_str += RDSSERVERIPV4S_GET_TAIL

        if self.operation == 'get':
            if self.serverMode is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.sourceInterfaceName is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.sharedKey is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.sourceAddress is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.weight is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-radius"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "radius/rdsTemplates/rdsTemplate")
        attributes_Info["rdsServerIPV4s"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["groupName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "rdsServerIPV4s/rdsServerIPV4")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["serverType",
                                                   "serverIPAddress",
                                                   "serverPort",
                                                   "serverMode",
                                                   "sourceInterfaceName",
                                                   "sharedKey",
                                                   "vpnName",
                                                   "sourceAddress",
                                                   "weight",
                                                   "serverCurrentState",
                                                   "isCurrentServer"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["rdsServerIPV4s"].append(
                            container_2_info_Table)

        if len(attributes_Info["rdsServerIPV4s"]) == 0:
            attributes_Info.clear()
        return attributes_Info

    def run(self):
        # self.check_params()

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
        groupName=dict(required=False, type='str'),
        serverType=dict(
            required=False,
            choices=[
                'Authentication',
                'Accounting']),
        serverIPAddress=dict(required=False, type='str'),
        serverPort=dict(required=False, type='str'),
        serverMode=dict(
            required=False,
            choices=[
                'Secondary-server',
                'Primary-server']),
        sourceInterfaceName=dict(required=False, type='str'),
        sharedKey=dict(required=False, type='str'),
        vpnName=dict(required=False, type='str'),
        sourceAddress=dict(required=False, type='str'),
        weight=dict(required=False, type='int'),
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
