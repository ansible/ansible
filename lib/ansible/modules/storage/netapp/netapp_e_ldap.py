#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: netapp_e_ldap
short_description: NetApp E-Series manage LDAP integration to use for authentication
description:
    - Configure an E-Series system to allow authentication via an LDAP server
version_added: '2.7'
author: Michael Price (@lmprice)
extends_documentation_fragment:
    - netapp.eseries
options:
    state:
        description:
            - Enable/disable LDAP support on the system. Disabling will clear out any existing defined domains.
        choices:
            - present
            - absent
        default: present
    identifier:
        description:
            - This is a unique identifier for the configuration (for cases where there are multiple domains configured).
            - If this is not specified, but I(state=present), we will utilize a default value of 'default'.
    username:
        description:
            - This is the user account that will be used for querying the LDAP server.
            - "Example: CN=MyBindAcct,OU=ServiceAccounts,DC=example,DC=com"
        required: yes
        aliases:
            - bind_username
    password:
        description:
            - This is the password for the bind user account.
        required: yes
        aliases:
            - bind_password
    attributes:
        description:
            - The user attributes that should be considered for the group to role mapping.
            - Typically this is used with something like 'memberOf', and a user's access is tested against group
              membership or lack thereof.
        default: memberOf
    server:
        description:
            - This is the LDAP server url.
            - The connection string should be specified as using the ldap or ldaps protocol along with the port
              information.
        aliases:
            - server_url
        required: yes
    name:
        description:
            - The domain name[s] that will be utilized when authenticating to identify which domain to utilize.
            - Default to use the DNS name of the I(server).
            - The only requirement is that the name[s] be resolvable.
            - "Example: user@example.com"
        required: no
    search_base:
        description:
            - The search base is used to find group memberships of the user.
            - "Example: ou=users,dc=example,dc=com"
        required: yes
    role_mappings:
        description:
            - This is where you specify which groups should have access to what permissions for the
              storage-system.
            - For example, all users in group A will be assigned all 4 available roles, which will allow access
              to all the management functionality of the system (super-user). Those in group B only have the
              storage.monitor role, which will allow only read-only access.
            - This is specified as a mapping of regular expressions to a list of roles. See the examples.
            - The roles that will be assigned to to the group/groups matching the provided regex.
            - storage.admin allows users full read/write access to storage objects and operations.
            - storage.monitor allows users read-only access to storage objects and operations.
            - support.admin allows users access to hardware, diagnostic information, the Major Event
              Log, and other critical support-related functionality, but not the storage configuration.
            - security.admin allows users access to authentication/authorization configuration, as well
              as the audit log configuration, and certification management.
        required: yes
    user_attribute:
        description:
            - This is the attribute we will use to match the provided username when a user attempts to
              authenticate.
        default: sAMAccountName
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: no
notes:
    - Check mode is supported.
    - This module allows you to define one or more LDAP domains identified uniquely by I(identifier) to use for
      authentication. Authorization is determined by I(role_mappings), in that different groups of users may be given
      different (or no), access to certain aspects of the system and API.
    - The local user accounts will still be available if the LDAP server becomes unavailable/inaccessible.
    - Generally, you'll need to get the details of your organization's LDAP server before you'll be able to configure
      the system for using LDAP authentication; every implementation is likely to be very different.
    - This API is currently only supported with the Embedded Web Services API v2.0 and higher, or the Web Services Proxy
      v3.0 and higher.
'''

EXAMPLES = '''
    - name: Disable LDAP authentication
      netapp_e_ldap:
        api_url: "10.1.1.1:8443"
        api_username: "admin"
        api_password: "myPass"
        ssid: "1"
        state: absent

    - name: Remove the 'default' LDAP domain configuration
      netapp_e_ldap:
        state: absent
        identifier: default

    - name: Define a new LDAP domain, utilizing defaults where possible
      netapp_e_ldap:
        state: present
        bind_username: "CN=MyBindAccount,OU=ServiceAccounts,DC=example,DC=com"
        bind_password: "mySecretPass"
        server: "ldap://example.com:389"
        search_base: 'OU=Users,DC=example,DC=com'
        role_mappings:
          ".*dist-dev-storage.*":
            - storage.admin
            - security.admin
            - support.admin
            - storage.monitor
