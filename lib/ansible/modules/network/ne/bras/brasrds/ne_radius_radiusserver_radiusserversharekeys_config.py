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
module: ne_radius_radiusserver_radiusserversharekeys_config
version_added: "2.6"
short_description: Sets the shared key for a RADIUS servers in a RADIUS server group.
description:
    - Sets the shared key for a RADIUS servers in a RADIUS server group.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name,Range Supported [a-z][A-Z][0-9] and [.,_,-].
        required: false
    radiusServerType:
        description:
            - Indicates the RADIUS authentication or accounting server.
        required: false
        choices: ['authentication', 'accounting']
    shareKey:
        description:
            - Specifies the shared key in cipher text.
        required: false
    radiusServerIpv4Address:
        description:
            - Specifies the IPv4 address of the RADIUS server.
        required: false
    vpnName:
        description:
            - Specifies the name of a VPN instance. The value must be the name of a configured VPN instance.
        required: false
    radiusServerIpv6Address:
        description:
            - Specifies the IPv6 address of the RADIUS server.
        required: false
    radiusServerSourceInterface:
        description:
            - Specifies the source interface name of a server.
        required: false
    radiusServerSourceIpAddress:
        description:
            - Specifies the source IP address of a server.
        required: false
    portNumber:
        description:
            - Specifies the protocal port of the RADIUS server. The value ranges from 1 to 65535.
        required: false
    radiusServerWeight:
        description:
            - Indicates the weight of the authentication server and is used for load sharing.
              The weight-value parameter is valid only when the load sharing mode is adopted through the radius-server algorithm command.
              The value ranges from 0 to 100.
        required: false
    operation:
        description:
            - Specifies the operation type.
            if the operation is get,the shareKey and radiusServerSourceInterface and  radiusServerSourceIpAddress and
            radiusServerWeight cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_radius_radiusserver_radiusserversharekeys_config test
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

    - name: "Sets the shared key for a RADIUS servers in a RADIUS server group, the operation type is 'create'."
      ne_radius_radiusserver_radiusserversharekeys_config:
        groupName='nametest'
        radiusServerType='accounting'
        sharedKey='Huawei@123'
        radiusServerIpv4Address='1.1.1.1'
        vpnName='_public_'
        radiusServerIpv6Address='0::0'
        portNumber='18'
        operation='create'
        provider: "{{ cli }}"

    - name: "Sets the shared key for a RADIUS servers in a RADIUS server group, the operation type is 'delete'."
      ne_radius_radiusserver_radiusserversharekeys_config:
        groupName='nametest'
        radiusServerType='accounting'
        sharedKey='Huawei@123'
        radiusServerIpv4Address='1.1.1.1'
        vpnName='_public_'
        radiusServerIpv6Address='0::0'
        portNumber='18'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Sets the shared key for a RADIUS servers in a RADIUS server group, the operation type is 'get'."
      ne_radius_radiusserver_radiusserversharekeys_config:
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
        "portNumber": "18",
        "radiusServerIpv4Address": "1.1.1.1",
        "radiusServerIpv6Address": "0::0",
        "radiusServerType": "accounting",
        "shareKey": "123",
        "vpnName": "_public_"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "radiusServerShareKeys": [
            {
                "groupName": "nametest",
                "portNumber": "1812",
                "radiusServerIpv4Address": "138.187.24.16",
                "radiusServerIpv6Address": "::",
                "radiusServerType": "authentication",
                "radiusServerWeight": "0",
                "shareKey": "%^%#m>svXydI>%<aVc%tV#*QCEdYLHXP.W8d*^55&z_:%^%#",
                "vpnName": "_public_"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "radiusServerShareKeys": [
            {
                "groupName": "nametest",
                "portNumber": "1812",
                "radiusServerIpv4Address": "138.187.24.16",
                "radiusServerIpv6Address": "::",
                "radiusServerType": "authentication",
                "radiusServerWeight": "0",
                "shareKey": "%^%#m>svXydI>%<aVc%tV#*QCEdYLHXP.W8d*^55&z_:%^%#",
                "vpnName": "_public_"
            }
        ]
    }
'''


RADIUSSERVERSHAREKEYS_CONFIG_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
        <rdsTemplates>
          <rdsTemplate>
"""

RADIUSSERVERSHAREKEYS_CONFIG_TAIL = """
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

RADIUSSERVERSHAREKEYS_START = """
            <radiusServerShareKeys>"""

RADIUSSERVERSHAREKEY_START = """
              <radiusServerShareKey>"""

RADIUSSERVERSHAREKEYS_CREATE = """
              <radiusServerShareKey nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSSERVERSHAREKEYS_DELETE = """
              <radiusServerShareKey nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSSERVERSHAREKEYS_MERGE = """
              <radiusServerShareKey nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSSERVERSHAREKEY_END = """
              </radiusServerShareKey>"""

RADIUSSERVERSHAREKEYS_END = """
            </radiusServerShareKeys>"""

RADIUSSERVERSHAREKEYS_GET_HEAD = """
  <filter type="subtree">
    <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <rdsTemplates>
        <rdsTemplate>"""

RADIUSSERVERSHAREKEYS_GET_TAIL = """
        </rdsTemplate>
      </rdsTemplates>
    </radius>
  </filter>"""

GROUPNAME = """
                <groupName>%s</groupName>"""

RADIUSSERVERTYPE = """
                <radiusServerType>%s</radiusServerType>"""

SHAREKEY = """
                <shareKey>%s</shareKey>"""

RADIUSSERVERIPV4ADDRESS = """
                <radiusServerIpv4Address>%s</radiusServerIpv4Address>"""

RADIUSSERVERIPV4ADDRESS_INVALID = """
                <radiusServerIpv4Address>255.255.255.255</radiusServerIpv4Address>"""

VPNNAME = """
                <vpnName>%s</vpnName>"""

VPNNAME_INVALID = """
                <vpnName>_public_</vpnName>"""

RADIUSSERVERIPV6ADDRESS = """
                <radiusServerIpv6Address>%s</radiusServerIpv6Address>"""

RADIUSSERVERIPV6ADDRESS_INVALID = """
                <radiusServerIpv6Address>0::0</radiusServerIpv6Address>"""

RADIUSSERVERSOURCEINTERFACE = """
                <radiusServerSourceInterface>%s</radiusServerSourceInterface>"""

RADIUSSERVERSOURCEIPADDRESS = """
                <radiusServerSourceIpAddress>%s</radiusServerSourceIpAddress>"""

PORTNUMBER = """
                <portNumber>%s</portNumber>"""

RADIUSSERVERWEIGHT = """
                <radiusServerWeight>%s</radiusServerWeight>"""


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
        self.radiusServerType = self.module.params['radiusServerType']
        self.shareKey = self.module.params['shareKey']
        self.radiusServerIpv4Address = self.module.params['radiusServerIpv4Address']
        self.vpnName = self.module.params['vpnName']
        self.radiusServerIpv6Address = self.module.params['radiusServerIpv6Address']
        self.radiusServerSourceInterface = self.module.params['radiusServerSourceInterface']
        self.radiusServerSourceIpAddress = self.module.params['radiusServerSourceIpAddress']
        self.portNumber = self.module.params['portNumber']
        self.radiusServerWeight = self.module.params['radiusServerWeight']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.radiusServerType is not None:
            self.proposed["radiusServerType"] = self.radiusServerType
        if self.shareKey is not None:
            self.proposed["shareKey"] = self.shareKey
        if self.radiusServerIpv4Address is not None:
            self.proposed["radiusServerIpv4Address"] = self.radiusServerIpv4Address
        if self.vpnName is not None:
            self.proposed["vpnName"] = self.vpnName
        if self.radiusServerIpv6Address is not None:
            self.proposed["radiusServerIpv6Address"] = self.radiusServerIpv6Address
        if self.radiusServerSourceInterface is not None:
            self.proposed["radiusServerSourceInterface"] = self.radiusServerSourceInterface
        if self.radiusServerSourceIpAddress is not None:
            self.proposed["radiusServerSourceIpAddress"] = self.radiusServerSourceIpAddress
        if self.portNumber is not None:
            self.proposed["portNumber"] = self.portNumber
        if self.radiusServerWeight is not None:
            self.proposed["radiusServerWeight"] = self.radiusServerWeight
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
        cfg_str += RADIUSSERVERSHAREKEYS_CONFIG_HEAD
        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName

        cfg_str += RADIUSSERVERSHAREKEYS_START
        if self.operation == 'create':
            cfg_str += RADIUSSERVERSHAREKEYS_CREATE
        if self.operation == 'merge':
            cfg_str += RADIUSSERVERSHAREKEYS_MERGE
        if self.operation == 'delete':
            cfg_str += RADIUSSERVERSHAREKEYS_DELETE

        if self.radiusServerType is not None:
            cfg_str += RADIUSSERVERTYPE % self.radiusServerType
        if self.shareKey is not None:
            cfg_str += SHAREKEY % self.shareKey
        if self.radiusServerIpv4Address is not None:
            cfg_str += RADIUSSERVERIPV4ADDRESS % self.radiusServerIpv4Address
        else:
            cfg_str += RADIUSSERVERIPV4ADDRESS_INVALID
        if self.vpnName is not None:
            cfg_str += VPNNAME % self.vpnName
        else:
            cfg_str += VPNNAME_INVALID
        if self.radiusServerIpv6Address is not None:
            cfg_str += RADIUSSERVERIPV6ADDRESS % self.radiusServerIpv6Address
        else:
            cfg_str += RADIUSSERVERIPV6ADDRESS_INVALID
        if self.radiusServerSourceInterface is not None:
            cfg_str += RADIUSSERVERSOURCEINTERFACE % self.radiusServerSourceInterface
        if self.radiusServerSourceIpAddress is not None:
            cfg_str += RADIUSSERVERSOURCEIPADDRESS % self.radiusServerSourceIpAddress
        if self.portNumber is not None:
            cfg_str += PORTNUMBER % self.portNumber
        if self.radiusServerWeight is not None:
            cfg_str += RADIUSSERVERWEIGHT % self.radiusServerWeight

        cfg_str += RADIUSSERVERSHAREKEY_END
        cfg_str += RADIUSSERVERSHAREKEYS_END
        cfg_str += RADIUSSERVERSHAREKEYS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += RADIUSSERVERSHAREKEYS_GET_HEAD

        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName
        cfg_str += RADIUSSERVERSHAREKEYS_START
        cfg_str += RADIUSSERVERSHAREKEY_START
        if self.radiusServerType is not None:
            cfg_str += RADIUSSERVERTYPE % self.radiusServerType
        if self.radiusServerIpv4Address is not None:
            cfg_str += RADIUSSERVERIPV4ADDRESS % self.radiusServerIpv4Address
        if self.vpnName is not None:
            cfg_str += VPNNAME % self.vpnName
        if self.radiusServerIpv6Address is not None:
            cfg_str += RADIUSSERVERIPV6ADDRESS % self.radiusServerIpv6Address
        if self.portNumber is not None:
            cfg_str += PORTNUMBER % self.portNumber
        cfg_str += RADIUSSERVERSHAREKEY_END
        cfg_str += RADIUSSERVERSHAREKEYS_END

        cfg_str += RADIUSSERVERSHAREKEYS_GET_TAIL

        if self.operation == 'get':
            if self.shareKey is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.radiusServerSourceInterface is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.radiusServerSourceIpAddress is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.radiusServerWeight is not None:
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
        attributes_Info["radiusServerShareKeys"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["groupName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "radiusServerShareKeys/radiusServerShareKey")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["radiusServerType",
                                                   "shareKey",
                                                   "radiusServerIpv4Address",
                                                   "vpnName",
                                                   "radiusServerIpv6Address",
                                                   "radiusServerSourceInterface",
                                                   "radiusServerSourceIpAddress",
                                                   "portNumber",
                                                   "radiusServerWeight"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["radiusServerShareKeys"].append(
                            container_2_info_Table)

        if len(attributes_Info["radiusServerShareKeys"]) == 0:
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
        radiusServerType=dict(
            required=False, choices=[
                'authentication', 'accounting']),
        shareKey=dict(required=False, type='str'),
        radiusServerIpv4Address=dict(required=False, type='str'),
        vpnName=dict(required=False, type='str'),
        radiusServerIpv6Address=dict(required=False, type='str'),
        radiusServerSourceInterface=dict(required=False, type='str'),
        radiusServerSourceIpAddress=dict(required=False, type='str'),
        portNumber=dict(required=False, type='str'),
        radiusServerWeight=dict(required=False, type='int'),
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
