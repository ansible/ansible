#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: na_ontap_vserver_cifs_security
short_description: NetApp ONTAP vserver CIFS security modification
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - modify vserver CIFS security.

options:

  vserver:
    description:
    - name of the vserver.
    required: true
    type: str

  kerberos_clock_skew:
    description:
    - The clock skew in minutes is the tolerance for accepting tickets with time stamps that do not exactly match the host's system clock.
    type: int

  kerberos_ticket_age:
    description:
    - Determine the maximum amount of time in hours that a user's ticket may be used for the purpose of Kerberos authentication.
    type: int

  kerberos_renew_age:
    description:
    - Determine the maximum amount of time in days for which a ticket can be renewed.
    type: int

  kerberos_kdc_timeout:
    description:
    - Determine the timeout value in seconds for KDC connections.
    type: int

  is_signing_required:
    description:
    - Determine whether signing is required for incoming CIFS traffic.
    type: bool

  is_password_complexity_required:
    description:
    - Determine whether password complexity is required for local users.
    type: bool

  is_aes_encryption_enabled:
    description:
    - Determine whether AES-128 and AES-256 encryption mechanisms are enabled for Kerberos-related CIFS communication.
    type: bool

  is_smb_encryption_required:
    description:
    - Determine whether SMB encryption is required for incoming CIFS traffic.
    type: bool

  lm_compatibility_level:
    description:
    - Determine the LM compatibility level.
    choices: ['lm_ntlm_ntlmv2_krb', 'ntlm_ntlmv2_krb', 'ntlmv2_krb', 'krb']
    type: str

  referral_enabled_for_ad_ldap:
    description:
    - Determine whether LDAP referral chasing is enabled or not for AD LDAP connections.
    type: bool

  session_security_for_ad_ldap:
    description:
    - Determine the level of security required for LDAP communications.
    choices: ['none', 'sign', 'seal']
    type: str

  smb1_enabled_for_dc_connections:
    description:
    - Determine if SMB version 1 is used for connections to domain controllers.
    choices: ['false', 'true', 'system_default']
    type: str

  smb2_enabled_for_dc_connections:
    description:
    - Determine if SMB version 2 is used for connections to domain controllers.
    choices: ['false', 'true', 'system_default']
    type: str

  use_start_tls_for_ad_ldap:
    description:
    - Determine whether to use start_tls for AD LDAP connections.
    type: bool

'''

EXAMPLES = '''
    - name: modify cifs security
      na_ontap_vserver_cifs_security:
        vserver: ansible
        hostname: "{{ hostname }}"
        kerberos_clock_skew: 5
        kerberos_ticket_age: 5
        kerberos_renew_age: 10
        kerberos_kdc_timeout: 5
        is_signing_required: true
        is_password_complexity_required: true
        is_aes_encryption_enabled: true
        is_smb_encryption_required: true
        lm_compatibility_level: krb
        smb1_enabled_for_dc_connections: true
        smb2_enabled_for_dc_connections: true
        use_start_tls_for_ad_ldap: true
        username: username
        password: password

    - name: modify cifs security
      na_ontap_vserver_cifs_security:
        vserver: ansible
        hostname: "{{ hostname }}"
        referral_enabled_for_ad_ldap: true
        username: username
        password: password

    - name: modify cifs security
      na_ontap_vserver_cifs_security:
        vserver: ansible
        hostname: "{{ hostname }}"
        session_security_for_ad_ldap: true
        username: username
        password: password
