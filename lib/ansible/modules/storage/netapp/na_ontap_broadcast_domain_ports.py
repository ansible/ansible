#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_broadcast_domain_ports
short_description: Manage NetApp Ontap broadcast domain ports
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)
description:
- Modify Ontap broadcast domain ports
options:
  state:
    description:
    - Whether the specified broadcast domain should exist or not.
    choices: ['present', 'absent']
    default: present
  vserver:
    description:
    - The name of the vserver
    required: true
  broadcast_domain:
    description:
    - Specify the broadcast_domain name
    required: true
  ipspace:
    description:
    - Specify the ipspace for the broadcast domain
  ports:
    description:
    - Specify the list of ports associated with this broadcast domain.

'''

EXAMPLES = """
    - name: create broadcast domain ports
      na_ontap_broadcast_domain_ports:
        state=present
        vserver={{ Vserver name }}
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        broadcast_domain=123kevin
        ports=khutton-vsim1:e0d-13
    - name: delete broadcast domain ports
      na_ontap_broadcast_domain_ports:
        state=absent
        vserver={{ Vserver name }}
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        broadcast_domain=123kevin
        ports=khutton-vsim1:e0d-13
"""

RETURN = """


"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapBroadcastDomainPorts(object):
    """
        Create and Destroys Broadcast Domain Ports
    """
    def __init__(self):
        """
            Initialize the Ontap Net Route class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=False, type='str'),
            broadcast_domain=dict(required=True, type='str'),
            ipspace=dict(required=False, type='str', default=None),
            ports=dict(required=True, type='list'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.vserver = parameters['vserver']
        self.broadcast_domain = parameters['broadcast_domain']
        self.ipspace = parameters['ipspace']
        self.ports = parameters['ports']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_broadcast_domain_ports(self):
        """
        Return details about the broadcast domain ports
        :param:
            name : broadcast domain name
        :return: Details about the broadcast domain. None if not found.
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
        # check if broadcast domain exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            domain_info = result.get_child_by_name('attributes-list').get_child_by_name('net-port-broadcast-domain-info')
            domain_name = domain_info.get_child_content('broadcast-domain')
            domain_ports = domain_info.get_child_content('port-info')
            domain_exists = {
                'domain-name': domain_name,
                'ports': domain_ports
            }
        return domain_exists

    def create_broadcast_domain_ports(self):
        """
        Creates new broadcast domain ports
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-add-ports')
        domain_obj.add_new_child("broadcast-domain", self.broadcast_domain)
        if self.ipspace:
            domain_obj.add_new_child("ipspace", self.ipspace)
        if self.ports:
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in self.ports:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            # Error 18605 denotes port already being used.
            if to_native(error.code) == "18605":
                return False
            else:
                self.module.fail_json(msg='Error creating port for broadcast domain %s: %s' %
                                      (self.broadcast_domain, to_native(error)),
                                      exception=traceback.format_exc())

    def delete_broadcast_domain_ports(self):
        """
        Deletes broadcast domain ports
        """
        domain_obj = netapp_utils.zapi.NaElement('net-port-broadcast-domain-remove-ports')
        domain_obj.add_new_child("broadcast-domain", self.broadcast_domain)
        if self.ipspace:
            domain_obj.add_new_child("ipspace", self.ipspace)
        if self.ports:
            ports_obj = netapp_utils.zapi.NaElement('ports')
            domain_obj.add_child_elem(ports_obj)
            for port in self.ports:
                ports_obj.add_new_child('net-qualified-port-name', port)
        try:
            self.server.invoke_successfully(domain_obj, True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            # Error 13001 denotes port already not being used.
            if to_native(error.code) == "13001":
                return False
            else:
                self.module.fail_json(msg='Error deleting port for broadcast domain %s: %s' %
                                      (self.broadcast_domain, to_native(error)),
                                      exception=traceback.format_exc())

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        broadcast_domain_details = self.get_broadcast_domain_ports()
        broadcast_domain_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_broadcast_domain_ports", cserver)
        if broadcast_domain_details:
            broadcast_domain_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':  # create
                changed = True
        else:
            pass
        if changed:
            if self.module.check_mode:
                pass
            else:
                if broadcast_domain_exists:
                    if self.state == 'present':  # execute create
                        changed = self.create_broadcast_domain_ports()
                    elif self.state == 'absent':  # execute delete
                        changed = self.delete_broadcast_domain_ports()
        self.module.exit_json(changed=changed)


def main():
    """
    Creates the NetApp Ontap Net Route object and runs the correct play task
    """
    obj = NetAppOntapBroadcastDomainPorts()
    obj.apply()


if __name__ == '__main__':
    main()
