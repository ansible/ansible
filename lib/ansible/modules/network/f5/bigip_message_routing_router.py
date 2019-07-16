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
module: bigip_message_routing_router
short_description: Manages router profiles for message-routing protocols
description:
  - Manages router profiles for message-routing protocols.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the router profile.
    required: True
    type: str
  description:
    description:
      - The user defined description of the router profile.
    type: str
  type:
    description:
      - Parameter used to specify the type of the router profile to manage.
      - Default setting is C(generic) with more options added in future.
    type: str
    choices:
      - generic
    default: generic
  parent:
    description:
      - The parent template of this router profile. Once this value has been set, it cannot be changed.
      - The default values are set by the system if not specified and they correspond to the router type created, ie.
        C(/Common/messagerouter) for C(generic) C(type) and so on.
    type: str
  ignore_client_port:
    description:
      - When C(yes), the remote port on clientside connections ie. connections where the peer connected to the BIG-IP
        is ignored when searching for an existing connection.
    type: bool
  inherited_traffic_group:
    description:
      - When set to C(yes) the C(traffic_group) will be inherited from the containing folder. When not specified the
        system sets this to C(no) when creating new router profile.
    type: bool
  traffic_group:
    description:
      - Specifies the traffic-group of the router profile.
      - Setting the C(traffic_group) to an empty string value C("") will cause the device to inherit from containing
        folder, which means the value of C(inherited_traffic_group) on device will be C(yes).
    type: str
  use_local_connection:
    description:
      - If C(yes), the router will route a message to an existing connection on the same TMM as the message was
        received on.
    type: bool
  max_pending_bytes:
    description:
      - The maximum number of bytes worth of pending messages that will be held while waiting for a connection to a
        peer to be created. Once reached, any additional messages to the peer will be flagged as undeliverable
        and returned to the originator.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  max_pending_messages:
    description:
      - The maximum number of pending messages that will be held while waiting for a connection to a peer to be created.
        Once reached, any additional messages to the peer will be flagged as undeliverable and returned
        to the originator.
      - The accepted range is between 0 and 65535 inclusive.
    type: int
  max_retries:
    description:
      - Sets the maximum number of time a message may be resubmitted for rerouting by the C(MR::retry) iRule command.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  mirror:
    description:
      - Enables or disables state mirroring. State mirroring can be used to maintain the same state information in the
        standby unit that is in the active unit.
    type: bool
  mirrored_msg_sweeper_interval:
    description:
      - Specifies the maximum time in milliseconds that a message will be held on the standby device as it waits for
        the active device to route the message.
      - Messages on the standby device held for longer then the configurable sweeper interval, will be dropped.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  routes:
    description:
      - Specifies a list of static routes for the router instance to use.
      - The route must be on the same partition as router profile.
    type: list
  partition:
    description:
      - Device partition to create router profile on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the router profile exists.
      - When C(absent), ensures the router profile is removed.
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
- name: Create a generic router profile
  bigip_message_routing_router:
    name: foo
    max_retries: 10
    ignore_client_port: yes
    routes:
      - /Common/route1
      - /Common/route2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify a generic router profile
  bigip_message_routing_router:
    name: foo
    ignore_client_port: no
    mirror: yes
    mirrored_msg_sweeper_interval: 4000
    traffic_group: /Common/traffic-group-2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove a generic router profile
  bigip_message_routing_router:
    name: foo
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The user defined description of the router profile.
  returned: changed
  type: str
  sample: My description
parent:
  description: The parent template of this router profile.
  returned: changed
  type: str
  sample: /Common/messagerouter
ignore_client_port:
  description: Enables ignoring of the remote port on clientside connections when searching for an existing connection.
  returned: changed
  type: bool
  sample: no
inherited_traffic_group:
  description: Specifies if traffic-group should be inherited from containing folder.
  returned: changed
  type: bool
  sample: yes
traffic_group:
  description: The traffic-group of the router profile.
  returned: changed
  type: str
  sample: /Common/traffic-group-1
use_local_connection:
  description: Enables routing of messages to an existing connection on the same TMM as the message was received on.
  returned: changed
  type: bool
  sample: yes
max_pending_bytes:
  description: The maximum number of bytes worth of pending messages that will be held.
  returned: changed
  type: int
  sample: 10000
max_pending_messages:
  description: The maximum number of pending messages that will be held.
  returned: changed
  type: int
  sample: 64
max_retries:
  description: The maximum number of time a message may be resubmitted for rerouting.
  returned: changed
  type: int
  sample: 10
mirror:
  description: Enables or disables state mirroring.
  returned: changed
  type: bool
  sample: yes
mirrored_msg_sweeper_interval:
  description: The maximum time in milliseconds that a message will be held on the standby device.
  returned: changed
  type: int
  sample: 2000
