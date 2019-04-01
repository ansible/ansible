#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Initialize Cluster
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_cluster

short_description: NetApp Element Software Create Cluster
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Initialize Element Software node ownership to form a cluster.

options:
    management_virtual_ip:
        description:
        - Floating (virtual) IP address for the cluster on the management network.
        required: true

    storage_virtual_ip:
        description:
        - Floating (virtual) IP address for the cluster on the storage (iSCSI) network.
        required: true

    replica_count:
        description:
        - Number of replicas of each piece of data to store in the cluster.
        default: '2'

    cluster_admin_username:
        description:
        - Username for the cluster admin.
        - If not provided, default to login username.

    cluster_admin_password:
        description:
        - Initial password for the cluster admin account.
        - If not provided, default to login password.

    accept_eula:
        description:
        - Required to indicate your acceptance of the End User License Agreement when creating this cluster.
        - To accept the EULA, set this parameter to true.
        type: bool

    nodes:
        description:
        - Storage IP (SIP) addresses of the initial set of nodes making up the cluster.
        - nodes IP must be in the list.
        required: true

    attributes:
        description:
        - List of name-value pairs in JSON object format.
'''

EXAMPLES = """

  - name: Initialize new cluster
    tags:
    - elementsw_cluster
    na_elementsw_cluster:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      management_virtual_ip: 10.226.108.32
      storage_virtual_ip: 10.226.109.68
      replica_count: 2
      accept_eula: true
      nodes:
      - 10.226.109.72
      - 10.226.109.74
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
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWCluster(object):
    """
    Element Software Initialize node with ownership for cluster formation
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            management_virtual_ip=dict(required=True, type='str'),
            storage_virtual_ip=dict(required=True, type='str'),
            replica_count=dict(required=False, type='str', default='2'),
            cluster_admin_username=dict(required=False, type='str'),
            cluster_admin_password=dict(required=False, type='str', no_log=True),
            accept_eula=dict(required=False, type='bool'),
            nodes=dict(required=True, type=list),
            attributes=dict(required=False, type='dict', default=None)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        self.management_virtual_ip = input_params['management_virtual_ip']
        self.storage_virtual_ip = input_params['storage_virtual_ip']
        self.replica_count = input_params['replica_count']
        self.accept_eula = input_params.get('accept_eula')
        self.attributes = input_params.get('attributes')
        self.nodes = input_params['nodes']
        self.cluster_admin_username = input_params.get('cluster_admin_username')
        self.cluster_admin_password = input_params.get('cluster_admin_password')

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        if self.attributes is not None:
            self.attributes.update(self.elementsw_helper.set_element_attributes(source='na_elementsw_cluster'))
        else:
            self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_cluster')

    def create_cluster(self):
        """
        Create Cluster
        """
        options = {
            'mvip': self.management_virtual_ip,
            'svip': self.storage_virtual_ip,
            'rep_count': self.replica_count,
            'accept_eula': self.accept_eula,
            'nodes': self.nodes,
            'attributes': self.attributes
        }
        if self.cluster_admin_username is not None:
            options['username'] = self.cluster_admin_username
        if self.cluster_admin_password is not None:
            options['password'] = self.cluster_admin_password
        try:
            self.sfe.create_cluster(**options)
        except Exception as exception_object:
            self.module.fail_json(msg='Error create cluster %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def check_connection(self):
        """
        Check connections to mvip, svip  address.
        :description: To test connection to given IP addressed for mvip and svip

        :rtype: bool
        """
        try:
            mvip_test = self.sfe.test_connect_mvip(mvip=self.management_virtual_ip)
            svip_test = self.sfe.test_connect_svip(svip=self.storage_virtual_ip)

            if mvip_test.details.connected and svip_test.details.connected:
                return True
            else:
                return False
        except Exception as e:
            return False

    def apply(self):
        """
        Check connection and initialize node with cluster ownership
        """
        changed = False
        result_message = None
        if self.module.supports_check_mode and self.accept_eula:
            if self.check_connection():
                self.create_cluster()
                changed = True
            else:
                self.module.fail_json(msg='Error connecting mvip and svip address')
        else:
            result_message = "Skipping changes, No change requested"
        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """
    na_elementsw_cluster = ElementSWCluster()
    na_elementsw_cluster.apply()


if __name__ == '__main__':
    main()
