#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_service_processor_network
short_description: Manage NetApp Ontap service processor network
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com)
description:
- Modify a Ontap service processor network
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
    choices: ['true', 'false']
  node:
    description:
    - The node where the the service processor network should be enabled
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
'''

EXAMPLES = """
    - name: Modify Service Processor Network
      na_ontap_service_processor_network:
        state=present
        address_type=ipv4
        is_enabled=true
        dhcp=v4
        node=FPaaS-A300-01
        node={{ netapp_node }}
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

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
            is_enabled=dict(required=True, choices=['true', 'false']),
            node=dict(required=True, type='str'),
            dhcp=dict(required=False, choices=['v4', 'none']),
            gateway_ip_address=dict(required=False, type='str'),
            ip_address=dict(required=False, type='str'),
            netmask=dict(required=False, type='str'),
            prefix_length=dict(required=False, type='int'),

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.address_type = parameters['address_type']
        self.dhcp = parameters['dhcp']
        self.gateway_ip_address = parameters['gateway_ip_address']
        self.ip_address = parameters['ip_address']
        self.is_enabled = parameters['is_enabled']
        self.netmask = parameters['netmask']
        self.node = parameters['node']
        self.prefix_length = parameters['prefix_length']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=None)
        return

    def get_service_processor_network(self):
        """
        Return details about service processor network
        :param:
            name : name of the vserver
        :return: Details about service processor network. None if not found.
        :rtype: dict
        """
        spn_get_iter = netapp_utils.zapi.NaElement(
            'service-processor-network-get-iter')
        spn_info = netapp_utils.zapi.NaElement(
            'service-processor-network-info')
        spn_info.add_new_child('node', self.node)
        spn_info.add_new_child('address-type', self.address_type)
        spn_info.add_new_child('is-enabled', self.is_enabled)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(spn_info)
        spn_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(spn_get_iter, True)
        sp_network_details = None
        # check if job exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            attributes_list = result.get_child_by_name('attributes-list').\
                get_child_by_name('service-processor-network-info')
            node_value = attributes_list.get_child_content('node')
            address_type_value = attributes_list.get_child_content(
                'address-type')
            dhcp_value = attributes_list.get_child_content('dhcp')
            gateway_ip_address_value = attributes_list.get_child_content(
                'gateway-ip-address')
            ip_address_value = attributes_list.get_child_content('ip-address')
            is_enabled_value = attributes_list.get_child_content('is-enabled')
            netmask_value = attributes_list.get_child_content('netmask')
            prefix_length_value = attributes_list.get_child_content(
                'prefix-length')
            sp_network_details = {
                'node_value': node_value,
                'address_type_value': address_type_value,
                'dhcp_value': dhcp_value,
                'gateway_ip_address_value': gateway_ip_address_value,
                'ip_address_value': ip_address_value,
                'is_enabled_value': is_enabled_value,
                'netmask_value': netmask_value,
                'prefix_length_value': prefix_length_value
            }
        return sp_network_details

    def modify_service_processor_network(self):
        """
        Modify a service processor network
        """
        service_obj = netapp_utils.zapi.NaElement(
            'service-processor-network-modify')
        service_obj.add_new_child("node", self.node)
        service_obj.add_new_child("address-type", self.address_type)
        service_obj.add_new_child("is-enabled", self.is_enabled)

        if self.dhcp:
            service_obj.add_new_child("dhcp", self.dhcp)
        if self.gateway_ip_address:
            service_obj.add_new_child(
                "gateway-ip-address", self.gateway_ip_address)
        if self.ip_address:
            service_obj.add_new_child("ip-address", self.ip_address)
        if self.netmask:
            service_obj.add_new_child("netmask", self.netmask)
        if self.prefix_length is not None:
            service_obj.add_new_child("prefix-length", str(self.prefix_length))

        try:
            result = self.server.invoke_successfully(service_obj,
                                                     enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying \
                                  service processor network: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event(
            "na_ontap_service_processor_network", cserver)
        spn_details = self.get_service_processor_network()
        spn_exists = False
        if spn_details:
            spn_exists = True
            if self.state == 'present':  # modify
                if (self.dhcp and
                    self.dhcp != spn_details['dhcp_value']) or \
                   (self.gateway_ip_address and
                    self.gateway_ip_address != spn_details['gateway_ip_address_value']) or \
                   (self.ip_address and
                    self.ip_address != spn_details['ip_address_value']) or \
                   (self.netmask and
                    self.netmask != spn_details['netmask_value']) or \
                   (self.prefix_length and str(self.prefix_length)
                        != spn_details['prefix_length_value']):
                    changed = True
        else:
            pass
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute modify
                    if spn_exists:
                        self.modify_service_processor_network()
        self.module.exit_json(changed=changed)


def main():
    """
    Create the NetApp Ontap Service Processor Network Object and modify it
    """

    obj = NetAppOntapServiceProcessorNetwork()
    obj.apply()


if __name__ == '__main__':
    main()
