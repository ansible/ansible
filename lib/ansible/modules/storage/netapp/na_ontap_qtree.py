#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_qtree

short_description: NetApp ONTAP manage qtrees
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create or destroy Qtrees.

options:

  state:
    description:
    - Whether the specified qtree should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the qtree to manage.
    required: true

  from_name:
    description:
    - Name of the qtree to be renamed.
    version_added: '2.7'

  flexvol_name:
    description:
    - The name of the FlexVol the qtree should exist on. Required when C(state=present).

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """
- name: Create Qtrees
  na_ontap_qtree:
    state: present
    name: ansibleQTree
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Rename Qtrees
  na_ontap_qtree:
    state: present
    from_name: ansibleQTree_rename
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


class NetAppOntapQTree(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
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
        self.from_name = p['from_name']
        self.flexvol_name = p['flexvol_name']
        self.vserver = p['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def get_qtree(self, name=None):
        """
        Checks if the qtree exists.

        :return:
            True if qtree found
            False if qtree is not found
        :rtype: bool
        """
        if name is None:
            name = self.name

        qtree_list_iter = netapp_utils.zapi.NaElement('qtree-list-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-info', **{'vserver': self.vserver,
                             'volume': self.flexvol_name,
                             'qtree': name})

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
        path = '/vol/%s/%s' % (self.flexvol_name, self.from_name)
        new_path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        qtree_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-rename', **{'qtree': path,
                               'new-qtree-name': new_path})

        try:
            self.server.invoke_successfully(qtree_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error renaming qtree %s: %s" % (self.from_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        qtree_exists = False
        rename_qtree = False
        netapp_utils.ems_log_event("na_ontap_qtree", self.server)
        qtree_detail = self.get_qtree()
        if qtree_detail:
            qtree_exists = True
            if self.state == 'absent':  # delete
                changed = True
        elif self.state == 'present':
            # create or rename qtree
            if self.from_name:
                if self.get_qtree(self.from_name) is None:
                    self.module.fail_json(msg="Error renaming qtree %s: does not exists" % self.from_name)
                else:
                    changed = True
                    rename_qtree = True
            else:
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if rename_qtree:
                        self.rename_qtree()
                    else:
                        self.create_qtree()
                elif self.state == 'absent':
                    self.delete_qtree()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapQTree()
    v.apply()


if __name__ == '__main__':
    main()
