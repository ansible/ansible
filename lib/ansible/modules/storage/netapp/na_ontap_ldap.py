#!/usr/bin/python
'''
(c) 2018-2019, NetApp, Inc
GNU General Public License v3.0+
(see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''

module: na_ontap_ldap

short_description: NetApp ONTAP LDAP
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: Milan Zink (@zeten30) <zeten30@gmail.com>/<mzink@redhat.com>

description:
- Create, modify or delete LDAP on NetApp ONTAP SVM/vserver

options:

  state:
    description:
    - Whether the LDAP is present or not.
    choices: ['present', 'absent']
    default: 'present'
    type: str

  vserver:
    description:
    - vserver/svm configured to use LDAP
    required: true
    type: str

  name:
    description:
    - The name of LDAP client configuration
    required: true
    type: str

  skip_config_validation:
    description:
    - Skip LDAP validation
    choices: ['true', 'false']
    type: str
'''

EXAMPLES = '''

    - name: Enable LDAP on SVM
      na_ontap_ldap:
        state:         present
        name:          'example_ldap'
        vserver:       'vserver1'
        hostname:      "{{ netapp_hostname }}"
        username:      "{{ netapp_username }}"
        password:      "{{ netapp_password }}"

'''

RETURN = '''
'''

import traceback
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapLDAP(object):
    '''
    LDAP Client definition class
    '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            name=dict(required=True, type='str'),
            skip_config_validation=dict(required=False, default=None, choices=['true', 'false']),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_ldap(self, client_config_name=None):
        '''
        Checks if LDAP config exists.

        :return:
            ldap config object if found
            None if not found
        :rtype: object/None
        '''
        # Make query
        config_info = netapp_utils.zapi.NaElement('ldap-config-get-iter')

        if client_config_name is None:
            client_config_name = self.parameters['name']

        query_details = netapp_utils.zapi.NaElement.create_node_with_children('ldap-config', **{'client-config': client_config_name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        config_info.add_child_elem(query)

        result = self.server.invoke_successfully(config_info, enable_tunneling=True)

        # Get LDAP configuration details
        config_details = None
        if (result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1):
            attributes_list = result.get_child_by_name('attributes-list')
            config_info = attributes_list.get_child_by_name('ldap-config')

            # Define config details structure
            config_details = {'client_config': config_info.get_child_content('client-config'),
                              'skip_config_validation': config_info.get_child_content('skip-config-validation'),
                              'vserver': config_info.get_child_content('vserver')}

        return config_details

    def create_ldap(self):
        '''
        Create LDAP configuration
        '''
        options = {
            'client-config': self.parameters['name'],
            'client-enabled': 'true'
        }

        if self.parameters.get('skip_config_validation') is not None:
            options['skip-config-validation'] = self.parameters['skip_config_validation']

        # Initialize NaElement
        ldap_create = netapp_utils.zapi.NaElement.create_node_with_children('ldap-config-create', **options)

        # Try to create LDAP configuration
        try:
            self.server.invoke_successfully(ldap_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error creating LDAP configuration %s: %s' % (self.parameters['name'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def delete_ldap(self):
        '''
        Delete LDAP configuration
        '''
        ldap_client_delete = netapp_utils.zapi.NaElement.create_node_with_children('ldap-config-delete', **{})

        try:
            self.server.invoke_successfully(ldap_client_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error deleting LDAP configuration %s: %s' % (
                self.parameters['name'], to_native(errcatch)), exception=traceback.format_exc())

    def modify_ldap(self, modify):
        '''
        Modify LDAP
        :param modify: list of modify attributes
        '''
        ldap_modify = netapp_utils.zapi.NaElement('ldap-config-modify')
        ldap_modify.add_new_child('client-config', self.parameters['name'])

        for attribute in modify:
            if attribute == 'skip_config_validation':
                ldap_modify.add_new_child('skip-config-validation', self.parameters[attribute])

        # Try to modify LDAP
        try:
            self.server.invoke_successfully(ldap_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error modifying LDAP %s: %s' % (self.parameters['name'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Call create/modify/delete operations.'''
        current = self.get_ldap()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        #  create an ems log event for users with auto support turned on
        netapp_utils.ems_log_event("na_ontap_ldap", self.server)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_ldap()
                elif cd_action == 'delete':
                    self.delete_ldap()
                elif modify:
                    self.modify_ldap(modify)
        self.module.exit_json(changed=self.na_helper.changed)


#
# MAIN
#
def main():
    '''ONTAP LDAP client configuration'''
    ldapclient = NetAppOntapLDAP()
    ldapclient.apply()


if __name__ == '__main__':
    main()
