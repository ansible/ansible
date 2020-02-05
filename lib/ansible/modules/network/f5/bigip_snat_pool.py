#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_snat_pool
short_description: Manage SNAT pools on a BIG-IP
description:
  - Manage SNAT pools on a BIG-IP.
version_added: 2.3
options:
  members:
    description:
      - List of members to put in the SNAT pool. When a C(state) of present is
        provided, this parameter is required. Otherwise, it is optional.
      - The members can be either IP addresses, or names of the SNAT translation objects.
    type: list
    aliases:
      - member
  description:
    description:
      - A general description of the SNAT pool, provided by the user for their
        benefit. It is optional.
    type: str
    version_added: 2.9
  name:
    description:
      - The name of the SNAT pool.
    type: str
    required: True
  state:
    description:
      - Whether the SNAT pool should exist or not.
    type: str
    choices:
      - present
      - absent
    default: present
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
notes:
  - When C(bigip_snat_pool) object is removed it also removes any associated C(bigip_snat_translation) objects.
  - This is a BIG-IP behavior not module behavior and it only occurs when the C(bigip_snat_translation) objects
    are also not referenced by another C(bigip_snat_pool).
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
    name: my-snat-pool
    state: present
    members:
      - 10.10.10.10
      - 20.20.20.20
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Change the SNAT pool's members to a single member
  bigip_snat_pool:
    name: my-snat-pool
    state: present
    member: 30.30.30.30
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
    name: johnd
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add the SNAT pool 'my-snat-pool' with a description
  bigip_snat_pool:
    name: my-snat-pool
    state: present
    members:
      - 10.10.10.10
      - 20.20.20.20
    description: A SNAT pool description
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
members:
  description:
    - List of members that are part of the SNAT pool.
  returned: changed and success
  type: list
  sample: "['10.10.10.10']"
'''

import re
import os

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
    from library.module_utils.network.f5.ipaddress import compress_address
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import compress_address
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {}

    updatables = [
        'members',
        'description',
    ]

    returnables = [
        'members',
        'description',
    ]

    api_attributes = [
        'members',
        'description',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    def _clear_member_prefix(self, member):
        result = os.path.basename(member)
        return result

    def _format_member_address(self, member):
        if len(member.split('%')) > 1:
            address, rd = member.split('%')
            if is_valid_ip(address):
                result = '/{0}/{1}%{2}'.format(self.partition, compress_address(address), rd)
                return result
        else:
            if is_valid_ip(member):
                address = '/{0}/{1}'.format(self.partition, member)
                return address
            else:
                # names must start with alphabetic character, and can contain hyphens and underscores and numbers
                # no special characters are allowed
                pattern = re.compile(r'(?!-)[A-Z-].*(?<!-)$', re.IGNORECASE)
                if pattern.match(member):
                    address = '/{0}/{1}'.format(self.partition, member)
                    return address
        raise F5ModuleError(
            'The provided member address: {0} is not a valid IP address or snat translation name'.format(member)
        )

    @property
    def members(self):
        if self._values['members'] is None:
            return None
        result = set()
        for member in self._values['members']:
            member = self._clear_member_prefix(member)
            address = self._format_member_address(member)
            result.update([address])
        return list(result)

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']


class Changes(Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            try:
                result[returnable] = getattr(self, returnable)
            except Exception:
                pass
            result = self._filter_params(result)
        return result


class UsableChanges(Changes):
    pass


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

    @property
    def members(self):
        if self.want.members is None:
            return None
        if set(self.want.members) == set(self.have.members):
            return None
        result = list(set(self.want.members))
        return result

    @property
    def description(self):
        result = cmp_str_with_none(self.want.description, self.have.description)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

        if self.module._diff and self.have:
            result['diff'] = self.make_diff()

        result.update(dict(changed=changed))
        self._announce_deprecations(result)

        return result

    def _grab_attr(self, item):
        result = dict()
        updatables = Parameters.updatables
        for k in updatables:
            if getattr(item, k) is not None:
                result[k] = getattr(item, k)
        return result

    def make_diff(self):
        result = dict(before=self._grab_attr(self.have), after=self._grab_attr(self.want))
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

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

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to create the SNAT pool")
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the SNAT pool")
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snatpool/{2}".format(
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/snatpool/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/snatpool/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snatpool/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snatpool/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        query = '?expandSubcollections=true'
        resp = self.client.api.get(uri + query)
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
            members=dict(
                type='list',
                aliases=['member']
            ),
            description=dict(),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['members']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
