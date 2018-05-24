#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: na_ontap_cluster
short_description: Create/Join ONTAP cluster. Apply license to cluster
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Suhas Bangalore Shekar (bsuhas@netapp.com), Archana Ganesan (garchana@netapp.com)
description:
- Create or join or apply licenses to ONTAP clusters
options:
  state:
    description:
    - Whether the specified cluster should exist or not.
    choices: ['present']
    default: present
  cluster_name:
    description:
    - The name of the cluster to manage.
  cluster_ip_address:
    description:
    - IP address of cluster to be joined
  license_code:
    description:
    - License code to be applied to the cluster
  license_package:
    description:
    - License package name of the license to be removed
  node_serial_number:
    description:
    - Serial number of the cluster node

'''

EXAMPLES = """
    - name: Create cluster
      na_ontap_cluster:
        state: present
        cluster_name: new_cluster
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Add license from cluster
      na_ontap_cluster:
        state: present
        cluster_name: FPaaS-A300-01
        license_code: SGHLQDBBVAAAAAAAAAAAAAAAAAAA
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Join cluster
      na_ontap_cluster:
        state: present
        cluster_name: FPaaS-A300
        cluster_ip_address: 10.61.184.181
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

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPCluster(object):
    """
    object initialize and class methods
    """
    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            cluster_name=dict(required=False, type='str'),
            cluster_ip_address=dict(required=False, type='str'),
            license_code=dict(required=False, type='str'),
            license_package=dict(required=False, type='str'),
            node_serial_number=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
            required_together=[
                ['license_package', 'node_serial_number']
            ],
            mutually_exclusive=[
                ['cluster_name', 'cluster_ip_address'],
            ]
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.cluster_ip_address = parameters['cluster_ip_address']
        self.cluster_name = parameters['cluster_name']
        self.license_code = parameters['license_code']
        self.license_package = parameters['license_package']
        self.node_serial_number = parameters['node_serial_number']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def create_cluster(self):
        """
        Create a cluster
        """
        cluster_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-create', **{'cluster-name': self.cluster_name})

        try:
            self.server.invoke_successfully(cluster_create,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            # Error 36503 denotes node already being used.
            if to_native(error.code) == "36503":
                return False
            else:
                self.module.fail_json(msg='Error creating cluster %s: %s'
                                      % (self.cluster_name, to_native(error)),
                                      exception=traceback.format_exc())

    def cluster_join(self):
        """
        Add a node to an existing cluster
        """
        cluster_add_node = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-join', **{'cluster-ip-address': self.cluster_ip_address})

        try:
            self.server.invoke_successfully(cluster_add_node, enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            # Error 36503 denotes node already being used.
            if to_native(error.code) == "36503":
                return False
            else:
                self.module.fail_json(msg='Error adding node to cluster %s: %s'
                                      % (self.cluster_name, to_native(error)),
                                      exception=traceback.format_exc())

    def license_v2_add(self):
        """
        Apply a license to cluster
        """
        license_add = netapp_utils.zapi.NaElement.create_node_with_children('license-v2-add')
        license_add.add_node_with_children('codes', **{'license-code-v2': self.license_code})
        try:
            self.server.invoke_successfully(license_add, enable_tunneling=True)

        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding license to the cluster %s: %s'
                                  % (self.cluster_name, to_native(error)),
                                  exception=traceback.format_exc())

    def license_v2_delete(self):
        """
        Delete license from cluster
        """
        license_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'license-v2-delete', **{'package': self.license_package,
                                    'serial-number': self.node_serial_number})
        try:
            self.server.invoke_successfully(license_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting license from cluster %s : %s'
                                  % (self.cluster_name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to cluster
        """
        property_changed = False
        create_flag = False
        join_flag = False
        changed = False

        if self.state == 'absent':
            pass
        elif self.state == 'present':  # license add, delete
            changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if self.cluster_name is not None:
                        create_flag = self.create_cluster()
                    if self.cluster_ip_address is not None:
                        join_flag = self.cluster_join()
                    if self.license_code is not None:
                        self.license_v2_add()
                        property_changed = True
                    if self.license_package is not None and self.node_serial_number is not None:
                        self.license_v2_delete()
                        property_changed = True
        changed = property_changed or create_flag or join_flag
        self.module.exit_json(changed=changed)


def main():
    """
    Create object and call apply
    """
    rule_obj = NetAppONTAPCluster()
    rule_obj.apply()


if __name__ == '__main__':
    main()
