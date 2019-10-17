#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_device_auth_ldap
short_description: Manage LDAP device authentication settings on BIG-IP
description:
  - Manage LDAP device authentication settings on BIG-IP.
version_added: 2.8
options:
  servers:
    description:
      - Specifies the LDAP servers that the system must use to obtain
        authentication information. You must specify a server when you
        create an LDAP configuration object.
    type: list
  port:
    description:
      - Specifies the port that the system uses for access to the remote host server.
      - When configuring LDAP device authentication for the first time, if this parameter
        is not specified, the default port is C(389).
    type: int
  remote_directory_tree:
    description:
      - Specifies the file location (tree) of the user authentication database on the
        server.
    type: str
  scope:
    description:
      - Specifies the level of the remote Active Directory or LDAP directory that the
        system should search for the user authentication.
    type: str
    choices:
      - sub
      - one
      - base
  bind_dn:
    description:
      - Specifies the distinguished name for the Active Directory or LDAP server user
        ID.
      - The BIG-IP client authentication module does not support Active Directory or
        LDAP servers that do not perform bind referral when authenticating referred
        accounts.
      - Therefore, if you plan to use Active Directory or LDAP as your authentication
        source and want to use referred accounts, make sure your servers perform bind
        referral.
    type: str
  bind_password:
    description:
      - Specifies a password for the Active Directory or LDAP server user ID.
    type: str
  user_template:
    description:
      - Specifies the distinguished name of the user who is logging on.
      - You specify the template as a variable that the system replaces with user-specific
        information during the logon attempt.
      - For example, you could specify a user template such as C(%s@siterequest.com) or
        C(uxml:id=%s,ou=people,dc=siterequest,dc=com).
      - When a user attempts to log on, the system replaces C(%s) with the name the user
        specified in the Basic Authentication dialog box, and passes that as the
        distinguished name for the bind operation.
      - The system passes the associated password as the password for the bind operation.
      - This field can contain only one C(%s) and cannot contain any other format
        specifiers.
    type: str
  check_member_attr:
    description:
      - Checks the user's member attribute in the remote LDAP or AD group.
    type: bool
  ssl:
    description:
      - Specifies whether the system uses an SSL port to communicate with the LDAP server.
    type: str
    choices:
      - "yes"
      - "no"
      - start-tls
  ca_cert:
    description:
      - Specifies the name of an SSL certificate from a certificate authority (CA).
      - To remove this value, use the reserved value C(none).
    type: str
    aliases: [ ssl_ca_cert ]
  client_key:
    description:
      - Specifies the name of an SSL client key.
      - To remove this value, use the reserved value C(none).
    type: str
    aliases: [ ssl_client_key ]
  client_cert:
    description:
      - Specifies the name of an SSL client certificate.
      - To remove this value, use the reserved value C(none).
    type: str
    aliases: [ ssl_client_cert ]
  validate_certs:
    description:
      - Specifies whether the system checks an SSL peer, as a result of which the
        system requires and verifies the server certificate.
    type: bool
    aliases: [ ssl_check_peer ]
  login_ldap_attr:
    description:
      - Specifies the LDAP directory attribute containing the local user name that is
        associated with the selected directory entry.
      - When configuring LDAP device authentication for the first time, if this parameter
        is not specified, the default port is C(samaccountname).
    type: str
  fallback_to_local:
    description:
      - Specifies that the system uses the Local authentication method if the remote
        authentication method is not available.
    type: bool
  state:
    description:
      - When C(present), ensures the device authentication method exists.
      - When C(absent), ensures the device authentication method does not exist.
    type: str
    choices:
      - present
      - absent
    default: present
  update_password:
    description:
      - C(always) will always update the C(bind_password).
      - C(on_create) will only set the C(bind_password) for newly created authentication
        mechanisms.
    type: str
    choices:
      - always
      - on_create
    default: always
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create an LDAP authentication object
  bigip_device_auth_ldap:
    name: foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
servers:
  description: LDAP servers used by the system to obtain authentication information.
  returned: changed
  type: list
  sample: ['192.168.1.1', '192.168.1.2']
port:
  description: The port that the system uses for access to the remote LDAP server.
  returned: changed
  type: int
  sample: 389
remote_directory_tree:
  description: File location (tree) of the user authentication database on the server.
  returned: changed
  type: str
  sample: "CN=Users,DC=FOOBAR,DC=LOCAL"
scope:
  description: The level of the remote Active Directory or LDAP directory searched for user authentication.
  returned: changed
  type: str
  sample: base
bind_dn:
  description: The distinguished name for the Active Directory or LDAP server user ID.
  returned: changed
  type: str
  sample: "user@foobar.local"
