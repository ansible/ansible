#!/usr/bin/python

# (c) 2017-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
module: na_ontap_cluster
short_description: NetApp ONTAP cluster - create, join, add license
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create or join or apply licenses to ONTAP clusters
- Cluster join can be performed using only one of the parameters, either cluster_name or cluster_ip_address
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
        cluster_ip_address: 10.61.184.181
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Join cluster
      na_ontap_cluster:
        state: present
        cluster_name: FPaaS-A300-01
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


def local_cmp(a, b):
    """
    compares with only values and not keys, keys should be the same for both dicts
    :param a: dict 1
    :param b: dict 2
    :return: difference of values in both dicts
    """
    diff = [key for key in a if a[key] != b[key]]
    return len(diff)


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
            ]
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_licensing_status(self):
        """
            Check licensing status

            :return: package (key) and licensing status (value)
            :rtype: dict
        """
        license_status = netapp_utils.zapi.NaElement(
            'license-v2-status-list-info')
        try:
            result = self.server.invoke_successfully(license_status,
                                                     enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error checking license status: %s" %
                                  to_native(error), exception=traceback.format_exc())

        return_dictionary = {}
        license_v2_status = result.get_child_by_name('license-v2-status')
        if license_v2_status:
            for license_v2_status_info in license_v2_status.get_children():
                package = license_v2_status_info.get_child_content('package')
                status = license_v2_status_info.get_child_content('method')
                return_dictionary[package] = status

        return return_dictionary

    def create_cluster(self):
        """
        Create a cluster
        """
        cluster_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-create', **{'cluster-name': self.parameters['cluster_name']})

        try:
            self.server.invoke_successfully(cluster_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            # Error 36503 denotes node already being used.
            if to_native(error.code) == "36503":
                return False
            else:
                self.module.fail_json(msg='Error creating cluster %s: %s'
                                      % (self.parameters['cluster_name'], to_native(error)),
                                      exception=traceback.format_exc())
        return True

    def cluster_join(self):
        """
        Add a node to an existing cluster
        """
        if self.parameters.get('cluster_ip_address') is not None:
            cluster_add_node = netapp_utils.zapi.NaElement.create_node_with_children(
                'cluster-join', **{'cluster-ip-address': self.parameters['cluster_ip_address']})
            for_fail_attribute = self.parameters.get('cluster_ip_address')
        elif self.parameters.get('cluster_name') is not None:
            cluster_add_node = netapp_utils.zapi.NaElement.create_node_with_children(
                'cluster-join', **{'cluster-name': self.parameters['cluster_name']})
            for_fail_attribute = self.parameters.get('cluster_name')
        else:
            return False
        try:
            self.server.invoke_successfully(cluster_add_node, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            # Error 36503 denotes node already being used.
            if to_native(error.code) == "36503":
                return False
            else:
                self.module.fail_json(msg='Error adding node to cluster %s: %s'
                                      % (for_fail_attribute, to_native(error)),
                                      exception=traceback.format_exc())
        return True

    def license_v2_add(self):
        """
        Apply a license to cluster
        """
        license_add = netapp_utils.zapi.NaElement.create_node_with_children('license-v2-add')
        license_add.add_node_with_children('codes', **{'license-code-v2': self.parameters['license_code']})
        try:
            self.server.invoke_successfully(license_add, enable_tunneling=True)

        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding license %s: %s'
                                  % (self.parameters['license_code'], to_native(error)),
                                  exception=traceback.format_exc())

    def license_v2_delete(self):
        """
        Delete license from cluster
        """
        license_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'license-v2-delete', **{'package': self.parameters['license_package'],
                                    'serial-number': self.parameters['node_serial_number']})
        try:
            self.server.invoke_successfully(license_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting license : %s' % (to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
        Autosupport log for cluster
        :return:
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_cluster", cserver)

    def apply(self):
        """
        Apply action to cluster
        """
        property_changed = False
        create_flag = False
        join_flag = False

        self.autosupport_log()
        license_status = self.get_licensing_status()

        if self.module.check_mode:
            pass
        else:
            if self.parameters.get('state') == 'present':
                if self.parameters.get('cluster_name') is not None:
                    create_flag = self.create_cluster()
                if not create_flag:
                    join_flag = self.cluster_join()
                if self.parameters.get('license_code') is not None:
                    self.license_v2_add()
                    property_changed = True
                if self.parameters.get('license_package') is not None and\
                        self.parameters.get('node_serial_number') is not None:
                    if license_status.get(str(self.parameters.get('license_package')).lower()) != 'none':
                        self.license_v2_delete()
                        property_changed = True
                if property_changed:
                    new_license_status = self.get_licensing_status()
                    if local_cmp(license_status, new_license_status) == 0:
                        property_changed = False
        changed = property_changed or create_flag or join_flag
        self.module.exit_json(changed=changed)


def main():
    """
    Create object and call apply
    """
    cluster_obj = NetAppONTAPCluster()
    cluster_obj.apply()


if __name__ == '__main__':
    main()
