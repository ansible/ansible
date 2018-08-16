#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_export_policy_rule

short_description: Manage ONTAP Export rules
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Suhas Bangalore Shekar (bsuhas@netapp.com), Archana Ganeshan (garchana@netapp.com)

description:
- Create or delete or modify export rules in ONTAP

options:
  state:
    description:
    - Whether the specified export policy rule should exist or not.
    required: false
    choices: ['present', 'absent']
    default: present

  policy_name:
    description:
    - The name of the export rule to manage.
    required: True

  client_match:
    description:
    - List of Client Match Hostnames, IP Addresses, Netgroups, or Domains

  ro_rule:
    description:
    - Read only access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  rw_rule:
    description:
    - Read Write access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  super_user_security:
    description:
    - Read Write access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  allow_suid:
    description:
    - If 'true', NFS server will honor SetUID bits in SETATTR operation. Default value is 'true'
    choices: ['True', 'False']

  protocol:
    description:
    - Client access protocol. Default value is 'any'
    choices: [any,nfs,nfs3,nfs4,cifs,flexcache]
    default: any

  rule_index:
    description:
    - rule index of the export policy for delete and modify

  vserver:
    description:
    - Name of the vserver to use.
    required: true

'''

EXAMPLES = """
    - name: Create ExportPolicyRule
      na_ontap_export_policy_rule:
        state: present
        policy_name: default123
        vserver: ci_dev
        client_match: 0.0.0.0/0
        ro_rule: any
        rw_rule: any
        protocol: any
        super_user_security: any
        allow_suid: true
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete ExportPolicyRule
      na_ontap_export_policy_rule:
        state: absent
        policy_name: default123
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Modify ExportPolicyRule
      na_ontap_export_policy_rule:
        state: present
        policy_name: default123
        client_match: 0.0.0.0/0
        ro_rule: any
        rw_rule: any
        super_user_security: none
        protocol: any
        allow_suid: false
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """


"""
import traceback

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppontapExportRule(object):
    ''' object initialize and class methods '''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            policy_name=dict(required=True, type='str'),
            protocol=dict(required=False,
                          type='str', default='any',
                          choices=['any', 'nfs', 'nfs3', 'nfs4', 'cifs', 'flexcache']),
            client_match=dict(required=False, type='str'),
            ro_rule=dict(required=False,
                         type='str', default=None,
                         choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            rw_rule=dict(required=False,
                         type='str', default=None,
                         choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            super_user_security=dict(required=False,
                                     type='str', default=None,
                                     choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            allow_suid=dict(required=False, choices=['True', 'False']),
            rule_index=dict(required=False, type='int', default=None),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['client_match', 'ro_rule', 'rw_rule']),
                ('state', 'absent', ['client_match'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.policy_name = parameters['policy_name']
        self.protocol = parameters['protocol']
        self.client_match = parameters['client_match']
        self.ro_rule = parameters['ro_rule']
        self.rw_rule = parameters['rw_rule']
        self.allow_suid = parameters['allow_suid']
        self.vserver = parameters['vserver']
        self.super_user_security = parameters['super_user_security']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def get_export_policy_rule(self):
        """
        Return details about the export policy rule
        :param:
            name : Name of the export_policy
        :return: Details about the export_policy. None if not found.
        :rtype: dict
        """
        rule_iter = netapp_utils.zapi.NaElement('export-rule-get-iter')
        rule_info = netapp_utils.zapi.NaElement('export-rule-info')
        rule_info.add_new_child('policy-name', self.policy_name)
        if self.vserver:
            rule_info.add_new_child('vserver-name', self.vserver)
        else:
            if self.client_match:
                rule_info.add_new_child('client-match', self.client_match)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(rule_info)

        rule_iter.add_child_elem(query)
        result = self.server.invoke_successfully(rule_iter, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            export_policy_rule_details = result.get_child_by_name('attributes-list').\
                get_child_by_name('export-rule-info')
            export_policy_name = export_policy_rule_details.get_child_content(
                'policy-name')
            export_rule_index = export_policy_rule_details.get_child_content(
                'rule-index')
            export_rule_protocol = export_policy_rule_details.get_child_by_name(
                'protocol').get_child_content('access-protocol')
            export_rule_ro_rule = export_policy_rule_details.get_child_by_name(
                'ro-rule').get_child_content('security-flavor')
            export_rule_rw_rule = export_policy_rule_details.get_child_by_name(
                'rw-rule').get_child_content('security-flavor')
            export_rule_super_user_security = export_policy_rule_details.get_child_by_name(
                'super-user-security').get_child_content('security-flavor')
            export_rule_allow_suid = export_policy_rule_details.get_child_content(
                'is-allow-set-uid-enabled')
            export_rule_client_match = export_policy_rule_details.get_child_content(
                'client-match')
            export_vserver = export_policy_rule_details.get_child_content(
                'vserver-name')
            return_value = {
                'policy-name': export_policy_name,
                'rule-index': export_rule_index,
                'protocol': export_rule_protocol,
                'ro-rule': export_rule_ro_rule,
                'rw-rule': export_rule_rw_rule,
                'super-user-security': export_rule_super_user_security,
                'is-allow-set-uid-enabled': export_rule_allow_suid,
                'client-match': export_rule_client_match,
                'vserver': export_vserver
            }

        elif result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            return_value = {
                'policy-name': self.policy_name
            }
        return return_value

    def get_export_policy(self):
        """
        Return details about the export-policy
        :param:
            name : Name of the export-policy

        :return: Details about the export-policy. None if not found.
        :rtype: dict
        """
        export_policy_iter = netapp_utils.zapi.NaElement(
            'export-policy-get-iter')
        export_policy_info = netapp_utils.zapi.NaElement('export-policy-info')
        export_policy_info.add_new_child('policy-name', self.policy_name)
        export_policy_info.add_new_child('vserver', self.vserver)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(export_policy_info)

        export_policy_iter.add_child_elem(query)

        result = self.server.invoke_successfully(export_policy_iter, True)

        return_value = None

        # check if query returns the expected export-policy
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            result.get_child_by_name('attributes-list').\
                get_child_by_name('export-policy-info').\
                get_child_by_name('policy-name')
            return_value = {
                'policy-name': self.policy_name
            }

        return return_value

    def create_export_policy_rule(self):
        """
        create rule for the export policy.
        """
        if self.allow_suid is not None:
            export_rule_create = netapp_utils.zapi.NaElement.create_node_with_children(
                'export-rule-create', **{'policy-name': self.policy_name,
                                         'client-match': self.client_match,
                                         'is-allow-set-uid-enabled': str(self.allow_suid)
                                         })
        else:
            export_rule_create = netapp_utils.zapi.NaElement.create_node_with_children(
                'export-rule-create', **{'policy-name': self.policy_name,
                                         'client-match': self.client_match
                                         })
        export_rule_create.add_node_with_children(
            'ro-rule', **{'security-flavor': self.ro_rule})
        export_rule_create.add_node_with_children(
            'rw-rule', **{'security-flavor': self.rw_rule})
        if self.protocol:
            export_rule_create.add_node_with_children(
                'protocol', **{'access-protocol': self.protocol})
        if self.super_user_security:
            export_rule_create.add_node_with_children(
                'super-user-security', **{'security-flavor': self.super_user_security})

        try:
            self.server.invoke_successfully(export_rule_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating export policy rule %s: %s'
                                  % (self.policy_name, to_native(error)),
                                  exception=traceback.format_exc())

    def create_export_policy(self):
        """
        Creates an export policy
        """
        export_policy_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-policy-create', **{'policy-name': self.policy_name})
        try:
            self.server.invoke_successfully(export_policy_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating export-policy %s: %s'
                                  % (self.policy_name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_export_policy_rule(self, rule_index):
        """
        delete rule for the export policy.
        """
        export_rule_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-destroy', **{'policy-name': self.policy_name,
                                      'rule-index': str(rule_index)})

        try:
            self.server.invoke_successfully(export_rule_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting export policy rule %s: %s'
                                  % (self.policy_name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_protocol(self, rule_index):
        """
        Modify the protocol.
        """
        export_rule_modify_protocol = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify',
            **{'policy-name': self.policy_name,
               'rule-index': rule_index})
        export_rule_modify_protocol.add_node_with_children(
            'protocol', **{'access-protocol': self.protocol})
        try:
            self.server.invoke_successfully(export_rule_modify_protocol,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying protocol %s: %s' % (self.policy_name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_ro_rule(self, rule_index):
        """
        Modify ro_rule.
        """
        export_rule_modify_ro_rule = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify',
            **{'policy-name': self.policy_name,
               'rule-index': rule_index})
        export_rule_modify_ro_rule.add_node_with_children(
            'ro-rule', **{'security-flavor': self.ro_rule})
        try:
            self.server.invoke_successfully(export_rule_modify_ro_rule,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying ro_rule %s: %s' % (self.ro_rule, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_rw_rule(self, rule_index):
        """
        Modify rw_rule.
        """
        export_rule_modify_rw_rule = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify',
            **{'policy-name': self.policy_name,
               'rule-index': rule_index})
        export_rule_modify_rw_rule.add_node_with_children(
            'rw-rule', **{'security-flavor': self.rw_rule})
        try:
            self.server.invoke_successfully(export_rule_modify_rw_rule,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying rw_rule %s: %s' % (self.rw_rule, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_super_user_security(self, rule_index):
        """
        Modify super_user_security.
        """
        export_rule_modify_super_user_security = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify',
            **{'policy-name': self.policy_name,
               'rule-index': rule_index})
        export_rule_modify_super_user_security.add_node_with_children(
            'super-user-security', **{'security-flavor': self.super_user_security})
        try:
            self.server.invoke_successfully(export_rule_modify_super_user_security,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying super_user_security %s: %s' % (self.super_user_security, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_allow_suid(self, rule_index):
        """
        Modify allow_suid.
        """
        export_rule_modify_allow_suid = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify',
            **{'policy-name': self.policy_name,
               'rule-index': rule_index,
               'is-allow-set-uid-enabled': str(self.allow_suid)})
        try:
            self.server.invoke_successfully(export_rule_modify_allow_suid,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying allow_suid %s: %s' % (self.allow_suid, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Apply action to export-policy'''
        changed = False
        export_policy_rule_exists = None
        export_rule_protocol_changed = False
        export_rule_ro_rule_changed = False
        export_rule_rw_rule_changed = False
        export_rule_allow_suid_enabled = False
        export_rule_clientmatch_changed = False
        export_rule_superuser_changed = False
        netapp_utils.ems_log_event("na_ontap_export_policy_rules", self.server)
        export_policy_details = self.get_export_policy()

        if not export_policy_details:
            if self.state == 'present':
                self.create_export_policy()
        export_policy_rule_exists = self.get_export_policy_rule()
        if self.state == 'absent':
            if export_policy_rule_exists:  # delete
                changed = True
                rule_index = export_policy_rule_exists['rule-index']

        elif self.state == 'present':
            if export_policy_rule_exists:  # modify
                rule_index = export_policy_rule_exists['rule-index']
                if rule_index:
                    if (self.protocol is not None) and \
                            (export_policy_rule_exists['protocol'] != self.protocol):
                        export_rule_protocol_changed = True
                        changed = True
                    if self.ro_rule is not None and \
                            (export_policy_rule_exists['ro-rule'] != self.ro_rule):
                        export_rule_ro_rule_changed = True
                        changed = True
                    if self.rw_rule is not None and \
                            (export_policy_rule_exists['rw-rule'] != self.rw_rule):
                        export_rule_rw_rule_changed = True
                        changed = True
                    if (self.allow_suid is not None) and \
                            (export_policy_rule_exists['is-allow-set-uid-enabled'] != self.allow_suid):
                        export_rule_allow_suid_enabled = True
                        changed = True
                    if (self.super_user_security is not None) and \
                            (export_policy_rule_exists['super-user-security'] != self.super_user_security):
                        export_rule_superuser_changed = True
                        changed = True
                    if self.client_match is not None and \
                            (export_policy_rule_exists['client-match'] != self.client_match):
                        export_rule_clientmatch_changed = True
                        changed = True
            else:  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not export_policy_rule_exists:
                        self.create_export_policy_rule()
                    else:
                        if export_rule_protocol_changed is True:
                            self.modify_protocol(rule_index)
                        if export_rule_ro_rule_changed is True:
                            self.modify_ro_rule(rule_index)
                        if export_rule_rw_rule_changed is True:
                            self.modify_rw_rule(rule_index)
                        if export_rule_allow_suid_enabled is True:
                            self.modify_allow_suid(rule_index)
                        if export_rule_clientmatch_changed is True:
                            self.modify_client_match(rule_index)
                        if export_rule_superuser_changed is True:
                            self.modify_super_user_security(rule_index)
                elif self.state == 'absent':
                    self.delete_export_policy_rule(rule_index)

        self.module.exit_json(changed=changed)


def main():
    ''' Create object and call apply '''
    rule_obj = NetAppontapExportRule()
    rule_obj.apply()


if __name__ == '__main__':
    main()
