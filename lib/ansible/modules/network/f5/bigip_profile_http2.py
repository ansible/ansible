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
module: bigip_profile_http2
short_description: Manage HTTP2 profiles on a BIG-IP
description:
  - Manage HTTP2 profiles on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(http2) profile.
    type: str
    default: /Common/http2
  description:
    description:
      - Description of the profile.
    type: str
  streams:
    description:
      - Specifies the number of outstanding concurrent requests that are allowed on a single HTTP/2 connection.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
      - The valid value range is C(1 - 256).
    type: int
  idle_timeout:
    description:
      - Specifies the number of seconds that an HTTP/2 connection is idly left open before being shut down.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
    type: int
  insert_header:
    description:
      - Specifies whether an HTTP header indicating the use of HTTP/2 should be inserted into the request
        that goes to the server.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
    type: bool
  insert_header_name:
    description:
      - Specifies the name of the HTTP header controlled by C(insert_header) parameter.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
    type: str
  enforce_tls_requirements:
    description:
      - Specifies whether the system requires TLS for communications between specified senders and recipients.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
    type: bool
  activation_modes:
    description:
      - Specifies what will cause an incoming connection to be handled as a HTTP/2 connection.
      - The C(alpn) and C(always) are mutually exclusive.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
    type: list
    choices:
      - alpn
      - always
  frame_size:
    description:
      - Specifies the size of data frames, in bytes, that HTTP/2 sends to the client.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
      - The valid value range in bytes is C(1024 - 16384).
    type: int
  write_size:
    description:
      - Specifies the total size of combined data frames, in bytes, that HTTP/2 sends in a single write.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
      - The valid value range in bytes is C(2048 - 32768).
    type: int
  receive_window:
    description:
      - Specifies the way that the HTTP/2 profile performs flow control.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
      - The valid value range in kilobytes is C(16 - 128).
    type: int
  header_table_size:
    description:
      - Specifies the size of the header table, in bytes.
      - When creating a new profile, if this parameter is not specified, the default is provided by the parent profile.
      - The valid value range in bytes is C(0 - 65535).
    type: int
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
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create HTTP2 profile
  bigip_profile_http2:
    name: my_profile
    insert_header: yes
    insert_header_name: FOO
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Remove HTTP profile
  bigip_profile_http2:
    name: my_profile
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add HTTP profile set activation modes
  bigip_profile_http:
    name: my_profile
    activation_modes:
      - always
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: Description of the profile.
  returned: changed
  type: str
  sample: My profile
insert_header_name:
  description: Specifies the name of the HTTP2 header
  returned: changed
  type: str
  sample: X-HTTP2
streams:
  description: The number of outstanding concurrent requests allowed on a single HTTP/2 connection
  returned: changed
  type: int
  sample: 30
enforce_tls_requirements:
  description: pecifies whether the system requires TLS for communications.
  returned: changed
  type: bool
  sample: yes
frame_size:
  description: The size of the data frames
  returned: changed
  type: int
  sample: 30
activation_modes:
  description: Specifies HTTP/2 connection handling modes
  returned: changed
  type: list
  sample: ['always']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import is_empty_list
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import is_empty_list
    from ansible.module_utils.network.f5.common import f5_argument_spec


class Parameters(AnsibleF5Parameters):
    api_map = {
        'activationModes': 'activation_modes',
        'concurrentStreamsPerConnection': 'streams',
        'connectionIdleTimeout': 'idle_timeout',
        'defaultsFrom': 'parent',
        'enforceTlsRequirements': 'enforce_tls_requirements',
        'frameSize': 'frame_size',
        'headerTableSize': 'header_table_size',
        'insertHeader': 'insert_header',
        'insertHeaderName': 'insert_header_name',
        'receiveWindow': 'receive_window',
        'writeSize': 'write_size',
    }

    api_attributes = [
        'activationModes',
        'concurrentStreamsPerConnection',
        'connectionIdleTimeout',
        'description',
        'defaultsFrom',
        'enforceTlsRequirements',
        'frameSize',
        'headerTableSize',
        'insertHeader',
        'insertHeaderName',
        'receiveWindow',
        'writeSize',
    ]

    returnables = [
        'activation_modes',
        'streams',
        'description',
        'idle_timeout',
        'parent',
        'enforce_tls_requirements',
        'frame_size',
        'header_table_size',
        'insert_header',
        'insert_header_name',
        'receive_window',
        'write_size',
    ]

    updatables = [
        'activation_modes',
        'streams',
        'description',
        'idle_timeout',
        'parent',
        'enforce_tls_requirements',
        'frame_size',
        'header_table_size',
        'insert_header',
        'insert_header_name',
        'receive_window',
        'write_size',
    ]


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
    def streams(self):
        streams = self._values['streams']
        if streams is None:
            return None
        if streams < 1 or streams > 256:
            raise F5ModuleError(
                "Streams value must be between 1 and 256"
            )
        return self._values['streams']

    @property
    def receive_window(self):
        window = self._values['receive_window']
        if window is None:
            return None
        if window < 16 or window > 128:
            raise F5ModuleError(
                "Receive Window value must be between 16 and 128"
            )
        return self._values['receive_window']

    @property
    def header_table_size(self):
        header = self._values['header_table_size']
        if header is None:
            return None
        if header < 0 or header > 65535:
            raise F5ModuleError(
                "Header Table Size value must be between 0 and 65535"
            )
        return self._values['header_table_size']

    @property
    def write_size(self):
        write = self._values['write_size']
        if write is None:
            return None
        if write < 2048 or write > 32768:
            raise F5ModuleError(
                "Write Size value must be between 2048 and 32768"
            )
        return self._values['write_size']

    @property
    def frame_size(self):
        frame = self._values['frame_size']
        if frame is None:
            return None
        if frame < 1024 or frame > 16384:
            raise F5ModuleError(
                "Write Size value must be between 1024 and 16384"
            )
        return self._values['frame_size']

    @property
    def enforce_tls_requirements(self):
        result = flatten_boolean(self._values['enforce_tls_requirements'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def insert_header(self):
        result = flatten_boolean(self._values['insert_header'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def activation_modes(self):
        value = self._values['activation_modes']
        if value is None:
            return None
        if is_empty_list(value):
            raise F5ModuleError(
                "Activation Modes cannot be empty, please provide a value"
            )
        return value


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
    def insert_header(self):
        if self._values['insert_header'] is None:
            return None
        elif self._values['insert_header'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def enforce_tls_requirements(self):
        if self._values['enforce_tls_requirements'] is None:
            return None
        elif self._values['enforce_tls_requirements'] == 'enabled':
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
                "The parent profile cannot be changed"
            )

    @property
    def description(self):
        if self.want.description is None:
            return None
        if self.want.description == '':
            if self.have.description is None or self.have.description == "none":
                return None
        if self.want.description != self.have.description:
            return self.want.description


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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http2/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http2/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http2/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http2/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http2/{2}".format(
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
            parent=dict(default='/Common/http2'),
            activation_modes=dict(
                type='list',
                choices=[
                    'alpn', 'always'
                ],
                mutually_exclusive=['always', 'alpn'],
            ),
            description=dict(),
            enforce_tls_requirements=dict(type='bool'),
            streams=dict(type='int'),
            idle_timeout=dict(type='int'),
            frame_size=dict(type='int'),
            header_table_size=dict(type='int'),
            insert_header=dict(type='bool'),
            insert_header_name=dict(),
            receive_window=dict(type='int'),
            write_size=dict(type='int'),
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
