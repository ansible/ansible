#!/usr/bin/python
'''
(c) 2019, Red Hat, Inc
GNU General Public License v3.0+
(see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''

module: na_ontap_kerberos_realm

short_description: NetApp ONTAP vserver nfs kerberos realm
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: Milan Zink (@zeten30) <zeten30@gmail.com>,<mzink@redhat.com>

description:
- Create, modify or delete vserver kerberos realm configuration

options:

  state:
    description:
    - Whether the Kerberos realm is present or absent.
    choices: ['present', 'absent']
    default: 'present'
    type: str

  vserver:
    description:
    - vserver/svm with kerberos realm configured
    required: true
    type: str

  realm:
    description:
    - Kerberos realm name
    required: true
    type: str

  kdc_vendor:
    description:
    - The vendor of the Key Distribution Centre (KDC) server
    - Required if I(state=present)
    choices: ['Other', 'Microsoft']
    type: str

  kdc_ip:
    description:
    - IP address of the Key Distribution Centre (KDC) server
    - Required if I(state=present)
    type: str

  kdc_port:
    description:
    - TCP port on the KDC to be used for Kerberos communication.
    - The default for this parameter is '88'.
    type: str

  clock_skew:
    description:
    - The clock skew in minutes is the tolerance for accepting tickets with time stamps that do not exactly match the host's system clock.
    - The default for this parameter is '5' minutes.
    type: str

  comment:
    description:
    - Optional comment
    type: str

  admin_server_ip:
    description:
    - IP address of the host where the Kerberos administration daemon is running. This is usually the master KDC.
    - If this parameter is omitted, the address specified in kdc_ip is used.
    type: str

  admin_server_port:
    description:
    - The TCP port on the Kerberos administration server where the Kerberos administration service is running.
    - The default for this parameter is '749'
    type: str

  pw_server_ip:
    description:
    - IP address of the host where the Kerberos password-changing server is running.
    - Typically, this is the same as the host indicated in the adminserver-ip.
    - If this parameter is omitted, the IP address in kdc-ip is used.
    type: str

  pw_server_port:
    description:
    - The TCP port on the Kerberos password-changing server where the Kerberos password-changing service is running.
    - The default for this parameter is '464'.
    type: str
'''

EXAMPLES = '''

    - name: Create kerberos realm
      na_ontap_kerberos_realm:
        state:         present
        realm:         'EXAMPLE.COM'
        vserver:       'vserver1'
        kdc_ip:        '1.2.3.4'
        kdc_vendor:    'Other'
        hostname:      "{{ netapp_hostname }}"
        username:      "{{ netapp_username }}"
        password:      "{{ netapp_password }}"

'''

RETURN = '''
'''

