#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = """
module: na_ontap_net_port
short_description: NetApp ONTAP network ports.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Modify a ONTAP network port.
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
  ports:
    aliases:
    - port
    description:
    - Specifies the name of port(s).
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
    - Valid values auto, half, full
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
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        node: "{{ node_name }}"
        ports: e0d,e0c
        autonegotiate_admin: true
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

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
            ports=dict(required=True, type="list", aliases=['port']),
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

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'mtu': 'mtu',
            'autonegotiate_admin': 'is-administrative-auto-negotiate',
            'duplex_admin': 'administrative-duplex',
            'speed_admin': 'administrative-speed',
            'flowcontrol_admin': 'administrative-flowcontrol',
            'ipspace': 'ipspace'
        }

    def get_net_port(self, port):
        """
        Return details about the net port
        :param: port: Name of the port
        :return: Dictionary with current state of the port. None if not found.
        :rtype: dict
        """
        net_port_get = netapp_utils.zapi.NaElement('net-port-get-iter')
        attributes = {
            'query': {
                'net-port-info': {
                    'node': self.parameters['node'],
                    'port': port
                }
            }
        }
        net_port_get.translate_struct(attributes)

        try:
            result = self.server.invoke_successfully(net_port_get, True)
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                port_info = result['attributes-list']['net-port-info']
                port_details = dict()
            else:
                return None
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting net ports for %s: %s' % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

        for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
            port_details[item_key] = port_info.get_child_content(zapi_key)
        return port_details

    def modify_net_port(self, port, modify):
        """
        Modify a port

        :param port: Name of the port
        :param modify: dict with attributes to be modified
        :return: None
        """
        port_modify = netapp_utils.zapi.NaElement('net-port-modify')
        port_attributes = {'node': self.parameters['node'],
                           'port': port}
        for key in modify:
            if key in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(key)
                port_attributes[zapi_key] = modify[key]
        port_modify.translate_struct(port_attributes)
        try:
            self.server.invoke_successfully(port_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying net ports for %s: %s' % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
        AutoSupport log for na_ontap_net_port
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_net_port", cserver)

    def apply(self):
        """
        Run Module based on play book
        """

        self.autosupport_log()
        # Run the task for all ports in the list of 'ports'
        for port in self.parameters['ports']:
            current = self.get_net_port(port)
            modify = self.na_helper.get_modified_attributes(current, self.parameters)
            if self.na_helper.changed:
                if self.module.check_mode:
                    pass
                else:
                    if modify:
                        self.modify_net_port(port, modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Create the NetApp Ontap Net Port Object and modify it
    """
    obj = NetAppOntapNetPort()
    obj.apply()


if __name__ == '__main__':
    main()
