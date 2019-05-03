#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_export_policy_rule

short_description: NetApp ONTAP manage export policy rules
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create or delete or modify export rules in ONTAP

options:
  state:
    description:
    - Whether the specified export policy rule should exist or not.
    required: false
    choices: ['present', 'absent']
    default: present

  name:
    description:
    - The name of the export rule to manage.
    required: True
    aliases:
    - policy_name

  client_match:
    description:
    - List of Client Match host names, IP Addresses, Netgroups, or Domains

  ro_rule:
    description:
    - List of Read only access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  rw_rule:
    description:
    - List of Read Write access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  super_user_security:
    description:
    - List of Read Write access specifications for the rule
    choices: ['any','none','never','krb5','krb5i','krb5p','ntlm','sys']

  allow_suid:
    description:
    - If 'true', NFS server will honor SetUID bits in SETATTR operation. Default value on creation is 'true'
    type: bool

  protocol:
    description:
    - List of Client access protocols.
    - Default value is set to 'any' during create.
    choices: [any,nfs,nfs3,nfs4,cifs,flexcache]

  rule_index:
    description:
    - rule index of the export policy
    - Required for delete and modify
    - If rule_index is not set for a modify, the module will create another rule with desired parameters

  vserver:
    description:
    - Name of the vserver to use.
    required: true

