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
module: ne_radius_radiusauthorizations_config
version_added: "2.6"
short_description: A set of authorization servers in a group.
description:
    - A set of authorization servers in a group.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    radiusAuthorServerIPAddress:
        description:
            - Specifies the IP address of a RADIUS authorization server, expressed in dotted decimal notation.
        required: false
    vpnInstanceName:
        description:
            - Indicates the VPN instance to which the RADIUS authorization server belongs.
        required: false
    destinationIPAddress:
        description:
            - Specifies the IP address of dynamic authorization packets.
        required: false
    destinationPort:
        description:
            - Specifies the port number of dynamic authorization packets.
        required: false
    radiusServerGroupName:
        description:
            - Specifies the name of the RADIUS server group corresponding to the RADIUS authorization server.
        required: false
    sharedKey:
        description:
            - Specifies the shared key for the RADIUS server.
        required: false
    authorAckReservedInterval:
        description:
            - Specifies the period when the authorization acknowledgment packets are saved.
        required: false
    operation:
        description:
            - Specifies the operation type.
            if the operation is get,the destinationIPAddress and destinationPort and radiusServerGroupName and
            authorAckReservedInterval and sharedKey and vpnInstanceName cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_radius_radiusauthorizations_config test
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

    - name: "A set of authorization servers in a group, the operation type is 'create'."
      ne_radius_radiusauthorizations_config:
        radiusAuthorServerIPAddress='138.187.24.28'
        sharedKey='Huawei@123'
        operation='create'
        provider: "{{ cli }}"

    - name: "A set of authorization servers in a group, the operation type is 'delete'."
      ne_radius_radiusauthorizations_config:
        radiusAuthorServerIPAddress='138.187.24.28'
        sharedKey='Huawei@123'
        operation='delete'
        provider: "{{ cli }}"

    - name: "A set of authorization servers in a group, the operation type is 'get'."
      ne_radius_radiusauthorizations_config:
        radiusAuthorServerIPAddress='138.187.24.28'
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
        "radiusAuthorServerIPAddress": "138.187.24.28",
        "sharedKey": "123",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "radiusAuthorizations": [
            {
                "authorAckReservedInterval": "0",
                "radiusAuthorServerIPAddress": "138.187.24.16",
                "sharedKey": "%^%#Q~'vJF.q&\":.%y9t:Tu28vc^>:3sANZk(!W{SW=!%^%#",
                "vpnInstanceName": "_public_"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "radiusAuthorizations": [
            {
                "authorAckReservedInterval": "0",
                "radiusAuthorServerIPAddress": "138.187.24.16",
                "sharedKey": "%^%#Q~'vJF.q&\":.%y9t:Tu28vc^>:3sANZk(!W{SW=!%^%#",
                "vpnInstanceName": "_public_"
            }
        ]
    }
'''


RADIUSAUTHORIZATIONS_CONFIG_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
        <radiusAuthorizations>
"""

RADIUSAUTHORIZATIONS_CONFIG_TAIL = """
          </radiusAuthorization>
        </radiusAuthorizations>
      </radius>
    </config>
"""

RADIUSAUTHORSERVERIPADDRESS = """
      <radiusAuthorServerIPAddress>%s</radiusAuthorServerIPAddress>"""

VPNINSTANCENAME = """
      <vpnInstanceName>%s</vpnInstanceName>"""

DESTINATIONIPADDRESS = """
      <destinationIPAddress>%s</destinationIPAddress>"""

DESTINATIONPORT = """
      <destinationPort>%s</destinationPort>"""

RADIUSSERVERGROUPNAME = """
      <radiusServerGroupName>%s</radiusServerGroupName>"""

SHAREDKEY = """
      <sharedKey>%s</sharedKey>"""

AUTHORACKRESERVEDINTERVAL = """
      <authorAckReservedInterval>%s</authorAckReservedInterval>"""

RADIUSAUTHORIZATION_CREATE = """
      <radiusAuthorization nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSAUTHORIZATION_DELETE = """
      <radiusAuthorization nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSAUTHORIZATION_MERGE = """
      <radiusAuthorization nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

RADIUSAUTHORIZATIONS_GET_HEAD = """
  <filter type="subtree">
    <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <radiusAuthorizations>
        <radiusAuthorization>"""

RADIUSAUTHORIZATIONS_GET_TAIL = """
        </radiusAuthorization>
      </radiusAuthorizations>
    </radius>
  </filter>"""


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
        self.radiusAuthorServerIPAddress = self.module.params['radiusAuthorServerIPAddress']
        self.vpnInstanceName = self.module.params['vpnInstanceName']
        self.destinationIPAddress = self.module.params['destinationIPAddress']
        self.destinationPort = self.module.params['destinationPort']
        self.radiusServerGroupName = self.module.params['radiusServerGroupName']
        self.sharedKey = self.module.params['sharedKey']
        self.authorAckReservedInterval = self.module.params['authorAckReservedInterval']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.radiusAuthorServerIPAddress is not None:
            self.proposed["radiusAuthorServerIPAddress"] = self.radiusAuthorServerIPAddress
        if self.vpnInstanceName is not None:
            self.proposed["vpnInstanceName"] = self.vpnInstanceName
        if self.destinationIPAddress is not None:
            self.proposed["destinationIPAddress"] = self.destinationIPAddress
        if self.destinationPort is not None:
            self.proposed["destinationPort"] = self.destinationPort
        if self.radiusServerGroupName is not None:
            self.proposed["radiusServerGroupName"] = self.radiusServerGroupName
        if self.sharedKey is not None:
            self.proposed["sharedKey"] = self.sharedKey
        if self.authorAckReservedInterval is not None:
            self.proposed["authorAckReservedInterval"] = self.authorAckReservedInterval
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
        cfg_str += RADIUSAUTHORIZATIONS_CONFIG_HEAD
        if self.operation == 'create':
            cfg_str += RADIUSAUTHORIZATION_CREATE
        if self.operation == 'merge':
            cfg_str += RADIUSAUTHORIZATION_MERGE
        if self.operation == 'delete':
            cfg_str += RADIUSAUTHORIZATION_DELETE

        if self.radiusAuthorServerIPAddress is not None:
            cfg_str += RADIUSAUTHORSERVERIPADDRESS % self.radiusAuthorServerIPAddress
        if self.vpnInstanceName is not None:
            cfg_str += VPNINSTANCENAME % self.vpnInstanceName
        if self.destinationIPAddress is not None:
            cfg_str += DESTINATIONIPADDRESS % self.destinationIPAddress
        if self.destinationPort is not None:
            cfg_str += DESTINATIONPORT % self.destinationPort
        if self.radiusServerGroupName is not None:
            cfg_str += RADIUSSERVERGROUPNAME % self.radiusServerGroupName
        if self.sharedKey is not None:
            cfg_str += SHAREDKEY % self.sharedKey
        if self.authorAckReservedInterval is not None:
            cfg_str += AUTHORACKRESERVEDINTERVAL % self.authorAckReservedInterval

        cfg_str += RADIUSAUTHORIZATIONS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += RADIUSAUTHORIZATIONS_GET_HEAD

        if self.radiusAuthorServerIPAddress:
            cfg_str += RADIUSAUTHORSERVERIPADDRESS % self.radiusAuthorServerIPAddress

        cfg_str += RADIUSAUTHORIZATIONS_GET_TAIL

        if self.operation == 'get':
            if self.destinationIPAddress is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.destinationPort is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.radiusServerGroupName is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.authorAckReservedInterval is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.sharedKey is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.vpnInstanceName is not None:
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
        container_attributes_Info = root.findall(
            "radius/radiusAuthorizations/radiusAuthorization")
        attributes_Info["radiusAuthorizations"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["radiusAuthorServerIPAddress",
                                                    "vpnInstanceName",
                                                    "destinationIPAddress",
                                                    "destinationPort",
                                                    "radiusServerGroupName",
                                                    "sharedKey",
                                                    "authorAckReservedInterval"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["radiusAuthorizations"].append(container_Table)

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
        radiusAuthorServerIPAddress=dict(required=False, type='str'),
        vpnInstanceName=dict(required=False, type='str'),
        destinationIPAddress=dict(required=False, type='str'),
        destinationPort=dict(required=False, type='str'),
        radiusServerGroupName=dict(required=False, type='str'),
        sharedKey=dict(required=False, type='str'),
        authorAckReservedInterval=dict(required=False, type='str'),
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
