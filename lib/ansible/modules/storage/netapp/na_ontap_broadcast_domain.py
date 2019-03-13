#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_broadcast_domain
short_description: NetApp ONTAP manage broadcast domains.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Modify a ONTAP broadcast domain.
options:
  state:
    description:
    - Whether the specified broadcast domain should exist or not.
    choices: ['present', 'absent']
    default: present
  name:
    description:
    - Specify the broadcast domain name.
    required: true
    aliases:
    - broadcast_domain
  from_name:
    description:
    - Specify the  broadcast domain name to be split into new broadcast domain.
    version_added: "2.8"
  mtu:
    description:
    - Specify the required mtu for the broadcast domain.
  ipspace:
    description:
    - Specify the required ipspace for the broadcast domain.
    - A domain ipspace can not be modified after the domain has been created.
  ports:
    description:
    - Specify the ports associated with this broadcast domain. Should be comma separated.
    - It represents the expected state of a list of ports at any time.
    - Add a port if it is specified in expected state but not in current state.
    - Delete a port if it is specified in current state but not in expected state.
    - For split action, it represents the ports to be split from current broadcast domain and added to the new broadcast domain.
    - if all ports are removed or splited from a broadcast domain, the broadcast domain will be deleted automatically.
'''

EXAMPLES = """
    - name: create broadcast domain
      na_ontap_broadcast_domain:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: ansible_domain
        mtu: 1000
        ipspace: Default
        ports: ["khutton-vsim1:e0d-12", "khutton-vsim1:e0d-13"]
    - name: modify broadcast domain
      na_ontap_broadcast_domain:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: ansible_domain
        mtu: 1100
        ipspace: Default
        ports: ["khutton-vsim1:e0d-12", "khutton-vsim1:e0d-13"]
    - name: split broadcast domain
      na_ontap_broadcast_domain:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        from_name: ansible_domain
        name: new_ansible_domain
        mtu: 1200
        ipspace: Default
        ports: khutton-vsim1:e0d-12
    - name: delete broadcast domain
      na_ontap_broadcast_domain:
        state: absent
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: ansible_domain
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


class NetAppOntapBroadcastDomain(object):
    """
        Create, Modifies and Destroys a Broadcast domain
    """
    def __init__(self):
        """
            Initialize the ONTAP Broadcast Domain class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str', aliases=["broadcast_domain"]),
            ipspace=dict(required=False, type='str'),
            mtu=dict(required=False, type='str'),
            ports=dict(required=False, type='list'),
            from_name=dict(required=False, type='str'),
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

    def get_broadcast_domain(self, broadcast_domain=None):
        """
        Return details about the broadcast domain
        :param broadcast_domain: specific broadcast domain to get.
        :return: Details about the broadcas domain. None if not found.
        :rtype: dict
        """
        if broadcast_domain is None:
            broadcast_domain = self.parameters['name']
        domain_get_iter = netapp_utils.zapi.NaElement('net-port-broadcast-domain-get-iter')
        broadcast_domain_info = netapp_utils.zapi.NaElement('net-port-broadcast-domain-info')
        broadcast_domain_info.add_new_child('broadcast-domain', broadcast_domain)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(broadcast_domain_info)
        domain_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(domain_get_iter, True)
        domain_exists = None
        # check if broadcast_domain exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            domain_info = result.get_child_by_name('attributes-list').\
                get_child_by_name('net-port-broadcast-domain-info')
            domain_name = domain_info.get_child_content('broadcast-domain')
            domain_mtu = domain_info.get_child_content('mtu')
            domain_ipspace = domain_info.get_child_content('ipspace')
            domain_ports = domain_info.get_child_by_name('ports')
            if domain_ports is not None:
                ports = [port.get_child_content('port') for port in domain_ports.get_children()]
            else:
                ports = []
            domain_exists = {
                'domain-name': domain_name,
                'mtu': domain_mtu,
                'ipspace': domain_ipspace,
                'ports': ports
            }
        return domain_exists

    def create_broadcast_domain(self):
        """
        Creates a new broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-create')
        domain_obj.add_new_child("broadcast-domain", self.parameters['name'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        if self.parameters.get('mtu'):
            domain_obj.add_new_child("mtu", self.parameters['mtu'])
        if self.parameters.get('ports'):
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in self.parameters['ports']:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating broadcast domain %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_broadcast_domain(self, broadcast_domain=None):
        """
        Deletes a broadcast domain
        """
        if broadcast_domain is None:
            broadcast_domain = self.parameters['name']
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-destroy')
        domain_obj.add_new_child("broadcast-domain", broadcast_domain)
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting broadcast domain %s: %s' %
                                  (broadcast_domain, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_broadcast_domain(self):
        """
        Modifies ipspace and mtu options of a broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-modify')
        domain_obj.add_new_child("broadcast-domain", self.parameters['name'])
        if self.parameters.get('mtu'):
            domain_obj.add_new_child("mtu", self.parameters['mtu'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying broadcast domain %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def split_broadcast_domain(self):
        """
        split broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-split')
        domain_obj.add_new_child("broadcast-domain", self.parameters['from_name'])
        domain_obj.add_new_child("new-broadcast-domain", self.parameters['name'])
        if self.parameters.get('ports'):
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in self.parameters['ports']:
                ports_obj.add_new_child('net-qualified-port-name', port)
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error splitting broadcast domain %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        if len(self.get_broadcast_domain_ports(self.parameters['from_name'])) == 0:
            self.delete_broadcast_domain(self.parameters['from_name'])

    def modify_redirect(self, modify):
        """
        :param modify: modify attributes.
        """
        for attribute in modify.keys():
            if attribute == 'mtu':
                self.modify_broadcast_domain()
            if attribute == 'ports':
                self.modify_broadcast_domain_ports()

    def get_modify_attributes(self, current, split):
        """
        :param current: current state.
        :param split: True or False of split action.
        :return: list of modified attributes.
        """
        modify = None
        if self.parameters['state'] == 'present':
            # split already handled ipspace and ports.
            if self.parameters.get('from_name'):
                current = self.get_broadcast_domain(self.parameters['from_name'])
                if split:
                    modify = self.na_helper.get_modified_attributes(current, self.parameters)
                    if modify.get('ipspace'):
                        del modify['ipspace']
                    if modify.get('ports'):
                        del modify['ports']
        # ipspace can not be modified.
            else:
                modify = self.na_helper.get_modified_attributes(current, self.parameters)
                if modify.get('ipspace'):
                    self.module.fail_json(msg='A domain ipspace can not be modified after the domain has been created.',
                                          exception=traceback.format_exc())
        return modify

    def modify_broadcast_domain_ports(self):
        """
        compare current and desire ports. Call add or remove ports methods if needed.
        :return: None.
        """
        current_ports = self.get_broadcast_domain_ports()
        expect_ports = self.parameters['ports']
        # if want to remove all ports, simply delete the broadcast domain.
        if len(expect_ports) == 0:
            self.delete_broadcast_domain()
            return
        ports_to_remove = list(set(current_ports) - set(expect_ports))
        ports_to_add = list(set(expect_ports) - set(current_ports))

        if len(ports_to_add) > 0:
            self.add_broadcast_domain_ports(ports_to_add)

        if len(ports_to_remove) > 0:
            self.delete_broadcast_domain_ports(ports_to_remove)

    def add_broadcast_domain_ports(self, ports):
        """
        Creates new broadcast domain ports
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-add-ports')
        domain_obj.add_new_child("broadcast-domain", self.parameters['name'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        if ports:
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in ports:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating port for broadcast domain %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_broadcast_domain_ports(self, ports):
        """
        Deletes broadcast domain ports
        :param: ports to be deleted.
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-remove-ports')
        domain_obj.add_new_child("broadcast-domain", self.parameters['name'])
        if self.parameters.get('ipspace'):
            domain_obj.add_new_child("ipspace", self.parameters['ipspace'])
        if ports:
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in ports:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting port for broadcast domain %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def get_broadcast_domain_ports(self, broadcast_domain=None):
        """
        Return details about the broadcast domain ports.
        :return: Details about the broadcast domain ports. None if not found.
        :rtype: list
        """
        if broadcast_domain is None:
            broadcast_domain = self.parameters['name']
        domain_get_iter = netapp_utils.zapi.NaElement('net-port-broadcast-domain-get-iter')
        broadcast_domain_info = netapp_utils.zapi.NaElement('net-port-broadcast-domain-info')
        broadcast_domain_info.add_new_child('broadcast-domain', broadcast_domain)
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

    def apply(self):
        """
        Run Module based on play book
        """
        self.asup_log_for_cserver("na_ontap_broadcast_domain")
        current = self.get_broadcast_domain()
        cd_action, split = None, None
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            # either create new domain or split domain.
            if self.parameters.get('from_name'):
                split = self.na_helper.is_rename_action(self.get_broadcast_domain(self.parameters['from_name']), current)
                if split is None:
                    self.module.fail_json(msg='A domain can not be split if it does not exist.',
                                          exception=traceback.format_exc())
                if split:
                    cd_action = None
        modify = self.get_modify_attributes(current, split)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if split:
                    self.split_broadcast_domain()
                if cd_action == 'create':
                    self.create_broadcast_domain()
                elif cd_action == 'delete':
                    self.delete_broadcast_domain()
                elif modify:
                    self.modify_redirect(modify)
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
    """
    Creates the NetApp ONTAP Broadcast Domain Object that can be created, deleted and modified.
    """
    obj = NetAppOntapBroadcastDomain()
    obj.apply()


if __name__ == '__main__':
    main()
