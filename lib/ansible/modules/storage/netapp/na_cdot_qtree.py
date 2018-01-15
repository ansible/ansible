#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_qtree

short_description: Manage qtrees
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy Qtrees.

options:

  state:
    description:
    - Whether the specified Qtree should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the Qtree to manage.
    required: true

  flexvol_name:
    description:
    - The name of the FlexVol the Qtree should exist on. Required when C(state=present).

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """
- name: Create QTree
  na_cdot_qtree:
    state: present
    name: ansibleQTree
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Rename QTree
  na_cdot_qtree:
    state: present
    name: ansibleQTree
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
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


class NetAppCDOTQTree(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            flexvol_name=dict(type='str'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['flexvol_name'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.flexvol_name = p['flexvol_name']
        self.vserver = p['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_qtree(self):
        """
        Checks if the qtree exists.

        :return:
            True if qtree found
            False if qtree is not found
        :rtype: bool
        """

        qtree_list_iter = netapp_utils.zapi.NaElement('qtree-list-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-info', **{'vserver': self.vserver,
                             'volume': self.flexvol_name,
                             'qtree': self.name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        qtree_list_iter.add_child_elem(query)

        result = self.server.invoke_successfully(qtree_list_iter,
                                                 enable_tunneling=True)

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_qtree(self):
        qtree_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-create', **{'volume': self.flexvol_name,
                               'qtree': self.name})

        try:
            self.server.invoke_successfully(qtree_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error provisioning qtree %s: %s" % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_qtree(self):
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        qtree_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-delete', **{'qtree': path})

        try:
            self.server.invoke_successfully(qtree_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error deleting qtree %s: %s" % (path, to_native(e)),
                                  exception=traceback.format_exc())

    def rename_qtree(self):
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        new_path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        qtree_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-rename', **{'qtree': path,
                               'new-qtree-name': new_path})

        try:
            self.server.invoke_successfully(qtree_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error renaming qtree %s: %s" % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        qtree_exists = False
        rename_qtree = False
        qtree_detail = self.get_qtree()

        if qtree_detail:
            qtree_exists = True

            if self.state == 'absent':
                # Qtree exists, but requested state is 'absent'.
                changed = True

            elif self.state == 'present':
                if self.name is not None and not self.name == \
                        self.name:
                    changed = True
                    rename_qtree = True

        else:
            if self.state == 'present':
                # Qtree does not exist, but requested state is 'present'.
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not qtree_exists:
                        self.create_qtree()

                    else:
                        if rename_qtree:
                            self.rename_qtree()

                elif self.state == 'absent':
                    self.delete_qtree()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTQTree()
    v.apply()


if __name__ == '__main__':
    main()
