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
module: bigip_message_routing_peer
short_description: Manage peers for routing generic message protocol messages
description:
  - Manage peers for routing generic message protocol messages.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the peer to manage.
    type: str
    required: True
  description:
    description:
      - The user defined description of the peer.
    type: str
  type:
    description:
      - Parameter used to specify the type of the peer to manage.
      - Default setting is C(generic) with more options added in future.
    type: str
    choices:
      - generic
    default: generic
  auto_init:
    description:
      - If C(yes), the BIGIP will automatically create outbound connections to the active pool members in the
        specified C(pool) using the configuration of the specified C(transport_config).
      - For auto-initialization to attempt to create a connection, the peer must be included in a route that is attached
        to a router instance. For each router instance that the peer is contained in, a connection will be initiated.
      - The C(auto_init) logic will verify at C(auto_init_interval) if the a connection exists between
        the BIG-IP and the pool members of the pool. If a connection does not exist, it will attempt to reestablish one.
    type: bool
  auto_init_interval:
    description:
      - Specifies the interval that attempts to initiate a connection occur.
      - The default value upon peer object creation, that supplied by the system is C(5000) milliseconds.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  connection_mode:
    description:
      - Specifies how the number of connections per host are to be limited.
    type: str
    choices:
      - per-blade
      - per-client
      - per-peer
      - per-tmm
  number_of_connections:
    description:
      - Specifies the distribution of connections between the BIG-IP and a remote host.
      - The accepted range is between 0 and 65535 inclusive.
    type: int
  pool:
    description:
      - Specifies the name of the pool that messages will be routed towards.
      - The specified pool must be on the same partition as the peer.
    type: str
  ratio:
    description:
      - Specifies the ratio to be used for selection of a peer within a list of peers in a ltm route.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  transport_config:
    description:
      - The name of the ltm virtual or ltm transport-config to use for creating an outgoing connection.
      - The resource must exist on the same partition as the peer object.
    type: str
  partition:
    description:
      - Device partition to create peer object on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the peer exists.
      - When C(absent), ensures the peer is removed.
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
- name: Create a simple peer
  bigip_message_routing_peer:
    name: foobar
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create message routing peer with additional settings
  bigip_message_routing_peer:
    name: foobar
    connection_mode: per-blade
    pool: /baz/bar
    partition: baz
    transport_config: foovirtual
    ratio: 10
    auto_init: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify message routing peer settings
  bigip_message_routing_peer:
    name: foobar
    partition: baz
    ratio: 20
    auto_init_interval: 2000
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove message routing peer
  bigip_message_routing_peer:
    name: foobar
    partition: baz
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
auto_init:
  description: Enables creation of outbound connections to the active pool members.
  returned: changed
  type: bool
  sample: yes
auto_init_interval:
  description: The interval that attempts to initiate a connection occur.
  returned: changed
  type: int
  sample: 2000
connection_mode:
  description: Specifies how the number of connections per host are to be limited.
  returned: changed
  type: str
  sample: per-peer
number_of_connections:
  description: The distribution of connections between the BIG-IP and a remote host.
  returned: changed
  type: int
  sample: 2000
transport_config:
  description: The ltm virtual or ltm transport-config to use for creating an outgoing connection.
  returned: changed
  type: str
  sample: /Common/foobar
description:
  description: The user defined description of the peer.
  returned: changed
  type: str
  sample: Some description
pool:
  description: The name of the pool that messages will be routed towards.
  returned: changed
  type: str
  sample: /Bazbar/foobar
ratio:
  description: The ratio to be used for selection of a peer within a list of peers in a ltm route.
  returned: changed
  type: int
  sample: 500
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
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'autoInitialization': 'auto_init',
        'autoInitializationInterval': 'auto_init_interval',
        'connectionMode': 'connection_mode',
        'numberConnections': 'number_of_connections',
        'transportConfig': 'transport_config',
    }

    api_attributes = [
        'autoInitialization',
        'autoInitializationInterval',
        'connectionMode',
        'description',
        'numberConnections',
        'pool',
        'ratio',
        'transportConfig',
    ]

    returnables = [
        'auto_init',
        'auto_init_interval',
        'connection_mode',
        'number_of_connections',
        'transport_config',
        'description',
        'pool',
        'ratio',
    ]

    updatables = [
        'auto_init',
        'auto_init_interval',
        'connection_mode',
        'number_of_connections',
        'transport_config',
        'description',
        'pool',
        'ratio',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def auto_init(self):
        result = flatten_boolean(self._values['auto_init'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def auto_init_interval(self):
        if self._values['auto_init_interval'] is None:
            return None
        if 0 <= self._values['auto_init_interval'] <= 4294967295:
            return self._values['auto_init_interval']
        raise F5ModuleError(
            "Valid 'auto_init_interval' must be in range 0 - 4294967295 milliseconds."
        )

    @property
    def number_of_connections(self):
        if self._values['number_of_connections'] is None:
            return None
        if 0 <= self._values['number_of_connections'] <= 65535:
            return self._values['number_of_connections']
        raise F5ModuleError(
            "Valid 'number_of_connections' must be in range 0 - 65535."
        )

    @property
    def ratio(self):
        if self._values['ratio'] is None:
            return None
        if 0 <= self._values['ratio'] <= 4294967295:
            return self._values['ratio']
        raise F5ModuleError(
            "Valid 'ratio' must be in range 0 - 4294967295."
        )

    @property
    def pool(self):
        if self._values['pool'] is None:
            return None
        if self._values['pool'] == "":
            return ""
        result = fq_name(self.partition, self._values['pool'])
        return result

    @property
    def transport_config(self):
        if self._values['transport_config'] is None:
            return None
        if self._values['transport_config'] == "":
            return ""
        result = fq_name(self.partition, self._values['transport_config'])
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
    @property
    def auto_init(self):
        result = flatten_boolean(self._values['auto_init'])
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
    def description(self):
        result = cmp_str_with_none(self.want.description, self.have.description)
        return result

    @property
    def transport_config(self):
        result = cmp_str_with_none(self.want.transport_config, self.have.transport_config)
        return result

    @property
    def pool(self):
        result = cmp_str_with_none(self.want.pool, self.have.pool)
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/peer/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/peer/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/peer/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/peer/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/peer/{2}".format(
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
            auto_init=dict(type='bool'),
            auto_init_interval=dict(type='int'),
            connection_mode=dict(
                choices=['per-blade', 'per-client', 'per-peer', 'per-tmm']
            ),
            description=dict(),
            number_of_connections=dict(type='int'),
            pool=dict(),
            ratio=dict(type='int'),
            transport_config=dict(),
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
        self.required_if = [
            ['auto_init', True, ['transport_config']]
        ]
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
