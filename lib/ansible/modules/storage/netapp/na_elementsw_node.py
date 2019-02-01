#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Node Operation
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_node

short_description: NetApp Element Software Node Operation
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
    - Add, remove cluster node on Element Software Cluster.

options:
    state:
        description:
        - Element Software Storage Node operation state.
        - present - To add pending node to participate in cluster data storage.
        - absent  - To remove node from active cluster.  A node cannot be removed if active drives are present.
        choices: ['present', 'absent']
        default: 'present'

    node_id:
        description:
        - List of IDs or Names or IP Address of nodes from cluster used for operation.
        required: true

'''

EXAMPLES = """
   - name: Add node from pending to active cluster
     tags:
     - elementsw_add_node
     na_elementsw_node:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       node_id: sf4805-meg-03

   - name: Remove active node from cluster
     tags:
     - elementsw_remove_node
     na_elementsw_node:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       node_id: 13

   - name: Add node from pending to active cluster using node IP
     tags:
     - elementsw_add_node_ip
     na_elementsw_node:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       node_id: 10.109.48.65
"""


RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWNode(object):
    """
    Element SW Storage Node operations
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            node_id=dict(required=True, type='list'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        self.state = input_params['state']
        self.node_id = input_params['node_id']

        if HAS_SF_SDK is False:
            self.module.fail_json(
                msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def check_node_has_active_drives(self, node_id=None):
        """
            Check if node has active drives attached to cluster
            :description: Validate if node have active drives in cluster

            :return: True or False
            :rtype: bool
        """
        if node_id is not None:
            cluster_drives = self.sfe.list_drives()
            for drive in cluster_drives.drives:
                if drive.node_id == node_id and drive.status == "active":
                    return True
        return False

    def get_node_list(self):
        """
            Get Node List
            :description: Find and retrieve node_id from the active cluster

            :return: None
            :rtype: None
        """
        if len(self.node_id) > 0:
            unprocessed_node_list = self.node_id
            list_nodes = []
            all_nodes = self.sfe.list_all_nodes()
            # For add operation lookup for nodes list with status pendingNodes list
            # else nodes will have to be traverse through active cluster
            if self.state == "present":
                list_nodes = all_nodes.pending_nodes
            else:
                list_nodes = all_nodes.nodes

            for current_node in list_nodes:
                if self.state == "absent" and \
                   (current_node.node_id in self.node_id or current_node.name in self.node_id or current_node.mip in self.node_id):
                    if self.check_node_has_active_drives(current_node.node_id):
                        self.module.fail_json(msg='Error deleting node %s: node has active drives' % current_node.name)
                    else:
                        self.action_nodes_list.append(current_node.node_id)
                if self.state == "present" and \
                   (current_node.pending_node_id in self.node_id or current_node.name in self.node_id or current_node.mip in self.node_id):
                    self.action_nodes_list.append(current_node.pending_node_id)

            # report an error if state == present and node is unknown
            if self.state == "present":
                for current_node in all_nodes.nodes:
                    if current_node.node_id in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.node_id)
                    elif current_node.name in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.name)
                    elif current_node.mip in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.mip)
                for current_node in all_nodes.pending_nodes:
                    if current_node.pending_node_id in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.node_id)
                    elif current_node.name in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.name)
                    elif current_node.mip in unprocessed_node_list:
                        unprocessed_node_list.remove(current_node.mip)
                if len(unprocessed_node_list) > 0:
                    self.module.fail_json(msg='Error adding node %s: node not in pending or active lists' % to_native(unprocessed_node_list))
        return None

    def add_node(self, nodes_list=None):
        """
        Add Node  that are on PendingNodes list available on Cluster
        """
        try:
            self.sfe.add_nodes(nodes_list,
                               auto_install=True)
        except Exception as exception_object:
            self.module.fail_json(msg='Error add node to cluster  %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def remove_node(self, nodes_list=None):
        """
        Remove active node from Cluster
        """
        try:
            self.sfe.remove_nodes(nodes_list)
        except Exception as exception_object:
            self.module.fail_json(msg='Error remove node from cluster  %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Check, process and initiate Cluster Node operation
        """
        changed = False
        self.action_nodes_list = []
        if self.module.check_mode is False:
            self.get_node_list()
            if self.state == "present" and len(self.action_nodes_list) > 0:
                self.add_node(self.action_nodes_list)
                changed = True
            elif self.state == "absent" and len(self.action_nodes_list) > 0:
                self.remove_node(self.action_nodes_list)
                changed = True
        result_message = 'List of nodes : %s - %s' % (to_native(self.action_nodes_list), to_native(self.node_id))
        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """

    na_elementsw_node = ElementSWNode()
    na_elementsw_node.apply()


if __name__ == '__main__':
    main()
