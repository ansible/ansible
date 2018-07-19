#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
author: "Suhas Bangalore Shekar (bsuhas@netapp.com), Archana Ganesan (garchana@netapp.com)"
description:
  - Create/Delete cluster peer
extends_documentation_fragment:
  - netapp.ontap
module: na_ontap_cluster_peer
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified cluster peer should exist or not.
    default: present
  peer_addresses:
    description:
      - List of remote intercluster addresses and hostnames of the peer cluster.
  passphrase:
    description:
      - The arbitrary passphrase that matches the one given to the peer cluster.
  cluster_name:
    description:
      - The name of the peer cluster to be deleted.
short_description: "Manage NetApp Cluster peering"
version_added: "2.7"
'''

EXAMPLES = """

    - name: Create cluster peer
      na_ontap_cluster_peer:
        state: present
        peer_addresses: 1.2.3.4,5.6.7.8
        passphrase: XXXX
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete cluster peer
      na_ontap_cluster_peer:
        state: absent
        cluster_name: test-peer-cluster
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPClusterPeer(object):
    """
    Class with cluster peer methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            peer_addresses=dict(required=False, type='list'),
            passphrase=dict(required=False, type='str'),
            cluster_name=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_together=['peer_addresses', 'passphrase'],
            required_if=[('state', 'absent', ['cluster_name'])],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def cluster_peer_get_iter(self):
        """
        Compose NaElement object to query current cluster using peer-cluster-name and peer-addresses parameters
        :return: NaElement object for cluster-get-iter with query
        """
        cluster_peer_get = netapp_utils.zapi.NaElement('cluster-peer-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        cluster_peer_info = netapp_utils.zapi.NaElement('cluster-peer-info')
        peer_addresses = netapp_utils.zapi.NaElement('peer-addresses')
        if self.parameters.get('peer-addresses'):
            for peer in self.parameters['peer_addresses']:
                peer_addresses.add_new_child('remote-inet-address', peer)
            cluster_peer_info.add_child_elem(peer_addresses)
        if self.parameters.get('cluster-name'):
            cluster_peer_info.add_new_child('cluster-name', self.parameters['cluster_name'])
        query.add_child_elem(cluster_peer_info)
        cluster_peer_get.add_child_elem(query)
        return cluster_peer_get

    def cluster_peer_get(self):
        """
        Get current cluster peer info
        :return: Dictionary of current cluster peer details if query successful, else return None
        """
        cluster_peer_get_iter = self.cluster_peer_get_iter()
        cluster_info = dict()
        try:
            result = self.server.invoke_successfully(cluster_peer_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching cluster peer %s: %s'
                                      % (self.parameters['cluster_name'], to_native(error)),
                                  exception=traceback.format_exc())
        # return cluster peer details
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            cluster_peer_info = result.get_child_by_name('attributes-list').get_child_by_name('cluster-peer-info')
            cluster_info['cluster_name'] = cluster_peer_info.get_child_content('cluster-name')
            peers = cluster_peer_info.get_child_by_name('peer-addresses')
            cluster_info['peer-addresses'] = [peer.get_content() for peer in peers.get_children()]
            return cluster_info
        return None

    def cluster_peer_delete(self):
        """
        Delete a cluster peer
        """
        cluster_peer_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-peer-delete', **{'cluster-name': self.parameters['cluster_name']})
        try:
            self.server.invoke_successfully(cluster_peer_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting cluster peer %s: %s'
                                      % (self.parameters['cluster_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def cluster_peer_create(self):
        """
        Create a cluster peer
        """
        cluster_peer_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-peer-create', **{'passphrase': self.parameters['passphrase']})
        peer_addresses = netapp_utils.zapi.NaElement('peer-addresses')
        for peer in self.parameters['peer_addresses']:
            peer_addresses.add_new_child('remote-inet-address', peer)
        cluster_peer_create.add_child_elem(peer_addresses)
        try:
            self.server.invoke_successfully(cluster_peer_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating cluster peer %s: %s'
                                  % (self.parameters['peer_addresses'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to cluster peer
        """
        current = self.cluster_peer_get()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            self.cluster_peer_create()
        elif cd_action == 'delete':
            self.cluster_peer_delete()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Execute action'''
    community_obj = NetAppONTAPClusterPeer()
    community_obj.apply()


if __name__ == '__main__':
    main()
