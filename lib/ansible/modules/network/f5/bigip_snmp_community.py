#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_snmp_community
short_description: Manages SNMP communities on a BIG-IP.
description:
  - Assists in managing SNMP communities on a BIG-IP. Different SNMP versions are supported
    by this module. Take note of the different parameters offered by this module, as different
    parameters work for different versions of SNMP. Typically this becomes an interest if you
    are mixing versions C(v2c) and C(3).
version_added: 2.6
options:
  state:
    description:
      - When C(present), ensures that the address list and entries exists.
      - When C(absent), ensures the address list is removed.
    default: present
    choices:
      - present
      - absent
  version:
    description:
      - Specifies to which Simple Network Management Protocol (SNMP) version the trap destination applies.
    choices: ['v1', 'v2c', 'v3']
    default: v2c
  name:
    description:
      - Name that identifies the SNMP community.
      - When C(version) is C(v1) or C(v2c), this parameter is required.
      - The name C(public) is a reserved name on the BIG-IP. This module handles that name differently
        than others. Functionally, you should not see a difference however.
  community:
    description:
      - Specifies the community string (password) for access to the MIB.
      - This parameter is only relevant when C(version) is C(v1), or C(v2c). If C(version) is
        something else, this parameter is ignored.
  source:
    description:
      - Specifies the source address for access to the MIB.
      - This parameter can accept a value of C(all).
      - If this parameter is not specified, the value C(all) is used.
      - This parameter is only relevant when C(version) is C(v1), or C(v2c). If C(version) is
        something else, this parameter is ignored.
      - If C(source) is set to C(all), then it is not possible to specify an C(oid). This will
        raise an error.
      - This parameter should be provided when C(state) is C(absent), so that the correct community
        is removed. To remove the C(public) SNMP community that comes with a BIG-IP, this parameter
        should be set to C(default).
  port:
    description:
      - Specifies the port for the trap destination.
      - This parameter is only relevant when C(version) is C(v1), or C(v2c). If C(version) is
        something else, this parameter is ignored.
  oid:
    description:
      - Specifies the object identifier (OID) for the record.
      - When C(version) is C(v3), this parameter is required.
      - When C(version) is either C(v1) or C(v2c), if this value is specified, then C(source)
        must not be set to C(all).
  access:
    description:
      - Specifies the user's access level to the MIB.
      - When creating a new community, if this parameter is not specified, the default is C(ro).
      - When C(ro), specifies that the user can view the MIB, but cannot modify the MIB.
      - When C(rw), specifies that the user can view and modify the MIB.
    choices:
      - ro
      - rw
      - read-only
      - read-write
  ip_version:
    description:
      - Specifies whether the record applies to IPv4 or IPv6 addresses.
      - When creating a new community, if this value is not specified, the default of C(4) will
        be used.
      - This parameter is only relevant when C(version) is C(v1), or C(v2c). If C(version) is
        something else, this parameter is ignored.
    choices: ['4', '6']
  snmp_username:
    description:
      - Specifies the name of the user for whom you want to grant access to the SNMP v3 MIB.
      - This parameter is only relevant when C(version) is C(v3). If C(version) is something
        else, this parameter is ignored.
      - When creating a new SNMP C(v3) community, this parameter is required.
      - This parameter cannot be changed once it has been set.
  snmp_auth_protocol:
    description:
      - Specifies the authentication method for the user.
      - When C(md5), specifies that the system uses the MD5 algorithm to authenticate the user.
      - When C(sha), specifies that the secure hash algorithm (SHA) to authenticate the user.
      - When C(none), specifies that user does not require authentication.
      - When creating a new SNMP C(v3) community, if this parameter is not specified, the default
        of C(sha) will be used.
    choices:
      - md5
      - sha
      - none
  snmp_auth_password:
    description:
      - Specifies the password for the user.
      - When creating a new SNMP C(v3) community, this parameter is required.
      - This value must be at least 8 characters long.
  snmp_privacy_protocol:
    description:
      - Specifies the encryption protocol.
      - When C(aes), specifies that the system encrypts the user information using AES
        (Advanced Encryption Standard).
      - When C(des), specifies that the system encrypts the user information using DES
        (Data Encryption Standard).
      - When C(none), specifies that the system does not encrypt the user information.
      - When creating a new SNMP C(v3) community, if this parameter is not specified, the
        default of C(aes) will be used.
    choices:
      - aes
      - des
      - none
  snmp_privacy_password:
    description:
      - Specifies the password for the user.
      - When creating a new SNMP C(v3) community, this parameter is required.
      - This value must be at least 8 characters long.
  update_password:
    description:
      - C(always) will allow to update passwords if the user chooses to do so.
        C(on_create) will only set the password for newly created resources.
    default: always
    choices:
      - always
      - on_create
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create an SMNP v2c read-only community
  bigip_snmp_community:
    name: foo
    version: v2c
    source: all
    oid: .1
    access: ro
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Create an SMNP v3 read-write community
  bigip_snmp_community:
    name: foo
    version: v3
    snmp_username: foo
    snmp_auth_protocol: sha
    snmp_auth_password: secret
    snmp_privacy_protocol: aes
    snmp_privacy_password: secret
    oid: .1
    access: rw
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove the default 'public' SNMP community
  bigip_snmp_community:
    name: public
    source: default
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
param1:
  description: The new param1 value of the resource.
  returned: changed
  type: bool
  sample: true
