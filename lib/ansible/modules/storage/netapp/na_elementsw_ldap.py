#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_ldap

short_description: NetApp Element Software Manage ldap admin users
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Enable, disable ldap, and add ldap users

options:

    state:
        description:
        - Whether the specified volume should exist or not.
        required: true
        choices: ['present', 'absent']

    authType:
        description:
        - Identifies which user authentication method to use.
        choices: ['DirectBind', 'SearchAndBind']

    groupSearchBaseDn:
        description:
        - The base DN of the tree to start the group search (will do a subtree search from here)

    groupSearchType:
        description:
        - Controls the default group search filter used
        choices: ['NoGroup', 'ActiveDirectory', 'MemberDN']

    serverURIs:
        description:
        - A comma-separated list of LDAP server URIs

    userSearchBaseDN:
        description:
        - The base DN of the tree to start the search (will do a subtree search from here)

    searchBindDN:
        description:
        - A dully qualified DN to log in with to perform an LDAp search for the user (needs read access to the LDAP directory).

    searchBindPassword:
        description:
        - The password for the searchBindDN account used for searching

    userSearchFilter:
        description:
        - the LDAP Filter to use

    userDNTemplate:
        description:
        - A string that is used form a fully qualified user DN.

    groupSearchCustomFilter:
        description:
        - For use with the CustomFilter Search type
'''

EXAMPLES = """
    - name: disable ldap authentication
      na_elementsw_ldap:
        state: absent
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        hostname: "{{ hostname }}"

    - name: Enable ldap authentication
      na_elementsw_ldap:
        state: present
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        hostname: "{{ hostname }}"
        authType: DirectBind
        serverURIs: ldap://svmdurlabesx01spd_ldapclnt
        groupSearchType: MemberDN
        userDNTemplate:  uid=%USERNAME%,cn=users,cn=accounts,dc=corp,dc="{{ company name }}",dc=com


"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except Exception:
    HAS_SF_SDK = False


class NetappElementLdap(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(
            state=dict(type='str', required=True, choices=['absent', 'present']),
            authType=dict(type='str', choices=['DirectBind', 'SearchAndBind']),
            groupSearchBaseDn=dict(type='str'),
            groupSearchType=dict(type='str', choices=['NoGroup', 'ActiveDirectory', 'MemberDN']),
            serverURIs=dict(type='str'),
            userSearchBaseDN=dict(type='str'),
            searchBindDN=dict(type='str'),
            searchBindPassword=dict(type='str', no_log=True),
            userSearchFilter=dict(type='str'),
            userDNTemplate=dict(type='str'),
            groupSearchCustomFilter=dict(type='str'),
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        param = self.module.params

        # set up state variables
        self.state = param['state']
        self.authType = param['authType']
        self.groupSearchBaseDn = param['groupSearchBaseDn']
        self.groupSearchType = param['groupSearchType']
        self.serverURIs = param['serverURIs']
        if self.serverURIs is not None:
            self.serverURIs = self.serverURIs.split(',')
        self.userSearchBaseDN = param['userSearchBaseDN']
        self.searchBindDN = param['searchBindDN']
        self.searchBindPassword = param['searchBindPassword']
        self.userSearchFilter = param['userSearchFilter']
        self.userDNTemplate = param['userDNTemplate']
        self.groupSearchCustomFilter = param['groupSearchCustomFilter']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_ldap_configuration(self):
        """
            Return ldap configuration if found

            :return: Details about the ldap configuration. None if not found.
            :rtype: solidfire.models.GetLdapConfigurationResult
        """
        ldap_config = self.sfe.get_ldap_configuration()
        return ldap_config

    def enable_ldap(self):
        """
        Enable LDAP
        :return: nothing
        """
        try:
            self.sfe.enable_ldap_authentication(self.serverURIs, auth_type=self.authType,
                                                group_search_base_dn=self.groupSearchBaseDn,
                                                group_search_type=self.groupSearchType,
                                                group_search_custom_filter=self.groupSearchCustomFilter,
                                                search_bind_dn=self.searchBindDN,
                                                search_bind_password=self.searchBindPassword,
                                                user_search_base_dn=self.userSearchBaseDN,
                                                user_search_filter=self.userSearchFilter,
                                                user_dntemplate=self.userDNTemplate)
        except solidfire.common.ApiServerError as error:
            self.module.fail_json(msg='Error enabling LDAP %s: %s' % (self.account_id, to_native(error)),
                                  exception=traceback.format_exc())

    def check_config(self, ldap_config):
        """
        Check to see if the ldap config has been modified.
        :param ldap_config: The LDAP configuration
        :return: False if the config is the same as the playbook, True if it is not
        """
        if self.authType != ldap_config.ldap_configuration.auth_type:
            return True
        if self.serverURIs != ldap_config.ldap_configuration.server_uris:
            return True
        if self.groupSearchBaseDn != ldap_config.ldap_configuration.group_search_base_dn:
            return True
        if self.groupSearchType != ldap_config.ldap_configuration.group_search_type:
            return True
        if self.groupSearchCustomFilter != ldap_config.ldap_configuration.group_search_custom_filter:
            return True
        if self.searchBindDN != ldap_config.ldap_configuration.search_bind_dn:
            return True
        if self.searchBindPassword != ldap_config.ldap_configuration.search_bind_password:
            return True
        if self.userSearchBaseDN != ldap_config.ldap_configuration.user_search_base_dn:
            return True
        if self.userSearchFilter != ldap_config.ldap_configuration.user_search_filter:
            return True
        if self.userDNTemplate != ldap_config.ldap_configuration.user_dntemplate:
            return True
        return False

    def apply(self):
        changed = False
        ldap_config = self.get_ldap_configuration()
        if self.state == 'absent':
            if ldap_config and ldap_config.ldap_configuration.enabled:
                changed = True
        if self.state == 'present' and self.check_config(ldap_config):
            changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    self.enable_ldap()
                elif self.state == 'absent':
                    self.sfe.disable_ldap_authentication()

        self.module.exit_json(changed=changed)


def main():
    v = NetappElementLdap()
    v.apply()


if __name__ == '__main__':
    main()
