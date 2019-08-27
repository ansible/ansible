#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_vlan

short_description: NetApp Element Software Manage VLAN
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, delete, modify VLAN

options:

    state:
      description:
      - Whether the specified vlan should exist or not.
      choices: ['present', 'absent']
      default: present

    vlan_tag:
      description:
      - Virtual Network Tag
      required: true

    name:
      description:
      - User defined name for the new VLAN
      - Name of the vlan is unique
      - Required for create

    svip:
      description:
      - Storage virtual IP which is unique
      - Required for create

    address_blocks:
      description:
      - List of address blocks for the VLAN
      - Each address block contains the starting IP address and size for the block
      - Required for create

    netmask:
      description:
      - Netmask for the VLAN
      - Required for create

    gateway:
      description:
      - Gateway for the VLAN

    namespace:
      description:
      - Enable or disable namespaces
      type: bool

    attributes:
      description:
      - Dictionary of attributes with name and value for each attribute

'''

EXAMPLES = """
- name: Create vlan
  na_elementsw_vlan:
    state: present
    name: test
    vlan_tag: 1
    svip: "{{ ip address }}"
    netmask: "{{ netmask }}"
    address_blocks:
      - start: "{{ starting ip_address }}"
        size: 5
      - start: "{{ starting ip_address }}"
        size: 5
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Delete Lun
  na_elementsw_vlan:
    state: absent
    vlan_tag: 1
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except ImportError:
    HAS_SF_SDK = False


class ElementSWVlan(object):
    """ class to handle VLAN operations """

    def __init__(self):
        """
            Setup Ansible parameters and ElementSW connection
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            name=dict(required=False, type='str'),
            vlan_tag=dict(required=True, type='str'),
            svip=dict(required=False, type='str'),
            netmask=dict(required=False, type='str'),
            gateway=dict(required=False, type='str'),
            namespace=dict(required=False, type='bool'),
            attributes=dict(required=False, type='dict'),
            address_blocks=dict(required=False, type='list')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.elem = netapp_utils.create_sf_connection(module=self.module)

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        self.elementsw_helper = NaElementSWModule(self.elem)

        # add telemetry attributes
        if self.parameters.get('attributes') is not None:
            self.parameters['attributes'].update(self.elementsw_helper.set_element_attributes(source='na_elementsw_vlan'))
        else:
            self.parameters['attributes'] = self.elementsw_helper.set_element_attributes(source='na_elementsw_vlan')

    def validate_keys(self):
        """
            Validate if all required keys are present before creating
        """
        required_keys = ['address_blocks', 'svip', 'netmask', 'name']
        if all(item in self.parameters.keys() for item in required_keys) is False:
            self.module.fail_json(msg="One or more required fields %s for creating VLAN is missing"
                                      % required_keys)
        addr_blk_fields = ['start', 'size']
        for address in self.parameters['address_blocks']:
            if 'start' not in address or 'size' not in address:
                self.module.fail_json(msg="One or more required fields %s for address blocks is missing"
                                          % addr_blk_fields)

    def create_network(self):
        """
            Add VLAN
        """
        try:
            self.validate_keys()
            create_params = self.parameters.copy()
            for key in ['username', 'hostname', 'password', 'state', 'vlan_tag']:
                del create_params[key]
            self.elem.add_virtual_network(virtual_network_tag=self.parameters['vlan_tag'], **create_params)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error creating VLAN %s"
                                  % self.parameters['vlan_tag'],
                                  exception=to_native(err))

    def delete_network(self):
        """
            Remove VLAN
        """
        try:
            self.elem.remove_virtual_network(virtual_network_tag=self.parameters['vlan_tag'])
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error deleting VLAN %s"
                                  % self.parameters['vlan_tag'],
                                  exception=to_native(err))

    def modify_network(self, modify):
        """
            Modify the VLAN
        """
        try:
            self.elem.modify_virtual_network(virtual_network_tag=self.parameters['vlan_tag'], **modify)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error modifying VLAN %s"
                                  % self.parameters['vlan_tag'],
                                  exception=to_native(err))

    def get_network_details(self):
        """
            Check existing VLANs
            :return: vlan details if found, None otherwise
            :type: dict
        """
        vlans = self.elem.list_virtual_networks(virtual_network_tag=self.parameters['vlan_tag'])
        vlan_details = dict()
        for vlan in vlans.virtual_networks:
            if vlan is not None:
                vlan_details['name'] = vlan.name
                vlan_details['address_blocks'] = list()
                for address in vlan.address_blocks:
                    vlan_details['address_blocks'].append({
                        'start': address.start,
                        'size': address.size
                    })
                vlan_details['svip'] = vlan.svip
                vlan_details['gateway'] = vlan.gateway
                vlan_details['netmask'] = vlan.netmask
                vlan_details['namespace'] = vlan.namespace
                vlan_details['attributes'] = vlan.attributes
                return vlan_details
        return None

    def apply(self):
        """
            Call create / delete / modify vlan methods
        """
        network = self.get_network_details()
        # calling helper to determine action
        cd_action = self.na_helper.get_cd_action(network, self.parameters)
        modify = self.na_helper.get_modified_attributes(network, self.parameters)
        if cd_action == "create":
            self.create_network()
        elif cd_action == "delete":
            self.delete_network()
        elif modify:
            self.modify_network(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """ Apply vlan actions """
    network_obj = ElementSWVlan()
    network_obj.apply()


if __name__ == '__main__':
    main()
