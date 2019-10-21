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
  - "Enable or disable HA on a cluster"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_cluster_ha
options:
  state:
    choices: ['present', 'absent']
    description:
      - "Whether HA on cluster should be enabled or disabled."
    default: present
short_description: NetApp ONTAP Manage HA status for cluster
version_added: "2.6"
'''

EXAMPLES = """
    - name: "Enable HA status for cluster"
      na_ontap_cluster_ha:
        state: present
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


class NetAppOntapClusterHA(object):
    """
    object initialize and class methods
    """
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
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

    def modify_cluster_ha(self, configure):
        """
        Enable or disable HA on cluster
        :return: None
        """
        cluster_ha_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cluster-ha-modify', **{'ha-configured': configure})
        try:
            self.server.invoke_successfully(cluster_ha_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying cluster HA to %s: %s'
                                  % (configure, to_native(error)),
                                  exception=traceback.format_exc())

    def get_cluster_ha_enabled(self):
        """
        Get current cluster HA details
        :return: dict if enabled, None if disabled
        """
        cluster_ha_get = netapp_utils.zapi.NaElement('cluster-ha-get')
        try:
            result = self.server.invoke_successfully(cluster_ha_get,
                                                     enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching cluster HA details',
                                  exception=traceback.format_exc())
        cluster_ha_info = result.get_child_by_name('attributes').get_child_by_name('cluster-ha-info')
        if cluster_ha_info.get_child_content('ha-configured') == 'true':
            return {'ha-configured': True}
        return None

    def apply(self):
        """
        Apply action to cluster HA
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_cluster_ha", cserver)
        current = self.get_cluster_ha_enabled()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            self.modify_cluster_ha("true")
        elif cd_action == 'delete':
            self.modify_cluster_ha("false")

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Create object and call apply
    """
    ha_obj = NetAppOntapClusterHA()
    ha_obj.apply()


if __name__ == '__main__':
    main()