user_template:
  description: The distinguished name of the user who is logging on.
  returned: changed
  type: str
  sample: "uid=%s,ou=people,dc=foobar,dc=local"
check_member_attr:
  description: The user's member attribute in the remote LDAP or AD group.
  returned: changed
  type: bool
  sample: yes
ssl:
  description: Specifies whether the system uses an SSL port to communicate with the LDAP server.
  returned: changed
  type: str
  sample: start-tls
ca_cert:
  description: The name of an SSL certificate from a certificate authority.
  returned: changed
  type: str
  sample: My-Trusted-CA-Bundle.crt
client_key:
  description: The name of an SSL client key.
  returned: changed
  type: str
  sample: MyKey.key
client_cert:
  description: The name of an SSL client certificate.
  returned: changed
  type: str
  sample: MyCert.crt
validate_certs:
  description: Indicates if the system checks an SSL peer.
  returned: changed
  type: bool
  sample: yes
login_ldap_attr:
  description: The LDAP directory attribute containing the local user name associated with the selected directory entry.
  returned: changed
  type: str
  sample: samaccountname
fallback_to_local:
  description: Specifies that the system uses the Local authentication method as fallback
  returned: changed
  type: bool
  sample: yes
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'bindDn': 'bind_dn',
        'bindPw': 'bind_password',
        'userTemplate': 'user_template',
        'fallback': 'fallback_to_local',
        'loginAttribute': 'login_ldap_attr',
        'sslCheckPeer': 'validate_certs',
        'sslClientCert': 'client_cert',
        'sslClientKey': 'client_key',
        'sslCaCertFile': 'ca_cert',
        'checkRolesGroup': 'check_member_attr',
        'searchBaseDn': 'remote_directory_tree',
    }

    api_attributes = [
        'bindDn',
        'bindPw',
        'checkRolesGroup',
        'loginAttribute',
        'port',
        'scope',
        'searchBaseDn',
        'servers',
        'ssl',
        'sslCaCertFile',
        'sslCheckPeer',
        'sslClientCert',
        'sslClientKey',
        'userTemplate',
    ]

    returnables = [
        'bind_dn',
        'bind_password',
        'check_member_attr',
        'fallback_to_local',
        'login_ldap_attr',
        'port',
        'remote_directory_tree',
        'scope',
        'servers',
        'ssl',
        'ca_cert',
        'validate_certs',
        'client_cert',
        'client_key',
        'user_template',
    ]

    updatables = [
        'bind_dn',
        'bind_password',
        'check_member_attr',
        'fallback_to_local',
        'login_ldap_attr',
        'port',
        'remote_directory_tree',
        'scope',
        'servers',
        'ssl',
        'ssl_ca_cert',
        'ssl_check_peer',
        'ssl_client_cert',
        'ssl_client_key',
        'user_template',
    ]

    @property
    def ssl_ca_cert(self):
        if self._values['ssl_ca_cert'] is None:
            return None
        elif self._values['ssl_ca_cert'] in ['none', '']:
            return ''
        return fq_name(self.partition, self._values['ssl_ca_cert'])

    @property
    def ssl_client_key(self):
        if self._values['ssl_client_key'] is None:
            return None
        elif self._values['ssl_client_key'] in ['none', '']:
            return ''
        return fq_name(self.partition, self._values['ssl_client_key'])

    @property
    def ssl_client_cert(self):
        if self._values['ssl_client_cert'] is None:
            return None
        elif self._values['ssl_client_cert'] in ['none', '']:
            return ''
        return fq_name(self.partition, self._values['ssl_client_cert'])

    @property
    def ssl_check_peer(self):
        return flatten_boolean(self._values['ssl_check_peer'])

    @property
    def fallback_to_local(self):
        return flatten_boolean(self._values['fallback_to_local'])

    @property
    def check_member_attr(self):
        return flatten_boolean(self._values['check_member_attr'])

    @property
    def login_ldap_attr(self):
        if self._values['login_ldap_attr'] is None:
            return None
        elif self._values['login_ldap_attr'] in ['none', '']:
            return ''
        return self._values['login_ldap_attr']

    @property
    def user_template(self):
        if self._values['user_template'] is None:
            return None
        elif self._values['user_template'] in ['none', '']:
            return ''
        return self._values['user_template']

    @property
    def ssl(self):
        if self._values['ssl'] is None:
            return None
        elif self._values['ssl'] == 'start-tls':
            return 'start-tls'
        return flatten_boolean(self._values['ssl'])


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def ssl_check_peer(self):
        if self._values['ssl_check_peer'] is None:
            return None
        elif self._values['ssl_check_peer'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def fallback_to_local(self):
        if self._values['fallback_to_local'] is None:
            return None
        elif self._values['fallback_to_local'] == 'yes':
            return 'true'
        return 'false'

    @property
    def check_member_attr(self):
        if self._values['check_member_attr'] is None:
            return None
        elif self._values['check_member_attr'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def ssl(self):
        if self._values['ssl'] is None:
            return None
        elif self._values['ssl'] == 'start-tls':
            return 'start-tls'
        elif self._values['ssl'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def bind_password(self):
        return None

    @property
    def ssl_check_peer(self):
        return flatten_boolean(self._values['ssl_check_peer'])

    @property
    def check_member_attr(self):
        return flatten_boolean(self._values['check_member_attr'])

    @property
    def ssl(self):
        if self._values['ssl'] is None:
            return None
        elif self._values['ssl'] == 'start-tls':
            return 'start-tls'
        return flatten_boolean(self._values['ssl'])


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def login_ldap_attr(self):
        return cmp_str_with_none(self.want.login_ldap_attr, self.have.login_ldap_attr)

    @property
    def user_template(self):
        return cmp_str_with_none(self.want.user_template, self.have.user_template)

    @property
    def ssl_ca_cert(self):
        return cmp_str_with_none(self.want.ssl_ca_cert, self.have.ssl_ca_cert)

    @property
    def ssl_client_key(self):
        return cmp_str_with_none(self.want.ssl_client_key, self.have.ssl_client_key)

    @property
    def ssl_client_cert(self):
        return cmp_str_with_none(self.want.ssl_client_cert, self.have.ssl_client_cert)

    @property
    def bind_password(self):
        if self.want.bind_password != self.have.bind_password and self.want.update_password == 'always':
            return self.want.bind_password


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def update_auth_source_on_device(self, source):
        """Set the system auth source.

        Configuring the authentication source is only one step in the process of setting
        up an auth source. The other step is to inform the system of the auth source
        you want to use.

        This method is used for situations where

        * The ``use_for_auth`` parameter is set to ``yes``
        * The ``use_for_auth`` parameter is set to ``no``
        * The ``state`` parameter is set to ``absent``

        When ``state`` equal to ``absent``, before you can delete the TACACS+ configuration,
        you must set the system auth to "something else". The system ships with a system
        auth called "local", so this is the logical "something else" to use.

        When ``use_for_auth`` is no, the same situation applies as when ``state`` equal
        to ``absent`` is done above.

        When ``use_for_auth`` is ``yes``, this method will set the current system auth
        state to TACACS+.

        Arguments:
            source (string): The source that you want to set on the device.
        """
        params = dict(
            type=source
        )
        uri = 'https://{0}:{1}/mgmt/tm/auth/source/'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_fallback_on_device(self, fallback):
        params = dict(
            fallback=fallback
        )
        uri = 'https://{0}:{1}/mgmt/tm/auth/source/'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        if self.want.fallback_to_local == 'yes':
            self.update_fallback_on_device('true')
        elif self.want.fallback_to_local == 'no':
            self.update_fallback_on_device('false')
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.update_auth_source_on_device('local')
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.want.fallback_to_local == 'yes':
            self.update_fallback_on_device('true')
        elif self.want.fallback_to_local == 'no':
            self.update_fallback_on_device('false')
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/ldap/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'system-auth')
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = 'system-auth'
        params['partition'] = 'Common'
        uri = "https://{0}:{1}/mgmt/tm/auth/ldap/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        if not params:
            return
        uri = "https://{0}:{1}/mgmt/tm/auth/ldap/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'system-auth')
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/ldap/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'system-auth')
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/ldap/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name('Common', 'system-auth')
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = ApiParameters(params=response)

        uri = 'https://{0}:{1}/mgmt/tm/auth/source/'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result.update({'fallback': response['fallback']})
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            servers=dict(type='list'),
            port=dict(type='int'),
            remote_directory_tree=dict(),
            scope=dict(
                choices=['sub', 'one', 'base']
            ),
            bind_dn=dict(),
            bind_password=dict(no_log=True),
            user_template=dict(),
            check_member_attr=dict(type='bool'),
            ssl=dict(
                choices=['yes', 'no', 'start-tls']
            ),
            ca_cert=dict(aliases=['ssl_ca_cert']),
            client_key=dict(aliases=['ssl_client_key']),
            client_cert=dict(aliases=['ssl_client_cert']),
            validate_certs=dict(type='bool', aliases=['ssl_check_peer']),
            login_ldap_attr=dict(),
            fallback_to_local=dict(type='bool'),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            state=dict(default='present', choices=['absent', 'present']),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
