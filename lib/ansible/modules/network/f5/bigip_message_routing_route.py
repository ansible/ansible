#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_message_routing_route
short_description: Manages static routes for routing message protocol messages
description:
  - Manages static routes for routing message protocol messages.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the static route.
    required: True
    type: str
  description:
    description:
      - The user defined description of the static route.
    type: str
  type:
    description:
      - Parameter used to specify the type of the route to manage.
      - Default setting is C(generic) with more options added in future.
    type: str
    choices:
      - generic
    default: generic
  src_address:
    description:
      - Specifies the source address of the route.
      - Setting the attribute to an empty string will create a wildcard matching all message source-addresses, which is
        the default when creating a new route.
    type: str
  dst_address:
    description:
      - Specifies the destination address of the route.
      - Setting the attribute to an empty string will create a wildcard matching all message destination-addresses,
        which is the default when creating a new route.
    type: str
  peer_selection_mode:
    description:
      - Specifies the method to use when selecting a peer from the provided list of C(peers).
    type: str
    choices:
      - ratio
      - sequential
  peers:
    description:
      - Specifies a list of ltm messagerouting-peer objects.
      - The specified peer must be on the same partition as the route.
    type: list
  partition:
    description:
      - Device partition to create route object on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the route exists.
      - When C(absent), ensures the route is removed.
    type: str
    choices:
      - present
      - absent
    default: present
notes:
  - Requires BIG-IP >= 14.0.0
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a simple generic route
  bigip_message_routing_route:
    name: foobar
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify a generic route
  bigip_message_routing_route:
    name: foobar
    peers:
      - peer1
      - peer2
    peer_selection_mode: ratio
    src_address: annoying_user
    dst_address: blackhole
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove a generic
  bigip_message_routing_route:
    name: foobar
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The user defined description of the route.
  returned: changed
  type: str
  sample: Some description
src_address:
  description: The source address of the route.
  returned: changed
  type: str
  sample: annyoing_user
dst_address:
  description: The destination address of the route.
  returned: changed
  type: str
  sample: blackhole
peer_selection_mode:
  description: The method to use when selecting a peer.
  returned: changed
  type: str
  sample: ratio
peers:
  description: The list of ltm messagerouting-peer object.
  returned: changed
  type: list
  sample: ['/Common/peer1', '/Common/peer2']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_empty_list
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.compare import cmp_simple_list
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_empty_list
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.compare import cmp_simple_list
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'peerSelectionMode': 'peer_selection_mode',
        'sourceAddress': 'src_address',
        'destinationAddress': 'dst_address',

    }

    api_attributes = [
        'description',
        'peerSelectionMode',
        'peers',
        'sourceAddress',
        'destinationAddress',
    ]

    returnables = [
        'peer_selection_mode',
        'peers',
        'description',
        'src_address',
        'dst_address'
    ]

    updatables = [
        'peer_selection_mode',
        'peers',
        'description',
        'src_address',
        'dst_address'
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def peers(self):
        if self._values['peers'] is None:
            return None
        if is_empty_list(self._values['peers']):
            return ""
        result = [fq_name(self.partition, peer) for peer in self._values['peers']]
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
    def description(self):
        result = cmp_str_with_none(self.want.description, self.have.description)
        return result

    @property
    def dst_address(self):
        result = cmp_str_with_none(self.want.dst_address, self.have.dst_address)
        return result

    @property
    def src_address(self):
        result = cmp_str_with_none(self.want.src_address, self.have.src_address)
        return result

    @property
    def peers(self):
        result = cmp_simple_list(self.want.peers, self.have.peers)
        return result


class BaseManager(object):
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


class GenericModuleManager(BaseManager):
    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/route/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/route/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/route/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/route/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/route/{2}".format(
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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def version_less_than_14(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        return False

    def exec_module(self):
        if self.version_less_than_14():
            raise F5ModuleError('Message routing is not supported on TMOS version below 14.x')
        if self.module.params['type'] == 'generic':
            manager = self.get_manager('generic')
        else:
            raise F5ModuleError(
                "Unknown type specified."
            )
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'generic':
            return GenericModuleManager(**self.kwargs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            src_address=dict(),
            dst_address=dict(),
            peer_selection_mode=dict(
                choices=['ratio', 'sequential']
            ),
            peers=dict(
                type='list'
            ),
            type=dict(
                choices=['generic'],
                default='generic'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
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
