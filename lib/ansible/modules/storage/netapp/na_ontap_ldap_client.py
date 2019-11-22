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

module: na_ontap_ldap_client

short_description: NetApp ONTAP LDAP client
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: Milan Zink (@zeten30) <zeten30@gmail.com>/<mzink@redhat.com>

description:
- Create, modify or delete LDAP client on NetApp ONTAP

options:

  state:
    description:
    - Whether the specified LDAP client configuration exist or not.
    choices: ['present', 'absent']
    default: 'present'
    type: str

  vserver:
    description:
    - vserver/svm that holds LDAP client configuration
    required: true
    type: str

  name:
    description:
    - The name of LDAP client configuration
    required: true
    type: str

  ldap_servers:
    description:
    - Comma separated list of LDAP servers. FQDN's or IP addresses
    - Required if I(state=present).
    type: list

  schema:
    description:
    - LDAP schema
    - Required if I(state=present).
    choices: ['AD-IDMU', 'AD-SFU', 'MS-AD-BIS', 'RFC-2307']
    type: str

  base_dn:
    description:
    - LDAP base DN
    type: str

  base_scope:
    description:
    - LDAP search scope
    choices: ['subtree', 'onelevel', 'base']
    type: str

  port:
    description:
    - LDAP server port
    type: int

  query_timeout:
    description:
    - LDAP server query timeout
    type: int

  min_bind_level:
    description:
    - Minimal LDAP server bind level.
    choices: ['anonymous', 'simple', 'sasl']
    type: str

  bind_dn:
    description:
    - LDAP bind user DN
    type: str

  bind_password:
    description:
    - LDAP bind user password
    type: str

  use_start_tls:
    description:
    - Start TLS on LDAP connection
    choices: ['true', 'false']
    type: str

  referral_enabled:
    description:
    - LDAP Referral Chasing
    choices: ['true', 'false']
    type: str

  session_security:
    description:
    - Client Session Security
    choices: ['true', 'false']
    type: str
'''

EXAMPLES = '''

    - name: Create LDAP client
      na_ontap_ldap_client:
        state:         present
        name:          'example_ldap'
        vserver:       'vserver1'
        ldap_servers:  'ldap1.example.company.com,ldap2.example.company.com'
        base_dn:       'dc=example,dc=company,dc=com'
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


