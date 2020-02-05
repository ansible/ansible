#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_service_processor_network
short_description: NetApp ONTAP service processor network
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Modify a ONTAP service processor network
options:
  state:
    description:
    - Whether the specified service processor network should exist or not.
    choices: ['present']
    default: present
  address_type:
    description:
    - Specify address class.
    required: true
    choices: ['ipv4', 'ipv6']
  is_enabled:
    description:
    - Specify whether to enable or disable the service processor network.
    required: true
    type: bool
  node:
    description:
    - The node where the service processor network should be enabled
    required: true
  dhcp:
    description:
    - Specify dhcp type.
    choices: ['v4', 'none']
  gateway_ip_address:
    description:
    - Specify the gateway ip.
  ip_address:
    description:
    - Specify the service processor ip address.
  netmask:
    description:
    - Specify the service processor netmask.
  prefix_length:
    description:
    - Specify the service processor prefix_length.
  wait_for_completion:
    description:
    - Set this parameter to 'true' for synchronous execution (wait until SP status is successfully updated)
    - Set this parameter to 'false' for asynchronous execution
    - For asynchronous, execution exits as soon as the request is sent, without checking SP status
    type: bool
    default: false
    version_added: '2.8'
'''

EXAMPLES = """
    - name: Modify Service Processor Network
      na_ontap_service_processor_network:
        state: present
        address_type: ipv4
        is_enabled: true
        dhcp: v4
        node: "{{ netapp_node }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
import time

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapServiceProcessorNetwork(object):
    """
        Modify a Service Processor Network
    """

    def __init__(self):
        """
            Initialize the NetAppOntapServiceProcessorNetwork class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            address_type=dict(required=True, choices=['ipv4', 'ipv6']),
            is_enabled=dict(required=True, type='bool'),
            node=dict(required=True, type='str'),
            dhcp=dict(required=False, choices=['v4', 'none']),
            gateway_ip_address=dict(required=False, type='str'),
            ip_address=dict(required=False, type='str'),
            netmask=dict(required=False, type='str'),
            prefix_length=dict(required=False, type='int'),
            wait_for_completion=dict(required=False, type='bool', default=False)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=None)
        return

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'address_type': 'address-type',
            'node': 'node',
            'dhcp': 'dhcp',
            'gateway_ip_address': 'gateway-ip-address',
            'ip_address': 'ip-address',
            'netmask': 'netmask'
        }
        self.na_helper.zapi_int_keys = {
            'prefix_length': 'prefix-length'
        }
        self.na_helper.zapi_bool_keys = {
            'is_enabled': 'is-enabled',
        }
        self.na_helper.zapi_required = {
            'address_type': 'address-type',
            'node': 'node',
            'is_enabled': 'is-enabled'
        }

    def get_sp_network_status(self):
        """
        Return status of service processor network
        :param:
            name : name of the node
        :return: Status of the service processor network
        :rtype: dict
        """
        spn_get_iter = netapp_utils.zapi.NaElement('service-processor-network-get-iter')
        query_info = {
            'query': {
                'service-processor-network-info': {
                    'node': self.parameters['node'],
                    'address-type': self.parameters['address_type']
                }
            }
        }
        spn_get_iter.translate_struct(query_info)
        result = self.server.invoke_successfully(spn_get_iter, True)
        if int(result['num-records']) >= 1:
            sp_attr_info = result['attributes-list']['service-processor-network-info']
            return sp_attr_info.get_child_content('setup-status')
        return None

    def get_service_processor_network(self):
        """
        Return details about service processor network
        :param:
            name : name of the node
        :return: Details about service processor network. None if not found.
        :rtype: dict
        """
        spn_get_iter = netapp_utils.zapi.NaElement('service-processor-network-get-iter')
        query_info = {
            'query': {
                'service-processor-network-info': {
                    'node': self.parameters['node']
                }
            }
        }
        spn_get_iter.translate_struct(query_info)
        result = self.server.invoke_successfully(spn_get_iter, True)
        sp_details = None
        # check if job exists
        if int(result['num-records']) >= 1:
            sp_details = dict()
            sp_attr_info = result['attributes-list']['service-processor-network-info']
            for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
                sp_details[item_key] = sp_attr_info.get_child_content(zapi_key)
            for item_key, zapi_key in self.na_helper.zapi_bool_keys.items():
                sp_details[item_key] = self.na_helper.get_value_for_bool(from_zapi=True,
                                                                         value=sp_attr_info.get_child_content(zapi_key))
            for item_key, zapi_key in self.na_helper.zapi_int_keys.items():
                sp_details[item_key] = self.na_helper.get_value_for_int(from_zapi=True,
                                                                        value=sp_attr_info.get_child_content(zapi_key))
        return sp_details

    def modify_service_processor_network(self, params=None):
        """
        Modify a service processor network.
        :param params: A dict of modified options.
        When dhcp is not set to v4, ip_address, netmask, and gateway_ip_address must be specified even if remains the same.
        """
        if self.parameters['is_enabled'] is False:
            if params.get('is_enabled') and len(params) > 1:
                self.module.fail_json(msg='Error: Cannot modify any other parameter for a service processor network if option "is_enabled" is set to false.')
            elif params.get('is_enabled') is None and len(params) > 0:
                self.module.fail_json(msg='Error: Cannot modify a service processor network if it is disabled.')

        sp_modify = netapp_utils.zapi.NaElement('service-processor-network-modify')
        sp_modify.add_new_child("node", self.parameters['node'])
        sp_modify.add_new_child("address-type", self.parameters['address_type'])
        sp_attributes = dict()
        for item_key in self.parameters:
            if item_key in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(item_key)
                sp_attributes[zapi_key] = self.parameters[item_key]
            elif item_key in self.na_helper.zapi_bool_keys:
                zapi_key = self.na_helper.zapi_bool_keys.get(item_key)
                sp_attributes[zapi_key] = self.na_helper.get_value_for_bool(from_zapi=False, value=self.parameters[item_key])
            elif item_key in self.na_helper.zapi_int_keys:
                zapi_key = self.na_helper.zapi_int_keys.get(item_key)
                sp_attributes[zapi_key] = self.na_helper.get_value_for_int(from_zapi=False, value=self.parameters[item_key])
        sp_modify.translate_struct(sp_attributes)
        try:
            self.server.invoke_successfully(sp_modify, enable_tunneling=True)
            if self.parameters.get('wait_for_completion'):
                retries = 10
                while self.get_sp_network_status() == 'in_progress' and retries > 0:
                    time.sleep(10)
                    retries = retries - 1
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying service processor network: %s' % (to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_service_processor_network", cserver)

    def apply(self):
        """
        Run Module based on play book
        """
        self.autosupport_log()
        current = self.get_service_processor_network()
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if not current:
            self.module.fail_json(msg='Error No Service Processor for node: %s' % self.parameters['node'])
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                self.modify_service_processor_network(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Create the NetApp Ontap Service Processor Network Object and modify it
    """

    obj = NetAppOntapServiceProcessorNetwork()
    obj.apply()


if __name__ == '__main__':
    main()
