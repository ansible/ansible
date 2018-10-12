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
module: bigip_profile_http
short_description: Manage HTTP profiles on a BIG-IP
description:
  - Manage HTTP profiles on a BIG-IP.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the profile.
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(http) profile.
    default: /Common/http
  description:
    description:
      - Description of the profile.
  proxy_type:
    description:
      - Specifies the proxy mode for the profile.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    choices:
      - reverse
      - transparent
      - explicit
  dns_resolver:
    description:
      - Specifies the name of a configured DNS resolver, this option is mandatory when C(proxy_type)
        is set to C(explicit).
      - Format of the name can be either be prepended by partition (C(/Common/foo)), or specified
        just as an object name (C(foo)).
      - To remove the entry a value of C(none) or C('') can be set, however the profile C(proxy_type)
        must not be set as C(explicit).
  insert_xforwarded_for:
    description:
      - When specified system inserts an X-Forwarded-For header in an HTTP request
        with the client IP address, to use with connection pooling.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: bool
  redirect_rewrite:
    description:
      - Specifies whether the system rewrites the URIs that are part of HTTP
        redirect (3XX) responses.
      - When set to C(none) the system will not rewrite the URI in any
        HTTP redirect responses.
      - When set to C(all) the system rewrites the URI in all HTTP redirect responses.
      - When set to C(matching) the system rewrites the URI in any
        HTTP redirect responses that match the request URI.
      - When set to C(nodes) if the URI contains a node IP address instead of a host name,
        the system changes it to the virtual server address.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    choices:
      - none
      - all
      - matching
      - nodes
  encrypt_cookies:
    description:
      - Cookie names for the system to encrypt.
      - To remove the entry completely a value of C(none) or C('') should be set.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: list
  encrypt_cookie_secret:
    description:
      - Passphrase for cookie encryption.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
  update_password:
    description:
      - C(always) will update passwords if the C(encrypt_cookie_secret) is specified.
      - C(on_create) will only set the password for newly created profiles.
    default: always
    choices:
      - always
      - on_create
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create HTTP profile
  bigip_profile_http:
    name: my_profile
    password: secret
    server: lb.mydomain.com
    insert_xforwarded_for: yes
    redirect_rewrite: all
    state: present
    user: admin
  delegate_to: localhost

- name: Remove HTTP profile
  bigip_profile_http:
    name: my_profile
    state: absent
    server: lb.mydomain.com
    user: admin
    password: secret
  delegate_to: localhost

- name: Add HTTP profile for transparent proxy
  bigip_profile_http:
    name: my_profile
    server: lb.mydomain.com
    user: admin
    proxy_type: transparent
    password: secret
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: Description of the profile.
  returned: changed
  type: string
  sample: My profile
proxy_type:
  description: Specify proxy mode of the profile.
  returned: changed
  type: string
  sample: explicit
insert_xforwarded_for:
  description: Insert X-Forwarded-For-Header.
  returned: changed
  type: bool
  sample: yes
redirect_rewrite:
  description: Rewrite URI that are part of 3xx responses.
  returned: changed
  type: string
  sample: all
encrypt_cookies:
  description: Cookie names to encrypt.
  returned: changed
  type: list
  sample: ['MyCookie1', 'MyCookie2']
dns_resolver:
  description: Configured dns resolver.
  returned: changed
  type: string
  sample: '/Common/FooBar'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import exit_json
    from library.module_utils.network.f5.common import fail_json
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import exit_json
    from ansible.module_utils.network.f5.common import fail_json


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'insertXforwardedFor': 'insert_xforwarded_for',
        'redirectRewrite': 'redirect_rewrite',
        'encryptCookies': 'encrypt_cookies',
        'encryptCookieSecret': 'encrypt_cookie_secret',
        'proxyType': 'proxy_type',
        'explicitProxy': 'explicit_proxy',

    }

    api_attributes = [
        'insertXforwardedFor',
        'description',
        'defaultsFrom',
        'redirectRewrite',
        'encryptCookies',
        'encryptCookieSecret',
        'proxyType',
        'explicitProxy',
    ]

    returnables = [
        'parent',
        'description',
        'insert_xforwarded_for',
        'redirect_rewrite',
        'encrypt_cookies',
        'proxy_type',
        'explicit_proxy',
        'dns_resolver',
    ]

    updatables = [
        'description',
        'insert_xforwarded_for',
        'redirect_rewrite',
        'encrypt_cookies',
        'encrypt_cookie_secret',
        'proxy_type',
        'dns_resolver',
    ]