import traceback
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapKerberosRealm(object):
    '''
    Kerberos Realm definition class
    '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            admin_server_ip=dict(required=False, default=None, type='str'),
            admin_server_port=dict(required=False, default=None, type='str'),
            clock_skew=dict(required=False, default=None, type='str'),
            comment=dict(required=False, default=None, type='str'),
            kdc_ip=dict(required_if=[["state", "present"]], default=None, type='str'),
            kdc_port=dict(required=False, default=None, type='str'),
            kdc_vendor=dict(required_if=[["state", "present"]], default=None, type='str', choices=['Microsoft', 'Other']),
            pw_server_ip=dict(required=False, default=None, type='str'),
            pw_server_port=dict(required=False, default=None, type='str'),
            realm=dict(required=True, type='str'),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
            required_if=[('state', 'present', ['kdc_vendor', 'kdc_ip'])],
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

        self.simple_attributes = [
            'admin_server_ip',
            'admin_server_port',
            'clock_skew',
            'kdc_ip',
            'kdc_port',
            'kdc_vendor',
        ]

    def get_krbrealm(self, realm_name=None, vserver_name=None):
        '''
        Checks if Kerberos Realm config exists.

        :return:
            kerberos realm object if found
            None if not found
        :rtype: object/None
        '''
        # Make query
        krbrealm_info = netapp_utils.zapi.NaElement('kerberos-realm-get-iter')

        if realm_name is None:
            realm_name = self.parameters['realm']

        if vserver_name is None:
            vserver_name = self.parameters['vserver']

        query_details = netapp_utils.zapi.NaElement.create_node_with_children('kerberos-realm', **{'realm': realm_name, 'vserver-name': vserver_name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        krbrealm_info.add_child_elem(query)

        result = self.server.invoke_successfully(krbrealm_info, enable_tunneling=True)

        # Get Kerberos Realm details
        krbrealm_details = None
        if (result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1):
            attributes_list = result.get_child_by_name('attributes-list')
            config_info = attributes_list.get_child_by_name('kerberos-realm')

            krbrealm_details = {
                'admin_server_ip': config_info.get_child_content('admin-server-ip'),
                'admin_server_port': config_info.get_child_content('admin-server-port'),
                'clock_skew': config_info.get_child_content('clock-skew'),
                'kdc_ip': config_info.get_child_content('kdc-ip'),
                'kdc_port': config_info.get_child_content('kdc-port'),
                'kdc_vendor': config_info.get_child_content('kdc-vendor'),
                'pw_server_ip': config_info.get_child_content('password-server-ip'),
                'pw_server_port': config_info.get_child_content('password-server-port'),
                'realm': config_info.get_child_content('realm'),
                'vserver': config_info.get_child_content('vserver'),
            }

        return krbrealm_details

    def create_krbrealm(self):
        '''supported
        Create Kerberos Realm configuration
        '''
        options = {
            'realm': self.parameters['realm']
        }

        # Other options/attributes
        for attribute in self.simple_attributes:
            if self.parameters.get(attribute) is not None:
                options[str(attribute).replace('_', '-')] = self.parameters[attribute]

        if self.parameters.get('pw_server_ip') is not None:
            options['password-server-ip'] = self.parameters['pw_server_ip']
        if self.parameters.get('pw_server_port') is not None:
            options['password-server-port'] = self.parameters['pw_server_port']

        # Initialize NaElement
        krbrealm_create = netapp_utils.zapi.NaElement.create_node_with_children('kerberos-realm-create', **options)

        # Try to create Kerberos Realm configuration
        try:
            self.server.invoke_successfully(krbrealm_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error creating Kerberos Realm configuration %s: %s' % (self.parameters['realm'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def delete_krbrealm(self):
        '''
        Delete Kerberos Realm configuration
        '''
        krbrealm_delete = netapp_utils.zapi.NaElement.create_node_with_children('kerberos-realm-delete', **{'realm': self.parameters['realm']})

        try:
            self.server.invoke_successfully(krbrealm_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error deleting Kerberos Realm configuration %s: %s' % (
                self.parameters['realm'], to_native(errcatch)), exception=traceback.format_exc())

    def modify_krbrealm(self, modify):
        '''
        Modify Kerberos Realm
        :param modify: list of modify attributes
        '''
        krbrealm_modify = netapp_utils.zapi.NaElement('kerberos-realm-modify')
        krbrealm_modify.add_new_child('realm', self.parameters['realm'])

        for attribute in modify:
            if attribute in self.simple_attributes:
                krbrealm_modify.add_new_child(str(attribute).replace('_', '-'), self.parameters[attribute])
            if attribute == 'pw_server_ip':
                krbrealm_modify.add_new_child('password-server-ip', self.parameters['pw_server_ip'])
            if attribute == 'pw_server_port':
                krbrealm_modify.add_new_child('password-server-port', self.parameters['pw_server_port'])

        # Try to modify Kerberos Realm
        try:
            self.server.invoke_successfully(krbrealm_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as errcatch:
            self.module.fail_json(msg='Error modifying Kerberos Realm %s: %s' % (self.parameters['realm'], to_native(errcatch)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Call create/modify/delete operations.'''
        current = self.get_krbrealm()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        #  create an ems log event for users with auto support turned on
        netapp_utils.ems_log_event("na_ontap_kerberos_realm", self.server)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_krbrealm()
                elif cd_action == 'delete':
                    self.delete_krbrealm()
                elif modify:
                    self.modify_krbrealm(modify)
        self.module.exit_json(changed=self.na_helper.changed)


#
# MAIN
#
def main():
    '''ONTAP Kerberos Realm'''
    krbrealm = NetAppOntapKerberosRealm()
    krbrealm.apply()


if __name__ == '__main__':
    main()
