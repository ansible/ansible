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
module: bigip_profile_persistence_cookie
short_description: Manage cookie persistence profiles on BIG-IP
description:
  - Manage cookie persistence profiles on BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  description:
    description:
      - Description of the profile.
    type: str
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(cookie) profile.
    type: str
    default: cookie
  cookie_method:
    description:
      - Specifies the type of cookie processing that the system uses.
      - When C(hash), specifies that the server provides the cookie, which the
        system then maps consistently to a specific node. This persistence type
        requires a C(cookie_name) value.
      - When C(insert), specifies that the system inserts server information,
        in the form of a cookie, into the header of the server response.
      - When C(passive), specifies that the server provides the cookie, formatted
        with the correct server information and timeout. This persistence type
        requires a C(cookie_name) value.
      - When C(rewrite), specifies that the system intercepts the BIGipCookie
        header, sent from the server, and overwrites the name and value of that
        cookie.
    type: str
    choices:
      - hash
      - insert
      - passive
      - rewrite
  cookie_name:
    description:
      - Specifies a unique name for the cookie.
    type: str
  http_only:
    description:
      - Specifies whether the httponly attribute should be enabled or
        disabled for the inserted cookies.
    type: bool
  match_across_services:
    description:
      - When C(yes), specifies that all persistent connections from a client IP address that go
        to the same virtual IP address also go to the same node.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: bool
  match_across_virtuals:
    description:
      - When C(yes), specifies that all persistent connections from the same client IP address
        go to the same node.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: bool
  match_across_pools:
    description:
      - When C(yes), specifies that the system can use any pool that contains this persistence
        record.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: bool
  cookie_encryption:
    description:
      - Specifies the way in which the cookie encryption format is used.
      - When C(disabled), generates the cookie format unencrypted.
      - When C(preferred), generate an encrypted cookie, but accepts both encrypted and unencrypted formats.
      - When C(required), cookie format must be encrypted.
    type: str
    choices:
      - disabled
      - preferred
      - required
  override_connection_limit:
    description:
      - When C(yes), specifies that the system allows you to specify that pool member connection
        limits will be overridden for persisted clients.
      - Per-virtual connection limits remain hard limits and are not overridden.
    type: bool
  encrypt_cookie_pool_name:
    description:
      - Specifies whether the pool-name in the inserted BIG-IP default cookie should be encrypted.
    type: bool
  always_send:
    description:
      - Send the cookie persistence entry on every reply, even if the
        entry has previously been supplied to the client.
    type: bool
  secure:
    description:
      - Specifies whether the secure attribute should be enabled or
        disabled for the inserted cookies.
    type: bool
  encryption_passphrase:
    description:
      - Specifies a passphrase to be used for cookie encryption.
    type: str
  update_password:
    description:
      - C(always) will allow to update passphrases if the user chooses to do so.
        C(on_create) will only set the passphrase for newly created profiles.
    type: str
    choices:
      - always
      - on_create
    default: always
  expiration:
    description:
      - Specifies the expiration time of the cookie. By default the system generates and uses session cookie.
        This cookie expires when the user session expires, that is when the browser is closed.
    suboptions:
      days:
        description:
          - Cookie expiration time in days, the value must be in range from C(0) to C(24855) days.
        type: int
      hours:
        description:
          - Cookie expiration time in hours, the value must be in the range from C(0) to C(23) hours.
        type: int
      minutes:
        description:
          - Cookie expiration time in minutes, the value must be in the range from C(0) to C(59) minutes.
        type: int
      seconds:
        description:
          - Cookie expiration time in seconds, the value must be in the range from C(0) to C(59) seconds.
        type: int
        default: 0
    type: dict
    version_added: 2.8
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a persistence cookie profile
  bigip_profile_persistence_cookie:
    name: foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
- name: Create a persistence cookie profile with expiration time
  bigip_profile_persistence_cookie:
    name: foo
    expiration:
      days: 7
      hours: 12
      minutes: 30
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
cookie_name:
  description: The new Cookie Name value.
  returned: changed
  type: str
  sample: cookie1
cookie_method:
  description: The new Cookie Method.
  returned: changed
  type: str
  sample: insert
parent:
  description: The parent profile.
  returned: changed
  type: str
  sample: /Common/cookie
cookie_encryption:
  description: The new Cookie Encryption type.
  returned: changed
  type: str
  sample: preferred
match_across_pools:
  description: The new Match Across Pools value.
  returned: changed
  type: bool
  sample: yes
match_across_services:
  description: The new Match Across Services value.
  returned: changed
  type: bool
  sample: no
match_across_virtuals:
  description: The new Match Across Virtuals value.
  returned: changed
  type: bool
  sample: yes
override_connection_limit:
  description: The new Override Connection Limit value.
  returned: changed
  type: bool
  sample: no
