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
module: bigip_device_ha_group
short_description: Manage HA group settings on a BIG-IP system
description:
  - Manage HA group settings on a BIG-IP system.
version_added: 2.8
options:
  name:
    description:
      - Name of the HA group to create/manage.
    type: str
    required: True
  enable:
    description:
      - When set to C(no) the system disables the ha score feature.
    type: bool
    default: yes
  description:
    description:
      - User created HA group description.
    type: str
  active_bonus:
    description:
      - Specifies the extra value to be added to the active unit's ha score.
      - When system creates HA group this value is set to C(10) by the system.
    type: int
  pools:
    description:
      - Specifies pools to contribute to the ha score.
      - The pools must exist on the BIG-IP otherwise the operation will fail.
    type: list
    suboptions:
      pool_name:
        description:
          - The pool name which is used to contribute to the ha score.
          - Referencing pool can be done in the full path format for example, C(/Common/pool_name).
          - When pool is referenced in full path format, the C(partition) parameter is ignored.
        type: str
        required: True
      attribute:
        description:
          - The pool attribute that contributes to the ha score.
        type: str
        choices:
          - percent-up-members
        default: 'percent-up-members'
      weight:
        description:
          - Maximum value the selected pool attribute contributes to the ha score.
        type: int
        required: True
      minimum_threshold:
        description:
          - Below this value the selected pool attribute contributes nothing to the ha score.
          - This value must be greater than the number of pool members present in the pool.
          - In TMOS versions 12.x this attribute is named C(threshold) however it has been deprecated
            in versions 13.x and above.
          - Specifying this attribute in the module running against v12.x will keep the same behavior
            as if C(threshold) option was set.
        type: int
      partition:
        description:
          - Device partition where the specified pool exists.
          - This parameter is ignored if the C(pool_name) is specified in full path format.
        type: str
        default: Common
  trunks:
    description:
      - Specifies trunks to contribute to the ha score.
      - The trunks must exist on the BIG-IP otherwise the operation will fail.
    type: list
    suboptions:
      trunk_name:
        description:
          - The trunk name which is used to contribute to the ha score.
        type: str
        required: True
      attribute:
        description:
          - The trunk attribute that contributes to the ha score.
        type: str
        choices:
          - percent-up-members
        default: 'percent-up-members'
      weight:
        description:
          - Maximum value the selected trunk attribute contributes to the ha score.
        type: int
        required: True
      minimum_threshold:
        description:
          - Below this value the selected trunk attribute contributes nothing to the ha score.
          - This value must be greater than the number of trunk members.
          - In TMOS versions 12.x this attribute is named C(threshold) however it has been deprecated
            in versions 13.x and above.
          - Specifying this attribute in the module running against v12.x will keep the same behavior
            as if C(threshold) option was set.
        type: int
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
    default: present
notes:
  - This module does not support atomic removal of HA group objects.
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create HA group no members, not active
  bigip_device_ha_group:
    name: foo_ha
    description: empty_foo
    active_bonus: 20
    enable: no
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create HA group with pools and trunks
  bigip_device_ha_group:
    name: baz_ha
    description: non_empty_baz
    active_bonus: 15
    pools:
      - pool_name: foopool
        weight: 30
        minimum_threshold: 1
    trunks:
      - trunk_name: footrunk
        weight: 70
        minimum_threshold: 2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create HA group pools using full_path format
  bigip_device_ha_group:
    name: bar_ha
    description: non_empty_bar
    active_bonus: 12
    pools:
      - pool_name: /Baz/foopool
        weight: 30
        minimum_threshold: 1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove HA group
  bigip_device_ha_group:
    name: foo_ha
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: Name of the HA group.
  returned: changed
  type: str
  sample: foo_HA
enable:
  description: Enables or disables HA score feature.
  returned: changed
  type: bool
  sample: yes
description:
  description: User created HA group description.
  returned: changed
  type: str
  sample: Some Group
active_bonus:
  description: The extra value to be added to the active unit's ha score.
  returned: changed
  type: int
  sample: 20
pools:
  description: The pools to contribute to the ha score.
  returned: changed
  type: complex
  contains:
    pool_name:
      description: The pool name which is used to contribute to the ha score.
      returned: changed
      type: str
      sample: foo_pool
    attribute:
      description: The pool attribute that contributes to the ha score.
      returned: changed
      type: str
      sample: percent-up-members
    weight:
      description: Maximum value the selected pool attribute contributes to the ha score.
      returned: changed
      type: int
      sample: 40
    minimum_threshold:
      description: Below this value the selected pool attribute contributes nothing to the ha score.
      returned: changed
      type: int
      sample: 2
    partition:
      description: Device partition where the specified pool exists.
      returned: changed
      type: str
      sample: Common
  sample: hash/dictionary of values
trunks:
  description: The trunks to contribute to the ha score.
  returned: changed
  type: complex
  contains:
    trunk_name:
      description: The trunk name which is used to contribute to the ha score.
      returned: changed
      type: str
      sample: foo_trunk
    attribute:
      description: The trunk attribute that contributes to the ha score.
      returned: changed
      type: str
      sample: percent-up-members
    weight:
      description: Maximum value the selected trunk attribute contributes to the ha score.
      returned: changed
      type: int
      sample: 40
    minimum_threshold:
      description: Below this value the selected trunk attribute contributes nothing to the ha score.
      returned: changed
      type: int
      sample: 2
  sample: hash/dictionary of values
