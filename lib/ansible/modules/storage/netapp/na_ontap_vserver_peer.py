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
  - Create/Delete vserver peer
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_vserver_peer
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified vserver peer should exist or not.
    default: present
  vserver:
    description:
      - Specifies name of the source Vserver in the relationship.
  applications:
    choices: ['snapmirror', 'file_copy', 'lun_copy', 'flexcache']
    description:
      - List of applications which can make use of the peering relationship.
      - FlexCache supported from ONTAP 9.5 onwards.
  peer_vserver:
    description:
      - Specifies name of the peer Vserver in the relationship.
  peer_cluster:
    description:
      - Specifies name of the peer Cluster.
      - Required for creating the vserver peer relationship with a remote cluster
  dest_hostname:
    description:
     - Destination hostname or IP address.
     - Required for creating the vserver peer relationship with a remote cluster
  dest_username:
    description:
     - Destination username.
     - Optional if this is same as source username.
  dest_password:
    description:
     - Destination password.
     - Optional if this is same as source password.
short_description: NetApp ONTAP Vserver peering
version_added: "2.7"
'''

EXAMPLES = """

    - name: Source vserver peer create
      na_ontap_vserver_peer:
        state: present
        peer_vserver: ansible2
        peer_cluster: ansibleCluster
        vserver: ansible
        applications: snapmirror
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        dest_hostname: "{{ netapp_dest_hostname }}"

    - name: vserver peer delete
      na_ontap_vserver_peer:
        state: absent
        peer_vserver: ansible2
        vserver: ansible
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


class NetAppONTAPVserverPeer(object):
    """
    Class with vserver peer methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            peer_vserver=dict(required=True, type='str'),
            peer_cluster=dict(required=False, type='str'),
            applications=dict(required=False, type='list', choices=['snapmirror', 'file_copy', 'lun_copy', 'flexcache']),
            dest_hostname=dict(required=False, type='str'),
            dest_username=dict(required=False, type='str'),
            dest_password=dict(required=False, type='str', no_log=True)
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
            if self.parameters.get('dest_hostname'):
                self.module.params['hostname'] = self.parameters['dest_hostname']
                if self.parameters.get('dest_username'):
                    self.module.params['username'] = self.parameters['dest_username']
                if self.parameters.get('dest_password'):
                    self.module.params['password'] = self.parameters['dest_password']
                self.dest_server = netapp_utils.setup_na_ontap_zapi(module=self.module)
                # reset to source host connection for asup logs
                self.module.params['hostname'] = self.parameters['hostname']

    def vserver_peer_get_iter(self):
        """
        Compose NaElement object to query current vserver using peer-vserver and vserver parameters
        :return: NaElement object for vserver-get-iter with query
        """
        vserver_peer_get = netapp_utils.zapi.NaElement('vserver-peer-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        vserver_peer_info = netapp_utils.zapi.NaElement('vserver-peer-info')
        vserver_peer_info.add_new_child('peer-vserver', self.parameters['peer_vserver'])
        vserver_peer_info.add_new_child('vserver', self.parameters['vserver'])
        query.add_child_elem(vserver_peer_info)
        vserver_peer_get.add_child_elem(query)
        return vserver_peer_get

    def vserver_peer_get(self):
        """
        Get current vserver peer info
        :return: Dictionary of current vserver peer details if query successful, else return None
        """
        vserver_peer_get_iter = self.vserver_peer_get_iter()
        vserver_info = dict()
        try:
            result = self.server.invoke_successfully(vserver_peer_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching vserver peer %s: %s'
                                      % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())
        # return vserver peer details
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) > 0:
            vserver_peer_info = result.get_child_by_name('attributes-list').get_child_by_name('vserver-peer-info')
            vserver_info['peer_vserver'] = vserver_peer_info.get_child_content('peer-vserver')
            vserver_info['vserver'] = vserver_peer_info.get_child_content('vserver')
            vserver_info['peer_state'] = vserver_peer_info.get_child_content('peer-state')
            return vserver_info
        return None

    def vserver_peer_delete(self):
        """
        Delete a vserver peer
        """
        vserver_peer_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-peer-delete', **{'peer-vserver': self.parameters['peer_vserver'],
                                      'vserver': self.parameters['vserver']})
        try:
            self.server.invoke_successfully(vserver_peer_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting vserver peer %s: %s'
                                      % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def get_peer_cluster_name(self):
        """
        Get local cluster name
        :return: cluster name
        """
        cluster_info = netapp_utils.zapi.NaElement('cluster-identity-get')
        try:
            result = self.server.invoke_successfully(cluster_info, enable_tunneling=True)
            return result.get_child_by_name('attributes').get_child_by_name(
                'cluster-identity-info').get_child_content('cluster-name')
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching peer cluster name for peer vserver %s: %s'
                                      % (self.parameters['peer_vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def vserver_peer_create(self):
        """
        Create a vserver peer
        """
        if self.parameters.get('applications') is None:
            self.module.fail_json(msg='applications parameter is missing')
        if self.parameters.get('peer_cluster') is not None and self.parameters.get('dest_hostname') is None:
            self.module.fail_json(msg='dest_hostname is required for peering a vserver in remote cluster')
        if self.parameters.get('peer_cluster') is None:
            self.parameters['peer_cluster'] = self.get_peer_cluster_name()
        vserver_peer_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-peer-create', **{'peer-vserver': self.parameters['peer_vserver'],
                                      'vserver': self.parameters['vserver'],
                                      'peer-cluster': self.parameters['peer_cluster']})
        applications = netapp_utils.zapi.NaElement('applications')
        for application in self.parameters['applications']:
            applications.add_new_child('vserver-peer-application', application)
        vserver_peer_create.add_child_elem(applications)
        try:
            self.server.invoke_successfully(vserver_peer_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating vserver peer %s: %s'
                                      % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def is_remote_peer(self):
        if self.parameters.get('dest_hostname') is None or \
                (self.parameters['dest_hostname'] == self.parameters['hostname']):
            return False
        return True

    def vserver_peer_accept(self):
        """
        Accept a vserver peer at destination
        """
        # peer-vserver -> remote (source vserver is provided)
        # vserver -> local (destination vserver is provided)
        vserver_peer_accept = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-peer-accept', **{'peer-vserver': self.parameters['vserver'],
                                      'vserver': self.parameters['peer_vserver']})
        try:
            self.dest_server.invoke_successfully(vserver_peer_accept, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error accepting vserver peer %s: %s'
                                      % (self.parameters['peer_vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to create/delete or accept vserver peer
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_vserver_peer", cserver)
        current = self.vserver_peer_get()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            self.vserver_peer_create()
            # accept only if the peer relationship is on a remote cluster
            if self.is_remote_peer():
                self.vserver_peer_accept()
        elif cd_action == 'delete':
            self.vserver_peer_delete()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPVserverPeer()
    community_obj.apply()


if __name__ == '__main__':
    main()
