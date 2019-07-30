#!/usr/bin/python
''' This is an Ansible module for ONTAP to manage ports for various resources.

 (c) 2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''

module: na_ontap_ports
short_description: NetApp ONTAP add/remove ports
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Add or remove ports for broadcast domain and portset.

options:
  state:
    description:
    - Whether the specified port should be added or removed.
    choices: ['present', 'absent']
    default: present
    type: str

  vserver:
    description:
      - Name of the SVM.
      - Specify this option when operating on portset.
    type: str

  names:
    description:
    - List of ports.
    type: list
    required: true

  resource_name:
    description:
    - name of the portset or broadcast domain.
    type: str
    required: true

  resource_type:
    description:
    - type of the resource to add a port to or remove a port from.
    choices: ['broadcast_domain', 'portset']
    required: true
    type: str

  ipspace:
    description:
    - Specify the required ipspace for the broadcast domain.
    - A domain ipspace can not be modified after the domain has been created.
    type: str

  portset_type:
    description:
    - Protocols accepted for portset.
    choices: ['fcp', 'iscsi', 'mixed']
    type: str

'''

EXAMPLES = '''

    - name: broadcast domain remove port
      tags:
      - remove
      na_ontap_ports:
        state: absent
        names: test-vsim1:e0d-1,test-vsim1:e0d-2
        resource_type: broadcast_domain
        resource_name: ansible_domain
        hostname: "{{ hostname }}"
        username: user
        password: password
        https: False

    - name: broadcast domain add port
      tags:
      - add
      na_ontap_ports:
        state: present
        names: test-vsim1:e0d-1,test-vsim1:e0d-2
        resource_type: broadcast_domain
        resource_name: ansible_domain
        ipspace: Default
        hostname: "{{ hostname }}"
        username: user
        password: password
        https: False

    - name: portset remove port
      tags:
      - remove
      na_ontap_ports:
        state: absent
        names: lif_2
        resource_type: portset
        resource_name: portset_1
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: user
        password: password
        https: False

    - name: portset add port
      tags:
      - add
      na_ontap_ports:
        state: present
        names: lif_2
        resource_type: portset
        resource_name: portset_1
        portset_type: iscsi
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: user
        password: password
        https: False

'''

