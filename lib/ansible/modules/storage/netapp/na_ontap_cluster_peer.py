#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create/Delete cluster peer relations on ONTAP
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_cluster_peer
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified cluster peer should exist or not.
    default: present
  source_intercluster_lifs:
    description:
      - List of intercluster addresses of the source cluster.
      - Used as peer-addresses in destination cluster.
      - All these intercluster lifs should belong to the source cluster.
    version_added: "2.8"
    aliases:
    - source_intercluster_lif
  dest_intercluster_lifs:
    description:
      - List of intercluster addresses of the destination cluster.
      - Used as peer-addresses in source cluster.
      - All these intercluster lifs should belong to the destination cluster.
    version_added: "2.8"
    aliases:
    - dest_intercluster_lif
  passphrase:
    description:
      - The arbitrary passphrase that matches the one given to the peer cluster.
  source_cluster_name:
    description:
      - The name of the source cluster name in the peer relation to be deleted.
  dest_cluster_name:
    description:
      - The name of the destination cluster name in the peer relation to be deleted.
      - Required for delete
  dest_hostname:
    description:
      - Destination cluster IP or hostname which needs to be peered
      - Required to complete the peering process at destination cluster.
    required: True
  dest_username:
    description:
     - Destination username.
     - Optional if this is same as source username.
  dest_password:
    description:
     - Destination password.
     - Optional if this is same as source password.
