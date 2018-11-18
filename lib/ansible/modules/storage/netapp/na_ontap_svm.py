#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_svm

short_description: Manage NetApp ONTAP svm
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)

description:
- Create, modify or delete svm on NetApp ONTAP

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

  from_name:
    description:
    - Name of the SVM to be renamed
    version_added: '2.7'

  root_volume:
    description:
    - Root volume of the SVM.
    - Cannot be modified after creation.

  root_volume_aggregate:
    description:
    - The aggregate on which the root volume will be created.
    - Cannot be modified after creation.

  root_volume_security_style:
    description:
    -   Security Style of the root volume.
    -   When specified as part of the vserver-create,
        this field represents the security style for the Vserver root volume.
    -   When specified as part of vserver-get-iter call,
        this will return the list of matching Vservers.
    -   The 'unified' security style, which applies only to Infinite Volumes,
        cannot be applied to a Vserver's root volume.
    -   Cannot be modified after creation.
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

  ipspace:
    description:
    - IPSpace name
    - Cannot be modified after creation.
    version_added: '2.7'


  snapshot_policy:
    description:
    - Default snapshot policy setting for all volumes of the Vserver.
      This policy will be assigned to all volumes created in this
      Vserver unless the volume create request explicitly provides a
      snapshot policy or volume is modified later with a specific
      snapshot policy. A volume-level snapshot policy always overrides
      the default Vserver-wide snapshot policy.
    version_added: '2.7'

  language:
    description:
    - Language to use for the SVM
    - Default to C.UTF-8
    - Possible values   Language
    - c                 POSIX
    - ar                Arabic
    - cs                Czech
    - da                Danish
    - de                German
    - en                English
    - en_us             English (US)
    - es                Spanish
    - fi                Finnish
    - fr                French
    - he                Hebrew
    - hr                Croatian
    - hu                Hungarian
    - it                Italian
    - ja                Japanese euc-j
    - ja_v1             Japanese euc-j
    - ja_jp.pck         Japanese PCK (sjis)
    - ja_jp.932         Japanese cp932
    - ja_jp.pck_v2      Japanese PCK (sjis)
    - ko                Korean
    - no                Norwegian
    - nl                Dutch
    - pl                Polish
    - pt                Portuguese
    - ro                Romanian
    - ru                Russian
    - sk                Slovak
    - sl                Slovenian
    - sv                Swedish
    - tr                Turkish
    - zh                Simplified Chinese
    - zh.gbk            Simplified Chinese (GBK)
    - zh_tw             Traditional Chinese euc-tw
    - zh_tw.big5        Traditional Chinese Big 5
    version_added: '2.7'

  subtype:
    description:
    - The subtype for vserver to be created.
    - Cannot be modified after creation.
    choices: ['default', 'dp_destination', 'sync_source', 'sync_destination']
    version_added: '2.7'


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
            from_name=dict(required=False, type='str'),
            root_volume=dict(type='str'),
            root_volume_aggregate=dict(type='str'),
            root_volume_security_style=dict(type='str', choices=['unix',
                                                                 'ntfs',
                                                                 'mixed',
                                                                 'unified'
                                                                 ]),
            allowed_protocols=dict(type='list'),
            aggr_list=dict(type='list'),
            ipspace=dict(type='str', required=False),
            snapshot_policy=dict(type='str', required=False),
            language=dict(type='str', required=False),
            subtype=dict(choices=['default', 'dp_destination', 'sync_source', 'sync_destination'])
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.from_name = p['from_name']
        self.root_volume = p['root_volume']
        self.root_volume_aggregate = p['root_volume_aggregate']
        self.root_volume_security_style = p['root_volume_security_style']
        self.allowed_protocols = p['allowed_protocols']
        self.aggr_list = p['aggr_list']
        self.language = p['language']
        self.ipspace = p['ipspace']
        self.snapshot_policy = p['snapshot_policy']
        self.subtype = p['subtype']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_vserver(self, vserver_name=None):
        """
        Checks if vserver exists.

        :return:
            vserver object if vserver found
            None if vserver is not found
        :rtype: object/None
        """
        if vserver_name is None:
            vserver_name = self.name

        vserver_info = netapp_utils.zapi.NaElement('vserver-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-info', **{'vserver-name': vserver_name})

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
            vserver_details = {'name': vserver_info.get_child_content('vserver-name'),
                               'root_volume': vserver_info.get_child_content('root-volume'),
                               'root_volume_aggregate': vserver_info.get_child_content('root-volume-aggregate'),
                               'root_volume_security_style': vserver_info.get_child_content('root-volume-security-style'),
                               'subtype': vserver_info.get_child_content('vserver-subtype'),
                               'aggr_list': aggr_list,
                               'language': vserver_info.get_child_content('language'),
                               'snapshot_policy': vserver_info.get_child_content('snapshot-policy'),
                               'allowed_protocols': protocols}
        return vserver_details

    def create_vserver(self):
        options = {'vserver-name': self.name, 'root-volume': self.root_volume}
        if self.root_volume_aggregate is not None:
            options['root-volume-aggregate'] = self.root_volume_aggregate
        if self.root_volume_security_style is not None:
            options['root-volume-security-style'] = self.root_volume_security_style
        if self.language is not None:
            options['language'] = self.language
        if self.ipspace is not None:
            options['ipspace'] = self.ipspace
        if self.snapshot_policy is not None:
            options['snapshot-policy'] = self.snapshot_policy
        if self.subtype is not None:
            options['vserver-subtype'] = self.subtype

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
            'vserver-rename', **{'vserver-name': self.from_name,
                                 'new-name': self.name})

        try:
            self.server.invoke_successfully(vserver_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error renaming SVM %s: %s'
                                  % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def modify_vserver(self, allowed_protocols, aggr_list, language, snapshot_policy):

        options = {'vserver-name': self.name}
        if language:
            options['language'] = self.language
        if snapshot_policy:
            options['snapshot-policy'] = self.snapshot_policy

        vserver_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'vserver-modify', **options)

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
# These are being commentted out as part of bugfix 595.