'''

RETURN = """
msg:
    description: Success message
    returned: on success
    type: str
    sample: The ldap settings have been updated.
"""

import json
import logging

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native


class Ldap(object):
    NO_CHANGE_MSG = "No changes were necessary."

    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent']),
            identifier=dict(type='str', required=False, ),
            username=dict(type='str', required=False, aliases=['bind_username']),
            password=dict(type='str', required=False, aliases=['bind_password'], no_log=True),
            name=dict(type='list', required=False, ),
            server=dict(type='str', required=False, aliases=['server_url']),
            search_base=dict(type='str', required=False, ),
            role_mappings=dict(type='dict', required=False, ),
            user_attribute=dict(type='str', required=False, default='sAMAccountName'),
            attributes=dict(type='list', default=['memberOf'], required=False, ),
            log_path=dict(type='str', required=False),
        ))

        required_if = [
            ["state", "present", ["username", "password", "server", "search_base", "role_mappings", ]]
        ]

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)
        args = self.module.params
        self.ldap = args['state'] == 'present'
        self.identifier = args['identifier']
        self.username = args['username']
        self.password = args['password']
        self.names = args['name']
        self.server = args['server']
        self.search_base = args['search_base']
        self.role_mappings = args['role_mappings']
        self.user_attribute = args['user_attribute']
        self.attributes = args['attributes']

        self.ssid = args['ssid']
        self.url = args['api_url']
        self.creds = dict(url_password=args['api_password'],
                          validate_certs=args['validate_certs'],
                          url_username=args['api_username'],
                          timeout=60)

        self.check_mode = self.module.check_mode

        log_path = args['log_path']

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

        self.embedded = None
        self.base_path = None

    def make_configuration(self):
        if not self.identifier:
            self.identifier = 'default'

        if not self.names:
            parts = urlparse.urlparse(self.server)
            netloc = parts.netloc
            if ':' in netloc:
                netloc = netloc.split(':')[0]
            self.names = [netloc]

        roles = list()
        for regex in self.role_mappings:
            for role in self.role_mappings[regex]:
                roles.append(dict(groupRegex=regex,
                                  ignoreCase=True,
                                  name=role))

        domain = dict(id=self.identifier,
                      ldapUrl=self.server,
                      bindLookupUser=dict(user=self.username, password=self.password),
                      roleMapCollection=roles,
                      groupAttributes=self.attributes,
                      names=self.names,
                      searchBase=self.search_base,
                      userAttribute=self.user_attribute,
                      )

        return domain

    def is_embedded(self):
        """Determine whether or not we're using the embedded or proxy implementation of Web Services"""
        if self.embedded is None:
            url = self.url
            try:
                parts = urlparse.urlparse(url)
                parts = parts._replace(path='/devmgr/utils/')
                url = urlparse.urlunparse(parts)

                (rc, result) = request(url + 'about', **self.creds)
                self.embedded = not result['runningAsProxy']
            except Exception as err:
                self._logger.exception("Failed to retrieve the About information.")
                self.module.fail_json(msg="Failed to determine the Web Services implementation type!"
                                          " Array Id [%s]. Error [%s]."
                                          % (self.ssid, to_native(err)))

        return self.embedded

    def get_full_configuration(self):
        try:
            (rc, result) = request(self.url + self.base_path, **self.creds)
            return result
        except Exception as err:
            self._logger.exception("Failed to retrieve the LDAP configuration.")
            self.module.fail_json(msg="Failed to retrieve LDAP configuration! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def get_configuration(self, identifier):
        try:
            (rc, result) = request(self.url + self.base_path + '%s' % (identifier), ignore_errors=True, **self.creds)
            if rc == 200:
                return result
            elif rc == 404:
                return None
            else:
                self.module.fail_json(msg="Failed to retrieve LDAP configuration! Array Id [%s]. Error [%s]."
                                          % (self.ssid, result))
        except Exception as err:
            self._logger.exception("Failed to retrieve the LDAP configuration.")
            self.module.fail_json(msg="Failed to retrieve LDAP configuration! Array Id [%s]. Error [%s]."
                                      % (self.ssid, to_native(err)))

    def update_configuration(self):
        # Define a new domain based on the user input
        domain = self.make_configuration()

        # This is the current list of configurations
        current = self.get_configuration(self.identifier)

        update = current != domain
        msg = "No changes were necessary for [%s]." % self.identifier
        self._logger.info("Is updated: %s", update)
        if update and not self.check_mode:
            msg = "The configuration changes were made for [%s]." % self.identifier
            try:
                if current is None:
                    api = self.base_path + 'addDomain'
                else:
                    api = self.base_path + '%s' % (domain['id'])

                (rc, result) = request(self.url + api, method='POST', data=json.dumps(domain), **self.creds)
            except Exception as err:
                self._logger.exception("Failed to modify the LDAP configuration.")
                self.module.fail_json(msg="Failed to modify LDAP configuration! Array Id [%s]. Error [%s]."
                                          % (self.ssid, to_native(err)))

        return msg, update

    def clear_single_configuration(self, identifier=None):
        if identifier is None:
            identifier = self.identifier

        configuration = self.get_configuration(identifier)
        updated = False
        msg = self.NO_CHANGE_MSG
        if configuration:
            updated = True
            msg = "The LDAP domain configuration for [%s] was cleared." % identifier
            if not self.check_mode:
                try:
                    (rc, result) = request(self.url + self.base_path + '%s' % identifier, method='DELETE', **self.creds)
                except Exception as err:
                    self.module.fail_json(msg="Failed to remove LDAP configuration! Array Id [%s]. Error [%s]."
                                              % (self.ssid, to_native(err)))
        return msg, updated

    def clear_configuration(self):
        configuration = self.get_full_configuration()
        updated = False
        msg = self.NO_CHANGE_MSG
        if configuration['ldapDomains']:
            updated = True
            msg = "The LDAP configuration for all domains was cleared."
            if not self.check_mode:
                try:
                    (rc, result) = request(self.url + self.base_path, method='DELETE', ignore_errors=True, **self.creds)

                    # Older versions of NetApp E-Series restAPI does not possess an API to remove all existing configs
                    if rc == 405:
                        for config in configuration['ldapDomains']:
                            self.clear_single_configuration(config['id'])

                except Exception as err:
                    self.module.fail_json(msg="Failed to clear LDAP configuration! Array Id [%s]. Error [%s]."
                                              % (self.ssid, to_native(err)))
        return msg, updated

    def get_base_path(self):
        embedded = self.is_embedded()
        if embedded:
            return 'storage-systems/%s/ldap/' % self.ssid
        else:
            return '/ldap/'

    def update(self):
        self.base_path = self.get_base_path()

        if self.ldap:
            msg, update = self.update_configuration()
        elif self.identifier:
            msg, update = self.clear_single_configuration()
        else:
            msg, update = self.clear_configuration()
        self.module.exit_json(msg=msg, changed=update, )

    def __call__(self, *args, **kwargs):
        self.update()


def main():
    settings = Ldap()
    settings()


if __name__ == '__main__':
    main()
