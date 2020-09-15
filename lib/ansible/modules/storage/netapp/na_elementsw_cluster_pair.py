#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_cluster_pair

short_description: NetApp Element Software Manage Cluster Pair
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, delete cluster pair

options:

    state:
      description:
      - Whether the specified cluster pair should exist or not.
      choices: ['present', 'absent']
      default: present

    dest_mvip:
      description:
      - Destination IP address of the cluster to be paired.
      required: true

    dest_username:
      description:
      - Destination username for the cluster to be paired.
      - Optional if this is same as source cluster username.

    dest_password:
      description:
      - Destination password for the cluster to be paired.
      - Optional if this is same as source cluster password.

'''

EXAMPLES = """
   - name: Create cluster pair
     na_elementsw_cluster_pair:
       hostname: "{{ src_hostname }}"
       username: "{{ src_username }}"
       password: "{{ src_password }}"
       state: present
       dest_mvip: "{{ dest_hostname }}"

   - name: Delete cluster pair
     na_elementsw_cluster_pair:
       hostname: "{{ src_hostname }}"
       username: "{{ src_username }}"
       password: "{{ src_password }}"
       state: absent
       dest_mvip: "{{ dest_hostname }}"
       dest_username: "{{ dest_username }}"
       dest_password: "{{ dest_password }}"

"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule
from ansible.module_utils.netapp_module import NetAppModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except ImportError:
    HAS_SF_SDK = False


class ElementSWClusterPair(object):
    """ class to handle cluster pairing operations """

    def __init__(self):
        """
            Setup Ansible parameters and ElementSW connection
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            dest_mvip=dict(required=True, type='str'),
            dest_username=dict(required=False, type='str'),
            dest_password=dict(required=False, type='str', no_log=True)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.elem = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.elem)
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # get element_sw_connection for destination cluster
        # overwrite existing source host, user and password with destination credentials
        self.module.params['hostname'] = self.parameters['dest_mvip']
        # username and password is same as source,
        # if dest_username and dest_password aren't specified
        if self.parameters.get('dest_username'):
            self.module.params['username'] = self.parameters['dest_username']
        if self.parameters.get('dest_password'):
            self.module.params['password'] = self.parameters['dest_password']
        self.dest_elem = netapp_utils.create_sf_connection(module=self.module)
        self.dest_elementsw_helper = NaElementSWModule(self.dest_elem)

    def check_if_already_paired(self, paired_clusters, hostname):
        for pair in paired_clusters.cluster_pairs:
            if pair.mvip == hostname:
                return pair.cluster_pair_id
        return None

    def get_src_pair_id(self):
        """
            Check for idempotency
        """
        # src cluster and dest cluster exist
        paired_clusters = self.elem.list_cluster_pairs()
        return self.check_if_already_paired(paired_clusters, self.parameters['dest_mvip'])

    def get_dest_pair_id(self):
        """
        Getting destination cluster_pair_id
        """
        paired_clusters = self.dest_elem.list_cluster_pairs()
        return self.check_if_already_paired(paired_clusters, self.parameters['hostname'])

    def pair_clusters(self):
        """
            Start cluster pairing on source, and complete on target cluster
        """
        try:
            pair_key = self.elem.start_cluster_pairing()
            self.dest_elem.complete_cluster_pairing(
                cluster_pairing_key=pair_key.cluster_pairing_key)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error pairing cluster %s and %s"
                                  % (self.parameters['hostname'],
                                     self.parameters['dest_mvip']),
                                  exception=to_native(err))

    def unpair_clusters(self, pair_id_source, pair_id_dest):
        """
            Delete cluster pair
        """
        try:
            self.elem.remove_cluster_pair(cluster_pair_id=pair_id_source)
            self.dest_elem.remove_cluster_pair(cluster_pair_id=pair_id_dest)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error unpairing cluster %s and %s"
                                  % (self.parameters['hostname'],
                                     self.parameters['dest_mvip']),
                                  exception=to_native(err))

    def apply(self):
        """
            Call create / delete cluster pair methods
        """
        pair_id_source = self.get_src_pair_id()
        # If already paired, find the cluster_pair_id of destination cluster
        if pair_id_source:
            pair_id_dest = self.get_dest_pair_id()
        # calling helper to determine action
        cd_action = self.na_helper.get_cd_action(pair_id_source, self.parameters)
        if cd_action == "create":
            self.pair_clusters()
        elif cd_action == "delete":
            self.unpair_clusters(pair_id_source, pair_id_dest)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """ Apply cluster pair actions """
    cluster_obj = ElementSWClusterPair()
    cluster_obj.apply()


if __name__ == '__main__':
    main()