class ApiParameters(Parameters):
    @property
    def dns_resolver(self):
        if self._values['explicit_proxy'] is None:
            return None
        if 'dnsResolver' in self._values['explicit_proxy']:
            return self._values['explicit_proxy']['dnsResolver']

    @property
    def dns_resolver_address(self):
        if self._values['explicit_proxy'] is None:
            return None
        if 'dnsResolverReference' in self._values['explicit_proxy']:
            return self._values['explicit_proxy']['dnsResolverReference']


class ModuleParameters(Parameters):
    @property
    def proxy_type(self):
        if self._values['proxy_type'] is None:
                return None
        if self._values['proxy_type'] == 'explicit':
            if self.dns_resolver is None or self.dns_resolver == '':
                raise F5ModuleError(
                    'A proxy type cannot be set to {0} without providing DNS resolver.'.format(self._values['proxy_type'])
                )
        return self._values['proxy_type']

    @property
    def dns_resolver(self):
        if self._values['dns_resolver'] is None:
            return None
        if self._values['dns_resolver'] == '' or self._values['dns_resolver'] == 'none':
            return ''
        result = fq_name(self.partition, self._values['dns_resolver'])
        return result

    @property
    def dns_resolver_address(self):
        resolver = self.dns_resolver
        if resolver is None:
            return None
        tmp = resolver.split('/')
        link = dict(link='https://localhost/mgmt/tm/net/dns-resolver/~{0}~{1}'.format(tmp[1], tmp[2]))
        return link

    @property
    def insert_xforwarded_for(self):
        result = flatten_boolean(self._values['insert_xforwarded_for'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def encrypt_cookies(self):
        if self._values['encrypt_cookies'] is None:
            return None
        if self._values['encrypt_cookies'] == [''] or self._values['encrypt_cookies'] == ['none']:
            return list()
        return self._values['encrypt_cookies']

    @property
    def explicit_proxy(self):
        if self.dns_resolver is None:
            return None
        result = dict(
            dnsResolver=self.dns_resolver,
            dnsResolverReference=self.dns_resolver_address
        )
        return result


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
    def explicit_proxy(self):
        result = dict()
        if self._values['dns_resolver'] is not None:
            result['dnsResolver'] = self._values['dns_resolver']
        if self._values['dns_resolver_address'] is not None:
            result['dnsResolverReference'] = self._values['dns_resolver_address']
        if not result:
            return None
        return result


class ReportableChanges(Changes):
    @property
    def insert_xforwarded_for(self):
        if self._values['insert_xforwarded_for'] is None:
            return None
        elif self._values['insert_xforwarded_for'] == 'enabled':
            return 'yes'
        return 'no'


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
                "The parent http profile cannot be changed"
            )

    @property
    def dns_resolver(self):
        if self.want.dns_resolver is None:
            return None
        if self.want.dns_resolver == '':
            if self.have.dns_resolver is None or self.have.dns_resolver == 'none':
                return None
            elif self.have.proxy_type == 'explicit' and self.want.proxy_type is None:
                raise F5ModuleError(
                    "DNS resolver cannot be empty or 'none' if an existing profile proxy type is set to {0}.".format(self.have.proxy_type)
                )
            elif self.have.dns_resolver is not None:
                return self.want.dns_resolver
        if self.have.dns_resolver is None:
            return self.want.dns_resolver

    @property
    def encrypt_cookies(self):
        if self.want.encrypt_cookies is None:
            return None
        if self.have.encrypt_cookies == [] and self.want.encrypt_cookies == []:
            return None
        if self.have.encrypt_cookies is not None and self.want.encrypt_cookies == []:
            return self.want.encrypt_cookies
        if self.have.encrypt_cookies is None:
            return self.want.encrypt_cookies
        if set(self.want.encrypt_cookies) != set(self.have.encrypt_cookies):
                return self.want.encrypt_cookies

    @property
    def encrypt_cookie_secret(self):
        if self.want.encrypt_cookie_secret != self.have.encrypt_cookie_secret:
            if self.want.update_password == 'always':
                result = self.want.encrypt_cookie_secret
                return result


class ModuleManager(object):
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http/{2}".format(
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
            parent=dict(default='/Common/http'),
            description=dict(),
            proxy_type=dict(
                choices=[
                    'reverse',
                    'transparent',
                    'explicit'
                ]
            ),
            dns_resolver=dict(),
            insert_xforwarded_for=dict(type='bool'),
            redirect_rewrite=dict(
                choices=[
                    'none',
                    'all',
                    'matching',
                    'nodes'
                ]
            ),
            encrypt_cookies=dict(type='list'),
            encrypt_cookie_secret=dict(no_log=True),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
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

    client = F5RestClient(**module.params)

    try:
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        exit_json(module, results, client)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        fail_json(module, ex, client)


if __name__ == '__main__':
    main()
