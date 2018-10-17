#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_broadcast_domain
short_description: Manage NetApp ONTAP broadcast domains.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Chris Archibald (carchi8py@gmail.com), Kevin Hutton (khutton@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)
description:
- Modify a ONTAP broadcast domain.
options:
  state:
    description:
    - Whether the specified broadcast domain should exist or not.
    choices: ['present', 'absent']
    default: present
  broadcast_domain:
    description:
    - Specify the broadcast_domain name
    required: true
  mtu:
    description:
    - Specify the required mtu for the broadcast domain
  ipspace:
    description:
    - Specify the required ipspace for the broadcast domain
  ports:
    description:
    - Specify the ports associated with this broadcast domain. Should be comma separated

'''

EXAMPLES = """
    - name: create broadcast domain
      na_ontap_broadcast_domain:
        state=present
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        broadcast_domain=123kevin
        mtu=1000
        ipspace=Default
        ports=khutton-vsim1:e0d-12,khutton-vsim1:e0d-13
    - name: delete broadcast domain
      na_ontap_broadcast_domain:
        state=absent
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        broadcast_domain=123kevin
        mtu=1000
        ipspace=Default
    - name: modify broadcast domain
      na_ontap_broadcast_domain:
        state=absent
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        broadcast_domain=123kevin
        mtu=1100
        ipspace=Default
"""

RETURN = """


"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

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
            broadcast_domain=dict(required=True, type='str'),
            ipspace=dict(required=False, type='str'),
            mtu=dict(required=False, type='str'),
            ports=dict(required=False, type='list'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.broadcast_domain = parameters['broadcast_domain']
        self.ipspace = parameters['ipspace']
        self.mtu = parameters['mtu']
        self.ports = parameters['ports']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_broadcast_domain(self):
        """
        Return details about the broadcast domain
        :param:
            name : broadcast domain name
        :return: Details about the broadcas domain. None if not found.
        :rtype: dict
        """
        domain_get_iter = netapp_utils.zapi.NaElement('net-port-broadcast-domain-get-iter')
        broadcast_domain_info = netapp_utils.zapi.NaElement('net-port-broadcast-domain-info')
        broadcast_domain_info.add_new_child('broadcast-domain', self.broadcast_domain)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(broadcast_domain_info)
        domain_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(domain_get_iter, True)
        domain_exists = None
        # check if job exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            domain_info = result.get_child_by_name('attributes-list').\
                get_child_by_name('net-port-broadcast-domain-info')
            domain_name = domain_info.get_child_content('broadcast-domain')
            domain_mtu = domain_info.get_child_content('mtu')
            domain_ipspace = domain_info.get_child_content('ipspace')
            domain_exists = {
                'domain-name': domain_name,
                'mtu': domain_mtu,
                'ipspace': domain_ipspace
            }
        return domain_exists

    def create_broadcast_domain(self):
        """
        Creates a new broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-create')
        domain_obj.add_new_child("broadcast-domain", self.broadcast_domain)
        if self.ipspace:
            domain_obj.add_new_child("ipspace", self.ipspace)
        domain_obj.add_new_child("mtu", self.mtu)
        if self.ports:
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in self.ports:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating broadcast domain %s: %s' %
                                  (self.broadcast_domain, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_broadcast_domain(self):
        """
        Deletes a broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-destroy')
        domain_obj.add_new_child("broadcast-domain", self.broadcast_domain)
        if self.ipspace:
            domain_obj.add_new_child("ipspace", self.ipspace)
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting broadcast domain %s: %s' %
                                  (self.broadcast_domain, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_broadcast_domain(self):
        """
        Modifies ipspace and mtu options of a broadcast domain
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-modify')
        domain_obj.add_new_child("broadcast-domain", self.broadcast_domain)
        if self.ipspace:
            domain_obj.add_new_child("ipspace", self.ipspace)
        if self.mtu:
            domain_obj.add_new_child("mtu", self.mtu)
        try:
            self.server.invoke_successfully(domain_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying broadcast domain %s: %s' %
                                  (self.broadcast_domain, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        broadcast_domain_details = self.get_broadcast_domain()
        broadcast_domain_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_broadcast_domain", cserver)
        if broadcast_domain_details:
            broadcast_domain_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':  # modify
                if (self.mtu and self.mtu != broadcast_domain_details['mtu']) or \
                   (self.ipspace and self.ipspace != broadcast_domain_details['ipspace']):
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create
                    if not broadcast_domain_exists:
                        self.create_broadcast_domain()
                    else:  # execute modify
                        self.modify_broadcast_domain()
                elif self.state == 'absent':  # execute delete
                    self.delete_broadcast_domain()
        self.module.exit_json(changed=changed)


def main():
    """
    Creates the NetApp ONTAP Broadcast Domain Object that can be created, deleted and modified.
    """
    obj = NetAppOntapBroadcastDomain()
    obj.apply()

if __name__ == '__main__':
    main()