param2:
  description: The new param2 value of the resource.
  returned: changed
  type: string
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'communityName': 'community',
        'oidSubset': 'oid',
        'ipv6': 'ip_version',
        'authProtocol': 'snmp_auth_protocol',
        'privacyProtocol': 'snmp_privacy_protocol',
        'username': 'snmp_username',
        'securityLevel': 'security_level',
        'authPassword': 'snmp_auth_password',
        'privacyPassword': 'snmp_privacy_password'
    }

    api_attributes = [
        'source', 'oidSubset', 'ipv6', 'communityName', 'access', 'authPassword',
        'authProtocol', 'username', 'securityLevel', 'privacyProtocol', 'privacyPassword'
    ]

    returnables = [
        'community', 'oid', 'ip_version', 'snmp_auth_protocol', 'snmp_privacy_protocol',
        'access', 'source', 'snmp_username', 'snmp_auth_password', 'snmp_privacy_password'
    ]

    updatables = [
        'community', 'oid', 'ip_version', 'snmp_auth_protocol', 'snmp_privacy_protocol',
        'access', 'source', 'snmp_auth_password', 'snmp_privacy_password', 'security_level',
        'snmp_username'
    ]

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        return int(self._values['port'])


class ApiParameters(Parameters):
    @property
    def ip_version(self):
        if self._values['ip_version'] is None:
            return None
        if self._values['ip_version'] == 'enabled':
            return 6
        return 4

    @property
    def source(self):
        if self._values['source'] is None:
            return 'all'
        return self._values['source']


class ModuleParameters(Parameters):
    @property
    def ip_version(self):
        if self._values['ip_version'] is None:
            return None
        return int(self._values['ip_version'])

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        if self._values['source'] == '':
            return 'all'
        return self._values['source']

    @property
    def access(self):
        if self._values['access'] is None:
            return None
        elif self._values['access'] in ['ro', 'read-only']:
            return 'ro'
        elif self._values['access'] in ['rw', 'read-write']:
            return 'rw'
        else:
            raise F5ModuleError(
                "Unknown access format specified: '{0}'.".format(self._values['access'])
            )

    @property
    def snmp_auth_password(self):
        if self._values['snmp_auth_password'] is None:
            return None
        if len(self._values['snmp_auth_password']) < 8:
            raise F5ModuleError(
                "snmp_auth_password must be at least 8 characters long."
            )
        return self._values['snmp_auth_password']

    @property
    def snmp_privacy_password(self):
        if self._values['snmp_privacy_password'] is None:
            return None
        if len(self._values['snmp_privacy_password']) < 8:
            raise F5ModuleError(
                "snmp_privacy_password must be at least 8 characters long."
            )
        return self._values['snmp_privacy_password']

    @property
    def name(self):
        if self._values['name'] == 'public':
            return 'comm-public'
        return self._values['name']


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
    def ip_version(self):
        if self._values['ip_version'] is None:
            return None
        elif self._values['ip_version'] == 4:
            return 'disabled'
        return 'enabled'

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        if self._values['source'] == 'all':
            return ''
        return self._values['source']