#         if vserver_details is not None:
#             results = netapp_utils.get_cserver(self.server)
#             cserver = netapp_utils.setup_ontap_zapi(
#                 module=self.module, vserver=results)
#             netapp_utils.ems_log_event("na_ontap_svm", cserver)

        rename_vserver = False
        modify_protocols = False
        modify_aggr_list = False
        modify_snapshot_policy = False
        modify_language = False

        if vserver_details is not None:
            if self.state == 'absent':
                changed = True
            elif self.state == 'present':
                # SVM is present, is it a modify?
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
                if self.snapshot_policy is not None:
                    if self.snapshot_policy != vserver_details['snapshot_policy']:
                        modify_snapshot_policy = True
                        changed = True
                if self.language is not None:
                    if self.language != vserver_details['language']:
                        modify_language = True
                        changed = True
                if self.root_volume is not None and self.root_volume != vserver_details['root_volume']:
                    self.module.fail_json(msg='Error modifying SVM %s: %s' % (self.name, 'cannot change root volume'))
                if self.root_volume_aggregate is not None and self.root_volume_aggregate != vserver_details['root_volume_aggregate']:
                    self.module.fail_json(msg='Error modifying SVM %s: %s' % (self.name, 'cannot change root volume aggregate'))
                if self.root_volume_security_style is not None and self.root_volume_security_style != vserver_details['root_volume_security_style']:
                    self.module.fail_json(msg='Error modifying SVM %s: %s' % (self.name, 'cannot change root volume security style'))
                if self.subtype is not None and self.subtype != vserver_details['subtype']:
                    self.module.fail_json(msg='Error modifying SVM %s: %s' % (self.name, 'cannot change subtype'))
                if self.ipspace is not None and self.ipspace != vserver_details['ipspace']:
                    self.module.fail_json(msg='Error modifying SVM %s: %s' % (self.name, 'cannot change ipspace'))
        else:
            if self.state == 'present':
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if vserver_details is None:
                        # create or rename
                        if self.from_name is not None and self.get_vserver(self.from_name):
                            self.rename_vserver()
                        else:
                            self.create_vserver()
                    else:
                        if modify_protocols or modify_aggr_list:
                            self.modify_vserver(
                                modify_protocols, modify_aggr_list, modify_language, modify_snapshot_policy)
                elif self.state == 'absent':
                    self.delete_vserver()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapSVM()
    v.apply()


if __name__ == '__main__':
    main()