encrypt_cookie_pool_name:
  description: The new Encrypt Cookie Pool Name value.
  returned: changed
  type: bool
  sample: yes
always_send:
  description: The new Always Send value.
  returned: changed
  type: bool
  sample: no
http_only:
  description: The new HTTP Only value.
  returned: changed
  type: bool
  sample: yes
description:
  description: The new description.
  returned: changed
  type: str
  sample: My description
secure:
  description: The new Secure Cookie value.
  returned: changed
  type: bool
  sample: no
expiration:
  description: The expiration time of the cookie.
  returned: changed
  type: complex
  contains:
    days:
      description: Cookie expiration time in days.
      returned: changed
      type: int
      sample: 125
    hours:
      description: Cookie expiration time in hours.
      returned: changed
      type: int
      sample: 22
    minutes:
      description: Cookie expiration time in minutes.
      returned: changed
      type: int
      sample: 58
    seconds:
      description: Cookie expiration time in seconds.
      returned: changed
      type: int
      sample: 20
  sample: hash/dictionary of values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'cookieName': 'cookie_name',
        'method': 'cookie_method',
        'defaultsFrom': 'parent',
        'cookieEncryption': 'cookie_encryption',
        'matchAcrossPools': 'match_across_pools',
        'matchAcrossServices': 'match_across_services',
        'matchAcrossVirtuals': 'match_across_virtuals',
        'overrideConnectionLimit': 'override_connection_limit',
        'encryptCookiePoolname': 'encrypt_cookie_pool_name',
        'alwaysSend': 'always_send',
        'httponly': 'http_only',
        'cookieEncryptionPassphrase': 'encryption_passphrase',
    }

    api_attributes = [
        'description',
        'cookieName',
        'defaultsFrom',
        'cookieEncryption',
        'matchAcrossPools',
        'matchAcrossServices',
        'matchAcrossVirtuals',
        'overrideConnectionLimit',
        'encryptCookiePoolname',
        'alwaysSend',
        'httponly',
        'secure',
        'cookieEncryptionPassphrase',
        'method',
        'expiration'
    ]

    returnables = [
        'cookie_name',
        'cookie_method',
        'parent',
        'cookie_encryption',
        'match_across_pools',
        'match_across_services',
        'match_across_virtuals',
        'override_connection_limit',
        'encrypt_cookie_pool_name',
        'always_send',
        'http_only',
        'encryption_passphrase',
        'description',
        'secure',
        'expiration',
    ]

    updatables = [
        'cookie_name',
        'cookie_method',
        'parent',
        'cookie_encryption',
        'match_across_pools',
        'match_across_services',
        'match_across_virtuals',
        'override_connection_limit',
        'encrypt_cookie_pool_name',
        'always_send',
        'http_only',
        'encryption_passphrase',
        'description',
        'secure',
        'expiration',
    ]

    @property
    def encrypt_cookie_pool_name(self):
        return flatten_boolean(self._values['encrypt_cookie_pool_name'])

    @property
    def always_send(self):
        return flatten_boolean(self._values['always_send'])

    @property
    def match_across_pools(self):
        return flatten_boolean(self._values['match_across_pools'])

    @property
    def match_across_services(self):
        return flatten_boolean(self._values['match_across_services'])

    @property
    def match_across_virtuals(self):
        return flatten_boolean(self._values['match_across_virtuals'])

    @property
    def http_only(self):
        return flatten_boolean(self._values['http_only'])

    @property
    def secure(self):
        return flatten_boolean(self._values['secure'])

    @property
    def override_connection_limit(self):
        return flatten_boolean(self._values['override_connection_limit'])


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']

    @property
    def expiration(self):
        if self._values['expiration'] is None:
            return None

        days = self.days
        hours = self.hours
        minutes = self.minutes
        seconds = self.seconds

        if days is not None:
            if hours is None:
                raise F5ModuleError(
                    "Incorrect format, 'hours' parameter is missing value."
                )
            if minutes is None:
                raise F5ModuleError(
                    "Incorrect format, 'minutes' parameter is missing value."
                )

            expiry_time = '{0}:{1}:{2}:{3}'.format(days, hours, minutes, seconds)
            return expiry_time

        if hours is not None:
            if minutes is None:
                raise F5ModuleError(
                    "Incorrect format, 'minutes' parameter is missing value."
                )

            expiry_time = '{0}:{1}:{2}'.format(hours, minutes, seconds)
            return expiry_time

        if minutes is not None:
            expiry_time = '{0}:{1}'.format(minutes, seconds)
            return expiry_time

        return str(seconds)

    @property
    def days(self):
        days = self._values['expiration']['days']
        if days is None:
            return None
        if days < 0 or days >= 24856:
            raise F5ModuleError(
                'The provided value is invalid, the correct value range is: 0 - 24855 days.'
            )
        return days

    @property
    def hours(self):
        hours = self._values['expiration']['hours']
        if hours is None:
            return None
        if hours < 0 or hours > 23:
            raise F5ModuleError(
                'The provided value is invalid, the correct value range is: 0 - 23 hours.'
            )
        return hours

    @property
    def minutes(self):
        minutes = self._values['expiration']['minutes']
        if minutes is None:
            return None
        if minutes < 0 or minutes > 59:
            raise F5ModuleError(
                'The provided value is invalid, the correct value range is: 0 - 59 minutes.'
            )
        return minutes

    @property
    def seconds(self):
        seconds = self._values['expiration']['seconds']
        if seconds < 0 or seconds > 59:
            raise F5ModuleError(
                'The provided value is invalid, the correct value range is: 0 - 59 seconds.'
            )
        return seconds


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
    def encrypt_cookie_pool_name(self):
        if self._values['encrypt_cookie_pool_name'] is None:
            return None
        elif self._values['encrypt_cookie_pool_name'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def always_send(self):
        if self._values['always_send'] is None:
            return None
        elif self._values['always_send'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def match_across_pools(self):
        if self._values['match_across_pools'] is None:
            return None
        elif self._values['match_across_pools'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def match_across_services(self):
        if self._values['match_across_services'] is None:
            return None
        elif self._values['match_across_services'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def match_across_virtuals(self):
        if self._values['match_across_virtuals'] is None:
            return None
        elif self._values['match_across_virtuals'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def http_only(self):
        if self._values['http_only'] is None:
            return None
        elif self._values['http_only'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def secure(self):
        if self._values['secure'] is None:
            return None
        elif self._values['secure'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def override_connection_limit(self):
        if self._values['override_connection_limit'] is None:
            return None
        elif self._values['override_connection_limit'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def encrypt_cookie_pool_name(self):
        return flatten_boolean(self._values['encrypt_cookie_pool_name'])

    @property
    def always_send(self):
        return flatten_boolean(self._values['always_send'])

    @property
    def match_across_pools(self):
        return flatten_boolean(self._values['match_across_pools'])

    @property
    def match_across_services(self):
        return flatten_boolean(self._values['match_across_services'])

    @property
    def match_across_virtuals(self):
        return flatten_boolean(self._values['match_across_virtuals'])

    @property
    def http_only(self):
        return flatten_boolean(self._values['http_only'])

    @property
    def secure(self):
        return flatten_boolean(self._values['secure'])

    @property
    def override_connection_limit(self):
        return flatten_boolean(self._values['override_connection_limit'])

    @property
    def encryption_passphrase(self):
        return None

    @property
    def expiration(self):
        expire = self._values['expiration']
        result = dict()

        if expire is None:
            return None
        tmp = expire.split(':')

        if len(tmp) == 1:
            result['seconds'] = int(tmp[0])
        if len(tmp) == 2:
            result['minutes'] = int(tmp[0])
            result['seconds'] = int(tmp[1])
        if len(tmp) == 3:
            result['hours'] = int(tmp[0])
            result['minutes'] = int(tmp[1])
            result['seconds'] = int(tmp[2])
        if len(tmp) == 4:
            result['days'] = int(tmp[0])
            result['hours'] = int(tmp[1])
            result['minutes'] = int(tmp[2])
            result['seconds'] = int(tmp[3])

        return result


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
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )

    @property
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)


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

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/persistence/cookie/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()

        if self.want.update_password == 'always':
            self.want.update({'encryption_passphrase': self.want.encryption_passphrase})
        else:
            if self.want.encryption_passphrase:
                del self.want._values['encryption_passphrase']

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

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/persistence/cookie/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/persistence/cookie/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/persistence/cookie/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True
        raise F5ModuleError(resp.content)

    def read_current_from_device(self):  # lgtm [py/similar-function]
        uri = "https://{0}:{1}/mgmt/tm/ltm/persistence/cookie/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            parent=dict(default='cookie'),
            cookie_name=dict(),
            cookie_method=dict(
                choices=[
                    'hash', 'insert', 'passive', 'rewrite'
                ]
            ),
            description=dict(),
            secure=dict(type='bool'),
            http_only=dict(type='bool'),
            cookie_encryption=dict(
                choices=[
                    'disabled', 'preferred', 'required'
                ]
            ),
            always_send=dict(type='bool'),
            match_across_services=dict(type='bool'),
            match_across_virtuals=dict(type='bool'),
            match_across_pools=dict(type='bool'),
            override_connection_limit=dict(type='bool'),
            encrypt_cookie_pool_name=dict(type='bool'),
            encryption_passphrase=dict(no_log=True),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            expiration=dict(
                type='dict',
                options=dict(
                    days=dict(
                        type='int'
                    ),
                    hours=dict(
                        type='int'
                    ),
                    minutes=dict(
                        type='int'
                    ),
                    seconds=dict(
                        type='int',
                        default=0
                    )
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
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
