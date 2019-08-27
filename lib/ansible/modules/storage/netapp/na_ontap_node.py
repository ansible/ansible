#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_node
short_description: NetApp ONTAP Rename a node.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Rename an ONTAP node.
options:
  name:
    description:
    - The new name for the node
    required: true

  from_name:
    description:
    - The name of the node to be renamed.  If I(name) already exists, no action will be performed.
    required: true

'''

EXAMPLES = """
- name: rename node
  na_ontap_node:
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
    from_name: laurentn-vsim1
    name: laurentncluster-2
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapNode(object):
    """
    Rename node
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            name=dict(required=True, type='str'),
            from_name=dict(required=True, type='str'),
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
            self.cluster = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def rename_node(self):
        """
        Rename an existing node
        :return: none
        """
        node_obj = netapp_utils.zapi.NaElement('system-node-rename')
        node_obj.add_new_child('node', self.parameters['from_name'])
        node_obj.add_new_child('new-name', self.parameters['name'])
        try:
            self.cluster.invoke_successfully(node_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating node: %s' %
                                  (to_native(error)),
                                  exception=traceback.format_exc())

    def get_node(self, name):
        node_obj = netapp_utils.zapi.NaElement('system-node-get')
        node_obj.add_new_child('node', name)
        try:
            self.cluster.invoke_successfully(node_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "13115":
                # 13115 (EINVALIDINPUTERROR) if the node does not exist
                return None
            else:
                self.module.fail_json(msg=to_native(
                    error), exception=traceback.format_exc())
        return True

    def apply(self):
        # logging ems event
        results = netapp_utils.get_cserver(self.cluster)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_node", cserver)

        exists = self.get_node(self.parameters['name'])
        from_exists = self.get_node(self.parameters['from_name'])
        changed = False
        if exists:
            pass
        else:
            if from_exists:
                self.rename_node()
                changed = True
            else:
                self.module.fail_json(msg='Error renaming node, from_name %s does not exist' % self.parameters['from_name'])

        self.module.exit_json(changed=changed)


def main():
    """
    Start, Stop and Enable node services.
    """
    obj = NetAppOntapNode()
    obj.apply()


if __name__ == '__main__':
    main()
