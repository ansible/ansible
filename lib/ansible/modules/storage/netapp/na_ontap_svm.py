#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_svm

short_description: Manage NetApp Ontap svm
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Sumit Kumar (sumit4@netapp.com), Archana Ganesan (garchana@netapp.com)

description:
- Create, modify or delete svm on NetApp Ontap

options:

  state:
    description:
    - Whether the specified SVM should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the SVM to manage.
    required: true

  new_name:
    description:
    - New name of the SVM to be renamed

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
    -   When specified as part of the vserver-create,
        this field represents the security style for the Vserver root volume.
    -   When specified as part of vserver-get-iter call,
        this will return the list of matching Vservers.
    -   The 'unified' security style, which applies only to Infinite Volumes,
        cannot be applied to a Vserver's root volume.
    -   Required when C(state=present)
    choices: ['unix', 'ntfs', 'mixed', 'unified']

  allowed_protocols:
    description:
    - Allowed Protocols.
    - When specified as part of a vserver-create,
      this field represent the list of protocols allowed on the Vserver.
    - When part of vserver-get-iter call,
      this will return the list of Vservers
      which have any of the protocols specified
      as part of the allowed-protocols.
    - When part of vserver-modify,
      this field should include the existing list
      along with new protocol list to be added to prevent data disruptions.
    - Possible values
    - nfs   NFS protocol,
    - cifs   CIFS protocol,
    - fcp   FCP protocol,
    - iscsi   iSCSI protocol,
    - ndmp   NDMP protocol,
    - http   HTTP protocol,
    - nvme   NVMe protocol

  aggr_list:
    description:
    - List of aggregates assigned for volume operations.
    - These aggregates could be shared for use with other Vservers.
    - When specified as part of a vserver-create,
      this field represents the list of aggregates
      that are assigned to the Vserver for volume operations.
    - When part of vserver-get-iter call,
      this will return the list of Vservers
      which have any of the aggregates specified as part of the aggr-list.

'''

EXAMPLES = """

    - name: Create SVM
      na_ontap_svm:
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

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSVM(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            new_name=dict(required=False, type='str'),
            root_volume=dict(type='str'),
            root_volume_aggregate=dict(type='str'),
            root_volume_security_style=dict(type='str', choices=['unix',
                                                                 'ntfs',
                                                                 'mixed',
                                                                 'unified'
                                                                 ]),
            allowed_protocols=dict(type='list'),
            aggr_list=dict(type='list')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.new_name = p['new_name']
        self.root_volume = p['root_volume']
        self.root_volume_aggregate = p['root_volume_aggregate']
        self.root_volume_security_style = p['root_volume_security_style']
        self.allowed_protocols = p['allowed_protocols']
        self.aggr_list = p['aggr_list']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

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
        vserver_details = None
        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            attributes_list = result.get_child_by_name('attributes-list')
            vserver_info = attributes_list.get_child_by_name('vserver-info')
            aggr_list = list()
            ''' vserver aggr-list can be empty by default'''
            get_list = vserver_info.get_child_by_name('aggr-list')
            if get_list is not None:
                aggregates = get_list.get_children()
                for aggr in aggregates:
                    aggr_list.append(aggr.get_content())

            protocols = list()
            '''allowed-protocols is not empty by default'''
            get_protocols = vserver_info.get_child_by_name(
                'allowed-protocols').get_children()
            for protocol in get_protocols:
                protocols.append(protocol.get_content())
            vserver_details = {'name': vserver_info.get_child_content(
                               'vserver-name'),
                               'aggr_list': aggr_list,
                               'allowed_protocols': protocols}
        return vserver_details

    def create_vserver(self):
        options = {'vserver-name': self.name, 'root-volume': self.root_volume}
        if self.root_volume_aggregate is not None:
            options['root-volume-aggregate'] = self.root_volume_aggregate
        if self.root_volume_security_style is not None:
            options['root-volume-security-style'] = self.root_volume_security_style

        vserver_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-create', **options)
        try:
            self.server.invoke_successfully(vserver_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error provisioning SVM %s \
                                  with root volume %s on aggregate %s: %s'
                                  % (self.name, self.root_volume,
                                     self.root_volume_aggregate, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_vserver(self):
        vserver_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-destroy', **{'vserver-name': self.name})

        try:
            self.server.invoke_successfully(vserver_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error deleting SVM %s \
                                  with root volume %s on aggregate %s: %s'
                                  % (self.name, self.root_volume,
                                     self.root_volume_aggregate, to_native(e)),
                                  exception=traceback.format_exc())

    def rename_vserver(self):
        vserver_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-rename', **{'vserver-name': self.name,
                                 'new-name': self.new_name})

        try:
            self.server.invoke_successfully(vserver_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error renaming SVM %s: %s'
                                  % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def modify_vserver(self, allowed_protocols, aggr_list):
        vserver_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-modify', **{'vserver-name': self.name})

        if allowed_protocols:
            allowed_protocols = netapp_utils.zapi.NaElement(
                'allowed-protocols')
            for protocol in self.allowed_protocols:
                allowed_protocols.add_new_child('protocol', protocol)
            vserver_modify.add_child_elem(allowed_protocols)

        if aggr_list:
            aggregates = netapp_utils.zapi.NaElement('aggr-list')
            for aggr in self.aggr_list:
                aggregates.add_new_child('aggr-name', aggr)
            vserver_modify.add_child_elem(aggregates)

        try:
            self.server.invoke_successfully(vserver_modify,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying SVM %s: %s'
                                  % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        vserver_details = self.get_vserver()
        if vserver_details is not None:
            results = netapp_utils.get_cserver(self.server)
            cserver = netapp_utils.setup_ontap_zapi(
                module=self.module, vserver=results)
            netapp_utils.ems_log_event("na_ontap_svm", cserver)

        rename_vserver = False
        modify_protocols = False
        modify_aggr_list = False
        obj = open('vserver-log', 'a')
        if vserver_details is not None:
            if self.state == 'absent':
                changed = True
            elif self.state == 'present':
                if self.new_name is not None and self.new_name != self.name:
                    rename_vserver = True
                    changed = True
                if self.allowed_protocols is not None:
                    self.allowed_protocols.sort()
                    vserver_details['allowed_protocols'].sort()
                    if self.allowed_protocols != vserver_details['allowed_protocols']:
                        modify_protocols = True
                        changed = True
                if self.aggr_list is not None:
                    self.aggr_list.sort()
                    vserver_details['aggr_list'].sort()
                    if self.aggr_list != vserver_details['aggr_list']:
                        modify_aggr_list = True
                        changed = True
        else:
            if self.state == 'present':
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if vserver_details is None:
                        self.create_vserver()
                    else:
                        if rename_vserver:
                            self.rename_vserver()
                        if modify_protocols or modify_aggr_list:
                            self.modify_vserver(
                                modify_protocols, modify_aggr_list)
                elif self.state == 'absent':
                    self.delete_vserver()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapSVM()
    v.apply()


if __name__ == '__main__':
    main()
