#!/usr/bin/python
""" this is interface module

 (c) 2018-2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified'
}

DOCUMENTATION = '''
---

module: na_ontap_interface
short_description: NetApp ONTAP LIF configuration

extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Creating / deleting and modifying the LIF.

options:
  state:
    description:
    - Whether the specified interface should exist or not.
    choices: ['present', 'absent']
    default: present

  interface_name:
    description:
    - Specifies the logical interface (LIF) name.
    required: true

  home_node:
    description:
    - Specifies the LIF's home node.
    - By default, the first node from the cluster is considered as home node

  home_port:
    description:
    - Specifies the LIF's home port.
    - Required when C(state=present)

  role:
    description:
    - Specifies the role of the LIF.
    - When setting role as "intercluster", setting protocol is not supported.
    - Required when C(state=present).

  address:
    description:
    - Specifies the LIF's IP address.
    - Required when C(state=present)

  netmask:
    description:
    - Specifies the LIF's netmask.
    - Required when C(state=present).

  vserver:
    description:
    - The name of the vserver to use.
    required: true

  firewall_policy:
    description:
    - Specifies the firewall policy for the LIF.

  failover_policy:
    choices: ['disabled', 'system-defined', 'local-only', 'sfo-partner-only', 'broadcast-domain-wide']
    description:
    - Specifies the failover policy for the LIF.

  subnet_name:
    description:
    - Subnet where the interface address is allocated from.
      If the option is not used, the IP address will need to be provided by
      the administrator during configuration.
    version_added: '2.8'

  admin_status:
    choices: ['up', 'down']
    description:
    - Specifies the administrative status of the LIF.

  is_auto_revert:
    description:
       If true, data LIF will revert to its home node under certain circumstances such as startup, and load balancing
       migration capability is disabled automatically
    type: bool

  force_subnet_association:
    description:
       Set this to true to acquire the address from the named subnet and assign the subnet to the LIF.
    type: bool
    version_added: '2.9'

  protocols:
    description:
    - Specifies the list of data protocols configured on the LIF. By default, the values in this element are nfs, cifs and fcache.
    - Other supported protocols are iscsi and fcp. A LIF can be configured to not support any data protocols by specifying 'none'.
    - Protocol values of none, iscsi, fc-nvme or fcp can't be combined with any other data protocol(s).
    - address, netmask and firewall_policy parameters are not supported for 'fc-nvme' option.

  dns_domain_name:
    description:
    - Specifies the unique, fully qualified domain name of the DNS zone of this LIF.
    type: str
    version_added: '2.9'

  listen_for_dns_query:
    description:
    - If True, this IP address will listen for DNS queries for the dnszone specified.
    type: bool
    version_added: '2.9'

  is_dns_update_enabled:
    description:
    - Specifies if DNS update is enabled for this LIF. Dynamic updates will be sent for this LIF if updates are enabled at Vserver level.
    type: bool
    version_added: '2.9'

'''

EXAMPLES = '''
    - name: Create interface
      na_ontap_interface:
        state: present
        interface_name: data2
        home_port: e0d
        home_node: laurentn-vsim1
        role: data
        protocols: nfs
        admin_status: up
        failover_policy: local-only
        firewall_policy: mgmt
        is_auto_revert: true
        address: 10.10.10.10
        netmask: 255.255.255.0
        force_subnet_association: false
        dns_domain_name: test.com
        listen_for_dns_query: true
        is_dns_update_enabled: true
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete interface
      na_ontap_interface:
        state: absent
        interface_name: data2
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

'''

RETURN = """

