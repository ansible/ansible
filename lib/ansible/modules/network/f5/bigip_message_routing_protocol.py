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
module: bigip_message_routing_protocol
short_description: Manage generic message parser profile.
description:
  - Manages generic message parser profile for use with the message routing framework.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the generic parser profile.
    required: True
    type: str
  description:
    description:
      - The user defined description of the generic parser profile.
    type: str
  parent:
    description:
      - The parent template of this parser profile. Once this value has been set, it cannot be changed.
      - When creating a new profile, if this parameter is not specified,
        the default is the system-supplied C(genericmsg) profile.
    type: str
  disable_parser:
    description:
      - When C(yes), the generic message parser will be disabled ignoring all incoming packets and not directly
        send message data.
      - This mode supports iRule script protocol implementations that will generate messages from the incoming transport
        stream and send outgoing messages on the outgoing transport stream.
    type: bool
  max_egress_buffer:
    description:
      - Specifies the maximum size of the send buffer in bytes. If the number of bytes in the send buffer for a
        connection exceeds this value, the generic message protocol will stop receiving outgoing messages from the
        router until the size of the size of the buffer drops below this setting.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  max_msg_size:
    description:
      - Specifies the maximum size of a received message. If a message exceeds this size, the connection will be reset.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  msg_terminator:
    description:
      - The string of characters used to terminate a message. If the message-terminator is not specified,
        the generic message parser will not separate the input stream into messages.
    type: str
  no_response:
    description:
      - When set, matching of responses to requests is disabled.
    type: bool
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
- name: Create a generic parser
  bigip_message_routing_protocol:
    name: foo
    description: 'This is parser'
    no_response: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify a generic parser
  bigip_message_routing_protocol:
    name: foo
    no_response: no
    max_egress_buffer: 10000
    max_msg_size: 2000
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove generic parser
  bigip_message_routing_protocol:
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
  description: The user defined description of the parser profile.
  returned: changed
  type: str
  sample: My description
parent:
  description: The parent template of this parser profile.
  returned: changed
  type: str
  sample: /Common/genericmsg
disable_parser:
  description: Disables generic message parser.
  returned: changed
  type: bool
  sample: yes
max_egress_buffer:
  description: The maximum size of the send buffer in bytes.
  returned: changed
  type: int
  sample: 10000
max_msg_size:
  description: The maximum size of a received message.
  returned: changed
  type: int
  sample: 4000
msg_terminator:
  description: The string of characters used to terminate a message.
  returned: changed
  type: str
  sample: '%%%%'
no_response:
  description: Disables matching of responses to requests.
  returned: changed
  type: bool
  sample: yes
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
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'disableParser': 'disable_parser',
        'maxEgressBuffer': 'max_egress_buffer',
        'maxMessageSize': 'max_msg_size',
        'messageTerminator': 'msg_terminator',
        'noResponse': 'no_response',

    }

    api_attributes = [
        'description',
        'defaultsFrom',
        'disableParser',
        'maxEgressBuffer',
        'maxMessageSize',
        'messageTerminator',
        'noResponse',
    ]

    returnables = [
        'description',
        'parent',
        'disable_parser',
        'max_egress_buffer',
        'max_msg_size',
        'msg_terminator',
        'no_response',
    ]

    updatables = [
        'description',
        'parent',
        'disable_parser',
        'max_egress_buffer',
        'max_msg_size',
        'msg_terminator',
        'no_response',
    ]

    @property
    def no_response(self):
        return flatten_boolean(self._values['no_response'])

    @property
    def disable_parser(self):
        return flatten_boolean(self._values['disable_parser'])


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
    def max_msg_size(self):
        if self._values['max_msg_size'] is None:
            return None
        if 0 <= self._values['max_msg_size'] <= 4294967295:
            return self._values['max_msg_size']
        raise F5ModuleError(
            "Valid 'max_msg_size' must be in range 0 - 4294967295."
        )

    @property
    def max_egress_buffer(self):
        if self._values['max_egress_buffer'] is None:
            return None
        if 0 <= self._values['max_egress_buffer'] <= 4294967295:
            return self._values['max_egress_buffer']
        raise F5ModuleError(
            "Valid 'max_egress_buffer' must be in range 0 - 4294967295."
        )


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
    def parent(self):
        if self.want.parent is None:
            return None
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent router profile cannot be changed."
            )

    @property
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def msg_terminator(self):
        return cmp_str_with_none(self.want.msg_terminator, self.have.msg_terminator)


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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def version_less_than_14(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        return False

    def exec_module(self):
        if self.version_less_than_14():
            raise F5ModuleError('Message routing is not supported on TMOS version below 14.x')
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/protocol/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/protocol/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/protocol/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/protocol/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/message-routing/generic/protocol/{2}".format(
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
            disable_parser=dict(type='bool'),
            max_egress_buffer=dict(type='int'),
            max_msg_size=dict(type='int'),
            msg_terminator=dict(),
            no_response=dict(type='bool'),
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
