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
module: bigip_profile_oneconnect
short_description: Manage OneConnect profiles on a BIG-IP
description:
  - Manage OneConnect profiles on a BIG-IP.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the OneConnect profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(oneconnect) profile.
    type: str
  source_mask:
    description:
      - Specifies a value that the system applies to the source address to determine
        its eligibility for reuse.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
      - The system applies the value of this setting to the server-side source address to
        determine its eligibility for reuse.
      - A mask of C(0) causes the system to share reused connections across all source
        addresses. A host mask of C(32) causes the system to share only those reused
        connections originating from the same source address.
      - When you are using a SNAT or SNAT pool, the server-side source address is
        translated first and then the OneConnect mask is applied to the translated address.
    type: str
  description:
    description:
      - Description of the profile.
    type: str
  maximum_size:
    description:
      - Specifies the maximum number of connections that the system holds in the
        connection reuse pool.
      - If the pool is already full, then a server-side connection closes after the
        response is completed.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: int
  maximum_age:
    description:
      - Specifies the maximum number of seconds allowed for a connection in the connection
        reuse pool.
      - For any connection with an age higher than this value, the system removes that
        connection from the re-use pool.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: int
  maximum_reuse:
    description:
      - Specifies the maximum number of times that a server-side connection can be reused.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
    type: int
  idle_timeout_override:
    description:
      - Specifies the number of seconds that a connection is idle before the connection
        flow is eligible for deletion.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
      - You may specify a number of seconds for the timeout override.
      - When C(disabled), specifies that there is no timeout override for the connection.
      - When C(indefinite), Specifies that a connection may be idle with no timeout
        override.
    type: str
  limit_type:
    description:
      - When C(none), simultaneous in-flight requests and responses over TCP connections
        to a pool member are counted toward the limit. This is the historical behavior.
      - When C(idle), idle connections will be dropped as the TCP connection limit is
        reached. For short intervals, during the overlap of the idle connection being
        dropped and the new connection being established, the TCP connection limit may
        be exceeded.
      - When C(strict), the TCP connection limit is honored with no exceptions. This means
        that idle connections will prevent new TCP connections from being made until
        they expire, even if they could otherwise be reused.
      - C(strict) is not a recommended configuration except in very special cases with
        short expiration timeouts.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: str
    choices:
      - none
      - idle
      - strict
  share_pools:
    description:
      - Indicates that connections may be shared not only within a virtual server, but
        also among similar virtual servers
      - When C(yes), all virtual servers that use the same OneConnect and other internal
        network profiles can share connections.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: bool
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
'''

EXAMPLES = r'''
- name: Create a OneConnect profile
  bigip_profile_oneconnect:
    name: foo
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
source_mask:
  description: Value that the system applies to the source address to determine its eligibility for reuse.
  returned: changed
  type: str
  sample: 255.255.255.255
description:
  description: Description of the profile.
  returned: changed
  type: str
  sample: My profile
maximum_size:
  description: Maximum number of connections that the system holds in the connection reuse pool.
  returned: changed
  type: int
  sample: 3000
maximum_age:
  description: Maximum number of seconds allowed for a connection in the connection reuse pool.
  returned: changed
  type: int
  sample: 2000
maximum_reuse:
  description: Maximum number of times that a server-side connection can be reused.
  returned: changed
  type: int
  sample: 1000
idle_timeout_override:
  description: The new idle timeout override.
  returned: changed
  type: str
  sample: disabled
limit_type:
  description: New limit type of the profile.
  returned: changed
  type: str
  sample: idle
share_pools:
  description: Share connections among similar virtual servers.
  returned: changed
  type: bool
  sample: yes
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
    from library.module_utils.network.f5.ipaddress import is_valid_ip
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip


class Parameters(AnsibleF5Parameters):
    api_map = {
        'sourceMask': 'source_mask',
        'maxSize': 'maximum_size',
        'maxReuse': 'maximum_reuse',
        'maxAge': 'maximum_age',
        'defaultsFrom': 'parent',
        'limitType': 'limit_type',
        'idleTimeoutOverride': 'idle_timeout_override',
        'sharePools': 'share_pools',
    }

    api_attributes = [
        'sourceMask',
        'maxSize',
        'defaultsFrom',
        'description',
        'limitType',
        'idleTimeoutOverride',
        'maxAge',
        'maxReuse',
        'sharePools',
    ]

    returnables = [
        'description',
        'source_mask',
        'maximum_size',
        'maximum_age',
        'maximum_reuse',
        'limit_type',
        'idle_timeout_override',
        'share_pools',
        'parent',
    ]

    updatables = [
        'description',
        'source_mask',
        'maximum_size',
        'maximum_age',
        'maximum_reuse',
        'limit_type',
        'idle_timeout_override',
        'share_pools',
    ]


class ApiParameters(Parameters):
    @property
    def source_mask(self):
        if self._values['source_mask'] is None:
            return None
        elif self._values['source_mask'] == 'any':
            return 0
        return self._values['source_mask']

    @property
    def idle_timeout_override(self):
        if self._values['idle_timeout_override'] is None:
            return None
        try:
            return int(self._values['idle_timeout_override'])
        except ValueError:
            return self._values['idle_timeout_override']


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def idle_timeout_override(self):
        if self._values['idle_timeout_override'] is None:
            return None
        try:
            return int(self._values['idle_timeout_override'])
        except ValueError:
            return self._values['idle_timeout_override']

    @property
    def source_mask(self):
        if self._values['source_mask'] is None:
            return None
        elif self._values['source_mask'] == 'any':
            return 0
        try:
            int(self._values['source_mask'])
            raise F5ModuleError(
                "'source_mask' must not be in CIDR format."
            )
        except ValueError:
            pass

        if is_valid_ip(self._values['source_mask']):
            return self._values['source_mask']

    @property
    def share_pools(self):
        if self._values['share_pools'] is None:
            return None
        elif self._values['share_pools'] is True:
            return 'enabled'
        return 'disabled'


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
    pass


class ReportableChanges(Changes):
    @property
    def idle_timeout_override(self):
        try:
            return int(self._values['idle_timeout_override'])
        except ValueError:
            return self._values['idle_timeout_override']

    @property
    def share_pools(self):
        if self._values['idle_timeout_override'] is None:
            return None
        elif self._values['idle_timeout_override'] == 'enabled':
            return 'yes'
        elif self._values['idle_timeout_override'] == 'disabled':
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
                "The parent profile cannot be changed"
            )


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect/".format(
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
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/one-connect/{2}".format(
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
            description=dict(),
            parent=dict(),
            source_mask=dict(),
            maximum_size=dict(type='int'),
            maximum_reuse=dict(type='int'),
            maximum_age=dict(type='int'),
            limit_type=dict(
                choices=['none', 'idle', 'strict']
            ),
            idle_timeout_override=dict(),
            share_pools=dict(type='bool'),
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