class ReportableChanges(Changes):
    pass


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

    def _check_source_and_oid(self):
        if self.have.oid is not None:
            if self.want.source == 'all' and self.want.oid != '':
                raise F5ModuleError(
                    "When specifying an 'all' source for a resource with an existing OID, you must specify a new, empty, OID."
                )
        if self.want.source == 'all' and self.want.oid != '':
            raise F5ModuleError(
                "When specifying an 'all' source for a resource, you may not specify an OID."
            )

    @property
    def source(self):
        self._check_source_and_oid()
        if self.want.source != self.have.source:
            return self.want.source

    @property
    def oid(self):
        self._check_source_and_oid()
        if self.want.oid != self.have.oid:
            return self.want.oid

    @property
    def snmp_privacy_password(self):
        if self.want.update_password == 'always' and self.want.snmp_privacy_password is not None:
            return self.want.snmp_privacy_password

    @property
    def snmp_auth_password(self):
        if self.want.update_password == 'always' and self.want.snmp_auth_password is not None:
            return self.want.snmp_auth_password


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)

    def exec_module(self):
        if self.version_is_less_than_3():
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)

    def version_is_less_than_3(self):
        version = self.module.params.get('version')
        if version == 'v3':
            return False
        else:
            return True


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False


class V1Manager(BaseManager):
    """Handles SNMP v1 and v2c

    """
    def create(self):
        if self.want.ip_version is None:
            self.want.update({'ip_version': 4})
        if self.want.access is None:
            self.want.update({'access': 'ro'})
        self._set_changed_options()
        if self.want.oid is not None and self.want.source == 'all':
            raise F5ModuleError(
                "When specify an oid, source may not be set to 'all'."
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        result = self.client.api.tm.sys.snmp.communities_s.community.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.sys.snmp.communities_s.community.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.sys.snmp.communities_s.community.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def remove_from_device(self):
        resource = self.client.api.tm.sys.snmp.communities_s.community.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.communities_s.community.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


class V2Manager(BaseManager):
    """Handles SNMP v3

    SNMP v3 has (almost) a completely separate set of variables than v2c or v1.
    The functionality is placed in this separate class to handle these differences.

    """
    def create(self):
        if self.want.access is None:
            self.want.update({'access': 'ro'})
        if self.want.snmp_auth_protocol is None:
            self.want.update({'snmp_auth_protocol': 'sha'})
        if self.want.snmp_privacy_protocol is None:
            self.want.update({'snmp_privacy_protocol': 'aes'})

        self._set_changed_options()
        if self.want.snmp_username is None:
            raise F5ModuleError(
                "snmp_username must be specified when creating a new v3 community."
            )
        if self.want.snmp_auth_password is None:
            raise F5ModuleError(
                "snmp_auth_password must be specified when creating a new v3 community."
            )
        if self.want.snmp_privacy_password is None:
            raise F5ModuleError(
                "snmp_privacy_password must be specified when creating a new v3 community."
            )
        if self.want.oid is None:
            raise F5ModuleError(
                "oid must be specified when creating a new v3 community."
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        result = self.client.api.tm.sys.snmp.users_s.user.exists(
            name=self.want.snmp_username,
            partition=self.want.partition
        )
        return result

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.sys.snmp.users_s.user.create(
            name=self.want.snmp_username,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.sys.snmp.users_s.user.load(
            name=self.want.snmp_username,
            partition=self.want.partition
        )
        resource.modify(**params)

    def remove_from_device(self):
        resource = self.client.api.tm.sys.snmp.users_s.user.load(
            name=self.want.snmp_username,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.users_s.user.load(
            name=self.want.snmp_username,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            version=dict(
                default='v2c',
                choices=['v1', 'v2c', 'v3']
            ),
            name=dict(),
            community=dict(),
            source=dict(),
            port=dict(type='int'),
            oid=dict(),
            access=dict(
                choices=['ro', 'rw', 'read-only', 'read-write']
            ),
            ip_version=dict(
                choices=['4', '6']
            ),
            snmp_username=dict(),
            snmp_auth_protocol=dict(
                choices=['md5', 'sha', 'none']
            ),
            snmp_auth_password=dict(no_log=True),
            snmp_privacy_protocol=dict(
                choices=['aes', 'des', 'none']
            ),
            snmp_privacy_password=dict(no_log=True),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            state=dict(default='present', choices=['absent', 'present']),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['version', 'v1', ['name']],
            ['version', 'v2', ['name']],
            ['version', 'v3', ['snmp_username']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