short_description: NetApp ONTAP Manage Cluster peering
version_added: "2.7"
'''

EXAMPLES = """

    - name: Create cluster peer
      na_ontap_cluster_peer:
        state: present
        source_intercluster_lifs: 1.2.3.4,1.2.3.5
        dest_intercluster_lifs: 1.2.3.6,1.2.3.7
        passphrase: XXXX
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        dest_hostname: "{{ dest_netapp_hostname }}"

    - name: Delete cluster peer
      na_ontap_cluster_peer:
        state: absent
        source_cluster_name: test-source-cluster
        dest_cluster_name: test-dest-cluster
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        dest_hostname: "{{ dest_netapp_hostname }}"
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

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            source_intercluster_lifs=dict(required=False, type='list', aliases=['source_intercluster_lif']),
            dest_intercluster_lifs=dict(required=False, type='list', aliases=['dest_intercluster_lif']),
            passphrase=dict(required=False, type='str', no_log=True),
            dest_hostname=dict(required=True, type='str'),
            dest_username=dict(required=False, type='str'),
            dest_password=dict(required=False, type='str', no_log=True),
            source_cluster_name=dict(required=False, type='str'),
            dest_cluster_name=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_together=[['source_intercluster_lifs', 'dest_intercluster_lifs']],
            required_if=[('state', 'absent', ['source_cluster_name', 'dest_cluster_name'])],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
            # set destination server connection
            self.module.params['hostname'] = self.parameters['dest_hostname']
            if self.parameters.get('dest_username'):
                self.module.params['username'] = self.parameters['dest_username']
            if self.parameters.get('dest_password'):
                self.module.params['password'] = self.parameters['dest_password']
            self.dest_server = netapp_utils.setup_na_ontap_zapi(module=self.module)
            # reset to source host connection for asup logs
            self.module.params['hostname'] = self.parameters['hostname']

    def cluster_peer_get_iter(self, cluster):
        """
        Compose NaElement object to query current source cluster using peer-cluster-name and peer-addresses parameters
        :param cluster: type of cluster (source or destination)
        :return: NaElement object for cluster-get-iter with query
        """
        cluster_peer_get = netapp_utils.zapi.NaElement('cluster-peer-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        cluster_peer_info = netapp_utils.zapi.NaElement('cluster-peer-info')
        if cluster == 'source':
            peer_lifs, peer_cluster = 'dest_intercluster_lifs', 'dest_cluster_name'
        else:
            peer_lifs, peer_cluster = 'source_intercluster_lifs', 'source_cluster_name'
        if self.parameters.get(peer_lifs):
            peer_addresses = netapp_utils.zapi.NaElement('peer-addresses')
            for peer in self.parameters.get(peer_lifs):
                peer_addresses.add_new_child('remote-inet-address', peer)
            cluster_peer_info.add_child_elem(peer_addresses)
        if self.parameters.get(peer_cluster):
            cluster_peer_info.add_new_child('cluster-name', self.parameters[peer_cluster])
        query.add_child_elem(cluster_peer_info)
        cluster_peer_get.add_child_elem(query)
        return cluster_peer_get

    def cluster_peer_get(self, cluster):
        """
        Get current cluster peer info
        :param cluster: type of cluster (source or destination)
        :return: Dictionary of current cluster peer details if query successful, else return None
        """
        cluster_peer_get_iter = self.cluster_peer_get_iter(cluster)
        result, cluster_info = None, dict()
        if cluster == 'source':
            server = self.server
        else:
            server = self.dest_server
        try:
            result = server.invoke_successfully(cluster_peer_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching cluster peer %s: %s'
                                      % (self.parameters['dest_cluster_name'], to_native(error)),
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

    def cluster_peer_delete(self, cluster):
        """
        Delete a cluster peer on source or destination
        For source cluster, peer cluster-name = destination cluster name and vice-versa
        :param cluster: type of cluster (source or destination)
        :return:
        """
        if cluster == 'source':
            server, peer_cluster_name = self.server, self.parameters['dest_cluster_name']
        else:
            server, peer_cluster_name = self.dest_server, self.parameters['source_cluster_name']
        cluster_peer_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-peer-delete', **{'cluster-name': peer_cluster_name})
        try:
            server.invoke_successfully(cluster_peer_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting cluster peer %s: %s'
                                      % (peer_cluster_name, to_native(error)),
                                  exception=traceback.format_exc())

    def cluster_peer_create(self, cluster):
        """
        Create a cluster peer on source or destination
        For source cluster, peer addresses = destination inter-cluster LIFs and vice-versa
        :param cluster: type of cluster (source or destination)
        :return: None
        """
        cluster_peer_create = netapp_utils.zapi.NaElement.create_node_with_children('cluster-peer-create')
        if self.parameters.get('passphrase') is not None:
            cluster_peer_create.add_new_child('passphrase', self.parameters['passphrase'])
        peer_addresses = netapp_utils.zapi.NaElement('peer-addresses')
        if cluster == 'source':
            server, peer_address = self.server, self.parameters['dest_intercluster_lifs']
        else:
            server, peer_address = self.dest_server, self.parameters['source_intercluster_lifs']
        for each in peer_address:
            peer_addresses.add_new_child('remote-inet-address', each)
        cluster_peer_create.add_child_elem(peer_addresses)
        try:
            server.invoke_successfully(cluster_peer_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating cluster peer %s: %s'
                                  % (peer_address, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to cluster peer
        :return: None
        """
        self.asup_log_for_cserver("na_ontap_cluster_peer")
        source = self.cluster_peer_get('source')
        destination = self.cluster_peer_get('destination')
        source_action = self.na_helper.get_cd_action(source, self.parameters)
        destination_action = self.na_helper.get_cd_action(destination, self.parameters)
        self.na_helper.changed = False
        # create only if expected cluster peer relation is not present on both source and destination clusters
        if source_action == 'create' and destination_action == 'create':
            self.cluster_peer_create('source')
            self.cluster_peer_create('destination')
            self.na_helper.changed = True
        # delete peer relation in cluster where relation is present
        else:
            if source_action == 'delete':
                self.cluster_peer_delete('source')
                self.na_helper.changed = True
            if destination_action == 'delete':
                self.cluster_peer_delete('destination')
                self.na_helper.changed = True

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
    Execute action
    :return: None
    """
    community_obj = NetAppONTAPClusterPeer()
    community_obj.apply()


if __name__ == '__main__':
    main()
