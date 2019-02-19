#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_disks

short_description: NetApp ONTAP Assign disks to nodes
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Assign all or part of disks to nodes.

options:

  node:
    required: true
    description:
    - It specifies the node to assign all visible unowned disks.
'''

EXAMPLES = """
- name: Assign unowned disks
  na_ontap_disks:
    node: cluster-01
    hostname: "{{ hostname }} "
    username: "{{ admin username }}"
    password: "{{ admin password }}"
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapDisks(object):
    ''' object initialize and class methods '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            node=dict(required=True, type='str'),
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

    def disk_check(self):
        """
        Check for disks
        """
        disk_iter = netapp_utils.zapi.NaElement('storage-disk-get-iter')
        disk_storage_info = netapp_utils.zapi.NaElement('storage-disk-info')
        disk_raid_info = netapp_utils.zapi.NaElement('disk-raid-info')
        disk_raid_info.add_new_child('container-type', 'unassigned')
        disk_storage_info.add_child_elem(disk_raid_info)

        disk_query = netapp_utils.zapi.NaElement('query')
        disk_query.add_child_elem(disk_storage_info)

        disk_iter.add_child_elem(disk_query)
        result = self.server.invoke_successfully(disk_iter, True)

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            has_disks = "true"
            return has_disks

    def disk_assign(self):
        """
        enable aggregate (online).
        """
        assign_disk = netapp_utils.zapi.NaElement.create_node_with_children(
            'disk-sanown-assign', **{'node-name': self.parameters['node'],
                                     'all': 'true'})
        try:
            self.server.invoke_successfully(assign_disk,
                                            enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == "13001":
                # Error 13060 denotes aggregate is already online
                return False
            else:
                self.module.fail_json(msg='Error assigning disks %s' %
                                      (to_native(error)),
                                      exception=traceback.format_exc())

    def apply(self):
        '''Apply action to disks'''
        changed = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_disks", cserver)

        # check if anything needs to be changed (add/delete/update)
        unowned_disks = self.disk_check()
        if unowned_disks == 'true':
            self.disk_assign()
            changed = True
        self.module.exit_json(changed=changed)


def main():
    ''' Create object and call apply '''
    obj_aggr = NetAppOntapDisks()
    obj_aggr.apply()


if __name__ == '__main__':
    main()