RETURN = '''
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapPorts(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=False, type='str'),
            names=dict(required=True, type='list'),
            resource_name=dict(required=True, type='str'),
            resource_type=dict(required=True, type='str', choices=['broadcast_domain', 'portset']),
            ipspace=dict(required=False, type='str'),
            portset_type=dict(required=False, type='str', choices=['fcp', 'iscsi', 'mixed']),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('resource_type', 'portset', ['vserver']),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            if self.parameters['resource_type'] == 'broadcast_domain':
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
            elif self.parameters['resource_type'] == 'portset':
                self.server = netapp_utils.setup_na_ontap_zapi(
                    module=self.module, vserver=self.parameters['vserver'])

    def add_broadcast_domain_ports(self, ports):
        """
        Add broadcast domain ports
        :param: ports to be added.
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-add-ports')
        domain_obj.add_new_child("broadcast-domain", self.parameters['resource_name'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        ports_obj = netapp_utils.zapi.NaElement('ports')
        domain_obj.add_child_elem(ports_obj)
        for port in ports:
            ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding port for broadcast domain %s: %s' %
                                  (self.parameters['resource_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def remove_broadcast_domain_ports(self, ports):
        """
        Deletes broadcast domain ports
        :param: ports to be removed.
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-remove-ports')
        domain_obj.add_new_child("broadcast-domain", self.parameters['resource_name'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        ports_obj = netapp_utils.zapi.NaElement('ports')
        domain_obj.add_child_elem(ports_obj)
        for port in ports:
            ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing port for broadcast domain %s: %s' %
                                  (self.parameters['resource_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def get_broadcast_domain_ports(self):
        """
        Return details about the broadcast domain ports.
        :return: Details about the broadcast domain ports. [] if not found.
        :rtype: list
        """
        domain_get_iter = netapp_utils.zapi.NaElement('net-port-broadcast-domain-get-iter')
        broadcast_domain_info = netapp_utils.zapi.NaElement('net-port-broadcast-domain-info')
        broadcast_domain_info.add_new_child('broadcast-domain', self.parameters['resource_name'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(broadcast_domain_info)
        domain_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(domain_get_iter, True)
        ports = []
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            domain_info = result.get_child_by_name('attributes-list').get_child_by_name('net-port-broadcast-domain-info')
            domain_ports = domain_info.get_child_by_name('ports')
            if domain_ports is not None:
                ports = [port.get_child_content('port') for port in domain_ports.get_children()]
        return ports

    def remove_portset_ports(self, port):
        """
        Removes all existing ports from portset
        :return: None
        """
        options = {'portset-name': self.parameters['resource_name'],
                   'portset-port-name': port.strip()}

        portset_modify = netapp_utils.zapi.NaElement.create_node_with_children('portset-remove', **options)

        try:
            self.server.invoke_successfully(portset_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing port in portset %s: %s' %
                                      (self.parameters['resource_name'], to_native(error)), exception=traceback.format_exc())

    def add_portset_ports(self, port):
        """
        Add the list of ports to portset
        :return: None
        """
        options = {'portset-name': self.parameters['resource_name'],
                   'portset-port-name': port.strip()}

        portset_modify = netapp_utils.zapi.NaElement.create_node_with_children('portset-add', **options)

        try:
            self.server.invoke_successfully(portset_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding port in portset %s: %s' %
                                      (self.parameters['resource_name'], to_native(error)), exception=traceback.format_exc())

    def portset_get_iter(self):
        """
        Compose NaElement object to query current portset using vserver, portset-name and portset-type parameters
        :return: NaElement object for portset-get-iter with query
        """
        portset_get = netapp_utils.zapi.NaElement('portset-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        portset_info = netapp_utils.zapi.NaElement('portset-info')
        portset_info.add_new_child('vserver', self.parameters['vserver'])
        portset_info.add_new_child('portset-name', self.parameters['resource_name'])
        if self.parameters.get('portset_type'):
            portset_info.add_new_child('portset-type', self.parameters['portset_type'])
        query.add_child_elem(portset_info)
        portset_get.add_child_elem(query)
        return portset_get

    def portset_get(self):
        """
        Get current portset info
        :return: List of current ports if query successful, else return []
        """
        portset_get_iter = self.portset_get_iter()
        result, ports = None, []
        try:
            result = self.server.invoke_successfully(portset_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching portset %s: %s'
                                      % (self.parameters['resource_name'], to_native(error)),
                                  exception=traceback.format_exc())
        # return portset details
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            portset_get_info = result.get_child_by_name('attributes-list').get_child_by_name('portset-info')
            if int(portset_get_info.get_child_content('portset-port-total')) > 0:
                port_info = portset_get_info.get_child_by_name('portset-port-info')
                ports = [port.get_content() for port in port_info.get_children()]
        return ports

    def modify_broadcast_domain_ports(self):
        """
        compare current and desire ports. Call add or remove ports methods if needed.
        :return: None.
        """
        current_ports = self.get_broadcast_domain_ports()
        cd_ports = self.parameters['names']
        if self.parameters['state'] == 'present':
            ports_to_add = [port for port in cd_ports if port not in current_ports]
            if len(ports_to_add) > 0:
                self.add_broadcast_domain_ports(ports_to_add)
                self.na_helper.changed = True

        if self.parameters['state'] == 'absent':
            ports_to_remove = [port for port in cd_ports if port in current_ports]
            if len(ports_to_remove) > 0:
                self.remove_broadcast_domain_ports(ports_to_remove)
                self.na_helper.changed = True

    def modify_portset_ports(self):
        current_ports = self.portset_get()
        cd_ports = self.parameters['names']
        if self.parameters['state'] == 'present':
            ports_to_add = [port for port in cd_ports if port not in current_ports]
            if len(ports_to_add) > 0:
                for port in ports_to_add:
                    self.add_portset_ports(port)
                self.na_helper.changed = True

        if self.parameters['state'] == 'absent':
            ports_to_remove = [port for port in cd_ports if port in current_ports]
            if len(ports_to_remove) > 0:
                for port in ports_to_remove:
                    self.remove_portset_ports(port)
                self.na_helper.changed = True

    def apply(self):
        self.asup_log_for_cserver("na_ontap_ports")
        if self.parameters['resource_type'] == 'broadcast_domain':
            self.modify_broadcast_domain_ports()
        elif self.parameters['resource_type'] == 'portset':
            self.modify_portset_ports()
        self.module.exit_json(changed=self.na_helper.changed)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)


def main():
    portset_obj = NetAppOntapPorts()
    portset_obj.apply()


if __name__ == '__main__':
    main()
