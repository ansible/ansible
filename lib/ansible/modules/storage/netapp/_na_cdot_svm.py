#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_svm

short_description: Manage NetApp cDOT svm
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (@timuster) <sumit4@netapp.com>

deprecated:
  removed_in: '2.11'
  why: Updated modules released with increased functionality
  alternative: Use M(na_ontap_svm) instead.

description:
- Create or destroy svm on NetApp cDOT

options:

  state:
    description:
    - Whether the specified SVM should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the SVM to manage.
    required: true

  root_volume:
    description:
    - Root volume of the SVM. Required when C(state=present).

  root_volume_aggregate:
    description:
    - The aggregate on which the root volume will be created.
    - Required when C(state=present).

  root_volume_security_style:
    description:
    -   Security Style of the root volume.
    -   When specified as part of the vserver-create, this field represents the security style for the Vserver root volume.
    -   When specified as part of vserver-get-iter call, this will return the list of matching Vservers.
    -   Possible values are 'unix', 'ntfs', 'mixed'.
    -   The 'unified' security style, which applies only to Infinite Volumes, cannot be applied to a Vserver's root volume.
    -   Valid options are "unix" for NFS, "ntfs" for CIFS, "mixed" for Mixed, "unified" for Unified.
    -   Required when C(state=present)
    choices: ['unix', 'ntfs', 'mixed', 'unified']

'''

EXAMPLES = """

    - name: Create SVM
      na_cdot_svm:
        state: present
        name: ansibleVServer
        root_volume: vol1
        root_volume_aggregate: aggr1
        root_volume_security_style: mixed
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


class NetAppCDOTSVM(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            root_volume=dict(type='str'),
            root_volume_aggregate=dict(type='str'),
            root_volume_security_style=dict(type='str', choices=['unix',
                                                                 'ntfs',
                                                                 'mixed',
                                                                 'unified'
                                                                 ]),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['root_volume',
                                      'root_volume_aggregate',
                                      'root_volume_security_style'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.root_volume = p['root_volume']
        self.root_volume_aggregate = p['root_volume_aggregate']
        self.root_volume_security_style = p['root_volume_security_style']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_vserver(self):
        """
        Checks if vserver exists.

        :return:
            True if vserver found
            False if vserver is not found
        :rtype: bool
        """

        vserver_info = netapp_utils.zapi.NaElement('vserver-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-info', **{'vserver-name': self.name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        vserver_info.add_child_elem(query)

        result = self.server.invoke_successfully(vserver_info,
                                                 enable_tunneling=False)

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):

            """
            TODO:
                Return more relevant parameters about vserver that can
                be updated by the playbook.
            """
            return True
        else:
            return False

    def create_vserver(self):
        vserver_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-create', **{'vserver-name': self.name,
                                 'root-volume': self.root_volume,
                                 'root-volume-aggregate':
                                     self.root_volume_aggregate,
                                 'root-volume-security-style':
                                     self.root_volume_security_style
                                 })

        try:
            self.server.invoke_successfully(vserver_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error provisioning SVM %s with root volume %s on aggregate %s: %s'
                                      % (self.name, self.root_volume, self.root_volume_aggregate, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_vserver(self):
        vserver_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-destroy', **{'vserver-name': self.name})

        try:
            self.server.invoke_successfully(vserver_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error deleting SVM %s with root volume %s on aggregate %s: %s'
                                      % (self.name, self.root_volume, self.root_volume_aggregate, to_native(e)),
                                      exception=traceback.format_exc())

    def rename_vserver(self):
        vserver_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-rename', **{'vserver-name': self.name,
                                 'new-name': self.name})

        try:
            self.server.invoke_successfully(vserver_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error renaming SVM %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        vserver_exists = self.get_vserver()
        rename_vserver = False
        if vserver_exists:
            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                # Update properties
                pass

        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not vserver_exists:
                        self.create_vserver()

                    else:
                        if rename_vserver:
                            self.rename_vserver()

                elif self.state == 'absent':
                    self.delete_vserver()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTSVM()
    v.apply()


if __name__ == '__main__':
    main()
