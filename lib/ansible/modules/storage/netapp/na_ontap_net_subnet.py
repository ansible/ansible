#!/usr/bin/python

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = """
module: na_ontap_net_subnet
short_description: NetApp ONTAP Create, delete, modify network subnets.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author:  Storage Engineering (@Albinpopote) <ansible@black-perl.fr>
description:
- Create, modify, destroy the network subnet
options:
  state:
    description:
    - Whether the specified network interface group should exist or not.
    choices: ['present', 'absent']
    default: present

  broadcast_domain:
    description:
    - Specify the required broadcast_domain name for the subnet.
    - A broadcast domain can not be modified after the subnet has been created
    required: true

  name:
    description:
    - Specify the subnet name.
    required: true

  from_name:
    description:
    - Name of the subnet to be renamed

  gateway:
    description:
    - Specify the gateway for the default route of the subnet.

  ipspace:
    description:
    - Specify the ipspace for the subnet.
    - The default value for this parameter is the default IPspace, named 'Default'.

  ip_ranges:
    description:
    - Specify the list of IP address ranges associated with the subnet.

  subnet:
    description:
    - Specify the subnet (ip and mask).
    required: true
"""

EXAMPLES = """
    - name: create subnet
      na_ontap_net_subnet:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        subnet: 10.10.10.0/24
        name: subnet-adm
        ip_ranges: [ '10.10.10.30-10.10.10.40', '10.10.10.51' ]
        gateway: 10.10.10.254
        ipspace: Default
        broadcast_domain: Default
    - name: delete subnet
      na_ontap_net_subnet:
        state: absent
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: subnet-adm
        ipspace: Default
    - name: rename subnet
      na_ontap_net_subnet:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: subnet-adm-new
        from_name: subnet-adm
        ipspace: Default
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSubnet(object):
    """
    Create, Modifies and Destroys a subnet
    """
    def __init__(self):
        """
        Initialize the ONTAP Subnet class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            broadcast_domain=dict(required=False, type='str'),
            gateway=dict(required=False, type='str'),
            ip_ranges=dict(required=False, type=list),
            ipspace=dict(required=False, type='str'),
            subnet=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_subnet(self, name=None):
        """
        Return details about the subnet
        :param:
            name : Name of the subnet
        :return: Details about the subnet. None if not found.
        :rtype: dict
        """
        if name is None:
            name = self.parameters.get('name')

        subnet_iter = netapp_utils.zapi.NaElement('net-subnet-get-iter')
        subnet_info = netapp_utils.zapi.NaElement('net-subnet-info')
        subnet_info.add_new_child('subnet-name', name)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(subnet_info)

        subnet_iter.add_child_elem(query)

        result = self.server.invoke_successfully(subnet_iter, True)

        return_value = None
        # check if query returns the expected subnet
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            subnet_attributes = result.get_child_by_name('attributes-list').get_child_by_name('net-subnet-info')
            broadcast_domain = subnet_attributes.get_child_content('broadcast-domain')
            gateway = subnet_attributes.get_child_content('gateway')
            ipspace = subnet_attributes.get_child_content('ipspace')
            subnet = subnet_attributes.get_child_content('subnet')
            name = subnet_attributes.get_child_content('subnet-name')

            ip_ranges = []
            range_obj = subnet_attributes.get_child_by_name('ip-ranges').get_children()
            for elem in range_obj:
                ip_ranges.append(elem.get_content())

            return_value = {
                'name': name,
                'broadcast_domain': broadcast_domain,
                'gateway': gateway,
                'ip_ranges': ip_ranges,
                'ipspace': ipspace,
                'subnet': subnet
            }

        return return_value

    def create_subnet(self):
        """
        Creates a new subnet
        """
        options = {'subnet-name': self.parameters.get('name'),
                   'broadcast-domain': self.parameters.get('broadcast_domain'),
                   'subnet': self.parameters.get('subnet')}
        subnet_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-subnet-create', **options)

        if self.parameters.get('gateway'):
            subnet_create.add_new_child('gateway', self.parameters.get('gateway'))
        if self.parameters.get('ip_ranges'):
            subnet_ips = netapp_utils.zapi.NaElement('ip-ranges')
            subnet_create.add_child_elem(subnet_ips)
            for ip_range in self.parameters.get('ip_ranges'):
                subnet_ips.add_new_child('ip-range', ip_range)
        if self.parameters.get('ipspace'):
            subnet_create.add_new_child('ipspace', self.parameters.get('ipspace'))

        try:
            self.server.invoke_successfully(subnet_create, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating subnet %s: %s' % (self.parameters.get('name'), to_native(error)),
                                  exception=traceback.format_exc())

    def delete_subnet(self):
        """
        Deletes a subnet
        """
        subnet_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-subnet-destroy', **{'subnet-name': self.parameters.get('name')})

        try:
            self.server.invoke_successfully(subnet_delete, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting subnet %s: %s' % (self.parameters.get('name'), to_native(error)),
                                  exception=traceback.format_exc())

    def modify_subnet(self):
        """
        Modifies a subnet
        """
        options = {'subnet-name': self.parameters.get('name')}

        subnet_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-subnet-modify', **options)

        if self.parameters.get('gateway'):
            subnet_modify.add_new_child('gateway', self.parameters.get('gateway'))
        if self.parameters.get('ip_ranges'):
            subnet_ips = netapp_utils.zapi.NaElement('ip-ranges')
            subnet_modify.add_child_elem(subnet_ips)
            for ip_range in self.parameters.get('ip_ranges'):
                subnet_ips.add_new_child('ip-range', ip_range)
        if self.parameters.get('ipspace'):
            subnet_modify.add_new_child('ipspace', self.parameters.get('ipspace'))
        if self.parameters.get('subnet'):
            subnet_modify.add_new_child('subnet', self.parameters.get('subnet'))

        try:
            self.server.invoke_successfully(subnet_modify, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying subnet %s: %s' % (self.parameters.get('name'), to_native(error)),
                                  exception=traceback.format_exc())

    def rename_subnet(self):
        """
        TODO
        """
        options = {'subnet-name': self.parameters.get('from_name'),
                   'new-name': self.parameters.get('name')}

        subnet_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-subnet-rename', **options)

        if self.parameters.get('ipspace'):
            subnet_rename.add_new_child('ipspace', self.parameters.get('ipspace'))

        try:
            self.server.invoke_successfully(subnet_rename, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming subnet %s: %s' % (self.parameters.get('name'), to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Apply action to subnet'''
        current = self.get_subnet()
        cd_action, rename = None, None

        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_subnet(self.parameters.get('from_name')), current)
            if rename is False:
                self.module.fail_json(msg="Error renaming: subnet %s does not exist" %
                                      self.parameters.get('from_name'))
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)

        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        for attribute in modify:
            if attribute in ['broadcast_domain']:
                self.module.fail_json(msg='Error modifying subnet %s: cannot modify broadcast_domain parameter.' % self.parameters.get('name'))

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_subnet()
                # If rename is True, cd_action is NOne but modify could be true
                if cd_action == 'create':
                    for attribute in ['subnet', 'broadcast_domain']:
                        if not self.parameters.get(attribute):
                            self.module.fail_json(msg='Error - missing required arguments: %s.' % attribute)
                    self.create_subnet()
                elif cd_action == 'delete':
                    self.delete_subnet()
                elif modify:
                    self.modify_subnet()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates the NetApp ONTAP Net Route object and runs the correct play task
    """
    subnet_obj = NetAppOntapSubnet()
    subnet_obj.apply()


if __name__ == '__main__':
    main()
