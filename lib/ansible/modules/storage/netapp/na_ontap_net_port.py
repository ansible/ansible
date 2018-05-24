#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_ontap_net_port
short_description: Manage NetApp Ontap network ports.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)
description:
- Modify a Ontap network port.
options:
  state:
    description:
    - Whether the specified net port should exist or not.
    choices: ['present']
    default: present
  node:
    description:
    - Specifies the name of node.
    required: true
  port:
    description:
    - Specifies the name of port.
    required: true
  mtu:
    description:
    - Specifies the maximum transmission unit (MTU) reported by the port.
  autonegotiate_admin:
    description:
    - Enables or disables Ethernet auto-negotiation of speed,
      duplex and flow control.
  duplex_admin:
    description:
    - Specifies the user preferred duplex setting of the port.
  speed_admin:
    description:
    - Specifies the user preferred speed setting of the port.
  flowcontrol_admin:
    description:
    - Specifies the user preferred flow control setting of the port.
  ipspace:
    description:
    - Specifies the port's associated IPspace name.
    - The 'Cluster' ipspace is reserved for cluster ports.
"""

EXAMPLES = """
    - name: Modify Net Port
      na_ontap_net_port:
        state=present
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        node={{ Vsim server name }}
        port=e0d
        autonegotiate_admin=true
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapNetPort(object):
    """
        Modify a Net port
    """

    def __init__(self):
        """
            Initialize the Ontap Net Port Class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            node=dict(required=True, type="str"),
            port=dict(required=True, type="str"),
            mtu=dict(required=False, type="str", default=None),
            autonegotiate_admin=dict(required=False, type="str", default=None),
            duplex_admin=dict(required=False, type="str", default=None),
            speed_admin=dict(required=False, type="str", default=None),
            flowcontrol_admin=dict(required=False, type="str", default=None),
            ipspace=dict(required=False, type="str", default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.node = p['node']
        self.port = p['port']
        # the following option are optional, but at least one need to be set
        self.mtu = p['mtu']
        self.autonegotiate_admin = p["autonegotiate_admin"]
        self.duplex_admin = p["duplex_admin"]
        self.speed_admin = p["speed_admin"]
        self.flowcontrol_admin = p["flowcontrol_admin"]

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_net_port(self):
        """
        Return details about the net port

        :return: Details about the net port. None if not found.
        :rtype: dict
        """
        net_port_info = netapp_utils.zapi.NaElement('net-port-get-iter')
        net_port_attributes = netapp_utils.zapi.NaElement('net-port-info')
        net_port_attributes.add_new_child('node', self.node)
        net_port_attributes.add_new_child('port', self.port)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(net_port_attributes)
        net_port_info.add_child_elem(query)
        result = self.server.invoke_successfully(net_port_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            net_port_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('net-port-info')
            return_value = {
                'node': net_port_attributes.get_child_content('node'),
                'port': net_port_attributes.get_child_content('port'),
                'mtu': net_port_attributes.get_child_content('mtu'),
                'autonegotiate_admin': net_port_attributes.get_child_content(
                    'is-administrative-auto-negotiate'),
                'duplex_admin': net_port_attributes.get_child_content(
                    'administrative-duplex'),
                'speed_admin': net_port_attributes.get_child_content(
                    'administrative-speed'),
                'flowcontrol_admin': net_port_attributes.get_child_content(
                    'administrative-flowcontrol'),
            }
        return return_value

    def modify_net_port(self):
        """
        Modify a port
        """
        port_obj = netapp_utils.zapi.NaElement('net-port-modify')
        port_obj.add_new_child("node", self.node)
        port_obj.add_new_child("port", self.port)
        # The following options are optional.
        # We will only call them if they are not set to None
        if self.mtu:
            port_obj.add_new_child("mtu", self.mtu)
        if self.autonegotiate_admin:
            port_obj.add_new_child(
                "is-administrative-auto-negotiate", self.autonegotiate_admin)
        if self.duplex_admin:
            port_obj.add_new_child("administrative-duplex", self.duplex_admin)
        if self.speed_admin:
            port_obj.add_new_child("administrative-speed", self.speed_admin)
        if self.flowcontrol_admin:
            port_obj.add_new_child(
                "administrative-flowcontrol", self.flowcontrol_admin)
        self.server.invoke_successfully(port_obj, True)

    def apply(self):
        """
        Run Module based on play book
        """
        changed = False
        net_port_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_net_port", cserver)
        net_port_details = self.get_net_port()
        if net_port_details:
            net_port_exists = True
            if self.state == 'present':
                if (self.mtu and self.mtu != net_port_details['mtu']) or \
                   (self.autonegotiate_admin and
                    self.autonegotiate_admin != net_port_details['autonegotiate_admin']) or \
                   (self.duplex_admin and
                    self.duplex_admin != net_port_details['duplex_admin']) or \
                   (self.speed_admin and
                    self.speed_admin != net_port_details['speed_admin']) or \
                   (self.flowcontrol_admin and
                        self.flowcontrol_admin != net_port_details['flowcontrol_admin']):
                    changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if net_port_exists:
                        self.modify_net_port()
        self.module.exit_json(changed=changed)


def main():
    """
    Create the NetApp Ontap Net Port Object and modify it
    """
    obj = NetAppOntapNetPort()
    obj.apply()


if __name__ == '__main__':
    main()