class NetAppOntapLDAPClient(object):
    '''
    LDAP Client definition class
    '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            base_dn=dict(required=False, type='str'),
            base_scope=dict(required=False, default=None, choices=['subtree', 'onelevel', 'base']),
            bind_dn=dict(required=False, default=None, type='str'),
            bind_password=dict(type='str', required=False, default=None, no_log=True),
            name=dict(required=True, type='str'),
            ldap_servers=dict(required_if=[["state", "present"]], type='list'),
            min_bind_level=dict(required=False, default=None, choices=['anonymous', 'simple', 'sasl']),
            port=dict(required=False, default=None, type='int'),
            query_timeout=dict(required=False, default=None, type='int'),
            referral_enabled=dict(required=False, default=None, choices=['true', 'false']),
            schema=dict(required_if=[["state", "present"]], default=None, type='str', choices=['AD-IDMU', 'AD-SFU', 'MS-AD-BIS', 'RFC-2307']),
            session_security=dict(required=False, default=None, choices=['true', 'false']),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            use_start_tls=dict(required=False, default=None, choices=['true', 'false']),
            vserver=dict(required=True, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
            required_if=[('state', 'present', ['ldap_servers', 'schema'])],
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

        self.simple_attributes = [
            'base_dn',
            'base_scope',
            'bind_dn',
            'bind_password',
            'min_bind_level',
            'port',
            'query_timeout',
            'referral_enabled',
            'session_security',
            'use_start_tls'
        ]

    def get_ldap_client(self, client_config_name=None, vserver_name=None):
        '''
        Checks if LDAP client config exists.

        :return:
            ldap client config object if found
            None if not found
        :rtype: object/None
        '''
        # Make query
        client_config_info = netapp_utils.zapi.NaElement('ldap-client-get-iter')

        if client_config_name is None:
            client_config_name = self.parameters['name']

        if vserver_name is None:
            vserver_name = '*'

        query_details = netapp_utils.zapi.NaElement.create_node_with_children('ldap-client',
                                                                              **{'ldap-client-config': client_config_name, 'vserver': vserver_name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        client_config_info.add_child_elem(query)

        result = self.server.invoke_successfully(client_config_info, enable_tunneling=False)

        # Get LDAP client configuration details
        client_config_details = None
        if (result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1):
            attributes_list = result.get_child_by_name('attributes-list')
            client_config_info = attributes_list.get_child_by_name('ldap-client')

            # Get LDAP servers list
            ldap_server_list = list()
            get_list = client_config_info.get_child_by_name('ldap-servers')
            if get_list is not None:
                ldap_servers = get_list.get_children()
                for ldap_server in ldap_servers:
                    ldap_server_list.append(ldap_server.get_content())

            # Define config details structure
            client_config_details = {'name': client_config_info.get_child_content('ldap-client-config'),
                                     'ldap_servers': client_config_info.get_child_content('ldap-servers'),
                                     'base_dn': client_config_info.get_child_content('base-dn'),
                                     'base_scope': client_config_info.get_child_content('base-scope'),
                                     'bind_dn': client_config_info.get_child_content('bind-dn'),
                                     'bind_password': client_config_info.get_child_content('bind-password'),
                                     'min_bind_level': client_config_info.get_child_content('min-bind-level'),
                                     'port': client_config_info.get_child_content('port'),
                                     'query_timeout': client_config_info.get_child_content('query-timeout'),
                                     'referral_enabled': client_config_info.get_child_content('referral-enabled'),
                                     'schema': client_config_info.get_child_content('schema'),
                                     'session_security': client_config_info.get_child_content('session-security'),
                                     'use_start_tls': client_config_info.get_child_content('use-start-tls'),
                                     'vserver': client_config_info.get_child_content('vserver')}

        return client_config_details

    def create_ldap_client(self):
        '''
        Create LDAP client configuration
        '''
        # LDAP servers NaElement
        ldap_servers_element = netapp_utils.zapi.NaElement('ldap-servers')

        # Mandatory options
        for ldap_server_name in self.parameters['ldap_servers']:
            ldap_servers_element.add_new_child('string', ldap_server_name)

        options = {
            'ldap-client-config': self.parameters['name'],
            'schema': self.parameters['schema'],
        }

        # Other options/attributes
        for attribute in self.simple_attributes:
            if self.parameters.get(attribute) is not None:
                options[str(attribute).replace('_', '-')] = self.parameters[attribute]

        # Initialize NaElement
        ldap_client_create = netapp_utils.zapi.NaElement.create_node_with_children('ldap-client-create', **options)
        ldap_client_create.add_child_elem(ldap_servers_element)

        # Try to create LDAP configuration
        try:
            self.server.invoke_successfully(ldap_client_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error creating LDAP client %s: %s' % (self.parameters['name'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def delete_ldap_client(self):
        '''
        Delete LDAP client configuration
        '''
        ldap_client_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'ldap-client-delete', **{'ldap-client-config': self.parameters['name']})

        try:
            self.server.invoke_successfully(ldap_client_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error deleting LDAP client configuration %s: %s' % (
                self.parameters['name'], to_native(errcatch)), exception=traceback.format_exc())

    def modify_ldap_client(self, modify):
        '''
        Modify LDAP client
        :param modify: list of modify attributes
        '''
        ldap_client_modify = netapp_utils.zapi.NaElement('ldap-client-modify')
        ldap_client_modify.add_new_child('ldap-client-config', self.parameters['name'])

        for attribute in modify:
            # LDAP_servers
            if attribute == 'ldap_servers':
                ldap_servers_element = netapp_utils.zapi.NaElement('ldap-servers')
                for ldap_server_name in self.parameters['ldap_servers']:
                    ldap_servers_element.add_new_child('string', ldap_server_name)
                ldap_client_modify.add_child_elem(ldap_servers_element)

            # Simple attributes
            if attribute in self.simple_attributes:
                ldap_client_modify.add_new_child(str(attribute).replace('_', '-'), self.parameters[attribute])

        # Try to modify LDAP client
        try:
            self.server.invoke_successfully(ldap_client_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error modifying LDAP client %s: %s' % (self.parameters['name'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Call create/modify/delete operations.'''
        current = self.get_ldap_client()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        # create an ems log event for users with auto support turned on
        netapp_utils.ems_log_event("na_ontap_ldap_client", self.server)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_ldap_client()
                elif cd_action == 'delete':
                    self.delete_ldap_client()
                elif modify:
                    self.modify_ldap_client(modify)
        self.module.exit_json(changed=self.na_helper.changed)


#
# MAIN
#
def main():
    '''ONTAP LDAP client configuration'''
    ldapclient = NetAppOntapLDAPClient()
    ldapclient.apply()


if __name__ == '__main__':
    main()