'''

RETURN = '''
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPCifsSecurity(object):
    '''
    modify vserver cifs security
    '''
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            vserver=dict(required=True, type='str'),
            kerberos_clock_skew=dict(required=False, type='int'),
            kerberos_ticket_age=dict(required=False, type='int'),
            kerberos_renew_age=dict(required=False, type='int'),
            kerberos_kdc_timeout=dict(required=False, type='int'),
            is_signing_required=dict(required=False, type='bool'),
            is_password_complexity_required=dict(required=False, type='bool'),
            is_aes_encryption_enabled=dict(required=False, type='bool'),
            is_smb_encryption_required=dict(required=False, type='bool'),
            lm_compatibility_level=dict(required=False, choices=['lm_ntlm_ntlmv2_krb', 'ntlm_ntlmv2_krb', 'ntlmv2_krb', 'krb']),
            referral_enabled_for_ad_ldap=dict(required=False, type='bool'),
            session_security_for_ad_ldap=dict(required=False, choices=['none', 'sign', 'seal']),
            smb1_enabled_for_dc_connections=dict(required=False, choices=['false', 'true', 'system_default']),
            smb2_enabled_for_dc_connections=dict(required=False, choices=['false', 'true', 'system_default']),
            use_start_tls_for_ad_ldap=dict(required=False, type='bool')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def cifs_security_get_iter(self):
        """
        get current vserver cifs security.
        :return: a dict of vserver cifs security
        """
        cifs_security_get = netapp_utils.zapi.NaElement('cifs-security-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        cifs_security = netapp_utils.zapi.NaElement('cifs-security')
        cifs_security.add_new_child('vserver', self.parameters['vserver'])
        query.add_child_elem(cifs_security)
        cifs_security_get.add_child_elem(query)
        cifs_security_details = dict()
        try:
            result = self.server.invoke_successfully(cifs_security_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching cifs security from %s: %s'
                                      % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            cifs_security_info = result.get_child_by_name('attributes-list').get_child_by_name('cifs-security')
            cifs_security_details['kerberos_clock_skew'] = cifs_security_info.get_child_content('kerberos-clock-skew')
            cifs_security_details['kerberos_ticket_age'] = cifs_security_info.get_child_content('kerberos-ticket-age')
            cifs_security_details['kerberos_renew_age'] = cifs_security_info.get_child_content('kerberos-renew-age')
            cifs_security_details['kerberos_kdc_timeout'] = cifs_security_info.get_child_content('kerberos-kdc-timeout')
            cifs_security_details['is_signing_required'] = bool(cifs_security_info.get_child_content('is-signing-required'))
            cifs_security_details['is_password_complexity_required'] = bool(cifs_security_info.get_child_content('is-password-complexity-required'))
            cifs_security_details['is_aes_encryption_enabled'] = bool(cifs_security_info.get_child_content('is-aes-encryption-enabled'))
            cifs_security_details['is_smb_encryption_required'] = bool(cifs_security_info.get_child_content('is-smb-encryption-required'))
            cifs_security_details['lm_compatibility_level'] = cifs_security_info.get_child_content('lm-compatibility-level')
            cifs_security_details['referral_enabled_for_ad_ldap'] = bool(cifs_security_info.get_child_content('referral-enabled-for-ad-ldap'))
            cifs_security_details['session_security_for_ad_ldap'] = cifs_security_info.get_child_content('session-security-for-ad-ldap')
            cifs_security_details['smb1_enabled_for_dc_connections'] = cifs_security_info.get_child_content('smb1-enabled-for-dc-connections')
            cifs_security_details['smb2_enabled_for_dc_connections'] = cifs_security_info.get_child_content('smb2-enabled-for-dc-connections')
            cifs_security_details['use_start_tls_for_ad_ldap'] = bool(cifs_security_info.get_child_content('use-start-tls-for-ad-ldap'))
            return cifs_security_details
        return None

    def cifs_security_modify(self, modify):
        """
        :param modify: A list of attributes to modify
        :return: None
        """
        cifs_security_modify = netapp_utils.zapi.NaElement('cifs-security-modify')
        for attribute in modify:
            cifs_security_modify.add_new_child(self.attribute_to_name(attribute), str(self.parameters[attribute]))
        try:
            self.server.invoke_successfully(cifs_security_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs security on %s: %s'
                                  % (self.parameters['vserver'], to_native(e)),
                                  exception=traceback.format_exc())

    @staticmethod
    def attribute_to_name(attribute):
        return str.replace(attribute, '_', '-')

    def apply(self):
        """Call modify operations."""
        self.asup_log_for_cserver("na_ontap_vserver_cifs_security")
        current = self.cifs_security_get_iter()
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if modify:
                    self.cifs_security_modify(modify)
        self.module.exit_json(changed=self.na_helper.changed)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)


def main():
    obj = NetAppONTAPCifsSecurity()
    obj.apply()


if __name__ == '__main__':
    main()
