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
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(oneconnect) profile.
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
  description:
    description:
      - Description of the profile.
  maximum_size:
    description:
      - Specifies the maximum number of connections that the system holds in the
        connection reuse pool.
      - If the pool is already full, then a server-side connection closes after the
        response is completed.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
  maximum_age:
    description:
      - Specifies the maximum number of seconds allowed for a connection in the connection
        reuse pool.
      - For any connection with an age higher than this value, the system removes that
        connection from the re-use pool.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
  maximum_reuse:
    description:
      - Specifies the maximum number of times that a server-side connection can be reused.
      - When creating a new profile, if this parameter is not specified, the
        default is provided by the parent profile.
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
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a OneConnect profile
  bigip_profile_oneconnect:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
source_mask:
  description: Value that the system applies to the source address to determine its eligibility for reuse.
  returned: changed
  type: string
  sample: 255.255.255.255
description:
  description: Description of the profile.
  returned: changed
  type: string
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
  type: string
  sample: disabled
limit_type:
  description: New limit type of the profile.
  returned: changed
  type: string
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
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.ipaddress import is_valid_ip
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
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'sourceMask': 'source_mask',
        'maxSize': 'maximum_size',
        'maxReuse': 'maximum_reuse',
        'maxAge': 'maximum_age',
        'defaultsFrom': 'parent',
        'limitType': 'limit_type',
        'idleTimeoutOverride': 'idle_timeout_override',
        'sharePools': 'share_pools'
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
        'sharePools'
    ]

    returnables = [
        'description',
        'source_mask',
        'maximum_size',
        'maximum_age',
        'maximum_reuse',
        'limit_type',
        'idle_timeout_override',
        'share_pools'
    ]

    updatables = [
        'description',
        'source_mask',
        'maximum_size',
        'maximum_age',
        'maximum_reuse',
        'limit_type',
        'idle_timeout_override',
        'share_pools'
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

    def exists(self):
        result = self.client.api.tm.ltm.profile.one_connects.one_connect.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

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
        self.client.api.tm.ltm.profile.one_connects.one_connect.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.ltm.profile.one_connects.one_connect.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.profile.one_connects.one_connect.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.ltm.profile.one_connects.one_connect.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


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
        supports_check_mode=spec.supports_check_mode
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