'''

EXAMPLES = """
    - name: Create ExportPolicyRule
      na_ontap_export_policy_rule:
        state: present
        name: default123
        vserver: ci_dev
        client_match: 0.0.0.0/0,1.1.1.0/24
        ro_rule: krb5,krb5i
        rw_rule: any
        protocol: nfs,nfs3
        super_user_security: any
        allow_suid: true
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Modify ExportPolicyRule
      na_ontap_export_policy_rule:
        state: present
        name: default123
        rule_index: 100
        client_match: 0.0.0.0/0
        ro_rule: ntlm
        rw_rule: any
        protocol: any
        allow_suid: false
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete ExportPolicyRule
      na_ontap_export_policy_rule:
        state: absent
        name: default123
        rule_index: 100
        vserver: ci_dev
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
from ansible.module_utils.netapp_module import NetAppModule


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppontapExportRule(object):
    ''' object initialize and class methods '''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str', aliases=['policy_name']),
            protocol=dict(required=False,
                          type='list', default=None,
                          choices=['any', 'nfs', 'nfs3', 'nfs4', 'cifs', 'flexcache']),
            client_match=dict(required=False, type='list'),
            ro_rule=dict(required=False,
                         type='list', default=None,
                         choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            rw_rule=dict(required=False,
                         type='list', default=None,
                         choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            super_user_security=dict(required=False,
                                     type='list', default=None,
                                     choices=['any', 'none', 'never', 'krb5', 'krb5i', 'krb5p', 'ntlm', 'sys']),
            allow_suid=dict(required=False, type='bool'),
            rule_index=dict(required=False, type='int'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters['vserver'])

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'client_match': 'client-match',
            'name': 'policy-name'
        }
        self.na_helper.zapi_list_keys = {
            'protocol': ('protocol', 'access-protocol'),
            'ro_rule': ('ro-rule', 'security-flavor'),
            'rw_rule': ('rw-rule', 'security-flavor'),
            'super_user_security': ('super-user-security', 'security-flavor'),
        }
        self.na_helper.zapi_bool_keys = {
            'allow_suid': 'is-allow-set-uid-enabled'
        }
        self.na_helper.zapi_int_keys = {
            'rule_index': 'rule-index'
        }

    def set_query_parameters(self):
        """
        Return dictionary of query parameters and
        :return:
        """
        query = {
            'policy-name': self.parameters['name'],
            'vserver': self.parameters['vserver']
        }

        if self.parameters.get('rule_index'):
            query['rule-index'] = self.parameters['rule_index']
        else:
            if self.parameters.get('ro_rule'):
                query['ro-rule'] = {'security-flavor': self.parameters['ro_rule']}
            if self.parameters.get('rw_rule'):
                query['rw-rule'] = {'security-flavor': self.parameters['rw_rule']}
            if self.parameters.get('protocol'):
                query['protocol'] = {'security-flavor': self.parameters['protocol']}
            if self.parameters.get('client_match'):
                query['client-match'] = self.parameters['client_match']
        attributes = {
            'query': {
                'export-rule-info': query
            }
        }
        return attributes

    def get_export_policy_rule(self):
        """
        Return details about the export policy rule
        :param:
            name : Name of the export_policy
        :return: Details about the export_policy. None if not found.
        :rtype: dict
        """
        current, result = None, None
        rule_iter = netapp_utils.zapi.NaElement('export-rule-get-iter')
        rule_iter.translate_struct(self.set_query_parameters())
        try:
            result = self.server.invoke_successfully(rule_iter, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting export policy rule %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

        if result is not None and \
                result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            current = dict()
            rule_info = result.get_child_by_name('attributes-list').get_child_by_name('export-rule-info')
            for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
                current[item_key] = rule_info.get_child_content(zapi_key)
            for item_key, zapi_key in self.na_helper.zapi_bool_keys.items():
                current[item_key] = self.na_helper.get_value_for_bool(from_zapi=True,
                                                                      value=rule_info[zapi_key])
            for item_key, zapi_key in self.na_helper.zapi_int_keys.items():
                current[item_key] = self.na_helper.get_value_for_int(from_zapi=True,
                                                                     value=rule_info[zapi_key])
            for item_key, zapi_key in self.na_helper.zapi_list_keys.items():
                parent, dummy = zapi_key
                current[item_key] = self.na_helper.get_value_for_list(from_zapi=True,
                                                                      zapi_parent=rule_info.get_child_by_name(parent))
            current['num_records'] = int(result.get_child_content('num-records'))
        return current

    def get_export_policy(self):
        """
        Return details about the export-policy
        :param:
            name : Name of the export-policy

        :return: Details about the export-policy. None if not found.
        :rtype: dict
        """
        export_policy_iter = netapp_utils.zapi.NaElement('export-policy-get-iter')
        attributes = {
            'query': {
                'export-policy-info': {
                    'policy-name': self.parameters['name'],
                    'vserver': self.parameters['vserver']
                }
            }
        }

        export_policy_iter.translate_struct(attributes)
        try:
            result = self.server.invoke_successfully(export_policy_iter, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting export policy %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) == 1:
            return result

        return None

    def add_parameters_for_create_or_modify(self, na_element_object, values):
        """
            Add children node for create or modify NaElement object
            :param na_element_object: modify or create NaElement object
            :param values: dictionary of cron values to be added
            :return: None
        """
        for key in values:
            if key in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(key)
                na_element_object[zapi_key] = values[key]
            elif key in self.na_helper.zapi_list_keys:
                parent_key, child_key = self.na_helper.zapi_list_keys.get(key)
                na_element_object.add_child_elem(self.na_helper.get_value_for_list(from_zapi=False,
                                                                                   zapi_parent=parent_key,
                                                                                   zapi_child=child_key,
                                                                                   data=values[key]))
            elif key in self.na_helper.zapi_int_keys:
                zapi_key = self.na_helper.zapi_int_keys.get(key)
                na_element_object[zapi_key] = self.na_helper.get_value_for_int(from_zapi=False,
                                                                               value=values[key])
            elif key in self.na_helper.zapi_bool_keys:
                zapi_key = self.na_helper.zapi_bool_keys.get(key)
                na_element_object[zapi_key] = self.na_helper.get_value_for_bool(from_zapi=False,
                                                                                value=values[key])

    def create_export_policy_rule(self):
        """
        create rule for the export policy.
        """
        for key in ['client_match', 'ro_rule', 'rw_rule']:
            if self.parameters.get(key) is None:
                self.module.fail_json(msg='Error: Missing required param for creating export policy rule %s' % key)
        export_rule_create = netapp_utils.zapi.NaElement('export-rule-create')
        self.add_parameters_for_create_or_modify(export_rule_create, self.parameters)
        try:
            self.server.invoke_successfully(export_rule_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating export policy rule %s: %s'
                                  % (self.parameters['name'], to_native(error)), exception=traceback.format_exc())

    def create_export_policy(self):
        """
        Creates an export policy
        """
        export_policy_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-policy-create', **{'policy-name': self.parameters['name']})
        try:
            self.server.invoke_successfully(export_policy_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating export-policy %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_export_policy_rule(self, rule_index):
        """
        delete rule for the export policy.
        """
        if self.parameters.get('rule_index') is None:
            self.parameters['rule_index'] = rule_index
        export_rule_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-destroy', **{'policy-name': self.parameters['name'],
                                      'rule-index': str(rule_index)})

        try:
            self.server.invoke_successfully(export_rule_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting export policy rule %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_export_policy_rule(self, params):
        '''
        Modify an existing export policy rule
        :param params: dict() of attributes with desired values
        :return: None
        '''
        export_rule_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-rule-modify', **{'policy-name': self.parameters['name'],
                                     'rule-index': str(self.parameters['rule_index'])})
        self.add_parameters_for_create_or_modify(export_rule_modify, params)
        try:
            self.server.invoke_successfully(export_rule_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying allow_suid %s: %s'
                                  % (self.parameters['allow_suid'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        netapp_utils.ems_log_event("na_ontap_export_policy_rules", self.server)

    def apply(self):
        ''' Apply required action from the play'''
        self.autosupport_log()
        # convert client_match list to comma-separated string
        if self.parameters.get('client_match') is not None:
            self.parameters['client_match'] = ','.join(self.parameters['client_match'])

        current, modify = self.get_export_policy_rule(), None
        action = self.na_helper.get_cd_action(current, self.parameters)
        if action is None and self.parameters['state'] == 'present':
            modify = self.na_helper.get_modified_attributes(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                # create export policy (if policy doesn't exist) only when changed=True
                if not self.get_export_policy():
                    self.create_export_policy()
                if action == 'create':
                    self.create_export_policy_rule()
                elif action == 'delete':
                    if current['num_records'] > 1:
                        self.module.fail_json(msg='Multiple export policy rules exist.'
                                                  'Please specify a rule_index to delete')
                    self.delete_export_policy_rule(current['rule_index'])
                elif modify:
                    self.modify_export_policy_rule(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    ''' Create object and call apply '''
    rule_obj = NetAppontapExportRule()
    rule_obj.apply()


if __name__ == '__main__':
    main()