"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapInterface(object):
    ''' object to describe  interface info '''
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            interface_name=dict(required=True, type='str'),
            home_node=dict(required=False, type='str', default=None),
            home_port=dict(required=False, type='str'),
            role=dict(required=False, type='str'),
            address=dict(required=False, type='str'),
            netmask=dict(required=False, type='str'),
            vserver=dict(required=True, type='str'),
            firewall_policy=dict(required=False, type='str', default=None),
            failover_policy=dict(required=False, type='str', default=None,
                                 choices=['disabled', 'system-defined',
                                          'local-only', 'sfo-partner-only', 'broadcast-domain-wide']),
            admin_status=dict(required=False, choices=['up', 'down']),
            subnet_name=dict(required=False, type='str'),
            is_auto_revert=dict(required=False, type='bool', default=None),
            protocols=dict(required=False, type='list'),
            force_subnet_association=dict(required=False, type='bool', default=None),
            dns_domain_name=dict(required=False, type='str'),
            listen_for_dns_query=dict(required=False, type='bool'),
            is_dns_update_enabled=dict(required=False, type='bool')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            mutually_exclusive=[
                ['subnet_name', 'address'],
                ['subnet_name', 'netmask']
            ],

            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_interface(self):
        """
        Return details about the interface
        :param:
            name : Name of the name of the interface

        :return: Details about the interface. None if not found.
        :rtype: dict
        """
        interface_info = netapp_utils.zapi.NaElement('net-interface-get-iter')
        interface_attributes = netapp_utils.zapi.NaElement('net-interface-info')
        interface_attributes.add_new_child('interface-name', self.parameters['interface_name'])
        interface_attributes.add_new_child('vserver', self.parameters['vserver'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(interface_attributes)
        interface_info.add_child_elem(query)
        result = self.server.invoke_successfully(interface_info, True)
        return_value = None
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            interface_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('net-interface-info')
            return_value = {
                'interface_name': self.parameters['interface_name'],
                'admin_status': interface_attributes['administrative-status'],
                'home_port': interface_attributes['home-port'],
                'home_node': interface_attributes['home-node'],
                'failover_policy': interface_attributes['failover-policy'].replace('_', '-'),
                'is_auto_revert': True if interface_attributes['is-auto-revert'] == 'true' else False,
            }
            if interface_attributes.get_child_by_name('address'):
                return_value['address'] = interface_attributes['address']
            if interface_attributes.get_child_by_name('netmask'):
                return_value['netmask'] = interface_attributes['netmask']
            if interface_attributes.get_child_by_name('firewall-policy'):
                return_value['firewall_policy'] = interface_attributes['firewall-policy']
            if interface_attributes.get_child_by_name('dns-domain-name') != 'none':
                return_value['dns_domain_name'] = interface_attributes['dns-domain-name']
            else:
                return_value['dns_domain_name'] = None
            if interface_attributes.get_child_by_name('listen-for-dns-query'):
                return_value['listen_for_dns_query'] = self.na_helper.get_value_for_bool(True, interface_attributes['listen-for-dns-query'])
            if interface_attributes.get_child_by_name('is-dns-update-enabled'):
                return_value['is_dns_update_enabled'] = self.na_helper.get_value_for_bool(True, interface_attributes['is-dns-update-enabled'])
        return return_value

    @staticmethod
    def set_options(options, parameters):
        """ set attributes for create or modify """
        if parameters.get('home_port') is not None:
            options['home-port'] = parameters['home_port']
        if parameters.get('subnet_name') is not None:
            options['subnet-name'] = parameters['subnet_name']
        if parameters.get('address') is not None:
            options['address'] = parameters['address']
        if parameters.get('netmask') is not None:
            options['netmask'] = parameters['netmask']
        if parameters.get('failover_policy') is not None:
            options['failover-policy'] = parameters['failover_policy']
        if parameters.get('firewall_policy') is not None:
            options['firewall-policy'] = parameters['firewall_policy']
        if parameters.get('is_auto_revert') is not None:
            options['is-auto-revert'] = 'true' if parameters['is_auto_revert'] is True else 'false'
        if parameters.get('admin_status') is not None:
            options['administrative-status'] = parameters['admin_status']
        if parameters.get('force_subnet_association') is not None:
            options['force-subnet-association'] = 'true' if parameters['force_subnet_association'] else 'false'
        if parameters.get('dns_domain_name') is not None:
            options['dns-domain-name'] = parameters['dns_domain_name']
        if parameters.get('listen_for_dns_query') is not None:
            options['listen-for-dns-query'] = str(parameters['listen_for_dns_query'])
        if parameters.get('is_dns_update_enabled') is not None:
            options['is-dns-update-enabled'] = str(parameters['is_dns_update_enabled'])

    def set_protocol_option(self, required_keys):
        """ set protocols for create """
        if self.parameters.get('protocols') is not None:
            data_protocols_obj = netapp_utils.zapi.NaElement('data-protocols')
            for protocol in self.parameters.get('protocols'):
                if protocol.lower() in ['fc-nvme', 'fcp']:
                    if 'address' in required_keys:
                        required_keys.remove('address')
                    if 'home_port' in required_keys:
                        required_keys.remove('home_port')
                    if 'netmask' in required_keys:
                        required_keys.remove('netmask')
                    not_required_params = set(['address', 'netmask', 'firewall_policy'])
                    if not not_required_params.isdisjoint(set(self.parameters.keys())):
                        self.module.fail_json(msg='Error: Following parameters for creating interface are not supported'
                                                  ' for data-protocol fc-nvme: %s' % ', '.join(not_required_params))
                data_protocols_obj.add_new_child('data-protocol', protocol)
            return data_protocols_obj
        return None

    def get_home_node_for_cluster(self):
        ''' get the first node name from this cluster '''
        get_node = netapp_utils.zapi.NaElement('cluster-node-get-iter')
        attributes = {
            'query': {
                'cluster-node-info': {}
            }
        }
        get_node.translate_struct(attributes)
        try:
            result = self.server.invoke_successfully(get_node, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error fetching node for interface %s: %s' %
                                  (self.parameters['interface_name'], to_native(exc)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            attributes = result.get_child_by_name('attributes-list')
            return attributes.get_child_by_name('cluster-node-info').get_child_content('node-name')
        return None

    def validate_create_parameters(self, keys):
        '''
            Validate if required parameters for create are present.
            Parameter requirement might vary based on given data-protocol.
            :return: None
        '''
        if self.parameters.get('home_node') is None:
            node = self.get_home_node_for_cluster()
            if node is not None:
                self.parameters['home_node'] = node
        # validate if mandatory parameters are present for create
        if not keys.issubset(set(self.parameters.keys())) and self.parameters.get('subnet_name') is None:
            self.module.fail_json(msg='Error: Missing one or more required parameters for creating interface: %s'
                                      % ', '.join(keys))
        # if role is intercluster, protocol cannot be specified
        if self.parameters['role'] == "intercluster" and self.parameters.get('protocols') is not None:
            self.module.fail_json(msg='Error: Protocol cannot be specified for intercluster role,'
                                      'failed to create interface')

    def create_interface(self):
        ''' calling zapi to create interface '''
        required_keys = set(['role', 'home_port'])
        data_protocols_obj = None
        if self.parameters.get('subnet_name') is None:
            required_keys.add('address')
            required_keys.add('netmask')
        data_protocols_obj = self.set_protocol_option(required_keys)
        self.validate_create_parameters(required_keys)

        options = {'interface-name': self.parameters['interface_name'],
                   'role': self.parameters['role'],
                   'home-node': self.parameters.get('home_node'),
                   'vserver': self.parameters['vserver']}
        NetAppOntapInterface.set_options(options, self.parameters)
        interface_create = netapp_utils.zapi.NaElement.create_node_with_children('net-interface-create', **options)
        if data_protocols_obj is not None:
            interface_create.add_child_elem(data_protocols_obj)
        try:
            self.server.invoke_successfully(interface_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error Creating interface %s: %s' %
                                  (self.parameters['interface_name'], to_native(exc)), exception=traceback.format_exc())

    def delete_interface(self, current_status):
        ''' calling zapi to delete interface '''
        if current_status == 'up':
            self.parameters['admin_status'] = 'down'
            self.modify_interface({'admin_status': 'down'})

        interface_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-interface-delete', **{'interface-name': self.parameters['interface_name'],
                                       'vserver': self.parameters['vserver']})
        try:
            self.server.invoke_successfully(interface_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error deleting interface %s: %s' % (self.parameters['interface_name'], to_native(exc)),
                                  exception=traceback.format_exc())

    def modify_interface(self, modify):
        """
        Modify the interface.
        """
        options = {'interface-name': self.parameters['interface_name'],
                   'vserver': self.parameters['vserver']
                   }
        NetAppOntapInterface.set_options(options, modify)
        interface_modify = netapp_utils.zapi.NaElement.create_node_with_children('net-interface-modify', **options)
        try:
            self.server.invoke_successfully(interface_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as err:
            self.module.fail_json(msg='Error modifying interface %s: %s' % (self.parameters['interface_name'],
                                  to_native(err)), exception=traceback.format_exc())

    def autosupport_log(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_interface", cserver)

    def apply(self):
        ''' calling all interface features '''
        self.autosupport_log()
        current = self.get_interface()
        # rename and create are mutually exclusive
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_interface()
                elif cd_action == 'delete':
                    self.delete_interface(current['admin_status'])
                elif modify:
                    self.modify_interface(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    interface = NetAppOntapInterface()
    interface.apply()


if __name__ == '__main__':
    main()