'''

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'activeBonus': 'active_bonus'
    }

    api_attributes = [
        'activeBonus',
        'description',
        'pools',
        'trunks',
        'enabled',
        'disabled',
    ]

    returnables = [
        'name',
        'enabled',
        'disabled',
        'description',
        'active_bonus',
        'pools',
        'trunks',
    ]

    updatables = [
        'enabled',
        'disabled',
        'description',
        'active_bonus',
        'pools',
        'trunks',
    ]


class ApiParameters(Parameters):
    @property
    def enabled(self):
        result = flatten_boolean(self._values['enabled'])
        if result == 'yes':
            return True
        return None

    @property
    def disabled(self):
        result = flatten_boolean(self._values['disabled'])
        if result == 'yes':
            return True
        return None


class ModuleParameters(Parameters):
    @property
    def enabled(self):
        result = flatten_boolean(self._values['enable'])
        if result == 'yes':
            return True
        return None

    @property
    def disabled(self):
        result = flatten_boolean(self._values['enable'])
        if result == 'no':
            return True
        return None

    @property
    def pools(self):
        version_13 = self._is_v13_and_above()
        result = list()
        if self._values['pools'] is None:
            return None
        for item in self._values['pools']:
            pool = dict()
            pool['name'] = fq_name(item['partition'], item['pool_name'])
            pool['weight'] = self._handle_weight(item['weight'])
            if 'attribute' in item:
                pool['attribute'] = item['attribute']
            if 'minimum_threshold' in item:
                if version_13:
                    pool['minimumThreshold'] = item['minimum_threshold']
                else:
                    pool['threshold'] = item['minimum_threshold']
            result.append(self._filter_params(pool))
        return result

    @property
    def trunks(self):
        version_13 = self._is_v13_and_above()
        result = list()
        if self._values['trunks'] is None:
            return None
        for item in self._values['trunks']:
            trunk = dict()
            trunk['name'] = item['trunk_name']
            trunk['weight'] = self._handle_weight(item['weight'])
            if 'attribute' in item:
                trunk['attribute'] = item['attribute']
            if 'minimum_threshold' in item:
                if version_13:
                    trunk['minimumThreshold'] = item['minimum_threshold']
                else:
                    trunk['threshold'] = item['minimum_threshold']
            result.append(self._filter_params(trunk))
        return result

    def _is_v13_and_above(self):
        version = tmos_version(self.client)
        if LooseVersion(version) >= LooseVersion('13.0.0'):
            return True
        return False

    def _handle_weight(self, weight):
        if weight < 10 or weight > 100:
            raise F5ModuleError(
                "Weight value must be in the range: '10 - 100'."
            )
        return weight


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
    returnables = [
        'name',
        'enable',
        'description',
        'active_bonus',
        'pools',
        'trunks',
    ]

    @property
    def enable(self):
        enabled = flatten_boolean(self._values['enabled'])
        disabled = flatten_boolean(self._values['disabled'])
        if enabled == 'yes':
            return 'yes'
        if disabled == 'yes':
            return 'no'
        return None

    @property
    def pools(self):
        result = list()
        if self._values['pools'] is None:
            return None
        for item in self._values['pools']:
            pool = dict()
            pool['pool_name'] = item['name']
            pool['weight'] = item['weight']
            if 'attribute' in item:
                pool['attribute'] = item['attribute']
            if 'minimumThreshold' in item:
                pool['minimum_threshold'] = item['minimumThreshold']
            if 'threshold' in item:
                pool['minimum_threshold'] = item['threshold']
            result.append(pool)
        return result

    @property
    def trunks(self):
        result = list()
        if self._values['trunks'] is None:
            return None
        for item in self._values['trunks']:
            trunk = dict()
            trunk['trunk_name'] = item['name']
            trunk['weight'] = item['weight']
            if 'attribute' in item:
                trunk['attribute'] = item['attribute']
            if 'minimumThreshold' in item:
                trunk['minimum_threshold'] = item['minimumThreshold']
            if 'threshold' in item:
                trunk['minimum_threshold'] = item['threshold']
            result.append(trunk)
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

    def to_tuple(self, items):
        result = []
        for x in items:
            tmp = [(str(k), str(v)) for k, v in iteritems(x)]
            result += tmp
        return result

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None:
            return None
        if have is None:
            return want
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def pools(self):
        result = self._diff_complex_items(self.want.pools, self.have.pools)
        return result

    @property
    def trunks(self):
        result = self._diff_complex_items(self.want.trunks, self.have.trunks)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params, client=self.client)
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/ha-group/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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
        params['name'] = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/sys/ha-group/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/ha-group/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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
        uri = "https://{0}:{1}/mgmt/tm/sys/ha-group/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/ha-group/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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
            name=dict(
                required=True
            ),
            enable=dict(
                type='bool',
                default='yes'
            ),
            description=dict(),
            active_bonus=dict(
                type='int'
            ),
            pools=dict(
                type='list',
                elements='dict',
                options=dict(
                    pool_name=dict(
                        required=True
                    ),
                    attribute=dict(
                        choices=[
                            'percent-up-members'
                        ],
                        default='percent-up-members'
                    ),
                    weight=dict(
                        required=True,
                        type='int'
                    ),
                    minimum_threshold=dict(
                        type='int'
                    ),
                    partition=dict(
                        default='Common',
                        fallback=(env_fallback, ['F5_PARTITION'])
                    )
                )
            ),
            trunks=dict(
                type='list',
                elements='dict',
                options=dict(
                    trunk_name=dict(
                        required=True
                    ),
                    attribute=dict(
                        choices=[
                            'percent-up-members'
                        ],
                        default='percent-up-members'
                    ),
                    weight=dict(
                        required=True,
                        type='int'
                    ),
                    minimum_threshold=dict(
                        type='int'
                    ),
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
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
