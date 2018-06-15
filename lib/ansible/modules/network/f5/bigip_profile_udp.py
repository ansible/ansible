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
module: bigip_profile_udp
short_description: Manage UDP profiles on a BIG-IP
description:
  - Manage UDP profiles on a BIG-IP. There are a variety of UDP profiles, each with their
    own adjustments to the standard C(udp) profile. Users of this module should be aware
    that many of the adjustable knobs have no module default. Instead, the default is
    assigned by the BIG-IP system itself which, in most cases, is acceptable.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the profile.
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(udp) profile.
  idle_timeout:
    description:
      - Specifies the length of time that a connection is idle (has no traffic) before
        the connection is eligible for deletion.
      - When creating a new profile, if this parameter is not specified, the remote
        device will choose a default value appropriate for the profile, based on its
        C(parent) profile.
      - When a number is specified, indicates the number of seconds that the UDP
        connection can remain idle before the system deletes it.
      - When C(0), or C(indefinite), specifies that UDP connections can remain idle
        indefinitely.
      - When C(immediate), specifies that you do not want the UDP connection to
        remain idle, and that it is therefore immediately eligible for deletion.
  datagram_load_balancing:
    description:
      - Specifies, when C(yes), that the system load balances UDP traffic
        packet-by-packet.
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
- name: Create a TCP profile
  bigip_profile_tcp:
    name: foo
    parent: udp
    idle_timeout: 300
    datagram_load_balancing: no
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: The new parent of the resource.
  returned: changed
  type: string
  sample: udp
idle_timeout:
  description: The new idle timeout of the resource.
  returned: changed
  type: int
  sample: 100
datagram_load_balancing:
  description: The new datagram load balancing setting of the resource.
  returned: changed
  type: bool
  sample: True
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
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'datagramLoadBalancing': 'datagram_load_balancing',
        'idleTimeout': 'idle_timeout',
        'defaultsFrom': 'parent'
    }

    api_attributes = [
        'datagramLoadBalancing',
        'idleTimeout',
        'defaultsFrom'
    ]

    returnables = [
        'datagram_load_balancing',
        'idle_timeout',
        'parent'
    ]

    updatables = [
        'datagram_load_balancing',
        'idle_timeout',
        'parent'
    ]

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        if self._values['idle_timeout'] in ['indefinite', 'immediate']:
            return self._values['idle_timeout']
        return int(self._values['idle_timeout'])


class ApiParameters(Parameters):
    @property
    def datagram_load_balancing(self):
        if self._values['datagram_load_balancing'] is None:
            return None
        if self._values['datagram_load_balancing'] == 'enabled':
            return True
        return False


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
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
    def datagram_load_balancing(self):
        if self._values['datagram_load_balancing'] is None:
            return None
        if self._values['datagram_load_balancing']:
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def datagram_load_balancing(self):
        if self._values['datagram_load_balancing'] is None:
            return None
        if self._values['datagram_load_balancing'] == 'enabled':
            return True
        return False


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
        result = self.client.api.tm.ltm.profile.udps.udp.exists(
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
        self.client.api.tm.ltm.profile.udps.udp.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.ltm.profile.udps.udp.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.profile.udps.udp.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.ltm.profile.udps.udp.load(
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
            parent=dict(),
            idle_timeout=dict(),
            datagram_load_balancing=dict(type='bool'),
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