routes:
  description: The list of static routes for the router instance to use.
  returned: changed
  type: list
  sample: ['/Common/route1', '/Common/route2']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.compare import cmp_simple_list
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.compare import cmp_simple_list
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'useLocalConnection': 'use_local_connection',
        'ignoreClientPort': 'ignore_client_port',
        'inheritedTrafficGroup': 'inherited_traffic_group',
        'maxPendingBytes': 'max_pending_bytes',
        'maxPendingMessages': 'max_pending_messages',
        'maxRetries': 'max_retries',
        'mirroredMessageSweeperInterval': 'mirrored_msg_sweeper_interval',
        'trafficGroup': 'traffic_group',
    }

    api_attributes = [
        'description',
        'useLocalConnection',
        'ignoreClientPort',
        'inheritedTrafficGroup',
        'maxPendingBytes',
        'maxPendingMessages',
        'maxRetries',
        'mirror',
        'mirroredMessageSweeperInterval',
        'trafficGroup',
        'routes',
        'defaultsFrom',
    ]

    returnables = [
        'parent',
        'description',
        'use_local_connection',
        'ignore_client_port',
        'inherited_traffic_group',
        'max_pending_bytes',
        'max_pending_messages',
        'max_retries',
        'mirrored_msg_sweeper_interval',
        'traffic_group',
        'mirror',
        'routes',
    ]

    updatables = [
        'description',
        'use_local_connection',
        'ignore_client_port',
        'inherited_traffic_group',
        'max_pending_bytes',
        'max_pending_messages',
        'max_retries',
        'mirrored_msg_sweeper_interval',
        'traffic_group',
        'mirror',
        'routes',
        'parent',
    ]

    @property
    def ignore_client_port(self):
        return flatten_boolean(self._values['ignore_client_port'])

    @property
    def use_local_connection(self):
        return flatten_boolean(self._values['use_local_connection'])


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def inherited_traffic_group(self):
        result = flatten_boolean(self._values['inherited_traffic_group'])
        if result is None:
            return None
        if result == 'yes':
            return 'true'
        return 'false'

    @property
    def mirror(self):
        result = flatten_boolean(self._values['mirror'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def max_pending_bytes(self):
        if self._values['max_pending_bytes'] is None:
            return None
        if 0 <= self._values['max_pending_bytes'] <= 4294967295:
            return self._values['max_pending_bytes']
        raise F5ModuleError(
            "Valid 'max_pending_bytes' must be in range 0 - 4294967295 bytes."
        )

    @property
    def max_retries(self):
        if self._values['max_retries'] is None:
            return None
        if 0 <= self._values['max_retries'] <= 4294967295:
            return self._values['max_retries']
        raise F5ModuleError(
            "Valid 'max_retries' must be in range 0 - 4294967295."
        )

    @property
    def max_pending_messages(self):
        if self._values['max_pending_messages'] is None:
            return None
        if 0 <= self._values['max_pending_messages'] <= 65535:
            return self._values['max_pending_messages']
        raise F5ModuleError(
            "Valid 'max_pending_messages' must be in range 0 - 65535 messages."
        )

    @property
    def mirrored_msg_sweeper_interval(self):
        if self._values['mirrored_msg_sweeper_interval'] is None:
            return None
        if 0 <= self._values['mirrored_msg_sweeper_interval'] <= 4294967295:
            return self._values['mirrored_msg_sweeper_interval']
        raise F5ModuleError(
            "Valid 'mirrored_msg_sweeper_interval' must be in range 0 - 4294967295 milliseconds."
        )

    @property
    def routes(self):
        if self._values['routes'] is None:
            return None
        if len(self._values['routes']) == 1 and self._values['routes'][0] == "":
            return ""
        result = [fq_name(self.partition, peer) for peer in self._values['routes']]
        return result

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None:
            return None
        if self._values['traffic_group'] == "":
            return ""
        result = fq_name('Common', self._values['traffic_group'])
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
    def mirror(self):
        result = flatten_boolean(self._values['mirror'])
        return result

    @property
    def inherited_traffic_group(self):
        result = self._values['inherited_traffic_group']
        if result == 'true':
            return 'yes'
        if result == 'false':
            return 'no'
        return None


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
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def parent(self):
        if self.want.parent is None:
            return None
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent router profile cannot be changed."
            )

    @property
    def routes(self):
        result = cmp_simple_list(self.want.routes, self.have.routes)
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/router/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/router/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/router/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/router/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/router/{2}".format(
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
            parent=dict(),
            ignore_client_port=dict(type='bool'),
            inherited_traffic_group=dict(type='bool'),
            use_local_connection=dict(type='bool'),
            max_pending_bytes=dict(type='int'),
            max_pending_messages=dict(type='int'),
            max_retries=dict(type='int'),
            mirror=dict(type='bool'),
            mirrored_msg_sweeper_interval=dict(type='int'),
            routes=dict(type='list'),
            traffic_group=dict(),
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
