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
short_description: "Manage HA status for cluster"
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
        parameters = self.module.params
        # set up state variable
        self.state = parameters['state']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def modify_cluster_ha(self, configure):
        """
        Enable or disable HA on cluster
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

    def apply(self):
        """
        Apply action to cluster HA
        """
        changed = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_cluster", cserver)
        if self.state == 'present':
            self.modify_cluster_ha("true")
            changed = True
        elif self.state == 'absent':
            self.modify_cluster_ha("false")
            changed = True

        self.module.exit_json(changed=changed)


def main():
    """
    Create object and call apply
    """
    ha_obj = NetAppOntapClusterHA()
    ha_obj.apply()


if __name__ == '__main__':
    main()
